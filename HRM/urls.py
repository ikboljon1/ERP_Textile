from django.urls import path

from .views import nfc_login_view

app_name = 'hrm'
urlpatterns = [
  # ... другие URL
  path('nfc_login/', nfc_login_view, name='nfc_login'),
]