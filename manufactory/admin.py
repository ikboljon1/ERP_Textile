from django.contrib import admin
from .models import Assignment, MaterialRequest, OperationLog, Defect


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_item',  'brigade', 'quantity', 'completed_quantity', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'brigade')


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

@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'employee', 'operation', 'quantity', 'description', 'created_at')
    list_filter = ('assignment', 'employee', 'operation')
