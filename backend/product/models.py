from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model

User = get_user_model()


class Product(models.Model):
    name = models.CharField(max_length=200, blank=False, null=False)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.BooleanField(default=False)
    image = models.ImageField(null=True, blank=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_ratings = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="ratings"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")  # One rating per user per product

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Update product average rating
        if is_new:
            self.product.total_ratings += 1

        ratings = Rating.objects.filter(product=self.product)
        self.product.average_rating = sum(r.rating for r in ratings) / len(ratings)
        self.product.save()


class Report(models.Model):
    REPORT_TYPES = (
        ("PRODUCT", "Product Issue"),
        ("SELLER", "Seller Issue"),
        ("OTHER", "Other"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("INVESTIGATING", "Under Investigation"),
        ("RESOLVED", "Resolved"),
        ("CLOSED", "Closed"),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reports_filed"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reports", null=True, blank=True
    )
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    evidence = models.FileField(upload_to="report_evidence/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.report_type} - {self.title}"
