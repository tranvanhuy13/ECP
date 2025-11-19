from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Notification, NotificationPreference


class NotificationService:
    @staticmethod
    def create_notification(
        user, notification_type, title, message, scheduled_for=None, related_order=None
    ):
        """Create a new notification"""
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            scheduled_for=scheduled_for,
            related_order=related_order,
        )

        # Send notification based on user preferences
        preferences = NotificationPreference.objects.get_or_create(user=user)[0]

        if notification_type == "ORDER_CONFIRMATION" and preferences.order_updates:
            NotificationService.send_email_notification(notification)
        elif notification_type == "DELIVERY_UPDATE" and preferences.delivery_updates:
            NotificationService.send_email_notification(notification)
        elif notification_type == "PROMOTIONAL" and preferences.promotional_emails:
            NotificationService.send_email_notification(notification)

        return notification

    @staticmethod
    def send_email_notification(notification):
        """Send email notification"""
        context = {
            "title": notification.title,
            "message": notification.message,
            "user": notification.user,
        }

        email_html = render_to_string("notifications/email_template.html", context)

        try:
            send_mail(
                subject=notification.title,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.user.email],
                html_message=email_html,
            )
            notification.mark_as_sent()
        except Exception as e:
            notification.status = "FAILED"
            notification.save()
            raise e

    @staticmethod
    def send_order_confirmation(order):
        """Send order confirmation notification"""
        message = f"""Thank you for your order #{order.id}!
        Order Total: ${order.total_price}
        Expected Delivery: {order.expected_delivery_date}
        
        You will receive updates about your order status."""

        return NotificationService.create_notification(
            user=order.user,
            notification_type="ORDER_CONFIRMATION",
            title=f"Order Confirmation #{order.id}",
            message=message,
            related_order=order,
        )

    @staticmethod
    def send_delivery_update(order, status_update):
        """Send delivery status update notification"""
        message = f"""Update for your order #{order.id}:
        Status: {status_update}
        
        Track your order for more details."""

        return NotificationService.create_notification(
            user=order.user,
            notification_type="DELIVERY_UPDATE",
            title=f"Delivery Update for Order #{order.id}",
            message=message,
            related_order=order,
        )

    @staticmethod
    def send_promotional_notification(user, title, message, scheduled_for=None):
        """Send promotional notification"""
        return NotificationService.create_notification(
            user=user,
            notification_type="PROMOTIONAL",
            title=title,
            message=message,
            scheduled_for=scheduled_for,
        )

    @staticmethod
    def send_reminder(user, title, message, scheduled_for):
        """Send reminder notification"""
        return NotificationService.create_notification(
            user=user,
            notification_type="REMINDER",
            title=title,
            message=message,
            scheduled_for=scheduled_for,
        )

    @staticmethod
    def mark_notification_as_read(notification_id, user):
        """Mark a notification as read"""
        notification = Notification.objects.get(id=notification_id, user=user)
        notification.mark_as_read()
        return notification

    @staticmethod
    def get_user_notifications(user, unread_only=False):
        """Get user's notifications"""
        queryset = Notification.objects.filter(user=user)
        if unread_only:
            queryset = queryset.filter(status__in=["PENDING", "SENT"])
        return queryset
