from django.core.validators import MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from wms.models import Product, Stock, Warehouse
from django.db.models import Sum, F

class ProductionItem(models.Model):
    """ Изделие в заказе на производство """
    name = models.CharField("Название", max_length=255)
    article = models.CharField("Артикул", max_length=50, blank=True)
    design_description = models.TextField("Описание дизайна", blank=True)
    size = models.CharField(max_length=255, verbose_name="Размеры")
    color = models.CharField("Цвет", max_length=50)
    batch_number = models.CharField("Номер партии", max_length=50, blank=True)
    cost_price = models.DecimalField("Себестоимость", max_digits=10, decimal_places=2, default=0, editable=False)
    def __str__(self):
        return f"{self.name}, {self.size}, {self.color}"

    def calculate_cost_price(self):
        """
        Рассчитывает себестоимость ОДНОГО ProductionItem на основе
        данных TechnologicalMap.
        """
        self.cost_price = 0

        if hasattr(self, 'technological_map'):
            tech_map = self.technological_map

            # Расчет стоимости материалов для одного изделия
            for material in tech_map.materials.all():
                try:
                    self.cost_price += material.product.selling_price * material.quantity
                except TypeError:
                    pass

            # Расчет стоимости операций для одного изделия
            for operation in tech_map.operation.all():
                self.cost_price += operation.piece_rate * operation.details_quantity_per_product

            def save(self, *args, **kwargs):
                self.calculate_cost_price()  # Вызываем calculate_cost_price перед сохранением
                super().save(*args, **kwargs)

        self.save(update_fields=['cost_price'])



class TechnologicalMap(models.Model):
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
        ordering = ['order']  # Сортировка по полю 'order'

    def __str__(self):
        return self.name

class Operation(models.Model):
    """Операция на этапе производства"""
    name = models.CharField("Название операции", max_length=255)
    description = models.TextField("Описание", blank=True)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, verbose_name="Этап производства")


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

    def __str__(self):
        return f"{self.product} в {self.technological_map}"

@receiver(post_save, sender=TechnologicalMapMaterial)
@receiver(post_save, sender=TechnologicalMapOperation)
def update_production_item_cost(sender, instance, **kwargs):
    """
    Обновляет себестоимость ProductionItem при
    изменении материалов или операций в TechnologicalMap.
    """
    if hasattr(instance, 'technological_map'):
        instance.technological_map.production_item.calculate_cost_price()

@receiver(pre_delete, sender=TechnologicalMapMaterial)
@receiver(pre_delete, sender=TechnologicalMapOperation)
def update_production_item_cost_on_delete(sender, instance, **kwargs):
    """
    Обновляет себестоимость ProductionItem
    ПЕРЕД УДАЛЕНИЕМ материалов или операций из TechnologicalMap.
    """
    if hasattr(instance, 'technological_map'):
        # Необходимо получить production_item до того, как instance будет удален
        production_item = instance.technological_map.production_item
        instance.delete()  # Удаляем материал/операцию
        production_item.calculate_cost_price()  # Пересчитываем себестоимость
