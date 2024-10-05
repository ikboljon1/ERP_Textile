from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Receipt, ReceiptItem, Stock, Moving, Return, POSOrderItem
from django.db.models.signals import pre_save
from django.db.models import Sum, F
# --- Сигналы для модели Receipt ---

@receiver(post_save, sender=Receipt)
def update_stock_on_receipt(sender, instance, created, **kwargs):
    """ Обновляет остатки при создании поступления. """
    if created:
        for item in instance.items.all():
            with transaction.atomic():
                stock, _ = Stock.objects.get_or_create(product=item.product, warehouse=instance.warehouse)
                stock.quantity += item.quantity
                stock.save()
    
# --- Сигналы для модели ReceiptItem ---

@receiver(post_save, sender=ReceiptItem)
def update_stock_on_receipt_item(sender, instance, created, **kwargs):
    """ Обновляет остатки при создании/изменении/удалении позиции поступления. """
    with transaction.atomic():
        if created:
            # Новый товар, добавляем к остаткам
            # Используем instance.receipt.pk для получения id склада,
            # так как сам объект Receipt еще не будет сохранен
            stock, _ = Stock.objects.get_or_create(
                product=instance.product,
                warehouse_id=instance.receipt.warehouse.id  # Обратите внимание на .id
            )
            stock.quantity += instance.quantity
            stock.save()
        else:
            # Обновление или удаление позиции
            try:
                old_item = ReceiptItem.objects.get(pk=instance.pk)
                stock, _ = Stock.objects.get_or_create(product=old_item.product, warehouse=old_item.receipt.warehouse)

                # Возвращаем старое количество на склад
                stock.quantity -= old_item.quantity
                stock.save()

                # Если это не удаление, добавляем новое количество
                if not instance.being_deleted:
                    stock, _ = Stock.objects.get_or_create(product=instance.product, warehouse=instance.receipt.warehouse)
                    stock.quantity += instance.quantity
                    stock.save()
            except ReceiptItem.DoesNotExist:
                pass  # Если старый объект не найден, ничего не делаем


# --- Сигналы для модели Moving ---

@receiver(post_save, sender=Moving)
def update_stock_on_move(sender, instance, created, **kwargs):
    """ Обновляет остатки при перемещении товара. """
    if created:
        if instance.quantity <= 0:
            raise ValueError("Количество для перемещения должно быть положительным числом.")
        with transaction.atomic():
            try:
                stock_from = Stock.objects.get(product=instance.product, warehouse=instance.warehouse_from_where)
                if stock_from.quantity >= instance.quantity:
                    stock_from.quantity -= instance.quantity
                    stock_from.save()
                else:
                    raise ValueError("Недостаточно товара на складе-источнике")
            except Stock.DoesNotExist:
                raise ValueError(f"Товар {instance.product.name} не найден на складе {instance.warehouse_from_where.name}")

            stock_to, _ = Stock.objects.get_or_create(product=instance.product, warehouse=instance.warehouse_where)
            stock_to.quantity += instance.quantity
            stock_to.save()

@receiver(pre_save, sender=ReceiptItem)
def calculate_cost_price(sender, instance, **kwargs):
    """ Рассчитывает себестоимость при создании/изменении позиции поступления. """

    vat_rate = instance.receipt.vat.rate if instance.receipt.vat else 0
    transport_cost_per_unit = instance.receipt.transport_costs / instance.quantity if instance.quantity > 0 else 0
    other_cost_per_unit = instance.receipt.other_costs / instance.quantity if instance.quantity > 0 else 0

    instance.cost_price = instance.price * (1 + vat_rate / 100) + transport_cost_per_unit + other_cost_per_unit

# --- Сигналы для модели Return ---

@receiver(post_save, sender=Return)
def update_stock_on_return(sender, instance, created, **kwargs):
    """ Обновляет остатки при возврате товара поставщику. """
    if created:
        if instance.quantity <= 0:
            raise ValueError("Количество возврата должно быть положительным числом.")

        with transaction.atomic():
            # 1. Уменьшаем количество товара на складе
            stock = Stock.objects.get(
                product=instance.receipt_item.product,
                warehouse=instance.receipt_item.receipt.warehouse  # Склад берем из поступления
            )
            if stock.quantity < instance.quantity:
                raise ValueError(f"Недостаточно товара {instance.receipt_item.product.name} на складе.")
            stock.quantity -= instance.quantity
            stock.save()

            # 2. (Опционально) Можете добавить логику обновления статуса позиции поступления
            # instance.receipt_item.status = ...
            # instance.receipt_item.save()

# --- Логирование изменений (для отладки) ---
# (Можно закомментировать или удалить после того, как все будет работать)

@receiver(pre_save, sender=POSOrderItem)
def update_price_from_product(sender, instance, **kwargs):
    """Обновляет цену позиции заказа из связанного товара перед сохранением."""
    instance.price = instance.product.selling_price  # Используйте selling_price
@receiver(post_save, sender=POSOrderItem)
def update_order_total(sender, instance, created, **kwargs):
    """ Обновляет общую сумму заказа при добавлении/изменении позиций """
    instance.order.total_amount = instance.order.items.aggregate(total=Sum(F('quantity') * F('product__selling_price')))['total'] or 0
    instance.order.save(update_fields=['total_amount'])
@receiver(post_save, sender=Receipt)
@receiver(post_save, sender=Moving)
@receiver(post_save, sender=Return)
def log_stock_changes(sender, instance, **kwargs):
    print(f"Изменения в модели {sender.__name__}: {instance}")