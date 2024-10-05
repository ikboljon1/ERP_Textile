from django.db import models
from django.contrib import admin
from django.db.models import Sum
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django.db import transaction

from CRM.models import Counterparty
from accounting.models import Account
from production.models import Color, ProductionItem

class Order(models.Model):

    class Meta:
        verbose_name= 'Заказы'
        verbose_name_plural = 'Заказы'

    """Заказ клиента"""
    customer = models.ForeignKey(Counterparty, on_delete=models.PROTECT, verbose_name="Клиент")
    name = models.CharField('Названия', max_length=255)
    uuid = models.CharField("Номер заказа", max_length=50, blank=True)
    photo = models.ImageField("Фотография", upload_to='order_photos/', blank=True, null=True)
    order_date = models.DateTimeField("Дата заказа", auto_now_add=True)
    due_date = models.DateField("Срок исполнения")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="Создан")
    order_type = models.CharField(
        "Тип заказа",
        max_length=50,
        choices=[
            ("retail", "Розничный"),
            ("wholesale", "Оптовый"),
            ("individual", "Индивидуальный пошив"),
        ],
        null=True
    )
    priority = models.CharField(
        "Приоритет",
        max_length=10,
        choices=[("high", "Высокий"), ("medium", "Средний"), ("low", "Низкий")],
        default="medium",
    )
    sales_channel = models.CharField("Канал продаж", max_length=50, blank=True)
    contact_person = models.CharField("Контактное лицо", max_length=255, blank=True)
    delivery_method = models.CharField(
        "Способ доставки",
        max_length=50,
        choices=[
            ("courier", "Курьер"),
            ("pickup", "Самовывоз"),
            ("post", "Почта России"),
        ],
        blank=True,
    )
    delivery_address = models.TextField("Адрес доставки", blank=True)
    # prepayment = models.DecimalField(
    #     "Предоплата (%)", max_digits=5, decimal_places=2, default=0
    # )
    expected_payment_date = models.DateField(
        "Ожидаемая дата оплаты", blank=True, null=True
    )
    discount = models.DecimalField("Скидка", max_digits=10, decimal_places=2, default=0)
    planned_production_start = models.DateField(
        "Планируемая дата начала производства", blank=True, null=True
    )
    planned_shipment_date = models.DateField(
        "Планируемая дата отгрузки", blank=True, null=True
    )
    STATUS_CHOICES = (
        ("new", "Новый"),
        ("in_progress", "В обработке"),
        ("completed", "Выполнен"),
        ("canceled", "Отменен"),
    )
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default="new")
    total_amount = models.DecimalField("Общая сумма", max_digits=10, decimal_places=2, default=0)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    comments = models.TextField("Комментарии", blank=True)
    total_cost = models.DecimalField("Общая стоимость", max_digits=10, decimal_places=2, default=0, editable=False)
    PAYMENT_STATUS_CHOICES = (
        ('not_paid', 'Не оплачен'),
        ('partially_paid', 'Частично оплачен'),
        ('paid', 'Оплачен'),
    )
    payment_status = models.CharField(
        "Статус оплаты",
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='not_paid'
    )
    is_paid = models.BooleanField("Оплачено", default=False)
    def __str__(self):
        return f"Заказ {self.uuid} от {self.order_date.strftime('%d.%m.%Y')}"

    def calculate_total_cost(self):
        """
        Рассчитывает общую стоимость заказа, суммируя
        стоимость всех позиций (OrderItem) в заказе.
        """
        self.total_cost = self.order_items.aggregate(total=Sum('cost_price'))['total'] or 0
        self.save(update_fields=['total_cost'])

class OrderItem(models.Model):
    """Позиция заказа"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(ProductionItem, on_delete=models.PROTECT, verbose_name="Товар")
    quantity = models.PositiveIntegerField("Количество")
    color = models.ForeignKey(Color, on_delete=models.PROTECT, verbose_name='Цвет')
    size = models.CharField("Размер", max_length=50)
    cost_price = models.DecimalField("Себестоимость", max_digits=10, decimal_places=2, default=0, editable=False)

    def __str__(self):
        return f"{self.product.name} {self.quantity} {self.color} {self.size}"

    class Meta:
        verbose_name = 'Пункты заказа'

class Payment(models.Model):
    class Meta:
        verbose_name = "Оплата заказа"
        verbose_name_plural = 'Оплата заказа'

    """Оплата по заказу"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Заказ")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name="Счет", null=True, blank=True)
    amount = models.DecimalField("Сумма оплаты", max_digits=10, decimal_places=2)
    payment_date = models.DateField("Дата оплаты", auto_now_add=True)
    payment_method = models.CharField(
        "Способ оплаты",
        max_length=50,
        choices=[
            ("cash", "Наличные"),
            ("card", "Карта"),
            ("bank_transfer", "Банковский перевод"),
        ],
    )
    comments = models.TextField("Комментарии", blank=True)

    def __str__(self):
        return f"Оплата {self.amount} по заказу {self.order.uuid}"

@receiver(post_save, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """ Обновляет total_amount заказа при изменении товаров. """
    total_cost = instance.order.order_items.aggregate(total=Sum('cost_price'))['total'] or 0
    instance.order.total_amount = total_cost
    instance.order.save()

@receiver(post_save, sender=Payment)
def update_account_balance_on_create(sender, instance, created, **kwargs):
    """ Обновляет баланс счета при создании оплаты. """
    if created and instance.account:
        with transaction.atomic():
            instance.account.balance += instance.amount
            instance.account.save()

@receiver(pre_delete, sender=Payment)
def update_account_balance_on_delete(sender, instance, **kwargs):
    """ Обновляет баланс счета при удалении оплаты. """
    if instance.account:
        with transaction.atomic():
            instance.account.balance -= instance.amount
            instance.account.save()

@receiver(post_save, sender=Payment)
def update_order_payment_status(sender, instance, created, **kwargs):
    """
    Обновляет статус оплаты заказа и баланс счета при создании/изменении оплаты.
    """
    order = instance.order

    with transaction.atomic():
        if created:
            # Новая оплата
            order.account.balance += instance.amount
            order.account.save()
        else:
            # Изменение существующей оплаты
            original_payment = Payment.objects.get(pk=instance.pk)
            order.account.balance -= original_payment.amount
            order.account.balance += instance.amount
            order.account.save()

        total_paid = order.payment_set.aggregate(total=Sum('amount'))['total'] or 0

        if total_paid == order.total_amount:
            order.payment_status = 'paid'
        elif total_paid > 0:
            order.payment_status = 'partially_paid'
        else:
            order.payment_status = 'not_paid'

        order.save()

@receiver(pre_delete, sender=Payment)
def update_order_payment_status_on_delete(sender, instance, **kwargs):
    """
    Обновляет статус оплаты заказа и баланс счета при удалении оплаты.
    """
    order = instance.order

    with transaction.atomic():
        order.account.balance -= instance.amount
        order.account.save()

        total_paid = order.payment_set.aggregate(total=Sum('amount'))['total'] or 0

        if total_paid == order.total_amount:
            order.payment_status = 'paid'
        elif total_paid > 0:
            order.payment_status = 'partially_paid'
        else:
            order.payment_status = 'not_paid'

        order.save()