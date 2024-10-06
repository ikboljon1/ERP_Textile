from decimal import Decimal
from django.db import models
from django.conf import settings
from datetime import date
from django.db.models import CASCADE
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from prompt_toolkit.validation import ValidationError
from CRM.models import Counterparty
from HRM.models import Employee, Sewing
from wms.models import VAT, Product, Warehouse, Stock, Currency
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

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


#Аванс
class Advance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник")
    issue_date = models.DateField("Дата выдачи", default=date.today)
    amount = models.DecimalField("Сумма аванса", max_digits=10, decimal_places=2)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name='Счет', null=True, blank=True)
    period = models.DateField("Период (год-месяц)", null=True, blank=True)
    accounted = models.BooleanField("Учтено в зарплате", default=False)

    def __str__(self):
        return f"Аванс для {self.employee.get_full_name()} от {self.issue_date.strftime('%Y-%m-%d')} на сумму {self.amount}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.pk:  # Новый аванс
            if self.account:
                self.account.balance -= self.amount
                self.account.save()
        else:  # Редактирование аванса
            original_advance = Advance.objects.get(pk=self.pk)
            if self.account != original_advance.account:
                # Если счет изменился, корректируем балансы обоих счетов
                if original_advance.account:
                    original_advance.account.balance += original_advance.amount
                    original_advance.account.save()
                if self.account:
                    self.account.balance -= self.amount
                    self.account.save()
            elif self.amount != original_advance.amount:
                # Если изменилась сумма, корректируем баланс текущего счета
                self.account.balance += original_advance.amount
                self.account.balance -= self.amount
                self.account.save()
        super().save(*args, **kwargs)
        AccountTransaction.objects.create(
            account=self.account,
            timestamp=self.issue_date,
            amount=self.amount,  # Или total_amount, если нужно учитывать вычеты
            operation_type='Выплата Аванс',
            description=f"Сотрудник: {self.employee.get_full_name()}",
            direction='out',
        )


#Премия
class Bonus(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник")
    reason = models.CharField("Причина премии", max_length=255)
    amount = models.DecimalField("Сумма премии", max_digits=10, decimal_places=2)
    issue_date = models.DateField("Дата выдачи", default=date.today)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name='Счет', null=True, blank=True)
    period = models.DateField("Период (год-месяц)", null=True, blank=True)
    accounted = models.BooleanField("Учтено в зарплате", default=False)

    def __str__(self):
        return f"Премия для {self.employee.get_full_name()} от {self.issue_date.strftime('%Y-%m-%d')} на сумму {self.amount}"

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.pk:  # Новый аванс
            if self.account:
                self.account.balance -= self.amount
                self.account.save()
        else:  # Редактирование аванса
            original_advance = Advance.objects.get(pk=self.pk)
            if self.account != original_advance.account:
                # Если счет изменился, корректируем балансы обоих счетов
                if original_advance.account:
                    original_advance.account.balance += original_advance.amount
                    original_advance.account.save()
                if self.account:
                    self.account.balance -= self.amount
                    self.account.save()
            elif self.amount != original_advance.amount:
                # Если изменилась сумма, корректируем баланс текущего счета
                self.account.balance += original_advance.amount
                self.account.balance -= self.amount
                self.account.save()
        super().save(*args, **kwargs)

        AccountTransaction.objects.create(
            account=self.account,
            timestamp=self.issue_date,
            amount=self.amount,  # Или total_amount, если нужно учитывать вычеты
            operation_type='Выплата Премия',
            reason=self.reason,
            description=f"Сотрудник: {self.employee.get_full_name()}",
            direction='out',
        )

