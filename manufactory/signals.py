from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Assignment, Cutting, OperationLog, Shipment, OrderItem


@receiver(post_save, sender=Assignment)
def create_cutting_and_operation_logs(sender, instance, created, **kwargs):
    if created:
        for order_item in instance.order.order_items.all():
            Cutting.objects.create(assignment=instance, order_item=order_item)

            # Проверяем наличие technological_map перед доступом к operation
            if hasattr(order_item.product, 'technological_map'):
                # Если technological_map существует, создаем OperationLog для каждой операции
                for operation in order_item.product.technological_map.operation.all():
                    OperationLog.objects.create(
                        assignment=instance,
                        order_item=order_item,
                        operation=operation
                    )
            else:
                # Если technological_map отсутствует, создаем OperationLog без операции
                OperationLog.objects.create(
                    assignment=instance,
                    order_item=order_item,
                   #operation=None # Можно оставить пустым или явно указать None, если поле допускает null
                )
@receiver(post_save, sender=Assignment)
def create_shipment(sender, instance, created, **kwargs):
    if instance.status == 'ready_for_shipment' and not hasattr(instance, 'shipment'):
        Shipment.objects.create(assignment=instance)

@receiver(post_save, sender=Shipment)
def update_stock(sender, instance, created, **kwargs):
    if instance.status == 'shipped':
        # Получите OrderItem, связанные с Assignment
        order_items = instance.assignment.order.order_items.all()
        for order_item in order_items:
            # Найдите Stock, соответствующий товару
            try:
                stock = Stock.objects.get(product=order_item.product)
                # Уменьшите количество на складе
                stock.quantity -= order_item.quantity
                stock.save()
            except Stock.DoesNotExist:
                # Обработайте случай, когда Stock не найден
                pass