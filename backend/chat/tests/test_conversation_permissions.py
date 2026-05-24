import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from chat.models import Conversation, Message

User = get_user_model()

@pytest.mark.django_db
def test_user_cannot_read_messages_from_another_users_conversation():
    owner = User.objects.create_user(
        email="owner@example.com",
        password="StrongPass123",
    )
    intruder = User.objects.create_user(
        email="intruder@example.com",
        password="StrongPass123",
    )

    conversation = Conversation.objects.create(
        user=owner,
        name="Owner conversation",
    )

    Message.objects.create(
        conversation=conversation,
        user_message="Private user message",
        bot_reply="Private bot reply",
    )

    client = APIClient()
    client.force_authenticate(user=intruder)

    response = client.get(
        "/api/v1/messages/",
        {"conversation_id": conversation.id},
    )

    assert response.status_code == 404
