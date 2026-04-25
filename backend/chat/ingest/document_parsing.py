import os, re, hashlib, json
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

import yaml
from haystack import Document as HDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.converters import (
    PDFMinerToDocument,
    TextFileToDocument,
    DOCXToDocument,
    MarkdownToDocument,
)

# ============================
# Regex utilities
# ============================

# Matches <!-- digest:xxxxxxxx --> appended at the end of scraper-generated files
_DIGEST_RE = re.compile(r"<!--\s*digest:([a-f0-9]{16,64})\s*-->\s*$", re.IGNORECASE)

# Matches YAML front matter block at the top of Markdown files
MD_FM_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


# ============================
# Helpers
# ============================

def _sha256_bytes(data: bytes) -> str:
    """Compute SHA256 hex digest for arbitrary bytes."""
    return hashlib.sha256(data).hexdigest()


def _read_text(path: str, encoding: str = "utf-8") -> str:
    """Read text file with fallback for minor encoding issues."""
    with open(path, "r", encoding=encoding, errors="ignore") as f:
        return f.read()


def _parse_md_front_matter_and_body(text: str) -> Tuple[Dict, str]:
    """
    Extract YAML front matter and Markdown body.
    
    Returns:
        (meta_dict, body_text)
        or ({}, full_text) if front matter is missing.
    """
    m = MD_FM_REGEX.match(text)
    if not m:
        return {}, text.strip()

    fm_raw, body = m.group(1), m.group(2)
    try:
        meta = yaml.safe_load(fm_raw) or {}
    except Exception:
        meta = {}
    return meta, body.strip()


def _extract_digest(text: str, meta: Dict) -> Optional[str]:
    """
    Extract stable digest for scraped documentation pages.

    Priority:
    1) digest field inside front matter
    2) <!-- digest:... --> marker at the end of the file
    """
    d = meta.get("digest")
    if isinstance(d, str) and len(d) >= 16:
        return d.lower()

    m = _DIGEST_RE.search(text)
    if m:
        return m.group(1).lower()

    return None


def _remove_pdf_artifacts(text: str) -> str:
    """
    Performs light cleanup for PDF-extracted text.
    Avoids aggressive transformations that may corrupt content.
    """
    text = re.sub(r"cid:\d+", "", text)
    ligatures = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}
    for k, v in ligatures.items():
        text = text.replace(k, v)
    text = text.replace("ǳ", "dz")
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def _infer_doc_kind_and_version(base_title: str, front_matter: Dict) -> Tuple[str, Optional[str]]:
    """
    Decide doc_type (docs/reference/category/other) and optional doc_version.

    Priority:
    1) file name prefix (docs__/reference__/category__)
    2) source_url path (/docs/, /reference/, /reference/category/)
    3) fallback: other

    Also detects scraper prefix like "2.18__something" and stores doc_version="2.18".
    """
    # version prefix like "2.18__foo"
    m = re.match(r"^(\d+\.\d+(?:\.\d+)?)__.+$", base_title)
    doc_version = m.group(1) if m else None

    # normalize name without version prefix
    normalized = base_title
    if doc_version:
        normalized = base_title.split("__", 1)[1]

    # 1) by file prefix
    if normalized.startswith("docs__"):
        return "docs", doc_version
    if normalized.startswith("reference__"):
        return "reference", doc_version
    if normalized.startswith("category__"):
        return "category", doc_version

    # 2) by source_url path
    url = (front_matter.get("source_url") or "").lower()
    if "/reference/category/" in url:
        return "category", doc_version
    if "/reference/" in url:
        return "reference", doc_version
    if "/docs/" in url:
        return "docs", doc_version

    return "other", doc_version


# ============================
# Splitting configuration
# ============================

@dataclass
class ConvertConfig:
    split_by: str = "word"
    split_length: int = 300
    split_overlap: int = 60


DEFAULT_CFG = ConvertConfig()


# ============================
# Main conversion pipeline
# ============================

