from django.urls import path, include
from rest_framework.routers import DefaultRouter
from product import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'ratings', views.RatingViewSet, basename='rating')
router.register(r'reports', views.ReportViewSet, basename='report')

# Nested routes for ratings
product_router = DefaultRouter()
product_router.register(r'ratings', views.RatingViewSet, basename='product-rating')

urlpatterns = [
    path('', include(router.urls)),
    path('products/<int:product_pk>/', include(product_router.urls)),
]