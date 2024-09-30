from django.contrib import admin
from django.db.models import Sum
from django.utils.safestring import mark_safe
from prompt_toolkit.validation import ValidationError

from .models import Assignment, MaterialRequest, OperationLog, Defect, Cutting


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('order', 'current_stage', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'current_stage', 'order__customer')
    search_fields = ('order__uuid', 'order__customer__name')

    readonly_fields = ('cutting_info','actual_operations', 'material_consumption')

    class Media:
        css = {
            "all": ("css/admin.css",)  # Путь к вашему CSS-файлу
        }

    def get_cutting_data(self, obj):
        """ Возвращает данные о крое для каждой позиции заказа. """
        cutting_data = []
        for order_item in obj.order.order_items.all():
            #  Изменение: проходим по всем Cutting, связанным с order_item
            for cutting in order_item.cutting_set.all():
                planned_cutting = order_item.quantity
                completed_cutting = cutting.quantity
                remaining_cutting = planned_cutting - completed_cutting
                cutting_data.append({
                    'order_item': order_item,
                    'planned_quantity': planned_cutting,
                    'completed_quantity': completed_cutting,
                    'remaining_quantity': remaining_cutting,
                    'fabric_leftovers': cutting.fabric_leftovers,
                    'fabric_waste': cutting.fabric_waste,
                    'waste_reason': cutting.waste_reason,
                })
        return cutting_data

    def display_cutting_table(self, cutting_data):
        """ Формирует HTML-код таблицы с информацией о крое. """
        if cutting_data:
            html = "<table><tr><th>Позиция заказа</th><th>План</th><th>Факт</th><th>Осталось</th><th>Остатки ткани</th><th>Отходы ткани</th><th>Причина отходов</th></tr>"
            for cutting in cutting_data:
                html += f"<tr><td>{cutting['order_item']}</td><td>{cutting['planned_quantity']}</td><td>{cutting['completed_quantity']}</td><td>{cutting['remaining_quantity']}</td><td>{cutting['fabric_leftovers']}</td><td>{cutting['fabric_waste']}</td><td>{cutting['waste_reason']}</td></tr>"
            html += "</table>"
            return mark_safe(html)
        return '-'

    def cutting_info(self, obj):
        """ Отображает информацию о крое в админке Assignment. """
        cutting_data = self.get_cutting_data(obj)
        return self.display_cutting_table(cutting_data)

    cutting_info.short_description = "Информация о крое"

    def actual_operations(self, obj):
        operations_data = obj.get_actual_operations_data()
        planned_operations_data = obj.get_planned_operations_data()

        if operations_data:
            html = "<table><tr><th>Операция</th><th>План</th><th>Факт</th><th>Осталось</th></tr>"
            for op_data in operations_data:
                operation_name = op_data['operation']
                planned_quantity = next((item['planned_quantity'] for item in planned_operations_data if
                                         item['operation'].operation.name == operation_name), 0)
                remaining_quantity = planned_quantity - op_data['completed_quantity']
                html += f"<tr><td>{operation_name}</td><td>{planned_quantity}</td><td>{op_data['completed_quantity']}</td><td>{remaining_quantity}</td></tr>"
            html += "</table>"
            return mark_safe(html)
        return '-'

    actual_operations.short_description = "Операции (план/факт)"  # Изменили описание


    def material_consumption(self, obj):
        """ Отображает плановый и фактический расход материалов. """
        order_item = obj.order.order_items.first()

        if not order_item:  # Проверка на случай, если order_items пуст
            return '-'

        html = "<table><tr><th>Материал</th> <th>План</th> <th>Факт</th> <th>Осталось</th></tr>"

        if hasattr(order_item.product, 'technological_map'):
            for material in order_item.product.technological_map.materials.all():
                planned_consumption = material.quantity * order_item.quantity
                issued_quantity = \
                obj.materialrequest_set.filter(material=material).aggregate(total_issued=Sum('issued_quantity'))[
                    'total_issued'] or 0
                remaining_quantity = planned_consumption - issued_quantity
                html += f"<tr><td>{material.product.name}</td><td>{planned_consumption:.2f}</td><td>{issued_quantity:.2f}</td> <td>{remaining_quantity:.2f}</td></tr>"

        html += "</table>"
        return mark_safe(html)

    material_consumption.short_description = "Расход материалов"

@admin.register(Cutting)
class CuttingAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'order_item', 'quantity', 'map' )
    list_filter = ('assignment',)

@admin.register(MaterialRequest)
class MaterialRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'material', 'requested_quantity', 'issued_quantity', 'status')
    list_filter = ('status', 'material__product')

@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'employee', 'operation', 'quantity', 'defect_quantity', 'status', 'start_time', 'end_time', 'duration')
    list_filter = ('status', 'operation', 'employee')

    #  Автоматически рассчитываем duration при сохранении
    def save_model(self, request, obj, form, change):
        if obj.end_time and obj.start_time:
            obj.duration = obj.end_time - obj.start_time
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """ Модифицируем форму для OperationLog. """
        form = super().get_form(request, obj, **kwargs)

        def clean_quantity(self):
            """ Проверяет, что количество не больше планового. """
            data = self.cleaned_data
            quantity = data.get('quantity')
            operation = data.get('operation')
            order_item = data.get('order_item')

            if quantity and operation and order_item:
                planned_quantity = operation.details_quantity_per_product * order_item.quantity
                if quantity > planned_quantity:
                    raise ValidationError(
                        f"Количество не может быть больше планового ({planned_quantity})."
                    )
            return quantity

        # "Внедряем" метод clean_quantity в форму
        form.clean_quantity = clean_quantity
        return form

@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'employee', 'operation', 'quantity', 'description', 'created_at')
    list_filter = ('assignment', 'employee', 'operation')

admin.site.site_title = 'Ak-Saray'
admin.site.site_header = 'Ak-Saray'