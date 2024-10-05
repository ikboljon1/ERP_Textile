from django.db import models
from django.conf import settings
from datetime import date

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from CRM.models import Counterparty
from HRM.models import Employee, Sewing
from wms.models import VAT, Product, Warehouse, Stock


class AccountType(models.TextChoices):
    ACTIVE = 'active', 'Активный'
    PASSIVE = 'passive', 'Пассивный'
    ACTIVE_PASSIVE = 'active_passive', 'Активно-пассивный'
    INCOME = 'income', 'Доходы'
    EXPENSE = 'expense', 'Затраты'



class Account(models.Model):
    code = models.CharField("Код счета", max_length=20, unique=True)
    name = models.CharField("Название счета", max_length=255)
    account_type = models.CharField("Тип счета", max_length=20,
                                    choices=AccountType.choices, default=AccountType.ACTIVE)
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
# class TransactionType(models.TextChoices):
#     OTHER = 'other', 'Другое'
#     SALARY = 'salary', 'Зарплата'
#     MATERIAL_PURCHASE = 'material_purchase', 'Покупка материалов'
#     MATERIAL_WRITE_OFF = 'material_write_off', 'Списание материалов'
#     PRODUCT_SALE = 'product_sale', 'Продажа продукции'
#     CASH_RECEIPT = 'cash_receipt', 'Поступление денежных средств'
#     CASH_DISBURSEMENT = 'cash_disbursement', 'Выплата денежных средств'
#     # ... Добавьте другие типы операций
#
#
# class Transaction(models.Model):
#     date = models.DateField("Дата", default=date.today)
#     transaction_type = models.CharField("Тип операции", max_length=50,
#                                         choices=TransactionType.choices,
#                                         default=TransactionType.OTHER)
#     description = models.CharField("Описание", max_length=255)
#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
#                                    verbose_name="Создано пользователем")
#     order = models.ForeignKey('order.Order', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Заказ")
#     document = models.OneToOneField(Document, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Документ")
#
#     def __str__(self):
#         return f"{self.date.strftime('%d.%m.%Y')} - {self.get_transaction_type_display()}: {self.description}"
#
#     class Meta:
#         verbose_name = "Хозяйственная операция"
#         verbose_name_plural = "Хозяйственные операции"
#
#
# class TransactionLine(models.Model):
#     transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE,
#                                     related_name='lines', verbose_name="Операция")
#     account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name="Счет")
#     debit = models.DecimalField("Дебет", max_digits=12, decimal_places=2, default=0)
#     credit = models.DecimalField("Кредит", max_digits=12, decimal_places=2, default=0)
#     line_description = models.CharField("Описание строки", max_length=255, blank=True)
#
#     def __str__(self):
#         return f"{self.account.code} - {self.account.name} ({'Дебет' if self.debit else 'Кредит'})"
#
#     class Meta:
#         verbose_name = "Строка операции"
#         verbose_name_plural = "Строки операции"
# class Payroll(models.Model):
#     employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник", null=True, blank=True)
#     period_start = models.DateField("Начало периода", default=date.today)
#     period_end = models.DateField("Конец периода", null=True)
#
#     # Оклад
#     salary_amount = models.DecimalField("Оклад за период", max_digits=10, decimal_places=2, default=0)
#
#     # Дополнительные начисления
#     bonus = models.DecimalField("Премия", max_digits=10, decimal_places=2, default=0)
#     overtime_hours = models.DecimalField("Сверхурочные часы", max_digits=5, decimal_places=2, default=0)
#     overtime_rate = models.DecimalField("Ставка за сверхурочные", max_digits=8, decimal_places=2, default=0)
#     other_allowances = models.DecimalField("Прочие надбавки", max_digits=10, decimal_places=2, default=0)
#
#     # Вычеты
#     taxes = models.DecimalField(VAT, max_digits=10, decimal_places=2, default=0)
#     social_security = models.DecimalField("Соц. отчисления", max_digits=10, decimal_places=2, default=0)
#     other_deductions = models.DecimalField("Прочие вычеты", max_digits=10, decimal_places=2, default=0)
#
#
#     # Итого
#     total_accrued = models.DecimalField("Итого начислено", max_digits=10, decimal_places=2, default=0,
#                                             editable=False)
#     total_deductions = models.DecimalField("Итого удержано", max_digits=10, decimal_places=2, default=0,
#                                                editable=False)
#     total_amount = models.DecimalField("Итого к выплате", max_digits=10, decimal_places=2, default=0,
#                                            editable=False)
#     paid = models.BooleanField("Выплачено", default=False)
#
#     def __str__(self):
#         return f"Зарплата {self.employee.name} за период с {self.period_start} по {self.period_end}"
#
#     class Meta:
#         verbose_name = "Зарплатная ведомость"
#         verbose_name_plural = "Зарплатные ведомости"

# @receiver(post_save, sender=Payroll)
# def create_salary_transaction(sender, instance, created, **kwargs):
#     """
#     Создает проводки для оклада.
#     """
#     if not created or instance.employee.payment_type != 'salary':
#         return
#
#     try:
#         salary_expense_account = Account.objects.get(code="7020")
#         salary_payable_account = Account.objects.get(code="2050")
#     except Account.DoesNotExist:
#         print(f"Ошибка: Не найдены счета для начисления оклада (7020, 2050)")
#         return
#
#     transaction = Transaction.objects.create(
#         description=f"Начисление оклада {instance.employee.get_full_name()} за период {instance.period_start} - {instance.period_end}",
#         transaction_type=Transaction.TransactionType.SALARY,
#         created_by=instance.employee
#     )
#
#     TransactionLine.objects.create(
#         transaction=transaction,
#         account=salary_expense_account,
#         debit=instance.salary_amount  # Используем instance.salary_amount
#     )
#     TransactionLine.objects.create(
#         transaction=transaction,
#         account=salary_payable_account,
#         credit=instance.salary_amount  # Используем instance.salary_amount
#     )

# @receiver(post_save, sender=Payroll)
# def create_piecework_transaction(sender, instance, created, **kwargs):
#     """
#     Создает проводки для сдельной оплаты.
#     """
#     if not created or instance.employee.payment_type != 'piecework':
#         return
#
#     try:
#         piecework_expense_account = Account.objects.get(code="7010")  # Замените на ваш код
#         piecework_payable_account = Account.objects.get(code="2050")  #  Можно использовать тот же счет, что и для оклада
#     except Account.DoesNotExist:
#         print(f"Ошибка: Не найдены счета для начисления сдельной оплаты")
#         return
#
#     transaction = Transaction.objects.create(
#         description=f"Начисление сдельной оплаты {instance.employee.get_full_name()} за период {instance.period_start} - {instance.period_end}",
#         transaction_type=Transaction.TransactionType.SALARY,
#         created_by=instance.employee
#     )
#
#     TransactionLine.objects.create(
#         transaction=transaction,
#         account=piecework_expense_account,
#         debit=instance.piecework_amount  # Используем instance.piecework_amount
#     )
#     TransactionLine.objects.create(
#         transaction=transaction,
#         account=piecework_payable_account,
#         credit=instance.piecework_amount  # Используем instance.piecework_amount
#     )

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
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.CASCADE, verbose_name='Названия', null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Количество')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Сумма')

    class Meta:
        verbose_name = "Покупка"
        verbose_name_plural = 'Покупка'

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.amount}"
