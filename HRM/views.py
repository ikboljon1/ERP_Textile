from .models import NfcTag
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt  # Добавь это для CSRF-защиты

#100% Рабочий
def login_view(request):
    if request.method == 'POST':
        rfid_tag = request.POST.get('rfid_tag')
        if rfid_tag:
            user = None
            try:
                nfc_tag = NfcTag.objects.get(uid=rfid_tag)
                user = nfc_tag.employee
            except NfcTag.DoesNotExist:
                pass

            if user is not None:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                if user.is_staff:  # Проверяем, есть ли права администратора
                    return redirect('admin:index')  # Перенаправляем в админку
                else:
                    return redirect('home')

    return render(request, 'login.html')