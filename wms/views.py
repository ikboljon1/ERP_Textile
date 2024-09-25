from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import Product, Warehouse, Supplier, Receipt, ReceiptItem
from .serializers import ProductSerializer, WarehouseSerializer, SupplierSerializer, ReceiptSerializer, ReceiptItemSerializer

# Вьюха для работы с продуктами
class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# Вьюха для работы со складами
class WarehouseListCreateView(generics.ListCreateAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

# Вьюха для работы с поставщиками
class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

# Вьюха для работы с поступлениями
class ReceiptListCreateView(generics.ListCreateAPIView):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer

class ReceiptDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer

# Вьюха для работы с позициями поступления
class ReceiptItemListCreateView(generics.ListCreateAPIView):
    queryset = ReceiptItem.objects.all()
    serializer_class = ReceiptItemSerializer

class ReceiptItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ReceiptItem.objects.all()
    serializer_class = ReceiptItemSerializer
