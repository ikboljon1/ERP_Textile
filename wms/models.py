from django.db import models
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
# Create your models here.
class ProductCategory(models.Model):
    """Категория товаров"""
    name = models.CharField("Название", max_length=255, unique=True)

    class Meta:
        verbose_name = "Категория товара"
        verbose_name_plural = "Категории товаров"

    def __str__(self):
        return self.name

class UnitOfMeasure(models.Model):
    """ Модель для единиц измерения """
    class Meta:
        verbose_name = "Единица измерения"
        verbose_name_plural = "Единицы измерения"

    name = models.CharField(max_length=50, verbose_name="Название")
    short_name = models.CharField(max_length=10, verbose_name="Краткое наименование")

    def __str__(self):
        return self.short_name


class Product(models.Model):
    """ Товар """
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, verbose_name="Категория", blank=True, null=True)
    name = models.CharField("Название", max_length=255)
    photo = models.ImageField("Фотография", upload_to='products/', blank=True, null=True)
    barcode = models.CharField("Штрих-код", max_length=50, blank=True, null=True)
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, verbose_name="Единица измерения")
    min_quantity = models.DecimalField("Мин. остаток", max_digits=10, decimal_places=2, default=0)
    manufacturer = models.CharField("Производитель", max_length=255, blank=True, null=True)
    brand = models.CharField("Бренд", max_length=255, blank=True, null=True)
    article = models.CharField("Артикул", max_length=50, blank=True, null=True)
    color = models.CharField("Цвет", max_length=50, blank=True, null=True)
    code = models.CharField("Код", max_length=50, blank=True, null=True)  # Дополнительный код
    weight = models.DecimalField("Граммаж", max_digits=10, decimal_places=2, blank=True, null=True)
    width = models.DecimalField("Ширина", max_digits=10, decimal_places=2, blank=True, null=True)
    hs_code = models.CharField("Код ТН ВЭД", max_length=20, blank=True, null=True)
    composition = models.CharField("Состав", max_length=255, blank=True, null=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, blank=True, null=True)
    selling_price = models.DecimalField("Цена продажи", max_digits=10, decimal_places=2, blank=True, null=True)
    min_selling_price = models.DecimalField("Мин. цена продажи", max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name

class Warehouse(models.Model):
    class Meta:
        verbose_name = 'Склад'
        verbose_name_plural = 'Склад'
    """Модель для представления склада"""
    name = models.CharField("Названия",max_length=255,unique=True)
    address = models.CharField("Адрес",max_length=255)
    description = models.TextField("Описание",blank=True,)
    type = models.CharField("тип",max_length=50, choices=[
        ('готовая_продукция', 'Склад готовой продукции'),
        ('сырье', 'Склад сырья'),
        ('продажи_готовой_продукции', 'Склад продаж готовой продукции'),
        ('продажи_материалов', 'Склад продаж материалов'),
        ('мобильный', 'Мобильный репозиторий'),
    ])
    def __str__(self):
        return self.name

class Supplier(models.Model):
    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщик'

    """Модель для хранения информации о поставщиках"""
    name = models.CharField("Название", max_length=255, unique=True)
    inn = models.CharField("ИНН", max_length=20, blank=True)
    address = models.TextField("Адрес", blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    contact_name = models.CharField("Контактное лицо", max_length=255, blank=True)
    description = models.TextField("Комментарий", blank=True)

    def __str__(self):
        return self.name
class VAT(models.Model):
    class Meta:
        verbose_name = 'НДС'
        verbose_name_plural = 'НДС'
    rate = models.DecimalField("Ставка НДС", max_digits=5, decimal_places=2)
    name = models.CharField("Название", max_length=50, blank=True)

    def __str__(self):
        return self.name


from django.db import models
from .models import Product, ProductCategory, UnitOfMeasure, Supplier, Warehouse, VAT


class Receipt(models.Model):
    """ Модель для общего поступления товаров/материалов """

    receipt_number = models.CharField("Номер поступления", max_length=50, unique=True, help_text="Уникальный номер поступления")
    receipt_date = models.DateTimeField("Дата поступления",auto_now_add=True)
    supplier = models.ForeignKey(Supplier,on_delete=models.PROTECT,verbose_name="Поставщик")
    warehouse = models.ForeignKey(Warehouse,on_delete=models.PROTECT,verbose_name="Склад")
    vat = models.ForeignKey(VAT,on_delete=models.SET_NULL,null=True,blank=True,verbose_name="НДС")
    transport_costs = models.DecimalField("Транспортные расходы", max_digits=10, decimal_places=2, default=0, null=True,blank=True)
    other_costs = models.DecimalField("Прочие расходы", max_digits=10, decimal_places=2, default=0)
    purchase_currency = models.CharField("Валюта покупки", max_length=3, default="USD")

    class Meta:
        verbose_name = "Поступление"
        verbose_name_plural = "Поступления"

    def __str__(self):
        return f"Поступление №{self.receipt_number} от {self.receipt_date.strftime('%d.%m.%Y')}"


class ReceiptItem(models.Model):
    """ Модель для позиции (строки) в поступления """

    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE,related_name='items', verbose_name="Поступление",null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, verbose_name="Категория", null=True)
    product = models.ForeignKey(Product,on_delete=models.PROTECT,verbose_name="Товар/Материал")
    roll = models.DecimalField("Рулон",max_digits=10,decimal_places=2, validators=[MinValueValidator(1)],blank=True, null=True )
    quantity = models.DecimalField("Количество кг/шт",max_digits=10,decimal_places=2, validators=[MinValueValidator(0.01)])  # Проверка на положительное значение
    price = models.DecimalField("Цена за единицу", max_digits=10,decimal_places=2, validators=[MinValueValidator(0.01)] ) # Проверка на положительное значение
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, verbose_name="Единица измерения")
    cost_price = models.DecimalField("Себестоимость", max_digits=10, decimal_places=2, default=0,)
    class Meta:
        verbose_name = "Позиция поступления"
        verbose_name_plural = "Позиции поступления"

    def __str__(self):
        return f"{self.product.name} ({self.quantity} {self.unit_of_measure.short_name})"