# Зарплата Сотрудников
class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Сотрудник", null=True)
    payment_date = models.DateField(_("Дата выплаты"), auto_now_add=True, null=True, editable=False)
    period_start = models.DateField("Начало периода", default=date.today)
    period_end = models.DateField("Конец периода", null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name='Счет', default=0, related_name="payrolls")
    # Оклад
    salary_amount = models.DecimalField("Оклад за период", max_digits=10, decimal_places=2, default=0)
    other_allowances = models.DecimalField("Прочие надбавки", max_digits=10, decimal_places=2, default=0)
    taxes_percent = models.DecimalField("Налоги (%)", max_digits=5, decimal_places=2, default=0)
    social_security_percent = models.DecimalField("Соц. отчисления (%)", max_digits=5, decimal_places=2, default=0)
    other_deductions = models.DecimalField("Прочие вычеты", max_digits=10, decimal_places=2, default=0)

    # Поля для сумм аванса и премии, учтенных в Payroll
    advance_paid = models.DecimalField("Выданный аванс", max_digits=10, decimal_places=2, default=0, editable=False)
    bonus_paid = models.DecimalField("Выплаченная премия", max_digits=10, decimal_places=2, default=0, editable=False)

    total_accrued = models.DecimalField("Итого начислено", max_digits=10, decimal_places=2, default=0, editable=False)
    total_deductions = models.DecimalField("Итого удержано", max_digits=10, decimal_places=2, default=0, editable=False)
    total_amount = models.DecimalField("Итого к выплате", max_digits=10, decimal_places=2, default=0, editable=False)
    paid = models.BooleanField("Выплачено", default=False)

    def __str__(self):
        return f"Зарплата {self.employee.get_full_name()} за период с {self.period_start} по {self.period_end}"

    class Meta:
        verbose_name = "Зарплатная ведомость"
        verbose_name_plural = "Зарплатные ведомости"

    def clean(self):
        if self.period_end and self.period_start > self.period_end:
            raise ValidationError("Дата окончания периода должна быть позже даты начала.")
        super().clean()

    def calculate_salary(self):
        """ Рассчитывает зарплату. """

        # Расчет налогов и соц. отчислений на основе процентов
        self.taxes = self.employee.salary * (self.taxes_percent / 100)
        self.social_security = self.employee.salary * (self.social_security_percent / 100)

        advances = Advance.objects.filter(
            employee=self.employee,
            issue_date__month=self.period_start.month,
            issue_date__year=self.period_start.year,
            accounted=False
        )
        self.advance_paid = advances.aggregate(total=models.Sum('amount'))['total'] or 0  # Сохраняем сумму аванса
        advances.update(accounted=True)  # Помечаем авансы как учтенные

        # Учитываем премии за период, которые еще не учтены
        bonuses = Bonus.objects.filter(
            employee=self.employee,
            issue_date__month=self.period_start.month,
            issue_date__year=self.period_start.year,
            accounted=False
        )
        self.bonus_paid = bonuses.aggregate(total=models.Sum('amount'))['total'] or 0  # Сохраняем сумму премии
        bonuses.update(accounted=True)  # Помечаем премии как учтенные

        self.total_accrued = self.salary_amount + self.bonus_paid + self.other_allowances
        self.total_deductions = self.taxes + self.social_security + self.other_deductions + self.advance_paid
        self.total_amount = self.total_accrued - self.total_deductions

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.calculate_salary()  # Рассчитываем зарплату перед сохранением

        # Списание с баланса счета (если счет указан)
        if self.account:
            # Проверяем, был ли счет изменен
            if self.pk:
                original_payroll = Payroll.objects.get(pk=self.pk)
                if original_payroll.account != self.account:
                    # Возвращаем деньги на старый счет
                    original_payroll.account.balance += original_payroll.salary_amount
                    original_payroll.account.save()

            # Списываем деньги с нового счета
            self.account.balance -= self.salary_amount
            self.account.save()

        # Помечаем использованные авансы и премии как учтенные
        if not self.pk:  # Только при создании Payroll
            Advance.objects.filter(
                employee=self.employee,
                issue_date__month=self.period_start.month,
                issue_date__year=self.period_start.year,
                accounted=False
            ).update(accounted=True)
            Bonus.objects.filter(
                employee=self.employee,
                issue_date__month=self.period_start.month,
                issue_date__year=self.period_start.year,
                accounted=False
            ).update(accounted=True)

        super().save(*args, **kwargs)

        # Создаем запись в AccountTransaction
        AccountTransaction.objects.create(
            account=self.account,
            timestamp=self.payment_date,
            amount=self.salary_amount,  # Или total_amount, если нужно учитывать вычеты
            operation_type='Выплата зарплаты',
            description=f"Сотрудник: {self.employee.get_full_name()}",
            related_object=self,  # Связываем с Payroll
            direction='out',
        )

