from django.urls import path
from . import views

app_name = 'wms'

urlpatterns = [
    path('', views.pos_view, name='pos'),
    path('add-item-to-sale/', views.add_item_to_sale, name='add_item_to_sale'),
    path('update-sale-item-quantity/', views.update_sale_item_quantity, name='update_sale_item_quantity'),
    path('delete-sale-item/', views.delete_sale_item, name='delete_sale_item'),
    path('complete-sale/', views.complete_sale, name='complete_sale'),
    path('search-products/', views.search_products, name='search_products'),
    path('empty-cart/', views.empty_cart, name='empty_cart'),
]