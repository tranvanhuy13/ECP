from .models import Product, Rating, Report
from rest_framework import status, viewsets, permissions
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .serializers import ProductSerializer, RatingSerializer, ReportSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Avg


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing products.
    """

    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]


class RatingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product ratings.
    """

    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        product_id = self.kwargs.get("product_pk")
        if product_id:
            return Rating.objects.filter(product_id=product_id)
        return Rating.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        product_id = self.kwargs.get("product_pk")
        product = get_object_or_404(Product, id=product_id)

        # Check if user already rated this product
        if Rating.objects.filter(user=self.request.user, product=product).exists():
            raise ValidationError("You have already rated this product")

        serializer.save(user=self.request.user, product=product)

    @action(detail=True, methods=["post"])
    def update_rating(self, request, pk=None):
        rating = self.get_object()
        serializer = self.get_serializer(rating, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product and seller reports.
    """

    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_staff:
            return Report.objects.filter(user=self.request.user)
        return Report.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ["update", "partial_update", "change_status"]:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        report = self.get_object()
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff can update report status"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(report, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
