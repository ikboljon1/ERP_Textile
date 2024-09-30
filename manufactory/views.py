from django.shortcuts import render
from .models import Order, OrderItem, OperationLog # Импортируйте ваши модели
from .models import get_produced_quantity_for_order_operation, get_remaining_quantity_for_order_operation

def production_monitoring(request, order_id):
    order = Order.objects.get(pk=order_id)

    context = {
        'order': order,
        'get_produced_quantity_for_order_operation': get_produced_quantity_for_order_operation,
        'get_remaining_quantity_for_order_operation': get_remaining_quantity_for_order_operation,
    }
    return render(request, 'Template/monitoring.html', context)