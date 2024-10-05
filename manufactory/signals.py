from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Assignment, Cutting, OperationLog, OrderItem


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