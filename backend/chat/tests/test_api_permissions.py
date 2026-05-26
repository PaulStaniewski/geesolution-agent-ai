import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from chat.models import Conversation, Message, Document
from django.core.files.uploadedfile import SimpleUploadedFile

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

@pytest.mark.django_db
def test_user_cannot_delete_another_users_conversation():
    owner = User.objects.create_user(
        email="owner2@example.com",
        password="StrongPass123",
    )
    intruder = User.objects.create_user(
        email="intruder2@example.com",
        password="StrongPass123",
    )

    conversation = Conversation.objects.create(
        user=owner,
        name="Owner conversation",
    )

    client = APIClient()
    client.force_authenticate(user=intruder)

    response = client.delete(f"/api/v1/conversations/{conversation.id}/")

    assert response.status_code == 404
    assert Conversation.objects.filter(id=conversation.id).exists()

@pytest.mark.django_db
def test_authenticated_user_can_read_own_conversation_messages():
    user = User.objects.create_user(
        email="reader@example.com",
        password="StrongPass123",
    )

    conversation = Conversation.objects.create(
        user=user,
        name="My conversation",
    )

    Message.objects.create(
        conversation=conversation,
        user_message="Hello bot",
        bot_reply="Hello user",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        "/api/v1/messages/",
        {"conversation_id": conversation.id},
    )

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["user_message"] == "Hello bot"
    assert response.data[0]["bot_reply"] == "Hello user"


@pytest.mark.django_db
def test_user_cannot_rename_another_users_conversation():
    owner = User.objects.create_user(
        email="rename-owner@example.com",
        password="StrongPass123",
    )
    intruder = User.objects.create_user(
        email="rename-intruder@example.com",
        password="StrongPass123",
    )

    conversation = Conversation.objects.create(
        user=owner,
        name="Original name",
    )

    client = APIClient()
    client.force_authenticate(user=intruder)

    response = client.patch(
        f"/api/v1/conversations/{conversation.id}/",
        {"name": "Hacked name"},
        format="json",
    )

    assert response.status_code == 404

    conversation.refresh_from_db()
    assert conversation.name == "Original name"


@pytest.mark.django_db
def test_user_can_rename_own_conversation():
    user = User.objects.create_user(
        email="rename-owner-ok@example.com",
        password="StrongPass123",
    )

    conversation = Conversation.objects.create(
        user=user,
        name="Old name",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        f"/api/v1/conversations/{conversation.id}/",
        {"name": "New name"},
        format="json",
    )

    assert response.status_code == 200

    conversation.refresh_from_db()
    assert conversation.name == "New name"    

@pytest.mark.django_db
def test_unauthenticated_user_cannot_list_conversations():
    client = APIClient()

    response = client.get("/api/v1/conversations/")

    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_unauthenticated_user_cannot_fetch_messages():
    client = APIClient()

    response = client.get("/api/v1/messages/")

    assert response.status_code in (401, 403)    

@pytest.mark.django_db
def test_document_upload_requires_authentication():
    client = APIClient()

    test_file = SimpleUploadedFile(
        "test.txt",
        b"hello world",
        content_type="text/plain",
    )

    response = client.post(
        "/api/v1/upload/",
        {"files": [test_file]},
        format="multipart",
    )

    assert response.status_code in (401, 403)

@pytest.mark.django_db
def test_document_list_requires_authentication():
    client = APIClient()

    response = client.get("/api/v1/documents/")

    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_user_only_sees_own_documents():
    owner = User.objects.create_user(
        email="doc-owner@example.com",
        password="StrongPass123",
    )

    intruder = User.objects.create_user(
        email="doc-intruder@example.com",
        password="StrongPass123",
    )

    Document.objects.create(
        user=owner,
        title="Private document",
    )

    client = APIClient()
    client.force_authenticate(user=intruder)

    response = client.get("/api/v1/documents/")

    assert response.status_code == 200

    titles = [doc["title"] for doc in response.data]

    assert "Private document" not in titles