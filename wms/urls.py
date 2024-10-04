from django.urls import path
from . import views

app_name = 'wms'
urlpatterns = [
    path('pos/', views.pos_view, name='pos_view'),
    path('add_item_to_sale/', views.add_item_to_sale, name='add_item_to_sale'),
    path('update_sale_item_quantity/', views.update_sale_item_quantity, name='update_sale_item_quantity'),
    path('delete_sale_item/', views.delete_sale_item, name='delete_sale_item'),
    path('search_products/', views.search_products, name='search_products'),
    path('complete_sale/', views.complete_sale, name='complete_sale'),
    path('empty_cart/', views.empty_cart, name='empty_cart'),
]