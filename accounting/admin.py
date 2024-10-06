from django.contrib import admin
from django.db.models import Sum
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export import resources
from manufactory.models import OperationLog
from order.models import Order
from .models import Account, Counterparty, Document, TransactionType, Expense, \
    WriteOff, Purchase
from rangefilter.filter import DateRangeFilter
from import_export.admin import ImportExportModelAdmin

@admin.register(TransactionType)
class TransactionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# class TransactionLineInline(admin.TabularInline):
#     model = TransactionLine
#     extra = 1  # Количество пустых строк для добавления

# @admin.register(Transaction)
# class TransactionAdmin(admin.ModelAdmin):
#     list_display = ('date', 'transaction_type', 'description', 'created_by', 'order', 'document')
#     list_filter = ('date', 'transaction_type', 'created_by', 'order')
#     search_fields = ('description', 'order__uuid')  #  Поиск по номеру заказа
#     inlines = [TransactionLineInline]
#
#     def save_model(self, request, obj, form, change):
#         obj.created_by = request.user
#         super().save_model(request, obj, form, change)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'account_type', 'currency_type','balance')
    list_filter = ('account_type', 'parent_account')
    search_fields = ('code', 'name')

@admin.register(Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'counterparty_type')
    list_filter = ('counterparty_type',)
    search_fields = ('name',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('document_type', 'number', 'date', 'counterparty')
    list_filter = ('document_type', 'date', 'counterparty')
    search_fields = ('number', 'counterparty__name')

# admin.site.register(TransactionLine)  # TransactionLine редактируется через Transaction
# @admin.register(Operation)
# class OperationAdmin(admin.ModelAdmin):
#     list_display = ('account', 'name')
#     list_filter = ('account',)  # Фильтрация по счету
#     search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('account', 'operation', 'amount')
    list_filter = ('account', 'operation')  # Фильтрация по счету и операции
    search_fields = ('operation__name',)  # Поиск по названию операции
    def has_change_permission(self, request, obj=None):
        """Запрещаем редактирование записей."""
        return False


@admin.register(WriteOff)
class WriteOffAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'product', 'warehouse', 'quantity')
    list_filter = ('transaction_type', 'product', 'warehouse')
    search_fields = ('product__name', 'warehouse__name')  # Поиск по названию товара и склада
    def has_change_permission(self, request, obj=None):
        """Запрещаем редактирование записей."""
        return False

class PurchaseResource(resources.ModelResource):
    class Meta:
        model = Purchase
        fields = ('account__name', 'transaction_type__name', 'quantity', 'amount', 'date')



@admin.register(Purchase)
class PurchaseAdmin(ImportExportModelAdmin):
    resource_class = PurchaseResource
    list_display = ('account', 'transaction_type', 'quantity', 'amount', 'date','receipt_link')
    list_filter = ('account', 'transaction_type',  ('date', DateRangeFilter)) # Добавляем date в list_filter
    search_fields = ('transaction_type__name',)

    def has_change_permission(self, request, obj=None):
        return False

    def receipt_link(self, obj):
        url = reverse('accounting:purchase_receipt', kwargs={'purchase_id': obj.pk})
        return format_html('<a href="{}" target="_blank">Чек</a>', url)

    receipt_link.short_description = "Чек"
    receipt_link.allow_tags = True
