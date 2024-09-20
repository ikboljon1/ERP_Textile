from django.db import models
from wms.models import Product, Stock
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

class PurchaseRequest(models.Model):
    material = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Материал")
    quantity = models.DecimalField("Количество", max_digits=10, decimal_places=2)
    request_date = models.DateTimeField("Дата заявки", auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Создан")
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('approved', 'Утверждена'),
        ('rejected', 'Отклонена'),
        ('ordered', 'Заказано'),
    )
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Заявка на закупку {self.product.name} ({self.quantity} ед.)"

    class Meta:
        verbose_name = "Заявка на закупку"
        verbose_name_plural = "Заявки на закупку"

@receiver(post_save, sender=Stock)
def check_stock_level(sender, instance, **kwargs):
    """Проверяет уровень запасов и создает заявку на закупку при необходимости."""
    if instance.quantity < instance.product.min_quantity:
        # Создаем заявку на закупку
        PurchaseRequest.objects.create(
            material=instance.product,
            quantity=instance.product.min_quantity - instance.quantity,
            created_by=instance.product.created_by
        )