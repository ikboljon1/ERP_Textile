# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Assignment, MaterialRequest
#
# @receiver(post_save, sender=Assignment)
# def create_material_requests(sender, instance, created, **kwargs):
#     """ Создаем MaterialRequest после сохранения Assignment. """
#     if created:  # Только для новых Assignment
#         for material in instance.production_item.technological_map.materials.all():
#             MaterialRequest.objects.create(
#                 assignment=instance,
#                 material=material,
#                 requested_quantity=material.quantity * instance.quantity
#             )