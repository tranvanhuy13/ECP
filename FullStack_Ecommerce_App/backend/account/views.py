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


# login user (customizing it so that we can see fields like username, email etc as a response
# from server, otherwise it will only provide access and refresh token)
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        serializer = UserRegisterTokenSerializer(self.user).data

        for k, v in serializer.items():
            data[k] = v

        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# list all the cards (of currently logged in user only)
class CardViewSet(viewsets.ModelViewSet):
    serializer_class = CardsListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return StripeModel.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def mask(self, request, pk=None):
        """Return masked card details (last 4 digits) for a card"""
        card = get_object_or_404(StripeModel, id=pk, user=request.user)
        last4 = card.card_number[-4:] if card.card_number else None
        return Response({"last4": last4})


# get user details
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_permissions(self):
        # Allow list/retrieve to authenticated users, updates only by owners or admin
        if self.action in ["list"]:
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ["retrieve"]:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """Get current authenticated user's data"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def change_password(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        if request.user.id != user.id and not request.user.is_staff:
            return Response(
                {"details": "Permission Denied."}, status=status.HTTP_403_FORBIDDEN
            )
        data = request.data
        old = data.get("old_password")
        new = data.get("new_password")
        if not old or not new:
            return Response(
                {"detail": "Both old_password and new_password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not check_password(old, user.password):
            return Response(
                {"detail": "Old password does not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.password = make_password(new)
        user.save()
        return Response({"detail": "Password changed successfully."})

    def update(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        if request.user.id != user.id and not request.user.is_staff:
            return Response(
                {"details": "Permission Denied."}, status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        user.username = data.get("username", user.username)
        user.email = data.get("email", user.email)
        if data.get("password"):
            user.password = make_password(data["password"])
        user.save()
        serializer = self.get_serializer(user)
        return Response(
            {"details": "User Successfully Updated.", "user": serializer.data}
        )

    def destroy(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        data = request.data
        if request.user.id != user.id and not request.user.is_staff:
            return Response(
                {"details": "Permission Denied."}, status=status.HTTP_403_FORBIDDEN
            )
        if (
            check_password(data.get("password", ""), user.password)
            or request.user.is_staff
        ):
            user.delete()
            return Response(
                {"details": "User successfully deleted."},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"details": "Incorrect password."}, status=status.HTTP_401_UNAUTHORIZED
        )


# update user account
# Note: update and delete are handled inside UserViewSet


# delete user account
# Note: delete handled via UserViewSet.destroy


# get billing address (details of user address, all addresses)
class BillingAddressViewSet(viewsets.ModelViewSet):
    serializer_class = BillingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BillingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, pk=None):
        address = get_object_or_404(BillingAddress, id=pk)
        if address.user != request.user and not request.user.is_staff:
            return Response(
                {"details": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(address)
        return Response(serializer.data)

    def update(self, request, pk=None):
        address = get_object_or_404(BillingAddress, id=pk)
        if address.user != request.user and not request.user.is_staff:
            return Response(
                {"details": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )
        data = request.data
        serializer = self.get_serializer(address, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        address = get_object_or_404(BillingAddress, id=pk)
        if address.user != request.user and not request.user.is_staff:
            return Response(
                {"details": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )
        address.delete()
        return Response(
            {"details": "Address successfully deleted."},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def validate(self, request, pk=None):
        """A simple validation endpoint that simulates address validation."""
        address = get_object_or_404(BillingAddress, id=pk)
        if address.user != request.user and not request.user.is_staff:
            return Response(
                {"details": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )
        # In real implementation, we'd call an external validation API.
        return Response({"valid": True, "message": "Address looks valid."})


# get specific address only
# create/retrieve/update/delete handled by BillingAddressViewSet


# edit billing address
# delete handled by BillingAddressViewSet


# all orders list
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = AllOrdersListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return OrderModel.objects.all()
        return OrderModel.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.action in ["update", "partial_update"]:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def update(self, request, pk=None):
        # Used for changing delivered status by admin
        order = get_object_or_404(OrderModel, id=pk)
        if not request.user.is_staff:
            return Response(
                {"details": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )
        data = request.data
        order.is_delivered = data.get("is_delivered", order.is_delivered)
        order.delivered_at = data.get("delivered_at", order.delivered_at)
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def mark_delivered(self, request, pk=None):
        order = get_object_or_404(OrderModel, id=pk)
        order.is_delivered = True
        order.delivered_at = request.data.get("delivered_at", order.delivered_at)
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def confirm_payment(self, request, pk=None):
        order = get_object_or_404(OrderModel, id=pk)
        if order.user != request.user and not request.user.is_staff:
            return Response(
                {"details": "Permission denied."}, status=status.HTTP_403_FORBIDDEN
            )
        order.paid_status = True
        order.paid_at = request.data.get("paid_at", order.paid_at)
        order.save()
        serializer = self.get_serializer(order)
        return Response(serializer.data)


# change order delivered status
# ChangeOrderStatus handled by OrderViewSet.update
