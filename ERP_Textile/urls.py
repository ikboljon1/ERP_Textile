from django.contrib import admin
from django.urls import path, include



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('admin_soft.urls')),
    path('pos/', include('wms.urls', namespace='wms')),  # Добавляем URL-ы приложения 'pos_app'
    path('order/', include('order.urls', namespace='get_orders')),
]