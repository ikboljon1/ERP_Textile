from django.db import models
from HRM.models import Sewing
# Create your models here.
class ManufatoryWages(models.Model):
    name = models.ForeignKey(Sewing.name, on_delete=models.CASCADE)