#Зарплата производство
class SalaryPayment(models.Model):
    employee = models.ForeignKey(Sewing, on_delete=models.CASCADE, verbose_name=_("Сотрудник"))
    payment_date = models.DateField(_("Дата выплаты"), auto_now_add=True, null=True, editable=False)
    period = models.DateField(_("Период"),default=date.today) # Используем DateField для периода
    amount = models.DecimalField(_("Сумма"), max_digits=10, decimal_places=2)
    account = models.ForeignKey('Account', on_delete=models.CASCADE, verbose_name='Счет', default=0)
    notes = models.TextField(_("Примечания"), blank=True)

    class Meta:
        verbose_name = _("Зарплата Производство")
        verbose_name_plural = _("Зарплата Производство")
        ordering = ["-payment_date", "-period"]

    def __str__(self):
        return f"Зарплата {self.employee} за {self.period:%Y-%m}" # Форматируем вывод

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Списание суммы с баланса счета, если операция еще не выполнена
        if not self.pk:  # Проверяем, создается ли объект (не обновляется)
            self.account.balance -= self.amount
            self.account.save()

        super().save(*args, **kwargs)
        AccountTransaction.objects.create(
            account=self.account,
            timestamp=self.payment_date,
            amount=self.amount,  # Или total_amount, если нужно учитывать вычеты
            operation_type='Выплата зарплаты',
            description=f"Сотрудник: {self.employee.name}-{self.employee.code}",
            related_object=self, # Связываем с Payroll
            direction = 'out',
        )


@receiver(post_save, sender=SalaryPayment)
def log_purchase(sender, instance, created, **kwargs):
    if created:  # Логируем только при создании новой покупки
        print(f"Создана новая покупка: {instance}")
        print(f"Баланс счета {instance.account.name} обновлен: {instance.account.balance}")



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
    date = models.DateTimeField(auto_now_add=True, verbose_name='Дата', null=True)

    class Meta:
        verbose_name = "Покупка"
        verbose_name_plural = 'Покупка'

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.amount} ({self.date})"

    @transaction.atomic
    def save(self, *args, **kwargs):
        # Списание суммы с баланса счета, если операция еще не выполнена
        if not self.pk:  # Проверяем, создается ли объект (не обновляется)
            self.account.balance -= self.amount
            self.account.save()

        super().save(*args, **kwargs)
        AccountTransaction.objects.create(
            account=self.account,
            quantity=self.quantity,
            operation_type=self.transaction_type,
            amount=self.amount,
            direction='out',
        )


@receiver(post_save, sender=Purchase)
def log_purchase(sender, instance, created, **kwargs):
    if created:  # Логируем только при создании новой покупки
        print(f"Создана новая покупка: {instance}")
        print(f"Баланс счета {instance.account.name} обновлен: {instance.account.balance}")

#История операции
class AccountTransaction(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE, verbose_name="Счет")
    timestamp = models.DateTimeField("Дата и время", auto_now_add=True)
    amount = models.DecimalField("Сумма", max_digits=12, decimal_places=2)
    operation_type = models.CharField("Тип операции", max_length=50)
    description = models.CharField("Описание", max_length=255, blank=True)
    quantity = models.DecimalField("Количество", max_digits=12, decimal_places=2, null=True, blank=True)
    # Поля для связи с любой моделью
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    DIRECTION_CHOICES = [
        ('in', 'Приход'),
        ('out', 'Расход'),
    ]
    direction = models.CharField("Направление", max_length=3, choices=DIRECTION_CHOICES, default='out')
    reason = models.CharField("Причина", max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.operation_type}: {self.amount} на счет {self.account} - {self.description}"