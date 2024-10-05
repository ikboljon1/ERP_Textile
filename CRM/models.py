
from django.db import models


class CounterpartyType(models.TextChoices):
    SUPPLIER = 'supplier', 'Поставщик'
    CUSTOMER = 'customer', 'Покупатель'


class Counterparty(models.Model):

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = verbose_name

    name = models.CharField("Название", max_length=255)
    inn = models.CharField("ИНН", max_length=20, blank=True)
    address = models.TextField("Адрес", blank=True)
    phone = models.CharField("Телефон", max_length=20, blank=True)
    email = models.EmailField("Email", blank=True)
    contact_name = models.CharField("Контактное лицо", max_length=255, blank=True)
    description = models.TextField("Комментарий", blank=True)
    counterparty_type = models.CharField("Тип контрагента", max_length=10,
                                         choices=CounterpartyType.choices, default=CounterpartyType.SUPPLIER)
    def __str__(self):
        return self.name
