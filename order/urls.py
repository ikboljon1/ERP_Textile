from django.urls import path
from . import views

app_name = 'order'
urlpatterns = [
    path('report/', views.OrderListView.as_view(), name='report_order'),
]