class Moving(models.Model):
    class Meta:
        verbose_name = 'Перемещения'
        verbose_name_plural = 'Перемещения'
    """ Модель для перемещения материалов между складами """
    product = models.ForeignKey('Product', on_delete=models.PROTECT, verbose_name='Материал')
    quantity = models.DecimalField('количество',max_digits=10, decimal_places=2)
    warehouse_from_where = models.ForeignKey('Warehouse', on_delete=models.PROTECT, related_name='перемещения_откуда', verbose_name='со склада')
    warehouse_where = models.ForeignKey('Warehouse', on_delete=models.PROTECT, related_name='перемещения_куда', verbose_name='на склад')
    move_date = models.DateTimeField('дата перемещения',auto_now_add=True)

class Stock(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name="Материал")
    warehouse = models.ForeignKey('Warehouse', on_delete=models.CASCADE, verbose_name="Склад")
    quantity = models.DecimalField("Количество", max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Остаток'
        verbose_name_plural = 'Остатки'
        unique_together = ['product', 'warehouse']

    def __str__(self):
        return self.product.name



class Return(models.Model):
    """ Возврат товара поставщику """
    receipt_item = models.ForeignKey(ReceiptItem, on_delete=models.CASCADE, verbose_name="Позиция поступления",null=True)
    return_date = models.DateTimeField("Дата возврата", auto_now_add=True)
    quantity = models.DecimalField("Количество", max_digits=10, decimal_places=2)
    reason = models.TextField("Причина возврата", blank=True)

    def __str__(self):
        return f"Возврат товара {self.receipt_item.product.name} от {self.return_date} (поступление №{self.receipt_item.receipt.receipt_number})"

