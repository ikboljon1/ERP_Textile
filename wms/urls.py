from django.urls import path
from .views import (
    ProductListCreateView, ProductDetailView,
    WarehouseListCreateView, WarehouseDetailView,
    SupplierListCreateView, SupplierDetailView,
    ReceiptListCreateView, ReceiptDetailView,
    ReceiptItemListCreateView, ReceiptItemDetailView
)

urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('warehouses/', WarehouseListCreateView.as_view(), name='warehouse-list'),
    path('warehouses/<int:pk>/', WarehouseDetailView.as_view(), name='warehouse-detail'),
    path('suppliers/', SupplierListCreateView.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', SupplierDetailView.as_view(), name='supplier-detail'),
    path('receipts/', ReceiptListCreateView.as_view(), name='receipt-list'),
    path('receipts/<int:pk>/', ReceiptDetailView.as_view(), name='receipt-detail'),
    path('receipt-items/', ReceiptItemListCreateView.as_view(), name='receiptitem-list'),
    path('receipt-items/<int:pk>/', ReceiptItemDetailView.as_view(), name='receiptitem-detail'),
]
