from django.contrib import admin
from .models import Customer, Order, OrderItem
# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'customer',
        'order_date',
        'due_date',
        'total_amount',
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



admin.site.register(Customer)
admin.site.register(Order, OrderAdmin)

