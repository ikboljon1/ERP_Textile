from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import  Order, OrderItem
# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'name',
        'customer',
        'get_photo',
        'order_date',
        'due_date',
        # 'total_amount',
        'status',
        'priority',
        'sales_channel',
        'total_cost',
    )
    list_filter = (
        'status',
        'customer',
        'order_type',
        'priority',
        'sales_channel',
    )
    search_fields = ('customer__name', 'uuid')



    fieldsets = (
        ('Основная информация', {
            'fields': ('customer', 'uuid', 'due_date', 'created_by', 'status')
        }),
        ('Детали заказа', {
            'fields': ('order_type', 'priority', 'sales_channel', 'photo', 'comments')
        }),
        ('Информация о клиенте', {
            'fields': ('contact_person', 'delivery_method', 'delivery_address')
        }),
        ('Финансовая информация', {
            'fields': ('prepayment', 'expected_payment_date', 'discount')
        }),
        ('Производство', {
            'fields': ('planned_production_start', 'planned_shipment_date')
        }),
    )
    inlines = [OrderItemInline]

    def get_photo(self, obj):
        return mark_safe(f'<img src={obj.photo.url} width="50" height="50"')

    get_photo.short_description = 'Изображения'

admin.site.register(Order, OrderAdmin)

