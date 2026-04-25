"""
URL routes for the chat application API.
"""

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    # Chat
    path("chat/", views.ChatbotResponse.as_view(), name="chatbot-response"),

    # Documents
    path("upload/", views.DocumentUploadView.as_view(), name="document-upload"),
    path("documents/", views.DocumentListView.as_view(), name="document-list"),
    path("documents/delete-all/", views.DocumentDeleteAllView.as_view(), name="document-delete-all"),
    path("documents/<int:doc_id>/", views.DocumentDeleteView.as_view(), name="document-delete"),

    # Conversations
    path("conversations/", views.ConversationListCreateView.as_view(), name="conversation-list-create"),
    path("conversations/<int:pk>/", views.ConversationDetailView.as_view(), name="conversation-detail"),

    # Messages
    path("messages/", views.MessageListView.as_view(), name="message-list"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)