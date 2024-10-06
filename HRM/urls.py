from django.urls import path
from . import views

urlpatterns = [
    path('nfc_auth/', views.nfc_auth, name='nfc_auth'), #  Добавьте этот путь
]