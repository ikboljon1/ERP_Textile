from idlelib.textview import view_text

from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

from HRM.models import Employee
from production.models import TechnologicalMap, Stage, TechnologicalMapOperation, TechnologicalMapMaterial
from order.models import OrderItem, Order
from wms.models import Stock


# class Employee(models.Model):
#     """ Модель сотрудника """
#     user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
#     group = models.ForeignKey(Group, on_delete=models.SET_NULL, verbose_name="Группа", blank=True, null=True)
#     nfc_id = models.CharField("NFC ID", max_length=255, unique=True, blank=True, null=True)
#     brigade = models.ForeignKey(Brigade, on_delete=models.SET_NULL, verbose_name="Бригада", blank=True, null=True)
#     # ... другие поля, например, ФИО, должность, табельный номер
#
#     def __str__(self):
#         return self.user.username

class Assignment(models.Model):
    """ Задание на производство """
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, verbose_name="Позиция заказа",default=1,)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, verbose_name="Этап производства",default=1)
    operation = models.ForeignKey(TechnologicalMapOperation, on_delete=models.CASCADE, verbose_name="Операция")
    user = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name='Сотрудник', default=1)
    quantity = models.PositiveIntegerField("Количество", default=0)
    completed_quantity = models.PositiveIntegerField("Выполнено", default=0)
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
        return f"Задание {self.id} ({self.operation.operation.name} для {self.order_item.product.name})"

    def is_completed(self):
        return self.completed_quantity >= self.quantity


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

class OperationLog(models.Model):
    """ Журнал операций производства """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, verbose_name="Задание")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник")
    operation = models.ForeignKey(TechnologicalMapOperation, on_delete=models.CASCADE, verbose_name="Операция")
    quantity = models.PositiveIntegerField("Количество")
    start_time = models.DateTimeField("Время начала", default=timezone.now)
    end_time = models.DateTimeField("Время окончания", blank=True, null=True)
    duration = models.DurationField("Длительность", blank=True, null=True)  # Новое поле
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
        return f"{self.employee.username} - {self.operation.name} - {self.quantity}"

    class Meta:
        verbose_name = "Запись журнала операций"
        verbose_name_plural = "Журнал операций"

class Cutting(models.Model):
    """ Кройка """
    assignment = models.ForeignKey('manufactory.Assignment', on_delete=models.CASCADE, verbose_name="Задание")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Кройщик")
    quantity_cut = models.PositiveIntegerField("Количество выкроенных изделий", default=0)
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

    def __str__(self):
        return f"Кройка по заданию {self.assignment.id}, кройщик: {self.employee.user.username if self.employee else 'Не назначен'}"

    class Meta:
        verbose_name = "Кройка"
        verbose_name_plural = "Кройка"

class Sewing(models.Model):  # Добавленная модель Sewing
    """ Пошив """
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, verbose_name="Задание")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Швея")
    quantity_sewn = models.PositiveIntegerField("Количество пошитых изделий", default=0)
    start_time = models.DateTimeField("Время начала", auto_now_add=True)
    end_time = models.DateTimeField("Время окончания", null=True, blank=True)
    # ... Добавьте поля для учета остатков и отходов по другим материалам, если нужно ...

    def __str__(self):
        return (f"Пошив по заданию {self.assignment.id}, "
                f"швея: {self.employee.user.username if self.employee else 'Не назначена'}"
                )

    class Meta:
        verbose_name = "Пошив"
        verbose_name_plural = "Пошив"


class Cleaning(models.Model):
    """ Очистка/Стирка """
    assignment = models.ForeignKey('manufactory.Assignment', on_delete=models.CASCADE, verbose_name="Задание")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Очиститель")
    quantity_cleaned = models.PositiveIntegerField("Количество очищенных изделий", default=0)
    start_time = models.DateTimeField("Время начала", auto_now_add=True)
    end_time = models.DateTimeField("Время окончания", null=True, blank=True)
    class Meta:
        verbose_name = "Очистка"
        verbose_name_plural = "Очистка"
    # ... поля и методы ...

class Ironing(models.Model):
    """ Утюжка """
    assignment = models.ForeignKey('manufactory.Assignment', on_delete=models.CASCADE, verbose_name="Задание")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Утюжильщик")
    quantity_ironed = models.PositiveIntegerField("Количество отутюженных изделий", default=0)
    start_time = models.DateTimeField("Время начала", auto_now_add=True)
    end_time = models.DateTimeField("Время окончания", null=True, blank=True)
    class Meta:
        verbose_name = "Утюжки"
        verbose_name_plural = "Утюжки"
    # ... поля и методы ...

class Packing(models.Model):
    """ Упаковка """
    assignment = models.ForeignKey('manufactory.Assignment', on_delete=models.CASCADE, verbose_name="Задание")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Упаковщик")
    quantity_packed = models.PositiveIntegerField("Количество упакованных изделий", default=0)
    start_time = models.DateTimeField("Время начала", auto_now_add=True)
    end_time = models.DateTimeField("Время окончания", null=True, blank=True)
    class Meta:
        verbose_name = "Упаковка"
        verbose_name_plural = "Упаковка"
    # ... поля и методы ...