def convert_file_to_documents(
    file_path: str,
    file_name: str,
    user_id: str,
    corpus_hint: Optional[str] = None,
    cfg: ConvertConfig = DEFAULT_CFG,
) -> List[HDocument]:
    """
    Convert any supported file (MD, PDF, TXT, DOCX) into Haystack Documents.

    Generates consistent metadata for:
        * corpus: "haystack" or "user"
        * namespace
        * title, source_url, scraped_at
        * digest (scraped MD) or file_sha256 (user uploads)
        * chunk_index
        * nav_level_1/2/3/nav_path (scraped docs only)
    """
    ext = os.path.splitext(file_path)[1].lower()
    base_title = os.path.splitext(file_name)[0]

    # Prepare variables
    docs: List[HDocument]
    raw_text: Optional[str] = None
    front_matter: Dict = {}
    digest: Optional[str] = None
    body: str = ""

    # ===========================================
    # Markdown branch
    # ===========================================
    if ext == ".md":
        raw_text = _read_text(file_path)
        front_matter, body = _parse_md_front_matter_and_body(raw_text)
        digest = _extract_digest(raw_text, front_matter)

        # Scraped Haystack docs → special handling
        is_scraped = (front_matter.get("source") == "haystack_docs") or bool(digest)

        if is_scraped:
            docs = [HDocument(content=body, meta={})]
            corpus = corpus_hint or "haystack"
            namespace = "haystack"
        else:
            # User-uploaded MD → standard converter
            result = MarkdownToDocument().run(sources=[file_path])
            docs = result["documents"]
            corpus = corpus_hint or "user"
            namespace = f"user:{user_id}"

            # Reconstruct body for hashing consistency
            body = "\n\n".join(d.content for d in docs) if docs else ""

    # ===========================================
    # Other supported formats
    # ===========================================
    elif ext == ".pdf":
        result = PDFMinerToDocument().run([file_path])
        docs = result["documents"]
        corpus = corpus_hint or "user"
        namespace = f"user:{user_id}"

    elif ext == ".txt":
        result = TextFileToDocument().run([file_path])
        docs = result["documents"]
        corpus = corpus_hint or "user"
        namespace = f"user:{user_id}"

    elif ext == ".docx":
        result = DOCXToDocument().run([file_path])
        docs = result["documents"]
        corpus = corpus_hint or "user"
        namespace = f"user:{user_id}"

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # ============================
    # Document type classification
    # ============================
    kind, doc_version = _infer_doc_kind_and_version(base_title, front_matter)

    # ============================
    # Base metadata (before splitting)
    # ============================
    for d in docs:
        base_meta = {
            "file_name": file_name,
            "title": front_matter.get("title") or base_title,
            "corpus": corpus,
            "namespace": namespace,
            "doc_type": kind,
            "doc_version": doc_version, 
        }

        # User ID only for user-uploaded documents
        if corpus != "haystack":
            base_meta["user_id"] = str(user_id)

        # Front matter fields from the scraper
        if front_matter:
            for key in ("source", "source_url", "scraped_at"):
                if key in front_matter and front_matter[key]:
                    base_meta[key] = front_matter[key]

            # Navigation metadata for sidebar grouping
            for key in ("nav_level_1", "nav_level_2", "nav_level_3", "nav_path"):
                if key in front_matter and front_matter[key]:
                    base_meta[key] = front_matter[key]

        if digest:
            base_meta["digest"] = digest

        d.meta.update(base_meta)

    # ============================
    # Basic cleanup
    # ============================
    for d in docs:
        d.content = _remove_pdf_artifacts(d.content)

    cleaned = DocumentCleaner(
        remove_empty_lines=True,
        remove_extra_whitespaces=True,
    ).run(documents=docs)["documents"]

    # ============================
    # Splitting
    # ============================
    splitter = DocumentSplitter(
        split_by=cfg.split_by,
        split_length=cfg.split_length,
        split_overlap=cfg.split_overlap,
    )
    split_docs = splitter.run(documents=cleaned)["documents"]

    # ============================
    # Deduplication hashing
    # ============================
    if digest:
        file_sha = None
    else:
        with open(file_path, "rb") as fh:
            file_sha = _sha256_bytes(fh.read())

    # ============================
    # Assign stable IDs + chunk metadata
    # ============================
    for i, d in enumerate(split_docs):
        d.meta["chunk_index"] = i

        if digest:
            d.meta["digest"] = digest
            d.id = f"{digest}:{i}"
        else:
            d.meta["file_sha256"] = file_sha

            if corpus == "user":
                d.id = f"{namespace}:{file_sha}:{i}"
            else:
                d.id = f"{file_sha}:{i}"

    # ============================
    # Logging
    # ============================
    total_chars = sum(len(d.content) for d in cleaned)
    print(
        f"[INGEST] {file_name}: ~{total_chars} chars → {len(split_docs)} chunks | "
        f"corpus={corpus} ns={namespace}"
    )

    if split_docs:
        keys = [
            "title", "corpus", "namespace", "digest", "file_sha256",
            "chunk_index", "source_url", "nav_level_1",
            "nav_level_2", "nav_level_3", "nav_path",
        ]
        meta_example = {k: v for k, v in split_docs[0].meta.items() if k in keys}
        print(f"[INGEST] META example: {json.dumps(meta_example, ensure_ascii=False)}")
    return split_docs
