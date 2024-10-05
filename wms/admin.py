from django.contrib import admin
from django.db.models import Sum
from django import forms
# Register your models here.
from wms.models import Product, Warehouse, Receipt, ReceiptItem, Moving, VAT, Stock, ProductCategory, \
    UnitOfMeasure, Return, POSOrderItem, POSOrder


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name','category','color','barcode', 'composition','hs_code', 'price')  # Поля, отображаемые в списке
    list_filter = ('name','category','color','barcode', 'composition','hs_code', 'price')  # Фильтры в списке
    search_fields = ('name', 'barcode','color', 'price')
admin.site.register(ProductCategory)

class StockInline(admin.TabularInline):
    model = Stock
    extra = 0

class WarehouseWithStockProxy(Warehouse):
    class Meta:
        proxy = True
        verbose_name = "Склад и остатки"
        verbose_name_plural = "Склады и остатки"

class WarehouseWithStockAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'type', 'get_stock_count')
    inlines = [StockInline]

    def get_stock_count(self, obj):
        total_quantity = obj.stock_set.aggregate(total=Sum('quantity'))['total']
        return total_quantity or 0  # Возвращаем 0, если total is None

    get_stock_count.short_description = "Общее количество товаров"

admin.site.register(WarehouseWithStockProxy, WarehouseWithStockAdmin)

class ReceiptItemInline(admin.TabularInline):
    model = ReceiptItem
    list_display = ('product', 'quantity', 'price','cost_price', 'unit_of_measure')
    search_fields = ('product', 'quantity', 'price', 'cost_price', 'unit_of_measure')
    readonly_fields = ('cost_price',)

class  ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'supplier','warehouse','receipt_date')
    search_fields = ('receipt_number', 'supplier','warehouse','receipt_date')


    def has_change_permission(self, request, obj=None):
        """Запрещаем редактирование записей."""
        return False

    inlines = [ReceiptItemInline]

admin.site.register(Receipt, ReceiptAdmin)


# class SupplierAdmin(admin.ModelAdmin):
#     list_display = ('name','inn', 'address','email', 'phone')
#     search_fields = ('name','inn', 'address','email', 'phone')
# admin.site.register(Supplier, SupplierAdmin)

class MovingAdmin(admin.ModelAdmin):
    list_display = ('product','warehouse_from_where','warehouse_where','quantity','move_date')
    search_fields = ('product','warehouse_from_where','warehouse_where','quantity','move_date')

    def has_change_permission(self, request, obj=None):
        """Запрещаем редактирование записей."""
        return False

admin.site.register(Moving, MovingAdmin)

class unitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ('name','short_name')
    search_fields = ('name','short_name')
admin.site.register(UnitOfMeasure, unitOfMeasureAdmin)

@admin.register(VAT)
class VATAdmin(admin.ModelAdmin):
    list_display = ('name','rate')
    search_fields = ('name','rate')



@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('receipt_item', 'quantity', 'return_date', 'reason')
    list_filter = ('receipt_item__product', 'return_date')
    search_fields = ('receipt_item__product__name', 'reason')

    def get_product(self, obj):
        return obj.receipt_item.product
    get_product.short_description = 'Товар'
    get_product.admin_order_field = 'receipt_item__product'

class POSOrderItemInline(admin.TabularInline):
    model = POSOrderItem
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'product':
            # Добавляем JavaScript код для обработки ввода в выпадающий список
            kwargs['widget'] = forms.Select(attrs={'onchange': 'handleBarcode(this)'})
            # ... (остальной код обработки barcode из request.GET)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        js = ('wms/js/admin_custom.js',)  # Путь к вашему JS файлу


@admin.register(POSOrder)
class POSOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_date', 'completed', 'warehouse',
                    'total_amount')
    list_filter = ('completed', 'order_date', 'warehouse',)
    search_fields = ('id','order_date', 'completed', 'warehouse__posorder__completed')
    readonly_fields = ('total_amount',)
    inlines = [POSOrderItemInline]

    actions = ['complete_orders']

    def complete_orders(self, request, queryset):
        for order in queryset:
            order.complete_order()
        self.message_user(request, f"{queryset.count()} заказов успешно завершены.")

    complete_orders.short_description = " завершить выбранные заказы"
# class StockAdmin(admin.ModelAdmin):
#     list_display = ('warehouse','material','quantity')
#     search_fields = ('warehouse','material','quantity')
# admin.site.register(Stock, StockAdmin)