# @admin.register(Payroll)
# class PayrollAdmin(admin.ModelAdmin):
#     list_display = (
#         'get_employee', 'get_period_start', 'get_period_end', 'get_salary_amount', 'get_piecework_amount',
#         'get_total_accrued', 'get_total_deductions', 'get_total_amount', 'get_paid'
#     )
#     list_filter = ('employee__username', 'period_start', 'period_end', 'paid')  # Изменили list_filter
#     search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')
#     readonly_fields = (
#         'get_salary_amount', 'get_piecework_amount', 'get_piecework_details', 'get_bonus', 'get_overtime_hours',
#         'get_overtime_rate', 'get_other_allowances', 'get_allowance_details', 'get_taxes', 'get_tax_details',
#         'get_social_security', 'get_other_deductions', 'get_deduction_details', 'get_advance_amount',
#         'get_total_accrued', 'get_total_deductions', 'get_total_amount', 'get_paid'
#     )
#
#     actions = ['calculate_salary']
#
#     def get_employee(self, obj):
#         return obj.employee
#
#     get_employee.short_description = "Сотрудник"
#
#     def get_period_start(self, obj):
#         return obj.period_start
#
#     get_period_start.short_description = "Начало периода"
#
#     def get_period_end(self, obj):
#         return obj.period_end
#
#     get_period_end.short_description = "Конец периода"
#
#     def get_salary_amount(self, obj):
#         return obj.salary_amount
#
#     get_salary_amount.short_description = "Оклад за период"
#
#     def get_piecework_amount(self, obj):
#         return obj.piecework_amount
#
#     get_piecework_amount.short_description = "Сдельная оплата"
#
#     def get_piecework_details(self, obj):
#         return obj.piecework_details
#
#     get_piecework_details.short_description = "Детализация сдельной оплаты"
#
#     def get_bonus(self, obj):
#         return obj.bonus
#
#     get_bonus.short_description = "Премия"
#
#     def get_overtime_hours(self, obj):
#         return obj.overtime_hours
#
#     get_overtime_hours.short_description = "Сверхурочные часы"
#
#     def get_overtime_rate(self, obj):
#         return obj.overtime_rate
#
#     get_overtime_rate.short_description = "Ставка за сверхурочные"
#
#     def get_other_allowances(self, obj):
#         return obj.other_allowances
#
#     get_other_allowances.short_description = "Прочие надбавки"
#
#     def get_allowance_details(self, obj):
#         return obj.allowance_details
#
#     get_allowance_details.short_description = "Детализация надбавок"
#
#     def get_taxes(self, obj):
#         return obj.taxes
#
#     get_taxes.short_description = "Налоги"
#
#     def get_tax_details(self, obj):
#         return obj.tax_details
#
#     get_tax_details.short_description = "Детализация налогов"
#
#     def get_social_security(self, obj):
#         return obj.social_security
#
#     get_social_security.short_description = "Соц. отчисления"
#
#     def get_other_deductions(self, obj):
#         return obj.other_deductions
#
#     get_other_deductions.short_description = "Прочие вычеты"
#
#     def get_deduction_details(self, obj):
#         return obj.deduction_details
#
#     get_deduction_details.short_description = "Детализация вычетов"
#
#     def get_advance_amount(self, obj):
#         return obj.advance_amount
#
#     get_advance_amount.short_description = "Аванс"
#
#     def get_total_accrued(self, obj):
#         return obj.total_accrued
#
#     get_total_accrued.short_description = "Итого начислено"
#
#     def get_total_deductions(self, obj):
#         return obj.total_deductions
#
#     get_total_deductions.short_description = "Итого удержано"
#
#     def get_total_amount(self, obj):
#         return obj.total_amount
#
#     get_total_amount.short_description = "Итого к выплате"
#
#     def get_paid(self, obj):
#         return obj.paid
#
#     get_paid.short_description = "Выплачено"
#
#     def operations_info(self, obj, order_id=None):
#         """ Отображает список выполненных операций и их количество для
#         выбранного заказа.
#         """
#         operations = OperationLog.objects.filter(employee=obj.employee)
#         if order_id:
#             operations = operations.filter(assignment__order_id=order_id)
#         operations = operations.values('operation__operation__name', 'operation__piece_rate') \
#             .annotate(total_quantity=Sum('quantity'))
#
#         info = ""
#         for op in operations:
#             info += f"Операция: {op['operation__operation__name']}, "
#             info += f"Ставка: {op['operation__piece_rate']} сом, "
#             info += f"Количество: {op['total_quantity']}<br>"
#         return mark_safe(info)
#
#     def calculated_salary(self, obj):
#         """ Рассчитывает зарплату за текущий месяц.  """
#         obj.calculate_salary()
#         return f"{obj.total_amount} сом"
#
#     calculated_salary.short_description = "Зарплата (текущий месяц)"
#
#     def changelist_view(self, request, extra_context=None):
#         """ Добавляем форму для выбора заказа и периода в список сотрудников """
#         extra_context = extra_context or {}
#         extra_context['orders'] = Order.objects.all()
#         return super().changelist_view(request, extra_context=extra_context)
#
#
#     def calculate_salary(self, request, queryset):
#         for payroll in queryset:
#             payroll.calculate_salary()
#         self.message_user(request, f"Зарплата рассчитана для {queryset.count()} сотрудников.")
#
#     calculate_salary.short_description = "Рассчитать зарплату"