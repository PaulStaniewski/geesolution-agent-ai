from hashlib import sha256
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Message, Conversation, Document
from .serializers import (
    DocumentSerializer,
    ConversationSerializer,
    MessageSerializer,
    ErrorResponseSerializer,
    ChatbotSaveRequestSerializer,
    ChatbotSaveResponseSerializer,
    MessageCreateRequestSerializer,
    MessageCreateResponseSerializer,
    DocumentUploadResponseSerializer,
    DeleteDocumentResponseSerializer,
    DeleteAllDocumentsResponseSerializer,
)
from .haystack_utils.document_store import document_store
import os
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .ingest.document_parsing import convert_file_to_documents
from chat.haystack_utils.embedder import embed_texts_batch
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone

ALLOWED_EXTS = {".pdf", ".txt", ".docx", ".md"}
MAX_FILE_BYTES = 25 * 1024 * 1024  # 25MB

@extend_schema(
    tags=["Chat"],
)
class ChatbotResponse(APIView):
    """
    Legacy API view for manually saving completed chatbot exchanges.

    Current primary chat flow:
    - FastAPI SSE endpoint streams the response.
    - Haystack runtime persists the user message and assistant reply.

    This endpoint is kept for backward compatibility and manual/fallback saves.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    @extend_schema(
        summary="Save chatbot exchange",
        description=(
            "Legacy endpoint. The current streaming flow persists messages in the Haystack runtime."
        ),
        request=ChatbotSaveRequestSerializer,
        responses={
            200: ChatbotSaveResponseSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Missing or invalid request data.",
            ),
            404: OpenApiResponse(
                description="Conversation not found or not owned by the user.",
            ),
        },
    )
    def post(self, request):
        user_message = request.data.get("message", "").strip()
        bot_reply = request.data.get("bot_reply", "").strip()
        conversation_id = request.data.get("conversation_id")

        if not conversation_id:
            return Response(
                {"error": "conversation_id is missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user_message:
            return Response(
                {"error": "message is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not bot_reply:
            return Response(
                {"error": "bot_reply is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user,
        )

        serializer = MessageSerializer(
            data={
                "conversation": conversation.id,
                "user_message": user_message,
                "bot_reply": bot_reply,
            }
        )

        if not serializer.is_valid():
            return Response(
                {"error": "Invalid message payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        message = serializer.save()
        conversation.updated_at = message.created_at
        conversation.save(update_fields=["updated_at"])

        return Response(
            {
                "message_id": message.id,
                "conversation_id": conversation.id,
                "status": "saved",
            },
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Messages"],
)
@extend_schema(
    tags=["Messages"],
)
class MessageListView(APIView):
    """
    API view for retrieving messages within a specific conversation.

    Current primary chat flow:
    - FastAPI SSE endpoint streams assistant responses.
    - Haystack runtime persists user messages and assistant replies.

    This API view is mainly used for:
    - retrieving conversation history,
    - legacy/manual message creation flows.

    Methods:
    - GET: Returns all messages in a conversation (if owned by the user).
    - POST: Legacy/manual message creation endpoint.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    @extend_schema(
        summary="List messages in conversation",
        description=(
            "Returns all messages for a conversation owned by the "
            "authenticated user."
        ),
        parameters=[
            OpenApiParameter(
                name="conversation_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Conversation ID.",
            )
        ],
        responses={
            200: MessageSerializer(many=True),
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="conversation_id query parameter is required.",
            ),
            404: OpenApiResponse(
                description="Conversation not found or not owned by the user.",
            ),
        },
    )
    def get(self, request):
        conversation_id = request.GET.get("conversation_id")

        if not conversation_id:
            return Response(
                {"error": "conversation_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user,
        )

        messages = Message.objects.filter(
            conversation=conversation
        ).order_by("created_at")

        serializer = MessageSerializer(messages, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Create message in conversation (legacy)",
        description=(
            "Legacy/manual endpoint for creating message entries in an "
            "existing conversation.\n\n"
            "The current production chat flow persists messages directly "
            "inside the Haystack runtime during SSE streaming."
        ),
        request=MessageCreateRequestSerializer,
        responses={
            201: MessageCreateResponseSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Required request data is missing or invalid.",
            ),
            404: OpenApiResponse(
                description="Conversation not found or not owned by the user.",
            ),
        },
    )
    def post(self, request):
        user_message = request.data.get("user_message", "").strip()
        bot_reply = request.data.get("bot_reply", "").strip()
        conversation_id = request.data.get("conversation_id")

        if not conversation_id:
            return Response(
                {"error": "conversation_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user_message:
            return Response(
                {"error": "user_message is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not bot_reply:
            return Response(
                {"error": "bot_reply is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = get_object_or_404(
            Conversation,
            id=conversation_id,
            user=request.user,
        )

        serializer = MessageSerializer(
            data={
                "conversation": conversation.id,
                "user_message": user_message,
                "bot_reply": bot_reply,
            }
        )

        if not serializer.is_valid():
            return Response(
                {"error": "Invalid message payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        message = serializer.save()

        conversation.updated_at = message.created_at
        conversation.save(update_fields=["updated_at"])

        return Response(
            {
                "message_id": message.id,
                "status": "created",
            },
            status=status.HTTP_201_CREATED,
        )



def F_EQ(field: str, value):
    return {"field": field, "operator": "==", "value": value}

def F_AND(*conds):
    return {"operator": "AND", "conditions": list(conds)}

def _delete_by_filters(filters, batch_size: int = 500) -> None:
    """
    Delete documents selected by filters, in batches, using ID-only deletion.
    Compatible with stores that accept only `document_ids` or legacy `ids`.
    """
    docs = document_store.filter_documents(filters=filters) or []
    if not docs:
        return

    ids = []
    for d in docs:
        # handle haystack Document and dict-like
        did = getattr(d, "id", None)
        if did is None and isinstance(d, dict):
            did = d.get("id") or (d.get("meta") or {}).get("id")
        if did:
            ids.append(str(did))

    # chunked delete to avoid huge SQL IN (...)
    for i in range(0, len(ids), batch_size):
        chunk = ids[i:i + batch_size]
        # Prefer modern signature
        try:
            document_store.delete_documents(document_ids=chunk)
        except TypeError:
            # Fallback to legacy signature (older integrations)
            document_store.delete_documents(ids=chunk)

def delete_docs_by_digest(digest: str, corpus: str = "haystack") -> None:
    _delete_by_filters(
        F_AND(
            F_EQ("meta.corpus", corpus),
            F_EQ("meta.digest", digest),
        )
    )

def docs_exist_for_digest(digest: str, corpus: str = "haystack") -> bool:
    found = document_store.filter_documents(
        filters=F_AND(
            F_EQ("meta.corpus", corpus),
            F_EQ("meta.digest", digest),
        )
    )
    return bool(found)

def delete_docs_by_file_sha(file_sha256: str, user_id: int) -> None:
    _delete_by_filters(
        F_AND(
            F_EQ("meta.corpus", "user"),
            F_EQ("meta.namespace", f"user:{user_id}"),
            F_EQ("meta.file_sha256", file_sha256),
        )
    )

@extend_schema(
    tags=["Documents"],
)
class DocumentUploadView(APIView):
    """
    Multi-file upload view:
    - Saves files to FS + DB record
    - Converts → cleans → splits into Haystack Documents
    - Adds consistent metadata (corpus / namespace / file_sha256 / user_id)
    - Embeds all chunks using a singleton embedder (batch processing)
    - Writes to PgVector store
    - Idempotency rules:
        * For Haystack .md files (with digest): remove previous chunks by digest
        * For user files: deduplicate by (file_sha256 + user_id)
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload one or more documents",
        description=(
            "Uploads one or more files, stores them in the database and filesystem, "
            "converts them into document chunks, generates embeddings, and writes them "
            "to the PgVector-backed document store."
        ),
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "format": "binary",
                        },
                        "description": "One or more files to upload.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional title applied to uploaded files.",
                    },
                },
                "required": ["files"],
            }
        },
        responses={
            201: DocumentUploadResponseSerializer,
            400: OpenApiResponse(
                response=DocumentUploadResponseSerializer,
                description="Upload failed or no valid files were provided.",
            ),
        },
    )
    def post(self, request):
        uploaded_files = request.FILES.getlist("files")

        if not uploaded_files:
            return Response(
                {
                    "uploaded_documents": [],
                    "errors": [
                        {
                            "file": "",
                            "error": "No files uploaded.",
                        }
                    ],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        success = []
        errors = []

        for f in uploaded_files:
            ext = os.path.splitext(f.name)[1].lower()

            if ext not in ALLOWED_EXTS:
                errors.append(
                    {
                        "file": f.name,
                        "error": f"Unsupported extension {ext}",
                    }
                )
                continue

            if f.size > MAX_FILE_BYTES:
                errors.append(
                    {
                        "file": f.name,
                        "error": "File too large (>25MB)",
                    }
                )
                continue

            title = request.data.get("title") or f.name
            doc_rec = Document.objects.create(title=title, file=f, user=request.user)
            file_path = doc_rec.file.path

            try:
                h = sha256()
                with open(file_path, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                        h.update(chunk)
                file_sha = h.hexdigest()

            except Exception as e:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass

                doc_rec.delete()
                errors.append(
                    {
                        "file": f.name,
                        "error": f"SHA256 error: {e}",
                    }
                )
                continue

            try:
                split_docs = convert_file_to_documents(file_path, f.name, request.user.id)

                if not split_docs:
                    raise ValueError("Empty document after conversion")

                sample_meta = split_docs[0].meta
                corpus = sample_meta.get("corpus", "user")
                digest = sample_meta.get("digest")
                is_haystack_corpus = corpus == "haystack"

                if is_haystack_corpus and digest:
                    if docs_exist_for_digest(digest, "haystack"):
                        delete_docs_by_digest(digest, "haystack")

                    for d in split_docs:
                        d.meta.setdefault("corpus", "haystack")
                else:
                    delete_docs_by_file_sha(file_sha, request.user.id)

                    for d in split_docs:
                        d.meta.setdefault("corpus", "user")
                        d.meta.setdefault("namespace", f"user:{request.user.id}")
                        d.meta.setdefault("file_name", f.name)
                        d.meta.setdefault("file_sha256", file_sha)
                        d.meta["user_id"] = str(request.user.id)

                texts = [d.content for d in split_docs]
                embs = embed_texts_batch(texts)

                for d, e in zip(split_docs, embs):
                    d.embedding = e

                document_store.write_documents(split_docs)

                success.append(
                    {
                        "document_id": doc_rec.id,
                        "document_title": doc_rec.title,
                    }
                )

            except Exception as e:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass

                doc_rec.delete()
                errors.append(
                    {
                        "file": f.name,
                        "error": str(e),
                    }
                )

        status_code = status.HTTP_201_CREATED if success else status.HTTP_400_BAD_REQUEST

        return Response(
            {
                "uploaded_documents": success,
                "errors": errors,
            },
            status=status_code,
        )



def list_global_haystack_documents():
    docs = document_store.filter_documents(
        filters=F_EQ("meta.corpus", "haystack")
    ) or []

    seen = {}
    for d in docs:
        meta = d.meta or {}
        file_name = meta.get("file_name")

        if not file_name:
            continue

        if file_name not in seen:
            seen[file_name] = {
                "id": f"haystack:{file_name}",
                "title": meta.get("title") or file_name,
                "file_name": file_name,
                "corpus": "haystack",
                "doc_type": meta.get("doc_type") or "docs",
                "source_url": meta.get("source_url"),
                "uploaded_at": None,
                "is_deletable": False,
            }

    return sorted(seen.values(), key=lambda x: x["file_name"])


@extend_schema(
    tags=["Documents"],
)
class DocumentListView(APIView):
    """
    API view to list global Haystack documents and documents uploaded by the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer

    @extend_schema(
        summary="List available documents",
        description=(
            "Returns global Haystack documentation documents and documents uploaded "
            "by the authenticated user."
        ),
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        global_documents = list_global_haystack_documents()

        user_documents_qs = Document.objects.filter(user=request.user).order_by("-uploaded_at")
        user_documents = DocumentSerializer(user_documents_qs, many=True).data

        normalized_user_documents = []
        for doc in user_documents:
            normalized_user_documents.append(
                {
                    **doc,
                    "file_name": doc.get("title"),
                    "corpus": "user",
                    "doc_type": "other",
                    "source_url": None,
                    "is_deletable": True,
                }
            )

        return Response(
            global_documents + normalized_user_documents,
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Documents"],
)
class DocumentDeleteView(APIView):
    """
    API view to delete a single document belonging to the authenticated user.

    Methods:
    - DELETE /api/v1/documents/<doc_id>/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer

    @extend_schema(
        summary="Delete single document",
        description="Deletes one document owned by the authenticated user and removes related vector entries.",
        responses={
            200: DeleteDocumentResponseSerializer,
            400: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="doc_id is required.",
            ),
            404: OpenApiResponse(
                description="Document not found.",
            ),
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
            ),
        },
    )
    def delete(self, request, doc_id=None):
        try:
            if not doc_id:
                return Response(
                    {"error": "doc_id is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            document = get_object_or_404(Document, id=doc_id, user=request.user)
            file_path = document.file.path if document.file else None
            file_name = os.path.basename(file_path) if file_path else document.title

            file_sha = None
            if file_path and os.path.exists(file_path):
                h = sha256()
                with open(file_path, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                        h.update(chunk)
                file_sha = h.hexdigest()

            deleted_vectors = 0
            if file_sha:
                matched_docs = document_store.filter_documents(
                    filters=F_AND(
                        F_EQ("meta.corpus", "user"),
                        F_EQ("meta.namespace", f"user:{request.user.id}"),
                        F_EQ("meta.file_sha256", file_sha),
                    )
                ) or []
                deleted_vectors = len(matched_docs)

                delete_docs_by_file_sha(file_sha, request.user.id)

            if file_path:
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass

            document.delete()

            return Response(
                {
                    "message": f"Deleted document '{file_name}'.",
                    "deleted_vector_entries": deleted_vectors,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Documents"],
)
class DocumentDeleteAllView(APIView):
    """
    API view to delete all documents belonging to the authenticated user.

    Methods:
    - DELETE /api/v1/documents/delete-all/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer

    @extend_schema(
        summary="Delete all user documents",
        description="Deletes all documents owned by the authenticated user and removes related vector entries.",
        responses={
            200: DeleteAllDocumentsResponseSerializer,
            500: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unexpected server error.",
            ),
        },
    )
    def delete(self, request):
        try:
            documents = Document.objects.filter(user=request.user)
            deleted_count = 0
            deleted_vectors = 0
            errors = []

            for document in documents:
                try:
                    file_path = document.file.path if document.file else None

                    file_sha = None
                    if file_path and os.path.exists(file_path):
                        h = sha256()
                        with open(file_path, "rb") as fh:
                            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                                h.update(chunk)
                        file_sha = h.hexdigest()

                    if file_sha:
                        matched_docs = document_store.filter_documents(
                            filters=F_AND(
                                F_EQ("meta.corpus", "user"),
                                F_EQ("meta.namespace", f"user:{request.user.id}"),
                                F_EQ("meta.file_sha256", file_sha),
                            )
                        ) or []
                        deleted_vectors += len(matched_docs)

                        delete_docs_by_file_sha(file_sha, request.user.id)

                    if file_path:
                        try:
                            os.remove(file_path)
                        except FileNotFoundError:
                            pass

                    document.delete()
                    deleted_count += 1

                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    errors.append(
                        {
                            "document_id": document.id,
                            "title": document.title,
                            "error": str(e),
                        }
                    )

            return Response(
                {
                    "message": f"Deleted {deleted_count} documents.",
                    "deleted_documents": deleted_count,
                    "deleted_vector_entries": deleted_vectors,
                    "errors": errors,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

@extend_schema(
    tags=["Conversations"],
)
class ConversationListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    @extend_schema(
        summary="List conversations",
        description="Returns all conversations owned by the authenticated user.",
        responses={200: ConversationSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create conversation",
        description="Creates a new conversation for the authenticated user.",
        request=ConversationSerializer,
        responses={201: ConversationSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user).order_by("-started_at")

    def perform_create(self, serializer):
        now = timezone.now()
        serializer.save(user=self.request.user, updated_at=now)


@extend_schema(
    tags=["Conversations"],
)
class ConversationDetailView(RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, or deleting a specific conversation.
    - GET: Retrieves the details of a specific conversation by ID (if it belongs to the user).
    - PUT/PATCH: Updates the conversation (only if it belongs to the user).
    - DELETE: Deletes the conversation (only if it belongs to the user).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    @extend_schema(
        summary="Retrieve conversation",
        description="Returns a single conversation owned by the authenticated user.",
        responses={200: ConversationSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update conversation",
        description="Updates a conversation owned by the authenticated user.",
        request=ConversationSerializer,
        responses={200: ConversationSerializer},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update conversation",
        description="Partially updates a conversation owned by the authenticated user.",
        request=ConversationSerializer,
        responses={200: ConversationSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Delete conversation",
        description="Deletes a conversation owned by the authenticated user.",
        responses={204: None},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

