# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from .models import NfcTag

@csrf_exempt  # Временно отключаем CSRF защиту для простоты примера
def nfc_auth(request):
    if request.method == 'POST':
        nfc_uid = request.POST.get('nfc_uid')
        if not nfc_uid:
            return JsonResponse({"error": "NFC UID не передан."}, status=400)

        try:
            nfc_tag = NfcTag.objects.get(uid=nfc_uid)
        except NfcTag.DoesNotExist:
            return JsonResponse({"error": "Метка не найдена."}, status=404)

        if not nfc_tag.employee:
            return JsonResponse({"error": "Метка не привязана к сотруднику."}, status=400)

        # Аутентификация пользователя
        user = nfc_tag.employee.user
        login(request, user)  # Выполняем вход пользователя в систему

        return JsonResponse({"success": True, "user_id": user.id})

    return JsonResponse({"error": "Метод не разрешен."}, status=405)
