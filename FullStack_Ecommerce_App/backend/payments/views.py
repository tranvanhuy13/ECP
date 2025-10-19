import stripe
from rest_framework import status, viewsets
from rest_framework import permissions
from rest_framework.response import Response
from account.models import StripeModel, OrderModel
from rest_framework.decorators import action
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.conf import settings

stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "your secret key here")


class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def test_payment(self, request):
        try:
            test_payment_process = stripe.PaymentIntent.create(
                amount=120,
                currency="inr",
                payment_method_types=["card"],
                receipt_email="test@example.com",
            )
            return Response(data=test_payment_process, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def check_token(self, request):
        return Response("Token is Valid", status=status.HTTP_200_OK)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def create_card_token(self, request):
        data = request.data
        email = data.get("email")
        save_card = data.get("save_card", False)

        try:
            stripe_token = stripe.Token.create(
                card={
                    "number": data["number"],
                    "exp_month": data["exp_month"],
                    "exp_year": data["exp_year"],
                    "cvc": data["cvc"],
                }
            )
        except stripe.error.CardError as e:
            return Response(
                {"detail": e.user_message}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        customer_data = stripe.Customer.list(email=email).data
        if not customer_data:
            customer = stripe.Customer.create(
                email=email, description="My new customer"
            )
        else:
            customer = customer_data[0]

        create_user_card = stripe.Customer.create_source(
            customer["id"], source=stripe_token.id
        )

        if save_card:
            try:
                StripeModel.objects.create(
                    email=email,
                    customer_id=customer["id"],
                    card_number=data["number"],
                    exp_month=data["exp_month"],
                    exp_year=data["exp_year"],
                    card_id=create_user_card.id,
                    user=request.user,
                )
            except Exception as e:
                return Response(
                    {"detail": "Card already in use or error saving card."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {"customer_id": customer["id"], "card": create_user_card},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def charge_customer(self, request):
        data = request.data
        email = data.get("email")
        try:
            customer_data = stripe.Customer.list(email=email).data
            customer = customer_data[0]

            stripe.Charge.create(
                customer=customer,
                amount=int(float(data.get("amount", 0)) * 100),
                currency="inr",
                description=data.get("description", "Charge"),
            )

            new_order = OrderModel.objects.create(
                name=data.get("name"),
                card_number=data.get("card_number"),
                address=data.get("address"),
                ordered_item=data.get("ordered_item"),
                paid_status=data.get("paid_status", True),
                paid_at=datetime.now(),
                total_price=data.get("total_price"),
                is_delivered=data.get("is_delivered", False),
                delivered_at=data.get("delivered_at"),
                user=request.user,
            )

            return Response(
                {"data": {"customer_id": customer.id, "message": "Payment Successful"}},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def retrieve_card(self, request):
        customer_id = request.headers.get("Customer-Id")
        card_id = request.headers.get("Card-Id")
        try:
            card_details = stripe.Customer.retrieve_source(customer_id, card_id)
            return Response(card_details, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def update_card(self, request):
        data = request.data
        try:
            update_card = stripe.Customer.modify_source(
                data["customer_id"],
                data["card_id"],
                exp_month=data.get("exp_month"),
                exp_year=data.get("exp_year"),
                name=data.get("name_on_card"),
                address_city=data.get("address_city"),
                address_country=data.get("address_country"),
                address_state=data.get("address_state"),
                address_zip=data.get("address_zip"),
            )

            obj = StripeModel.objects.filter(
                card_number=data.get("card_number")
            ).first()
            if obj:
                obj.name_on_card = data.get("name_on_card", obj.name_on_card)
                obj.exp_month = data.get("exp_month", obj.exp_month)
                obj.exp_year = data.get("exp_year", obj.exp_year)
                obj.address_city = data.get("address_city", obj.address_city)
                obj.address_country = data.get("address_country", obj.address_country)
                obj.address_state = data.get("address_state", obj.address_state)
                obj.address_zip = data.get("address_zip", obj.address_zip)
                obj.save()

            return Response(
                {
                    "detail": "card updated successfully",
                    "data": {"Updated Card": update_card},
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def delete_card(self, request):
        data = request.data
        obj_card = StripeModel.objects.filter(
            card_number=data.get("card_number")
        ).first()
        if not obj_card:
            return Response(
                {"detail": "Card not found."}, status=status.HTTP_404_NOT_FOUND
            )

        customerId = obj_card.customer_id
        cardId = obj_card.card_id

        try:
            stripe.Customer.delete_source(customerId, cardId)
            obj_card.delete()
            stripe.Customer.delete(customerId)
            return Response(
                {"detail": "Card deleted successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
