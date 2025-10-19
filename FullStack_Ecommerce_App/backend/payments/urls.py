from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payments import views

router = DefaultRouter()
router.register(r"payments", views.PaymentViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]
