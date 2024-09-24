from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Assignment, MaterialRequest, OperationLog, Cutting, Sewing, Cleaning, Ironing, Packing
)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',  'operation', 'stage', 'quantity', 'completed_quantity', 'status', 'user',
        'start_date', 'end_date'
    )
    list_filter = ('status', 'stage', 'user', 'operation')
    search_fields = ('order_item__order__id', 'operation__name')
    readonly_fields = ('completed_quantity',)

    # def order_item_link(self, obj):
    #     link = reverse("admin:order_orderitem_change", args=[obj.order_item.id])
    #     return format_html('<a href="{}">{}</a>', link, obj.order_item)
    #
    # order_item_link.short_description = "Позиция заказа"

@admin.register(MaterialRequest)
class MaterialRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'material', 'requested_quantity', 'issued_quantity', 'status')
    list_filter = ('status', 'material', 'assignment__order_item__order')
    search_fields = ('material__product__name', 'assignment__order_item__product__name')


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment', 'employee', 'operation', 'quantity', 'start_time', 'end_time', 'duration',
                    'status')
    list_filter = ('status', 'employee', 'operation', 'assignment__order_item__order')
    search_fields = ('employee__user__username', 'operation__name')


# Регистрация моделей этапов производства
@admin.register(Cutting)
class CuttingAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment_link', 'employee', 'quantity_cut', 'fabric_leftovers',
                    'fabric_waste', 'waste_reason', 'start_time', 'end_time')
    list_filter = ('employee', 'assignment__order_item__order')
    search_fields = ('employee__user__username', 'assignment__order_item__product__name')

    def assignment_link(self, obj):
        link = reverse("admin:manufactory_assignment_change", args=[obj.assignment.id])
        return format_html('<a href="{}">{}</a>', link, obj.assignment)

    assignment_link.short_description = "Задание"

@admin.register(Sewing)
class SewingAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment_link', 'employee', 'quantity_sewn', 'start_time', 'end_time')
    list_filter = ('employee', 'assignment__order_item__order')
    search_fields = ('employee__user__username', 'assignment__order_item__product__name')

    def assignment_link(self, obj):
        link = reverse("admin:manufactory_assignment_change", args=[obj.assignment.id])
        return format_html('<a href="{}">{}</a>', link, obj.assignment)

    assignment_link.short_description = "Задание"

@admin.register(Cleaning)
class CleaningAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment_link', 'employee', 'quantity_cleaned', 'start_time', 'end_time')
    list_filter = ('employee', 'assignment__order_item__order')
    search_fields = ('employee__user__username', 'assignment__order_item__product__name')

    def assignment_link(self, obj):
        link = reverse("admin:manufactory_assignment_change", args=[obj.assignment.id])
        return format_html('<a href="{}">{}</a>', link, obj.assignment)

    assignment_link.short_description = "Задание"

@admin.register(Ironing)
class IroningAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment_link', 'employee', 'quantity_ironed', 'start_time', 'end_time')
    list_filter = ('employee', 'assignment__order_item__order')
    search_fields = ('employee__user__username', 'assignment__order_item__product__name')

    def assignment_link(self, obj):
        link = reverse("admin:manufactory_assignment_change", args=[obj.assignment.id])
        return format_html('<a href="{}">{}</a>', link, obj.assignment)

    assignment_link.short_description = "Задание"

@admin.register(Packing)
class PackingAdmin(admin.ModelAdmin):
    list_display = ('id', 'assignment_link', 'employee', 'quantity_packed', 'start_time', 'end_time')
    list_filter = ('employee', 'assignment__order_item__order')
    search_fields = ('employee__user__username', 'assignment__order_item__product__name')

    def assignment_link(self, obj):
        link = reverse("admin:manufactory_assignment_change", args=[obj.assignment.id])
        return format_html('<a href="{}">{}</a>', link, obj.assignment)

    assignment_link.short_description = "Задание"