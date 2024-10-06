from django.urls import path
from .views import generate_purchase_receipt

app_name = 'accounting'  # Замените your_app_name на имя вашего приложения

urlpatterns = [
    # ... другие URL-шаблоны вашего приложения ...
    path('purchase/<int:purchase_id>/receipt/', generate_purchase_receipt, name='purchase_receipt'),
    # ...
]