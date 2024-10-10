from django import forms

class RFIDLoginForm(forms.Form):
    rfid_tag = forms.CharField(label='RFID Метка', max_length=255)