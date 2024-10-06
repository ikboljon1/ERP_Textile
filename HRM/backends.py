from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .models import NfcTag

class MyBackend(BaseBackend):
    def authenticate(self, request, token=None):
        print('aaaa')
        if token: #  Если токен передан (любой)
            try:
                user = User.objects.get(username='lucky') #  Замените 'testuser' на имя вашего тестового пользователя
                return user
            except User.DoesNotExist:
                return None # Или создайте тестового пользователя здесь, если его нет.
        return None


    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None