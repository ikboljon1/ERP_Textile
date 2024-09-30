from django.db.models import Sum
from datetime import date, timedelta
from .models import OperationLog, TechnologicalMapOperation

def calculate_piecework_salary(employee, year, month):
    """
    Рассчитывает сдельную зарплату сотрудника (Sewing) за указанный месяц.
    """
    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=31)).replace(day=1)

    operations = OperationLog.objects.filter(
        employee=employee,
        start_time__range=[start_date, end_date]
    )

    grouped_operations = operations.values('operation').annotate(total_quantity=Sum('quantity'))

    total_salary = 0
    for op in grouped_operations:
        operation_id = op['operation']
        total_quantity = op['total_quantity']

        piece_rate = TechnologicalMapOperation.objects.get(id=operation_id).piece_rate
        total_salary += total_quantity * piece_rate

    return total_salary