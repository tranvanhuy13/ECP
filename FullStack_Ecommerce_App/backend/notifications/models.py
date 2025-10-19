from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ("ORDER_CONFIRMATION", "Order Confirmation"),
        ("DELIVERY_UPDATE", "Delivery Update"),
        ("PROMOTIONAL", "Promotional"),
        ("REMINDER", "Reminder"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("SENT", "Sent"),
        ("FAILED", "Failed"),
        ("READ", "Read"),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    related_order = models.ForeignKey(
        "account.OrderModel", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type} - {self.title} ({self.user.username})"

    def mark_as_sent(self):
        self.status = "SENT"
        self.sent_at = timezone.now()
        self.save()

    def mark_as_read(self):
        self.status = "READ"
        self.read_at = timezone.now()
        self.save()


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    order_updates = models.BooleanField(default=True)
    delivery_updates = models.BooleanField(default=True)
    promotional_emails = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification Preferences for {self.user.username}"
