from datetime import datetime

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from django.db.models import Sum
from django.urls import reverse
from django.utils.safestring import mark_safe

from order.models import Order
from .models import Role, Permission, Branch, Employee, Brigade, Sewing, NfcTag
from django.contrib.contenttypes.models import ContentType
from manufactory.models import OperationLog
from manufactory.utils import calculate_piecework_salary


class PermissionAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'can_view', 'can_create', 'can_edit', 'can_delete')
    list_filter = ('role', 'content_type')
    search_fields = ('role__name', 'content_type__app_label', 'content_type__model')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "content_type":
            app_labels = ['order', 'wms', 'manufactory', 'production', 'HRM']
            kwargs["queryset"] = ContentType.objects.filter(app_label__in=app_labels)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Permission, PermissionAdmin)

# Регистрируем остальные модели
admin.site.register(Branch)


@admin.register(Employee)
class EmployeeAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'position', 'branch', 'is_staff',)
    list_filter = ('branch', 'role', 'is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    actions = ['calculate_salary_action']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),  # Основные поля
        ('Личная информация', {'fields': ('first_name', 'last_name', 'email')}),  # Личная информация
        ('Информация о компании', {'fields': ('branch', 'position', 'hire_date',)}),  # Данные о работе
        ('Права', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups',)}),  # Права доступа
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),  # Даты
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'groups',),
        }),
    )

    # filter_horizontal = ('groups', 'user_permissions')

    # def save_related(self, request, obj, form, change):
    #     super().save_related(request, obj, form, change)  # Сохраняем связанные объекты
    #     if obj.role:  # Если роль назначена, применяем её
    #         obj.assign_role(obj.role)
    #
    # def calculate_salary_action(self, request, queryset):
    #     # Здесь добавьте логику для расчета зарплаты
    #     pass
    #
    # calculate_salary_action.short_description = "Рассчитать зарплату для выбранных сотрудников"

class CustomGroupAdmin(BaseGroupAdmin):
    def get_app_label(self):
        # Возвращаем метку приложения "HRM"
        return 'HRM'

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)

# @admin.register(Role)
# class RoleAdmin(admin.ModelAdmin):
#     list_display = ('name',)
#     search_fields = ('name',)

admin.site.register(Brigade)


# @admin.register(Sewing)
# class SewingAdmin(admin.ModelAdmin):
#     list_display = ('name', 'code', 'operations_info', 'calculated_salary')
#     readonly_fields = ('operations_info', 'calculated_salary')
#
#     def operations_info(self, obj):
#         """ Отображает список выполненных операций и их количество. """
#         operations = OperationLog.objects.filter(employee=obj) \
#             .values('operation__name', 'operation__piece_rate') \
#             .annotate(total_quantity=Sum('quantity'))
#
#         info = ""
#         for op in operations:
#             info += f"Операция: {op['operation__name']}, "
#             info += f"Ставка: {op['operation__piece_rate']} сом, "
#             info += f"Количество: {op['total_quantity']}<br>"
#         return info
#
#     operations_info.short_description = "Выполненные операции"
#     operations_info.allow_tags = True
#
#     def calculated_salary(self, obj):
#         """ Рассчитывает и отображает зарплату за текущий месяц.  """
#         salary = calculate_piecework_salary(obj, 2023, 10)
#         return f"{salary} сом"
#
#     calculated_salary.short_description = "Зарплата (текущий месяц)"

@admin.register(Sewing)
class SewingAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'calculated_salary')
    readonly_fields = ('operations_info', 'calculated_salary')

    def operations_info(self, obj, order_id=None):
        """ Отображает список выполненных операций и их количество для
        выбранного заказа.
        """
        operations = OperationLog.objects.filter(employee=obj)
        if order_id:
            operations = operations.filter(assignment__order_id=order_id)
        operations = operations.values('operation__operation__name', 'operation__piece_rate') \
            .annotate(total_quantity=Sum('quantity'))

        info = ""
        for op in operations:
            info += f"Операция: {op['operation__operation__name']}, "
            info += f"Ставка: {op['operation__piece_rate']} сом, "
            info += f"Количество: {op['total_quantity']}<br>"
        return mark_safe(info)

    def calculated_salary(self, obj):
        """ Рассчитывает зарплату за текущий месяц.  """
        now = datetime.now()
        salary = calculate_piecework_salary(obj, now.year, now.month)
        return f"{salary} сом"

    calculated_salary.short_description = "Зарплата (текущий месяц)"

    def changelist_view(self, request, extra_context=None):
        """ Добавляем форму для выбора заказа и периода в список сотрудников """
        extra_context = extra_context or {}
        extra_context['orders'] = Order.objects.all()
        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(NfcTag)
