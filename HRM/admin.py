from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Role, Permission, Branch, Employee, Brigade
# from .utils import calculate_payroll, has_permission
from datetime import date
from django.contrib.contenttypes.models import ContentType



class PermissionInline(admin.TabularInline):
    model = Permission
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "content_type":
            # Ограничиваем выбор моделями (по желанию)
            app_labels = ['order', 'wms', 'manufactory', 'production', 'HRM']
            kwargs["queryset"] = ContentType.objects.filter(app_label__in=app_labels)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    inlines = [PermissionInline]

admin.site.register(Brigade)

# Регистрируем остальные модели
admin.site.register(Branch)

@admin.register(Employee)
class EmployeeAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'position', 'is_staff',)
    actions = ['calculate_salary_action']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Company info', {'fields': ('branch', 'position', 'hire_date', 'salary', 'role')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    filter_horizontal = ('groups', 'user_permissions')
