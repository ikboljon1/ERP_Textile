from django.urls import path, include
from HRM.views import login_view


app_name= "admin"
urlpatterns = [
    # ... (другие URL-шаблоны)
    path('login/', login_view, name='login'),
    # ... (другие URL-шаблоны)
]
