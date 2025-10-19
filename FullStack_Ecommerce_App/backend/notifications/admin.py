from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("type", "user", "title", "status", "created_at", "sent_at")
    list_filter = ("type", "status", "created_at")
    search_fields = ("user__username", "title", "message")
    ordering = ("-created_at",)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "order_updates",
        "delivery_updates",
        "promotional_emails",
        "email_notifications",
        "push_notifications",
    )
    list_filter = (
        "order_updates",
        "delivery_updates",
        "promotional_emails",
        "email_notifications",
        "push_notifications",
    )
    search_fields = ("user__username",)
