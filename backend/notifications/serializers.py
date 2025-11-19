from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "title",
            "message",
            "status",
            "created_at",
            "scheduled_for",
            "sent_at",
            "read_at",
            "related_order",
        ]
        read_only_fields = ["status", "created_at", "sent_at", "read_at"]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "order_updates",
            "delivery_updates",
            "promotional_emails",
            "email_notifications",
            "push_notifications",
        ]
