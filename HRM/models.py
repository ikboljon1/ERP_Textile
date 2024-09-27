from datetime import date

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.contrib.contenttypes.models import ContentType


class Branch(models.Model):
    """ Филиал компании """
    name = models.CharField("Название филиала", max_length=100, unique=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Филиал"
        verbose_name_plural = "Филиалы"

class Role(models.Model):
    """ Модель для хранения ролей """
    name = models.CharField("Название роли", max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"


class Employee(AbstractUser):
    """ Сотрудник """
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Филиал")
    position = models.CharField("Должность", max_length=100)
    hire_date = models.DateField("Дата приема на работу", null=True, blank=True)
    PAYMENT_TYPE_CHOICES = [
        ('piecework', 'Сдельная'),
        ('salary', 'Повременная'),
    ]
    payment_type = models.CharField(
        "Тип оплаты труда",
        max_length=20,
        choices=PAYMENT_TYPE_CHOICES,
        default='piecework'
    )
    hourly_rate = models.DecimalField(
        "Почасовая ставка",
        max_digits=8,
        decimal_places=2,
        default=0,
        blank=True,
        null=True
    )
    piece_rate = models.DecimalField(
        "Ставка за штуку",
        max_digits=8,
        decimal_places=2,
        default=0,
        blank=True,
        null=True
    )
    is_active = models.BooleanField("Работает в данный момент", default=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Роль")
    allowed_stages = models.ManyToManyField(
        'production.Stage',
        verbose_name="Разрешенные  этапы",
        blank=True
    )
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

class Permission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="Роль")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="hrm_permissions")
    can_view = models.BooleanField("Просмотр", default=False)
    can_create = models.BooleanField("Создание", default=False)
    can_edit = models.BooleanField("Редактирование", default=False)
    can_delete = models.BooleanField("Удаление", default=False)

    def __str__(self):
        model_name = self.content_type.model_class().__name__ if self.content_type else "N/A"
        return f"Разрешения для {self.role.name} на {model_name}"

    class Meta:
        verbose_name = "Разрешение"
        verbose_name_plural = "Разрешения"



class NfcTag(models.Model):
    uid = models.CharField("UID метки", max_length=255, unique=True)
    employee = models.OneToOneField('HRM.Employee', on_delete=models.CASCADE, verbose_name="Сотрудник", null=True, blank=True)

    def __str__(self):
        return self.uid

class Brigade(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
# class  Payroll(models.Model):
#     employee  =  models.ForeignKey(Employee,  on_delete=models.CASCADE,  verbose_name="Сотрудник")
#     period  =  models.DateField("Период",  default=date.today)  #  Дата  (например,  первый  день  месяца)  для  обозначения  периода  начисления
#     salary  =  models.DecimalField("Оклад",  max_digits=10,  decimal_places=2,  default=0)
#     bonuses  =  models.DecimalField("Премии",  max_digits=10,  decimal_places=2,  default=0)
#     deductions  =  models.DecimalField("Удержания",  max_digits=10,  decimal_places=2,  default=0)
#     total  =  models.DecimalField("Итого",  max_digits=10,  decimal_places=2,  default=0)
#
#     def  __str__(self):
#         return  f"Зарплата  {self.employee}  за  {self.period.strftime('%Y-%m')}"