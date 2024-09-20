# from  manufactory.models  import  Operation
# from HRM.models import Employee, Permission
# from django.shortcuts import get_object_or_404
# from HRM.models import Employee, Payroll
# from datetime import date
# from manufactory.models import EmployeeWorkContribution
# from production.models import TechnologicalMapOperation
#
# def calculate_payroll(employee: Employee, period: date = None) -> Payroll:
#     """ Рассчитывает и сохраняет зарплату сотрудника за определенный период. """
#
#     if not period:
#         period = date.today().replace(day=1)  # По умолчанию - текущий месяц
#
#     # 1. Оклад
#     salary = employee.salary or 0
#
#     # 2. Сдельная оплата (оптимизированный запрос):
#     piecework_earnings = 0
#     contributions = EmployeeWorkContribution.objects.filter(
#         employee=employee,
#         assignment__start_date__month=period.month,
#         assignment__start_date__year=period.year,
#     ).select_related(
#         'assignment',
#         'assignment__order',
#         'assignment__order__production_item',
#         'assignment__order__production_item__technological_map'
#     ).prefetch_related(
#         'assignment__order__production_item__technological_map__technological_map_operations'
#     )
#
#     for contribution in contributions:
#         # Используем get_object_or_404() для упрощения кода:
#         tech_map_operation = get_object_or_404(
#             TechnologicalMapOperation,
#             technological_map=contribution.assignment.order.production_item.technological_map,
#             operation=contribution.assignment.operation
#         )
#         operation_rate = tech_map_operation.piecework_rate
#
#         piecework_earnings += contribution.quantity * operation_rate
#
#     # 3. Итоговая сумма (пока без премий и штрафов)
#     total_salary = salary + piecework_earnings
#
#     # 4. Сохранение в Payroll (пока без премий и штрафов)
#     payroll, created = Payroll.objects.get_or_create(
#         employee=employee,
#         period=period,
#         defaults={
#             'salary': salary,
#             'total': total_salary,
#         }
#     )
#
#     if not created:
#         payroll.salary = salary
#         payroll.total = total_salary
#         payroll.save()
#
#     return payroll
#
# from django.contrib.contenttypes.models import ContentType
#
# def has_permission(user, permission_codename, model_class=None, obj=None):
#     """ Проверяет, имеет ли пользователь разрешение на выполнение действия. """
#     if user.is_superuser:
#         return True
#
#     # Получаем роль сотрудника
#     role = getattr(user, 'employee.role', None)
#     if not role:
#         return False
#
#     try:
#         content_type = ContentType.objects.get_for_model(model_class or obj.__class__)
#         permission = Permission.objects.get(
#             role=role,
#             content_type=content_type,
#             # Если нужна проверка на уровне объекта:
#             object_id=obj.pk if obj else None,
#             **{f"can_{permission_codename}": True}
#         )
#         return True
#     except Permission.DoesNotExist:
#         return False
#
