# class MaterialRequest(models.Model):
#     # ...
#
#     def reserve_material(self):
#         """ Резервирует материал """
#         if self.status == "requested":  # Только для новых заявок
#             try:
#                 stock = Stock.objects.get(product=self.material.product, warehouse=self.material.stock)
#                 if stock.quantity >= self.requested_quantity:
#                     # материала достаточно
#                     stock.quantity -= self.requested_quantity
#                     self.issued_quantity = self.requested_quantity
#                     self.status = "issued"  # Изменено на "Выдано"
#                 elif stock.quantity > 0:
#                     # материала частично достаточно
#                     self.issued_quantity = stock.quantity
#                     stock.quantity = 0
#                     self.status = "partially_issued"
#                 else:
#                     # материала нет в наличии
#                     self.status = "pending"  # или другой статус, например, "Ожидает"
#                 stock.save()
#                 self.save()
#             except Stock.DoesNotExist:
#                 # Обработка случая, если остатков для материала не найдено
#                 self.status = "error"
#                 self.save()
#
#     def cancel_reservation(self):
#         """ Отменяет резервирование, возвращает материал на склад """
#         if self.status in ["partially_issued", "issued"]:  # Только для выданных или частично выданных
#             try:
#                 stock = Stock.objects.get(product=self.material.product, warehouse=self.material.stock)
#                 stock.quantity += self.issued_quantity
#                 stock.save()
#                 self.issued_quantity = 0
#                 self.status = "canceled"  # или "requested", если заявка снова активна
#                 self.save()
#             except Stock.DoesNotExist:
#                 # Обработка случая, если остатков для материала не найдено
#                 self.status = "error"
#                 self.save()