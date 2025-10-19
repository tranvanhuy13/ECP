from django.contrib import admin
from .models import Product, Rating, Report


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "stock", "average_rating", "total_ratings")
    search_fields = ("name", "description")
    list_filter = ("stock",)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "product__name", "comment")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "report_type", "status", "created_at")
    list_filter = ("report_type", "status", "created_at")
    search_fields = ("title", "description", "user__username")
    readonly_fields = ("created_at", "updated_at")
