from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from wms.models import Product, Stock  # Импортируем модель Material из вашего приложения wms
class Customer(models.Model):
    """Клиент"""
    name = models.CharField("Название", max_length=255)
    address = models.TextField("Адрес", blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)

    def __str__(self):
        return self.name

class Order(models.Model):
    """Заказ клиента"""
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name="Клиент")
    uuid = models.CharField("Номер заказа", max_length=50, blank=True)
    photo = models.ImageField("Фотография", upload_to='order_photos/', blank=True, null=True )
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
    prepayment = models.DecimalField(
        "Предоплата", max_digits=10, decimal_places=2, default=0
    )
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
    total_amount = models.DecimalField("Общая сумма", max_digits=10, decimal_places=2, default=0, editable=False)
    comments = models.TextField("Комментарии", blank=True)
    total_cost = models.DecimalField("Общая стоимость", max_digits=10, decimal_places=2, default=0, editable=False)

    def __str__(self):
        return f"Заказ №{self.uuid} от {self.order_date.strftime('%d.%m.%Y')}"

    def calculate_total_cost(self):
        """
        Рассчитывает общую стоимость заказа, суммируя
        стоимость всех позиций (OrderItem) в заказе.
        """
        self.total_cost = 0
        for order_item in self.order_items.all():
            self.total_cost += order_item.product.cost_price * order_item.quantity
        self.save(update_fields=['total_cost'])

class OrderItem(models.Model):
    """Позиция заказа"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey('production.ProductionItem', on_delete=models.PROTECT, verbose_name="Товар")
    quantity = models.PositiveIntegerField("Количество")
    color = models.CharField("Цвет", max_length=50)
    size = models.CharField("Размер", max_length=50)
    cost_price = models.DecimalField("Себестоимость", max_digits=10, decimal_places=2, default=0, editable=False)

@receiver(post_save, sender=OrderItem)
def update_order_cost_on_create_or_update(sender, instance, **kwargs):
    """ Обновляет общую стоимость заказа при СОЗДАНИИ или ОБНОВЛЕНИИ OrderItem """
    instance.order.calculate_total_cost()

@receiver(pre_delete, sender=OrderItem)
def update_order_cost_on_delete(sender, instance, **kwargs):
    """ Обновляет общую стоимость заказа ПЕРЕД УДАЛЕНИЕМ OrderItem """
    order = instance.order  # Сохраняем ссылку на заказ
    instance.delete()      # Удаляем позицию заказа
    order.calculate_total_cost()  # Пересчитываем стоимость заказа