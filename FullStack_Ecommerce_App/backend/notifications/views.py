from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer
from .services import NotificationService


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationService.get_user_notifications(self.request.user)

    def list(self, request):
        unread_only = request.query_params.get("unread_only", False)asdasdasdasdasd
        queryset = NotificationService.get_user_notifications(
            request.user, unread_only=unread_only
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        try:
            notification = NotificationService.mark_notification_as_read(
                pk, request.user
            )
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
        except Notification.DoesNotExist:
            return Response(
                {"detail": "Notification not found"}, status=status.HTTP_404_NOT_FOUND
            )


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def list(self, request):
        preference, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(preference)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        preference, created = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        serializer = self.get_serializer(preference, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
