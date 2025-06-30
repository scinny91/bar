
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('in_attesa', 'In Attesa'),
        ('in_preparazione', 'In Preparazione'),
        ('completato', 'Completato'),
    ]
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_attesa')

    def __str__(self):
        return f"Ordine {self.id} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
