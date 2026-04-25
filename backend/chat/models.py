from django.db import models
from django.conf import settings
class Document(models.Model):
    """
    Represents a document uploaded to the system by a specific user.

    Fields:
    - user (ForeignKey): The user who uploaded the document.
    - title (str): The title of the document.
    - file (FileField): The uploaded file, stored in the 'chat/data/' directory.
    - uploaded_at (DateTime): The timestamp when the document was uploaded.

    Methods:
    - __str__(): Returns the title of the document as a string representation.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='chat/data/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations"
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name or f"Conversation #{self.id}"

    def update_last_message_time(self):
        last_message = self.messages.order_by("-created_at").first()
        if last_message:
            self.updated_at = last_message.created_at
            self.save(update_fields=["updated_at"])



class Message(models.Model):
    """
    Represents a message exchanged in a conversation.

    Fields:
    - conversation (ForeignKey): The conversation to which this message belongs.
    - user_message (TextField): The message sent by the user.
    - bot_reply (TextField): The chatbot's reply to the user message.
    - created_at (DateTime): The timestamp when the message was created.

    Methods:
    - __str__(): Returns a short representation of the message with the timestamp.
    """
    conversation = models.ForeignKey(
        Conversation, 
        related_name="messages", 
        on_delete=models.CASCADE, 
        null=False,  # Field cannot be null
        blank=False  # Field cannot be blank
    )
    user_message = models.TextField()
    bot_reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """
        Returns a string representation of the message, including the conversation it belongs to 
        and the timestamp when it was created.
        """
        return f"Message in {self.conversation} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
