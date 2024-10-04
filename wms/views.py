from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F
from django.db import transaction

from .models import Product, POSCart, POSCartItem, POSOrder, POSOrderItem, Stock, Warehouse


def pos_view(request):
    products = Product.objects.all()
    cart = get_or_create_cart(request)
    context = {
        'products': products,
        'cart': cart,
    }
    return render(request, 'POS.html', context)


def get_or_create_cart(request):
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = POSCart.objects.get(id=cart_id)
        except POSCart.DoesNotExist:
            cart = POSCart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = POSCart.objects.create()
        request.session['cart_id'] = cart.id
    return cart

@require_POST
def add_item_to_sale(request):
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))

    product = get_object_or_404(Product, pk=product_id)
    cart = get_or_create_cart(request)

    cart_item, created = POSCartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return JsonResponse({
        'success': True,
        'product_id': product.id,
        'product_name': product.name,
        'product_price': float(product.selling_price),  # Convert to float
        'cart_items': list(cart.items.values('product__name', 'quantity', 'product__selling_price'))
    })

@require_POST
def update_sale_item_quantity(request):
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity'))

    cart_item = get_object_or_404(POSCartItem, pk=item_id)
    cart_item.quantity = quantity
    cart_item.save()

    # ... (логика расчета скидки и общей суммы)
    cart = cart_item.cart
    subtotal = cart.items.aggregate(total=Sum(F('product__selling_price') * F('quantity')))['total'] or 0
    total = subtotal  # Замените на расчет с учетом скидки

    return JsonResponse({
        'success': True,
        'new_total_price': float(cart_item.product.selling_price * cart_item.quantity),
        'sale_subtotal': float(subtotal),
        'sale_total': float(total),
        'cart_items': list(cart.items.values('product__name', 'quantity', 'product__selling_price'))
    })


@require_POST
def delete_sale_item(request):
    item_id = request.POST.get('item_id')
    cart_item = get_object_or_404(POSCartItem, pk=item_id)
    cart_item.delete()

    # ... (логика расчета скидки и общей суммы)
    cart = cart_item.cart
    subtotal = cart.items.aggregate(total=Sum(F('product__selling_price') * F('quantity')))['total'] or 0
    total = subtotal  # Замените на расчет с учетом скидки

    return JsonResponse({
        'success': True,
        'sale_subtotal': float(subtotal),
        'sale_total': float(total),
        'cart_items': list(cart.items.values('product__name', 'quantity', 'product__selling_price'))
    })

def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(barcode=query)
    )
    results = [{'id': product.id, 'name': product.name, 'barcode': product.barcode} for product in products]
    return JsonResponse({'products': results})

def empty_cart(request):
    cart = get_or_create_cart(request) #  Получите  корзину  из  сессии
    cart.items.all().delete() #  Очистите  элементы  корзины
    return JsonResponse({'success': True})

@require_POST
@transaction.atomic
def complete_sale(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        return JsonResponse({'success': False, 'error': 'Корзина пуста!'})

    # Получите выбранный склад (предполагается, что он отправляется с формы)
    selected_warehouse_id = request.POST.get('warehouse_id')
    selected_warehouse = get_object_or_404(Warehouse, pk=selected_warehouse_id)

    # Создание заказа POS (POSOrder)
    order = POSOrder.objects.create(
        warehouse=selected_warehouse,
        # ... (добавьте другие поля заказа)
    )

    # Создание позиций заказа (POSOrderItem) и обновление остатков
    for item in cart.items.all():
        POSOrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.selling_price
        )

        try:
            # Находим остатки на складе
            stock = Stock.objects.get(product=item.product, warehouse=selected_warehouse)
        except Stock.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Товар не найден на складе!'})

        # Проверяем, достаточно ли товара на складе
        if stock.quantity < item.quantity:
            return JsonResponse({
                'success': False,
                'error': f'Недостаточно товара "{item.product.name}" на складе!'
            })

        # Списываем товар со склада
        stock.quantity -= item.quantity
        stock.save()

    # Очищаем корзину
    cart.items.all().delete()
    request.session.pop('cart_id', None)

    return JsonResponse({'success': True})