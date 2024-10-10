from django.contrib.auth.backends import BaseBackend
from .models import Employee, NfcTag

class RFIDBackend(BaseBackend):
    def authenticate(self, request, rfid_tag=None, **kwargs):
        if rfid_tag is not None:
            try:
                nfc_tag = NfcTag.objects.get(uid=rfid_tag)
                employee = nfc_tag.employee

                if employee is not None:
                    return employee
            except (NfcTag.DoesNotExist, Employee.DoesNotExist):
                return None

    def get_user(self, user_id):
        try:
            return Employee.objects.get(pk=user_id)
        except Employee.DoesNotExist:
            return None