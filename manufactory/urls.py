from django.urls import path
from . import views

urlpatterns = [
    # ... ваши существующие URL-адреса ...
    path('<int:order_id>/monitoring/', views.production_monitoring, name='monitoring'),
]