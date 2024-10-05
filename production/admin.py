from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (
    ProductionItem,
    TechnologicalMap,
    Stage,
    Operation,
    TechnologicalMapOperation,
    TechnologicalMapMaterial,
    Color,
)

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_tag')
    search_fields = ('name', 'color')




@admin.register(ProductionItem)
class ProductionItemAdmin(admin.ModelAdmin):
    list_display = ( 'name','get_photo','article', 'design_description', 'size',  'batch_number', 'cost_price')
    search_fields = ('name', 'article', 'batch_number')

    def get_photo(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="50"')

    get_photo.short_description = 'Изображения'

# @admin.register(TechnologicalMap)
# class TechnologicalMapAdmin(admin.ModelAdmin):
#     list_display = ('production_item', 'name', 'description')
#     search_fields = ('production_item__name', 'name')

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name',  'order')
    search_fields = ('name', 'order')

@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    list_filter = ('stage',)
    search_fields = ('name',)

class TechnologicalMapOperationInline(admin.TabularInline):
    """Вложенная таблица для операций в тех. карте"""
    model = TechnologicalMapOperation
    extra = 1  # Одна пустая строка для добавления новой операции
    fields = ('operation', 'piece_rate', 'time_norm', 'unit', 'details_quantity_per_product')

class TechnologicalMapMaterialInline(admin.TabularInline):
    """Вложенная таблица для материалов в тех. карте"""
    model = TechnologicalMapMaterial
    extra = 1  # Одна пустая строка для добавления нового материала
    fields = ('product', 'quantity', 'stock')

@admin.register(TechnologicalMap)
class TechnologicalMapAdmin(admin.ModelAdmin):
    """Админка для технологической карты"""
    list_display = ('production_item', 'name', 'description')
    search_fields = ('production_item__name', 'name')
    inlines = [TechnologicalMapOperationInline, TechnologicalMapMaterialInline] # Добавляем вложенные таблицы