from django.db.models import Q
from django.views.generic import ListView
from django.http import JsonResponse
from .models import Order

from django.views.generic import ListView
from django.http import JsonResponse
from .models import Order  # Импортируйте вашу модель Order

class OrderListView(ListView):
    model = Order
    template_name = 'report_order1.html'  # Путь к вашему шаблону

    def get_queryset(self):
        queryset = super().get_queryset()

        # Поиск
        query = self.request.GET.get('search')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |  # Поиск по имени заказа
                Q(status__icontains=query)  # Поиск по статусу
                # ... другие поля для поиска
            )

        # Фильтрация по дате
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(due_date__lte=end_date)

        return queryset

    def get(self, request, *args, **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # AJAX-запрос
            orders = Order.objects.all()
            orders_data = [
                {
                    'id': order.id,
                    'name': order.name,
                    'order_date': order.order_date.strftime('%Y-%m-%d'),
                    'due_date': order.due_date.strftime('%Y-%m-%d'),
                    'completion': order.completion,
                    'status': order.status
                }
                for order in orders
            ]
            return JsonResponse({'orders': orders_data})
        else:
            # Обычный запрос - отображаем шаблон
            return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for order in context['object_list']:
            order.status_class = self.get_status_class(order.status)
        return context

    def get_status_class(self, status):
        status_classes = {
            'Выполнено': 'bg-success',
            'Отменено': 'bg-danger',
            'Заблокировать': 'bg-warning',
            'Выполняется': 'bg-info',
            # ... другие статусы
        }
        return status_classes.get(status, 'bg-secondary')  # Класс по умолчанию