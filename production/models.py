from colorfield.fields import ColorField
from django.core.validators import MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete, pre_delete, pre_save
from django.dispatch import receiver
from django.db import transaction
from wms.models import Product, Stock, Warehouse
from django.db.models import Sum, F
from django.utils.safestring import mark_safe

class Color(models.Model):
    class Meta:
        verbose_name = 'Цвет'
        verbose_name_plural = verbose_name

    color = ColorField(default='#FF0000')
    name = models.CharField('Названия', max_length=50)

    def color_tag(self):
        return mark_safe(
            f'<div style="background-color: {self.color}; width: 30px; height: 30px; border-radius: 50%;"></div>')

    color_tag.short_description = 'Цвет'

    def __str__(self):
        return self.name



class ProductionItem(models.Model):
    class Meta:
        verbose_name = 'Карточка модели'
        verbose_name_plural = verbose_name

    """ Изделие в заказе на производство """
    name = models.CharField("Название", max_length=255)
    article = models.CharField("Артикул", max_length=50, blank=True)
    design_description = models.TextField("Описание дизайна", blank=True)
    size = models.CharField(max_length=255, verbose_name="Размеры")
    color = models.ManyToManyField(Color)
    batch_number = models.CharField("Номер партии", max_length=50, blank=True)

    # Себестоимость - теперь не редактируемое поле и свойство
    _cost_price = models.DecimalField("Себестоимость", max_digits=10, decimal_places=2, default=0, editable=False)

    @property
    def cost_price(self):
        """ Возвращает актуальное значение себестоимости. """
        if hasattr(self, '_cost_price'):
            return self._cost_price
        else:
            return self.update_cost_price()

    def update_cost_price(self):
        """
        Обновляет себестоимость ОДНОГО ProductionItem на основе
        данных TechnologicalMap.
        """
        self._cost_price = 0  # Используем _cost_price

        if hasattr(self, 'technological_map'):
            tech_map = self.technological_map

            # Расчет стоимости материалов для одного изделия
            self._cost_price += tech_map.materials.aggregate(
                total=Sum(F('product__selling_price') * F('quantity'))
            )['total'] or 0

            # Расчет стоимости операций для одного изделия
            self._cost_price += tech_map.operation.aggregate(
                total=Sum(F('piece_rate') * F('details_quantity_per_product'))
            )['total'] or 0

        self.save(update_fields=['_cost_price'])  # Обновляем _cost_price
        return self._cost_price

    def __str__(self):
        return f"{self.name}, {self.size}, {self.color.name}"



class TechnologicalMap(models.Model):
    class Meta:
        verbose_name = 'Технологическая карта'
        verbose_name_plural = verbose_name

    """ Технологическая карта изделия """
    production_item = models.OneToOneField(
        ProductionItem,
        on_delete=models.CASCADE,
        verbose_name="Изделие",
        related_name='technological_map'
    )
    name = models.CharField("Название карты", max_length=255)
    description = models.TextField("Описание", blank=True)

    def __str__(self):
        return f"Карта для {self.production_item.name}"

class Stage(models.Model):
    """Этап производства"""
    name = models.CharField("Название этапа", max_length=255)
    order = models.PositiveIntegerField("Порядок в тех. процессе", default=0)

    class Meta:
        verbose_name = 'Этапы'
        verbose_name_plural = verbose_name
        ordering = ['order']  # Сортировка по полю 'order'

    def __str__(self):
        return self.name

class Operation(models.Model):
    """Операция на этапе производства"""
    name = models.CharField("Название операции", max_length=255)
    description = models.TextField("Описание", blank=True)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, verbose_name="Этап производства")

    class Meta:
        verbose_name = 'Операции'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class TechnologicalMapOperation(models.Model):
    technological_map = models.ForeignKey(
        TechnologicalMap,
        on_delete=models.CASCADE,
        verbose_name="Технологическая карта",
        related_name='operation'
    )
    operation = models.ForeignKey(Operation, on_delete=models.PROTECT, verbose_name='Операция')
    piece_rate = models.DecimalField("Ставка за штуку", max_digits=8, decimal_places=2, default=0)
    time_norm = models.PositiveIntegerField("Норма времени (мин)", default=0)
    unit = models.CharField("Единица измерения", max_length=50, default="шт")
    details_quantity_per_product = models.PositiveIntegerField("Количество деталей на одно изделие", default=0)

    class Meta:
        verbose_name = 'Тех карта операции'
        verbose_name_plural = verbose_name

    def __str__(self):
        return str(self.operation)

class TechnologicalMapMaterial(models.Model):
    """ Материал в технологической карте """
    technological_map = models.ForeignKey(
        TechnologicalMap,
        on_delete=models.CASCADE,
        verbose_name="Технологическая карта",
        related_name='materials'
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Материал')
    quantity = models.DecimalField("Количество", max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    stock = models.ForeignKey(Warehouse, on_delete=models.PROTECT, verbose_name="Склад", null=True, blank=True)

    class Meta:
        verbose_name = 'Тех карта материала'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.product} в {self.technological_map}"

@receiver(pre_save, sender=TechnologicalMapMaterial)
@receiver(pre_save, sender=TechnologicalMapOperation)
def update_production_item_cost(sender, instance, **kwargs):
    """
    Обновляет себестоимость ProductionItem при создании, изменении
    или удалении материалов или операций в TechnologicalMap.
    """

    def update_cost():
        if hasattr(instance, 'technological_map'):
            instance.technological_map.production_item.update_cost_price()

    if instance.pk:  # Если объект уже существует (обновление или удаление)
        update_cost()
    else:  # Если объект новый (создание)
        transaction.on_commit(update_cost)