from .models import StripeModel, BillingAddress, OrderModel
from django.http import Http404
from rest_framework import status, viewsets, permissions
from django.contrib.auth.models import User
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView  # for login page
from django.contrib.auth.hashers import check_password
from django.shortcuts import get_object_or_404
from .serializers import (
    UserSerializer,
    UserRegisterTokenSerializer,
    CardsListSerializer,
    BillingAddressSerializer,
    AllOrdersListSerializer,
)

from rest_framework.decorators import action
from rest_framework.views import APIView


# register user
class UserRegisterView(APIView):
    """To Register the User (kept as function-style view)

    Note: We're keeping registration as a separate endpoint; user CRUD is handled by
    UserViewSet below.
    """

    def post(self, request, format=None):
        data = request.data  # holds username and password (in dictionary)
        username = data.get("username", "")
        email = data.get("email", "")

        if username == "" or email == "":
            return Response(
                {"detail": "username or email cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        check_username = User.objects.filter(username=username).exists()
        check_email = User.objects.filter(email=email).exists()

        if check_username:
            return Response(
                {"detail": "A user with that username already exist!"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if check_email:
            return Response(
                {"detail": "A user with that email address already exist!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(data.get("password", "")),
        )
        serializer = UserRegisterTokenSerializer(user, many=False)
        return Response(serializer.data)