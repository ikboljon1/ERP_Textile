# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from .models import NfcTag
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.contrib.auth import login
from .models import NfcTag
from django.contrib.auth.models import User  # Добавьте импорт User
from rest_framework.authtoken.models import Token # Если используете token authentication
from django.core.exceptions import ObjectDoesNotExist # Для обработки общего исключения
# @csrf_exempt  # Временно отключаем CSRF защиту для простоты примера
# def nfc_auth(request):
#     if request.method == 'POST':
#         nfc_uid = request.POST.get('nfc_uid')
#         if not nfc_uid:
#             return JsonResponse({"error": "NFC UID не передан."}, status=400)
#
#         try:
#             nfc_tag = NfcTag.objects.get(uid=nfc_uid)
#         except NfcTag.DoesNotExist:
#             return JsonResponse({"error": "Метка не найдена."}, status=404)
#
#         if not nfc_tag.employee:
#             return JsonResponse({"error": "Метка не привязана к сотруднику."}, status=400)
#
#         # Аутентификация пользователя
#         user = nfc_tag.employee.user
#         login(request, user)  # Выполняем вход пользователя в систему
#
#         return JsonResponse({"success": True, "user_id": user.id})
#
#     return JsonResponse({"error": "Метод не разрешен."}, status=405)

# @ensure_csrf_cookie  # Для GET-запросов, чтобы установить CSRF-токен
# @csrf_protect  # Для POST-запросов, чтобы проверить CSRF-токен
# def nfc_auth(request):
#     if request.method == 'POST':
#         nfc_uid = request.POST.get('nfc_uid')
#         if not nfc_uid:
#             return JsonResponse({"error": "NFC UID не передан."}, status=400)
#
#         try:
#             nfc_tag = NfcTag.objects.get(uid=nfc_uid)
#             user = nfc_tag.employee.user if nfc_tag.employee else None
#             if user:
#                  login(request, user)
#
#                  #  Вариант 1:  Просто id пользователя
#                  # return JsonResponse({"success": True, "user_id": user.id})
#
#                  #  Вариант 2:  Сериализатор (рекомендуется)
#                  # from rest_framework import serializers # Импортируйте serializers
#
#                  # class UserSerializer(serializers.ModelSerializer):
#                  #     class Meta:
#                  #         model = User
#                  #         fields = ('id', 'username', 'first_name', 'last_name') #  Добавьте нужные поля
#
#                  # serializer = UserSerializer(user)
#                  # return JsonResponse({"success": True, "user": serializer.data})
#
#                  # Вариант 3: Token authentication (если используется DRF)
#                  token, _ = Token.objects.get_or_create(user=user)
#                  return JsonResponse({"success": True, "token": token.key})
#
#
#
#
#             else:
#                 return JsonResponse({"error": "Метка не привязана к сотруднику."}, status=400)
#
#
#
#         except ObjectDoesNotExist:  # Общая обработка исключений
#             return JsonResponse({"error": "Метка не найдена или произошла другая ошибка."}, status=404)
#         except Exception as e: # Ловим все остальные исключения
#              return JsonResponse({"error": f"Произошла ошибка: {str(e)}"}, status=500)
#
#
#
#     return JsonResponse({"error": "Метод не разрешен."}, status=405)

from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt  # Временно!
from django.http import JsonResponse
from .models import NfcTag, Employee
from django.contrib.auth import login

@csrf_exempt  # ВАЖНО: Замените на безопасный механизм!
def nfc_login_view(request):
    """ Обрабатывает POST запрос от NFC считывателя. """
    if request.method == 'POST':
        nfc_uid = request.POST.get('nfc_uid')
        if not nfc_uid:
            return JsonResponse({'error': 'NFC UID не найден'}, status=400)

        try:
            nfc_tag = NfcTag.objects.get(uid=nfc_uid)
        except NfcTag.DoesNotExist:
            return JsonResponse({'error': 'Метка не найдена'}, status=404)

        employee = nfc_tag.employee
        if employee and employee.is_active:
            login(request, employee)  # Выполняем вход пользователя
            return redirect('home')  # Перенаправляем на главную
        else:
            return JsonResponse({'error': 'Ошибка аутентификации'}, status=401)

    return JsonResponse({'error': 'Неверный метод запроса'}, status=405)