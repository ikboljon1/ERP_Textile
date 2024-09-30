from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models import CharField, Sum
from django.utils import timezone
from HRM.models import Employee, Brigade, Sewing
from production.models import TechnologicalMap, Stage, TechnologicalMapOperation, TechnologicalMapMaterial, ProductionItem
from order.models import OrderItem, Order
from wms.models import Stock


class Assignment(models.Model):

    class Meta:
        verbose_name = 'Заказ на производство'
        verbose_name_plural = 'Заказ на производство'

    """ Задание на производство """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ', null=True, blank=True)
    # order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, verbose_name="Позиция заказа")
    start_date = models.DateTimeField("Дата начала", blank=True, null=True)
    end_date = models.DateTimeField("Дата окончания", blank=True, null=True)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=[
            ("new", "Новое"),
            ("in_progress", "В работе"),
            ("completed", "Выполнено"),
            ("paused", "Приостановлено"),
        ],
        default="new",
    )
    def __str__(self):
        return f"Задание {self.order}"



class MaterialRequest(models.Model):
    """ Заявка на материал """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, verbose_name="Задание")
    material = models.ForeignKey(TechnologicalMapMaterial, on_delete=models.CASCADE, verbose_name="Материал")
    requested_quantity = models.DecimalField("Запрошенное количество", max_digits=10, decimal_places=2)
    issued_quantity = models.DecimalField("Выданное количество", max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=[
            ("requested", "Запрошено"),
            ("partially_issued", "Частично выдано"),
            ("issued", "Выдано"),
            ("canceled", "Отменено"),
        ],
        default="requested",
    )

    def __str__(self):
        return f"Заявка на {self.material.product.name} для задания {self.assignment.id}"

    class Meta:
        verbose_name = "Заявка на материал"
        verbose_name_plural = "Заявки на материалы"

class Cutting(models.Model):
    class Meta:
        verbose_name = 'Крой'
        verbose_name_plural = 'Крой'

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, verbose_name="Задание")
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, verbose_name="Позиция заказа")
    quantity = models.PositiveIntegerField("Количество выкроенных изделий", default=0)
    fabric_leftovers = models.DecimalField(
         "Остатки ткани", max_digits=10, decimal_places=2, default=0,
         help_text="Укажите количество остатков ткани после кроя"
    )
    fabric_waste = models.DecimalField(
         "Отходы ткани", max_digits=10, decimal_places=2, default=0,
          help_text="Укажите количество отходов ткани (брак)"
    )
    waste_reason = models.TextField("Причина отходов", blank=True)
    start_time = models.DateTimeField("Время начала", auto_now_add=True)
    end_time = models.DateTimeField("Время окончания", null=True, blank=True)
    map = models.CharField('Карта', max_length=255 )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=[
            ("new", "Новое"),
            ("in_progress", "В работе"),
            ("completed", "Выполнено"),
            ("paused", "Приостановлено"),
        ],
        default="new",
    )

    def __str__(self):
        return f"Кройка по заданию {self.assignment.id},{self.order_item}{self.quantity}"



class OperationLog(models.Model):

    """ Журнал операций производства """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, verbose_name="Задание")
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, verbose_name="Позиция заказа", null=True, blank=True)
    brigade = models.ForeignKey(Brigade, on_delete=models.CASCADE, verbose_name="Бригада", null=True, blank=True)
    employee = models.ForeignKey(Sewing, on_delete=models.CASCADE, verbose_name="Сотрудник")
    operation = models.ForeignKey('production.TechnologicalMapOperation', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("Количество")
    start_time = models.DateTimeField("Время начала", default=timezone.now)
    end_time = models.DateTimeField("Время окончания", blank=True, null=True)
    duration = models.DurationField("Длительность", blank=True, null=True)  # Новое поле
    defect_quantity = models.PositiveIntegerField("Количество брака", default=0)
    comments = models.TextField("Комментарии", blank=True)
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=[
            ("started", "Начата"),
            ("completed", "Завершена"),
            ("paused", "Приостановлена"),
            ("problem", "Проблема"),
        ],
        default="started",
    )


    def __str__(self):
        return f"Фактические данные по операции '{self.operation.operation.name}Задании №{self.assignment.pk}"

    class Meta:
        verbose_name = "Назначения"
        verbose_name_plural = "Назначения"

class  Defect(models.Model):

    """  Модель  для  учета  брака  """
    assignment  =  models.ForeignKey(Assignment,  on_delete=models.CASCADE,  verbose_name="Задание")
    employee  =  models.ForeignKey(Sewing,  on_delete=models.CASCADE,  verbose_name="Сотрудник")
    operation  =  models.ForeignKey(TechnologicalMapOperation,  on_delete=models.CASCADE,  verbose_name="Операция")
    quantity  =  models.PositiveIntegerField("Количество  бракованных  изделий")
    description  =  models.TextField("Описание  брака",  blank=True)
    created_at  =  models.DateTimeField("Дата  создания",  auto_now_add=True)

    def  __str__(self):
        return  f"Брак  в  задании  {self.assignment}  ({self.quantity}  шт.)"

    class  Meta:
        verbose_name  =  "Брак"
        verbose_name_plural  =  "Брак"

def get_produced_quantity_for_order_operation(order_item, operation):
    """Возвращает общее количество произведенных изделий."""
    return OperationLog.objects.filter(
        order_item=order_item,
        operation=operation
    ).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

def get_remaining_quantity_for_order_operation(order_item, operation):
    """Возвращает количество оставшихся изделий."""
    produced_quantity = get_produced_quantity_for_order_operation(order_item, operation)
    return order_item.quantity - produced_quantity