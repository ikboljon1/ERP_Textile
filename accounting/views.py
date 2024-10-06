# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import HttpResponse
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .models import Purchase
import os
from django.conf import settings
import json  # Для обработки JSON, если нужно

# Регистрация шрифта (путь должен быть корректным)
pdfmetrics.registerFont(TTFont('Ubuntu_Condensed', os.path.join(settings.BASE_DIR, 'accounting/static/fonts/Ubuntu_Condensed.ttf')))

def generate_purchase_receipt(request, purchase_id):
    try:
        purchase = Purchase.objects.get(pk=purchase_id)
    except Purchase.DoesNotExist:
        return HttpResponse("Покупка не найдена.", status=404)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="purchase_receipt_{purchase_id}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    story = []
    try:
        logo_path = os.path.join(settings.BASE_DIR, 'accounting/static/logo.png')
        logo = Image(logo_path, width=100, height=100)
        story.append(logo)
        story.append(Spacer(1, 12))
    except FileNotFoundError:
        print(f"Ошибка: Логотип не найден по пути: {logo_path}")
    except Exception as e:
        print(f"Ошибка при добавлении логотипа: {e}")

    style_normal = ParagraphStyle('Normal', parent=styles['Normal'], fontName='Ubuntu_Condensed')
    style_h2 = ParagraphStyle('Heading2', parent=styles['h2'], fontName='Ubuntu_Condensed')

    story.append(Paragraph(f"Чек на покупку № {purchase_id}", style_h2))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Дата: {purchase.date.strftime('%d.%m.%Y')}", style_normal))
    story.append(Paragraph(f"Счет: {purchase.account.name}", style_normal))
    story.append(Paragraph(f"Тип транзакции: {purchase.transaction_type.name}", style_normal))
    story.append(Paragraph(f"Количество: {purchase.quantity}", style_normal))
    story.append(Paragraph(f"Сумма: {purchase.amount}", style_normal))

    seller_info = Paragraph("<b>Название компании: Ak-Saray textile</b><br/>Адрес: ул. Примерная, д. 1<br/>Тел.: +7 (123) 456-78-90<br/>ИНН/КПП: 1234567890/123456789", style_normal)
    story.append(seller_info)
    story.append(Spacer(1, 12))


    # items_table_data = []
    # items_table_data.append(["Наименование", "Количество", "Цена", "Сумма"])

    # ВАРИАНТ 1:  Если данные в отдельных полях модели Purchase
    # items_table_data.append([purchase.item_name, purchase.quantity, purchase.price, purchase.quantity * purchase.price])


    # ВАРИАНТ 2: Если данные в JSON
    try:
        items_data = json.loads(purchase.items_json)  # Замените 'items_json' на имя поля
        for item in items_data:
            items_table_data.append([item['name'], item['quantity'], item['price'], item['quantity'] * item['price']])
    except (json.JSONDecodeError, AttributeError, TypeError, KeyError) as e: # ловим все возможные ошибки
        print(f"Ошибка обработки данных о товарах: {e}")


    # items_table = Table(items_table_data, colWidths=[150, 50, 50, 50], style=[('FONT', (0, 0), (-1, -1), 'Ubuntu_Condensed')])
    # story.append(items_table)
    # story.append(Spacer(1, 12))


    story.append(Paragraph(f"<b>Итого:</b> {purchase.amount}", style_normal))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response