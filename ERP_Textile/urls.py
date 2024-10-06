from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('admin_soft.urls')),
    path('pos/', include('wms.urls', namespace='wms')),
    path('order/', include('order.urls', namespace='get_orders')),
    path('accounting/', include('accounting.urls', namespace='accounting')),
    path('hrm', include('HRM.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)