from django.urls import path, include
from account import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"addresses", views.BillingAddressViewSet, basename="address")
router.register(r"cards", views.CardViewSet, basename="card")
router.register(r"orders", views.OrderViewSet, basename="order")

urlpatterns = [
    path("register/", views.UserRegisterView.as_view(), name="register-page"),
    path("login/", views.MyTokenObtainPairView.as_view(), name="login-page"),
    path("", include(router.urls)),
]
