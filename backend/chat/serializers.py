from rest_framework import serializers
from .models import Document, Conversation, Message


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Document model.
    Used for returning uploaded document metadata.
    """

    class Meta:
        model = Document
        fields = ["id", "title", "file", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Conversation model.
    Used for listing, retrieving, creating, and updating user conversations.
    """

    class Meta:
        model = Conversation
        fields = ["id", "name", "started_at", "updated_at"]
        read_only_fields = ["id", "started_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for the Message model.
    Used for listing and storing conversation messages.
    """

    class Meta:
        model = Message
        fields = ["id", "conversation", "user_message", "bot_reply", "created_at"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "conversation": {"required": True},
        }


# =========================
# Custom request/response serializers for API documentation
# =========================

class ErrorResponseSerializer(serializers.Serializer):
    """
    Generic error response serializer.
    """
    error = serializers.CharField()


class ChatbotSaveRequestSerializer(serializers.Serializer):
    """
    Request body for saving a chatbot exchange.
    """
    message = serializers.CharField(help_text="User message text.")
    bot_reply = serializers.CharField(help_text="Assistant reply text.")
    conversation_id = serializers.IntegerField(help_text="Target conversation ID.")


class ChatbotSaveResponseSerializer(serializers.Serializer):
    """
    Response returned after saving a chatbot exchange.
    """
    message_id = serializers.IntegerField()
    conversation_id = serializers.IntegerField()
    status = serializers.CharField()


class MessageCreateRequestSerializer(serializers.Serializer):
    """
    Request body for creating a message in a conversation.
    """
    conversation_id = serializers.IntegerField(help_text="Target conversation ID.")
    user_message = serializers.CharField(help_text="User message text.")
    bot_reply = serializers.CharField(help_text="Assistant reply text.")


class MessageCreateResponseSerializer(serializers.Serializer):
    """
    Response returned after creating a message.
    """
    message_id = serializers.IntegerField()
    status = serializers.CharField()


class UploadedDocumentItemSerializer(serializers.Serializer):
    """
    Single successfully uploaded document item.
    """
    document_id = serializers.IntegerField()
    document_title = serializers.CharField()


class UploadErrorItemSerializer(serializers.Serializer):
    """
    Single upload error item.
    """
    file = serializers.CharField()
    error = serializers.CharField()


class DocumentUploadResponseSerializer(serializers.Serializer):
    """
    Response returned after upload processing.
    """
    uploaded_documents = UploadedDocumentItemSerializer(many=True)
    errors = UploadErrorItemSerializer(many=True)


class DeleteDocumentResponseSerializer(serializers.Serializer):
    """
    Response returned after deleting a single document.
    """
    message = serializers.CharField()
    deleted_vector_entries = serializers.IntegerField()


class DeleteAllDocumentsResponseSerializer(serializers.Serializer):
    """
    Response returned after deleting all user documents.
    """
    message = serializers.CharField()
    deleted_documents = serializers.IntegerField()
    deleted_vector_entries = serializers.IntegerField()