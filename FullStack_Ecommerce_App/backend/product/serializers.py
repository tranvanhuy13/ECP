from rest_framework import serializers
from .models import Product, Rating, Report


class RatingSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Rating
        fields = [
            "id",
            "user",
            "user_name",
            "product",
            "rating",
            "comment",
            "created_at",
        ]
        read_only_fields = ["user"]

    def get_user_name(self, obj):
        return obj.user.username if obj.user.username else obj.user.email

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ReportSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id",
            "user",
            "user_name",
            "product",
            "report_type",
            "title",
            "description",
            "evidence",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "status"]

    def get_user_name(self, obj):
        return obj.user.username if obj.user.username else obj.user.email

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    ratings = RatingSerializer(many=True, read_only=True)
    average_rating = serializers.DecimalField(
        max_digits=3, decimal_places=2, read_only=True
    )
    total_ratings = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "stock",
            "image",
            "average_rating",
            "total_ratings",
            "ratings",
        ]
