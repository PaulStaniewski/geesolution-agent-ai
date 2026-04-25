import os

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import AdminSite
from django.shortcuts import redirect
from django.urls import path

from .haystack_utils.document_store import document_store
from .models import Conversation, Document, Message


class CustomAdminSite(AdminSite):
    """
    Custom admin site for GeeBOT with additional maintenance actions.
    """
    site_header = "GeeBOT Admin"
    site_title = "GeeBOT Panel"
    index_title = "Welcome to the GeeBOT Admin Panel"

    def get_urls(self):
        """
        Add custom admin URLs.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "wipe-all/",
                self.admin_view(self.wipe_all_view),
                name="custom_admin_wipe_all",
            ),
        ]
        return custom_urls + urls

    def wipe_all_view(self, request):
        """
        Delete all uploaded files, vector documents, and database records.
        """
        data_dir = os.path.join(settings.MEDIA_ROOT, "chat", "data")
        deleted_files = 0

        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                file_path = os.path.join(data_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files += 1
                    except Exception:
                        pass

        all_docs = document_store.filter_documents()
        doc_ids = [doc.id for doc in all_docs] if all_docs else []

        if doc_ids:
            document_store.delete_documents(document_ids=doc_ids)

        msg_count = Message.objects.count()
        conv_count = Conversation.objects.count()
        doc_count = Document.objects.count()

        Message.objects.all().delete()
        Conversation.objects.all().delete()
        Document.objects.all().delete()

        messages.success(
            request,
            (
                f"Deleted {doc_count} documents, {conv_count} conversations, "
                f"{msg_count} messages, {deleted_files} files from disk, "
                f"and {len(doc_ids)} documents from PgVector."
            ),
        )
        return redirect("/admin/")


custom_admin_site = CustomAdminSite(name="custom_admin")


class MessageInline(admin.TabularInline):
    """
    Inline view of messages inside a conversation.
    """
    model = Message
    extra = 0
    fields = (
        "conversation_user_email",
        "short_user_message",
        "short_bot_reply",
        "created_at",
    )
    readonly_fields = (
        "conversation_user_email",
        "short_user_message",
        "short_bot_reply",
        "created_at",
    )
    show_change_link = True

    @admin.display(description="User")
    def conversation_user_email(self, obj):
        if obj.conversation and obj.conversation.user:
            return obj.conversation.user.email
        return "-"

    @admin.display(description="User message")
    def short_user_message(self, obj):
        if not obj.user_message:
            return "-"
        return obj.user_message[:80] + ("..." if len(obj.user_message) > 80 else "")

    @admin.display(description="Bot reply")
    def short_bot_reply(self, obj):
        if not obj.bot_reply:
            return "-"
        return obj.bot_reply[:80] + ("..." if len(obj.bot_reply) > 80 else "")


@admin.register(Conversation, site=custom_admin_site)
class ConversationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Conversation model.
    """
    list_display = (
        "id",
        "name",
        "user_email",
        "started_at",
        "updated_at",
        "message_count",
    )
    search_fields = (
        "id",
        "name",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    list_filter = ("started_at", "updated_at")
    ordering = ("-updated_at", "-started_at")
    fields = ("name", "user", "started_at", "updated_at")
    readonly_fields = ("started_at", "updated_at")
    autocomplete_fields = ("user",)
    list_select_related = ("user",)
    inlines = [MessageInline]

    @admin.display(description="User", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email if obj.user else "-"

    @admin.display(description="Message Count")
    def message_count(self, obj):
        return obj.messages.count()


@admin.register(Document, site=custom_admin_site)
class DocumentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Document model.
    """
    list_display = (
        "id",
        "title",
        "user_email",
        "file_name",
        "uploaded_at",
    )
    search_fields = (
        "id",
        "title",
        "user__email",
        "user__first_name",
        "user__last_name",
        "file",
    )
    list_filter = ("uploaded_at", "user")
    ordering = ("-uploaded_at",)
    fields = ("title", "file", "user", "uploaded_at")
    readonly_fields = ("uploaded_at",)
    autocomplete_fields = ("user",)
    list_select_related = ("user",)

    @admin.display(description="User", ordering="user__email")
    def user_email(self, obj):
        return obj.user.email if obj.user else "-"

    @admin.display(description="File")
    def file_name(self, obj):
        if not obj.file:
            return "-"
        return os.path.basename(obj.file.name)


@admin.register(Message, site=custom_admin_site)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for Message model.
    """
    list_display = (
        "id",
        "conversation_id_display",
        "conversation_user_email",
        "short_user_message",
        "short_bot_reply",
        "created_at",
    )
    search_fields = (
        "id",
        "user_message",
        "bot_reply",
        "conversation__id",
        "conversation__name",
        "conversation__user__email",
        "conversation__user__first_name",
        "conversation__user__last_name",
    )
    list_filter = ("created_at", "conversation")
    ordering = ("-created_at",)
    fields = ("conversation", "user_message", "bot_reply", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("conversation",)
    list_select_related = ("conversation", "conversation__user")

    @admin.display(description="Conversation ID", ordering="conversation__id")
    def conversation_id_display(self, obj):
        return obj.conversation.id if obj.conversation else "-"

    @admin.display(description="User", ordering="conversation__user__email")
    def conversation_user_email(self, obj):
        if obj.conversation and obj.conversation.user:
            return obj.conversation.user.email
        return "-"

    @admin.display(description="User Message")
    def short_user_message(self, obj):
        if not obj.user_message:
            return "-"
        return obj.user_message[:80] + ("..." if len(obj.user_message) > 80 else "")

    @admin.display(description="Bot Reply")
    def short_bot_reply(self, obj):
        if not obj.bot_reply:
            return "-"
        return obj.bot_reply[:80] + ("..." if len(obj.bot_reply) > 80 else "")