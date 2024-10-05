from django.db import models
from django.conf import settings
from datetime import date

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from CRM.models import Counterparty
from HRM.models import Employee, Sewing
from wms.models import VAT, Product, Warehouse, Stock, Currency


class AccountType(models.TextChoices):
    ACTIVE = 'active', 'Активный'
    PASSIVE = 'passive', 'Пассивный'
    ACTIVE_PASSIVE = 'active_passive', 'Активно-пассивный'
    INCOME = 'income', 'Доходы'
    EXPENSE = 'expense', 'Затраты'



class Account(models.Model):
    code = models.CharField("Код счета", max_length=20, unique=True)
    name = models.CharField("Название счета", max_length=255)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Баланс")
    account_type = models.CharField('Тип счета', max_length=20, choices=AccountType.choices, default=AccountType.ACTIVE)
    currency_type = models.CharField("Валюта счета", max_length=20,
                                    choices=Currency.choices, default=Currency.USD)
    parent_account = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Родительский счет"
    )
    description = models.TextField("Описание", blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Счет"
        verbose_name_plural = "План счетов"


class DocumentType(models.TextChoices):
    INVOICE = 'invoice', 'Счет-фактура'
    WAYBILL = 'waybill', 'Накладная'
    ACT = 'act', 'Акт'
    # ... Добавьте другие типы документов


class Document(models.Model):

    class Meta:
        verbose_name = 'Документы'
        verbose_name_plural = verbose_name

    document_type = models.CharField("Тип документа", max_length=20, choices=DocumentType.choices)
    number = models.CharField("Номер", max_length=50)
    date = models.DateField("Дата")
    counterparty = models.ForeignKey(Counterparty, on_delete=models.PROTECT, verbose_name="Контрагент")

    # ... Добавьте другие поля (сумма, НДС, файл документа)

    def __str__(self):
        return f"{self.get_document_type_display()} № {self.number} от {self.date.strftime('%d.%m.%Y')}"

class TransactionType(models.Model):

    class Meta:
        verbose_name = 'Тип транзакции'
        verbose_name_plural = verbose_name

    name = models.CharField("Название Транзакции", max_length=255)
    parent_transaction = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Родительский счет"
    )
    description = models.TextField("Описание", blank=True)

    def __str__(self):
        parent_name = self.parent_transaction.name + " - " if self.parent_transaction else ""
        return f"{parent_name}{self.name} "

class AdvanceAmount(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField('Сумма', max_digits=10, decimal_places=2, default=0)
    period_start = models.DateField("Начало периода", default=date.today)
    period_end = models.DateField("Конец периода", null=True)

    def __str__(self):
        return self.employee.name

#Расходы
class Expense(models.Model):
    class Meta:
        verbose_name = 'Расходы'
        verbose_name_plural = 'Расходы'

    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name='Счет')
    operation = models.ForeignKey(TransactionType, on_delete=models.CASCADE, verbose_name="Операция")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Сумма")
    def __str__(self):
        return f"{self.operation} {self.amount}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Списание суммы с баланса счета, если операция еще не выполнена
        if not self.pk:  # Проверяем, создается ли объект (не обновляется)
            self.account.balance -= self.amount
            self.account.save()

        super().save(*args, **kwargs)


@receiver(post_save, sender=Expense)
def log_expense(sender, instance, created, **kwargs):
    if created:  # Логируем только при создании новой записи расходов
        print(f"Создана новая запись расходов: {instance}")
        print(f"Баланс счета {instance.account.name} обновлен: {instance.account.balance}")

#Списание товара на Актива
class  WriteOff(models.Model):
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.CASCADE, verbose_name="Названия", null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                   verbose_name="Создано пользователем", null=True, blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, verbose_name="Склад")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Количество')

    class Meta:
        verbose_name = 'Списание'
        verbose_name_plural = 'Списание'

@receiver(post_save, sender=WriteOff)
def update_stock_on_write_of(sender, instance, created, **kwargs):
    """ Обновляет остатки при перемещении товара. """
    if created:
        if instance.quantity <= 0:
            raise ValueError("Количество для перемещения должно быть положительным числом.")
        with transaction.atomic():
            try:
                stock_from = Stock.objects.get(product=instance.product, warehouse=instance.warehouse)
                if stock_from.quantity >= instance.quantity:
                    stock_from.quantity -= instance.quantity
                    stock_from.save()
                else:
                    raise ValueError("Недостаточно товара на складе-источнике")
            except Stock.DoesNotExist:
                raise ValueError(f"Товар {instance.product.name} не найден на складе {instance.warehouse.name}")
@receiver(post_save, sender=WriteOff)
def log_stock_changes(sender, instance, **kwargs):
    print(f"Изменения в модели {sender.__name__}: {instance}")

#Покупка
class Purchase(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.CASCADE, verbose_name='Тип Транзакции', null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Количество')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Сумма')

    class Meta:
        verbose_name = "Покупка"
        verbose_name_plural = 'Покупка'

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.amount}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Списание суммы с баланса счета, если операция еще не выполнена
        if not self.pk:  # Проверяем, создается ли объект (не обновляется)
            self.account.balance -= self.amount
            self.account.save()

        super().save(*args, **kwargs)


@receiver(post_save, sender=Purchase)
def log_purchase(sender, instance, created, **kwargs):
    if created:  # Логируем только при создании новой покупки
        print(f"Создана новая покупка: {instance}")
        print(f"Баланс счета {instance.account.name} обновлен: {instance.account.balance}")
