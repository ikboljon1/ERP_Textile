# # manufactory/templatetags/dashboard_tags.py
#
# from django import template
# from django.db.models import Count, Avg, F, ExpressionWrapper, fields
# from manufactory.models import Stage, Operation  # Импортируйте модель Operation
#
# register = template.Library()
#
# @register.simple_tag
# def get_stage_data():
#    """ Возвращает данные для таблицы этапов. """
#    stages_data = []
#    for stage in Stage.objects.all():
#        # Получаем операции, связанные с текущим этапом
#        # (адаптируйте эту часть под связи ваших моделей)
#        operations = Operation.objects.filter(stage=stage)
#
#        total_operations = operations.count()
#        completed_operations = operations.filter(status='выполнено').count() # Адаптируйте под ваши статусы
#        in_progress_operations = operations.filter(status='в процессе').count()
#        overdue_operations = operations.filter(status='просрочено').count()
#
#        # Расчет среднего времени выполнения (в днях) - адаптируйте под ваши поля
#        average_duration = operations.filter(status='выполнено').annotate(
#            duration=ExpressionWrapper(F('completed_at') - F('created_at'), output_field=fields.DurationField())
#        ).aggregate(avg_duration=Avg('duration'))['avg_duration']
#
#        if average_duration:
#            average_duration = round(average_duration.total_seconds() / (60 * 60 * 24), 1)
#
#        stages_data.append({
#            'stage': stage,
#            'total_operations': total_operations, # Изменено
#            'completed_operations': completed_operations, # Изменено
#            'in_progress_operations': in_progress_operations, # Изменено
#            'overdue_operations': overdue_operations, # Изменено
#            'average_duration': average_duration
#        })
#    return stages_data