
from django.db import models
from django.conf import settings

class Order(models.Model):
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    # Add more fields as needed (address, phone, etc.)
    def __str__(self):
        return f"Order #{self.id} by {self.customer_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    def __str__(self):
        return f"{self.quantity} x {self.name} (Order #{self.order_id})"
from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.CharField(max_length=255, blank=True, null=True,
                             help_text='Relative static path, e.g. devloom/images/laptop1.jpg')

    def __str__(self):
        return self.name
