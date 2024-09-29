from django.contrib import admin
from .models import Assignment, MaterialRequest, OperationLog, Defect, Cutting


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'start_date', 'end_date','status',)
    list_filter = ('status',)

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

@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'employee', 'operation', 'quantity', 'description', 'created_at')
    list_filter = ('assignment', 'employee', 'operation')

admin.site.site_title = 'Ak-Saray'
admin.site.site_header = 'Ak-Saray'