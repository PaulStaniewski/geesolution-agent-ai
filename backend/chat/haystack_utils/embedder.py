# chat/haystack_utils/embedder.py
"""
Embedder singleton dla Haystack 2.x:
- Text: SentenceTransformersTextEmbedder (pojedynczy string)
- Batch: SentenceTransformersDocumentEmbedder (lista tekstów / Documentów)
- Preload przy starcie (Django.ready / FastAPI.on_startup)
- Kontrola wymiaru vs PgVector (opcjonalnie rygorystyczna)
"""

import os
import threading
from typing import List, Sequence, Optional

# 👇 UCISZAMY paski postępu/tqdm globalnie (dotyczy sentence-transformers)
os.environ.setdefault("TQDM_DISABLE", "1")  # respektowane przez tqdm
# (opcjonalnie) gdyby jakaś warstwa mimo to pokazywała progress:
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from haystack.components.embedders import (
    SentenceTransformersTextEmbedder,
    SentenceTransformersDocumentEmbedder,
)
from haystack import Document as HDocument

# === Konfiguracja przez ENV ===
DEFAULT_MODEL = os.getenv("EMBEDDER_MODEL_NAME", "sentence-transformers/all-mpnet-base-v2")  # 768-dim
MAX_BATCH = int(os.getenv("EMBEDDER_MAX_BATCH", "32"))
DIM_CHECK_STRICT = os.getenv("EMBEDDER_DIM_CHECK_STRICT", "true").lower() == "true"

# === Singletony i lock ===
_lock = threading.Lock()
_text_embedders: dict[str, SentenceTransformersTextEmbedder] = {}
_doc_embedders: dict[str, SentenceTransformersDocumentEmbedder] = {}
_dim_checked_for_model: set[str] = set()


def _disable_progress_if_supported(emb) -> None:
    """
    Niektóre wersje komponentów mają atrybuty sterujące paskiem postępu.
    Jeśli istnieją – wyłączamy.
    """
    for attr in ("show_progress_bar", "progress_bar"):
        if hasattr(emb, attr):
            try:
                setattr(emb, attr, False)
            except Exception:
                pass


def _new_text_embedder(model_name: str) -> SentenceTransformersTextEmbedder:
    emb = SentenceTransformersTextEmbedder(model=model_name)
    _disable_progress_if_supported(emb)
    # warm_up może wewnętrznie robić encode; TQDM_DISABLE powinno uciszyć progress
    emb.warm_up()
    return emb


def _new_doc_embedder(model_name: str) -> SentenceTransformersDocumentEmbedder:
    emb = SentenceTransformersDocumentEmbedder(model=model_name)
    _disable_progress_if_supported(emb)
    emb.warm_up()
    return emb


def _ensure_dim_matches(model_name: str) -> None:
    """
    Jednorazowo na model sprawdza, czy wymiar vektora zgadza się z PgVectorDocumentStore.embedding_dimension.
    Uwaga: pierwsze wywołanie może wykonać minimalny embed (bez progress barów).
    """
    if model_name in _dim_checked_for_model:
        return

    try:
        te = get_text_embedder(model_name)
        # Minimalny embed do sprawdzenia wymiaru
        vec = te.run("dim-check")["embedding"]
        dim = len(vec)

        try:
            # opóźniony import by uniknąć cyklicznych zależności
            from chat.haystack_utils.document_store import document_store
            expected = getattr(document_store, "embedding_dimension", None)
        except Exception:
            expected = None

        if expected and expected != dim:
            msg = (
                f"[EMBEDDER] Dimension mismatch: embedder={dim}, pgvector={expected}. "
                f"Zmień EMBEDDER_MODEL_NAME na model o wymiarze {expected} (np. all-mpnet-base-v2 dla 768) "
                f"albo zaktualizuj konfigurację PgVector."
            )
            if DIM_CHECK_STRICT:
                raise ValueError(msg)
            else:
                print("WARN:", msg)
    finally:
        _dim_checked_for_model.add(model_name)


# === API: pobieranie singletonów ===
def get_text_embedder(model_name: Optional[str] = None) -> SentenceTransformersTextEmbedder:
    name = model_name or DEFAULT_MODEL
    with _lock:
        emb = _text_embedders.get(name)
        if emb is None:
            emb = _new_text_embedder(name)
            _text_embedders[name] = emb
    return emb


def get_document_embedder(model_name: Optional[str] = None) -> SentenceTransformersDocumentEmbedder:
    name = model_name or DEFAULT_MODEL
    with _lock:
        emb = _doc_embedders.get(name)
        if emb is None:
            emb = _new_doc_embedder(name)
            _doc_embedders[name] = emb
    return emb


def preload_embedder(model_name: Optional[str] = None) -> None:
    """
    Wywołaj przy starcie serwisu, aby rozgrzać modele i sprawdzić wymiar.
    Dzięki temu „pierwszy request” nie zobaczy inicjalizacji.
    """
    name = model_name or DEFAULT_MODEL
    get_text_embedder(name)
    get_document_embedder(name)
    _ensure_dim_matches(name)


# === Wygodne helpery ===
def embed_text(text: str, model_name: Optional[str] = None) -> List[float]:
    """
    Zwraca wektor dla pojedynczego tekstu (query).
    """
    name = model_name or DEFAULT_MODEL
    _ensure_dim_matches(name)  # no-op po pierwszym razie
    te = get_text_embedder(name)
    return te.run(text)["embedding"]


def embed_texts_batch(texts: Sequence[str], model_name: Optional[str] = None) -> List[List[float]]:
    """
    Batch embedding listy stringów z automatycznym porcjowaniem na MAX_BATCH.
    Realizacja przez DocumentEmbedder (stabilne API w Haystack 2.x).
    """
    name = model_name or DEFAULT_MODEL
    _ensure_dim_matches(name)
    de = get_document_embedder(name)

    out: List[List[float]] = []
    n = len(texts)
    if n == 0:
        return out

    for i in range(0, n, MAX_BATCH):
        chunk_texts = list(texts[i:i + MAX_BATCH])
        docs = [HDocument(content=t) for t in chunk_texts]
        res = de.run(docs)  # embeddings zapisane w .embedding
        docs_out = res["documents"]
        out.extend([d.embedding for d in docs_out])
    return out


def embed_documents_batch(docs: Sequence[HDocument], model_name: Optional[str] = None) -> List[HDocument]:
    """
    Batch embedding istniejących Documentów (embedding trafia w .embedding).
    Zwraca listę tych samych Documentów (dla wygody).
    """
    name = model_name or DEFAULT_MODEL
    _ensure_dim_matches(name)
    de = get_document_embedder(name)

    out_docs: List[HDocument] = []
    n = len(docs)
    if n == 0:
        return out_docs

    for i in range(0, n, MAX_BATCH):
        chunk_docs = list(docs[i:i + MAX_BATCH])
        res = de.run(chunk_docs)
        out_docs.extend(res["documents"])
    return out_docs
