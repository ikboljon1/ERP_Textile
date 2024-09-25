# # serializers.py
# from rest_framework import serializers
# from .models import Assignment, Cutting
#
# class AssignmentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Assignment
#         fields = ['id', 'order_item', 'quantity', 'status'] # Добавьте нужные поля
#
# class CuttingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Cutting
#         fields = ['id', 'assignment', 'employee', 'quantity_cut']    # Добавьте нужные поля