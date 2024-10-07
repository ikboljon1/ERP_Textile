from django.contrib import admin
from django.db.models import Sum
from django.utils.safestring import mark_safe

from .models import Order, OrderItem, Payment


# # Register your models here.
# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     extra = 1  # Можно добавить одну пустую форму для товара по умолчанию
#
# class PaymentInline(admin.TabularInline):
#     model = Payment
#     extra = 0  # Не показывать пустых форм для оплаты по умолчанию
#
# class OrderAdmin(admin.ModelAdmin):
#     list_display = (
#         'uuid',
#         'name',
#         'customer',
#         'get_photo',
#         'order_date',
#         'due_date',
#         'total_amount',
#         'status',
#         'priority',
#         'sales_channel',
#         'total_amount',
#         'total_cost',
#         'total_paid',
#         'remaining_amount',
#     )
#     list_filter = (
#         'status',
#         'customer',
#         'order_type',
#         'priority',
#         'sales_channel',
#     )
#     search_fields = ('customer__name', 'uuid')
#
#
#
#     fieldsets = (
#         ('Основная информация', {
#             'fields': ('customer', 'uuid', 'due_date', 'created_by', 'status')
#         }),
#         ('Детали заказа', {
#             'fields': ('order_type', 'priority', 'sales_channel', 'photo', 'comments')
#         }),
#         ('Информация о клиенте', {
#             'fields': ('contact_person', 'delivery_method', 'delivery_address')
#         }),
#         ('Финансовая информация', {
#             'fields': ('prepayment','total_amount','account_type', 'expected_payment_date', 'discount')
#         }),
#         ('Производство', {
#             'fields': ('planned_production_start', 'planned_shipment_date')
#         }),
#     )
#     inlines = [OrderItemInline, PaymentInline]  # Регистрируем Inline для OrderItem и Payment
#
#     def get_photo(self, obj):
#         return mark_safe(f'<img src={obj.photo.url} width="50" height="50"')
#
#     get_photo.short_description = 'Изображения'
#
#     def total_paid(self, obj):
#         total = obj.payment_set.aggregate(total=Sum('amount'))['total'] or 0
#         return total
#     total_paid.short_description = "Всего оплачено"
#
#     def remaining_amount(self, obj):
#         return obj.total_amount - self.total_paid(obj)
#     remaining_amount.short_description = "Остаток к оплате"
#
# admin.site.register(Order, OrderAdmin)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

class OrderAdmin(admin.ModelAdmin):

    list_display = ('uuid', 'customer', 'order_date', "total_cost",'total_amount', 'total_paid', 'remaining_amount', 'status', 'payment_status')
    list_filter = ('status', 'customer', 'order_date')
    inlines = [OrderItemInline, PaymentInline]
    readonly_fields = ('total_paid', 'remaining_amount')

    @admin.display(description='Всего оплачено')
    def total_paid(self, obj):
        return obj.payment_set.aggregate(total=Sum('amount'))['total'] or 0

    @admin.display(description='Остаток к оплате')
    def remaining_amount(self, obj):
        return obj.total_amount - self.total_paid(obj)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'payment_date', 'payment_method', 'account', 'comments')
    list_filter = ('payment_date', 'payment_method', 'account')
    search_fields = ('order__uuid', 'order__customer__name')

admin.site.register(Order, OrderAdmin)
admin.site.register(Payment, PaymentAdmin)