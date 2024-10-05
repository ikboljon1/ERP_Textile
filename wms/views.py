from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F
from django.db import transaction

from .models import Product, POSCart, POSCartItem, POSOrder, POSOrderItem, Stock, Warehouse, ProductCategory

def pos_view(request):
    products = Product.objects.all()
    categories = ProductCategory.objects.all()
    warehouses = Warehouse.objects.all() #  Получите  все  склады
    cart = get_or_create_cart(request)

    context = {
        'products': products,
        'categories': categories,
        'warehouses': warehouses,  #  Передайте  склады  в  контекст
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
        'cart_items': list(cart.items.values('product__id', 'product__name', 'quantity', 'product__selling_price'))
    })

@require_POST
def update_sale_item_quantity(request):
    try:
        item_id = int(request.POST.get('item_id'))
        quantity = int(request.POST.get('quantity'))

        cart_item = POSCartItem.objects.get(pk=item_id)
        cart_item.quantity = quantity
        cart_item.save()

        #  Получаем  обновленную  сумму  для  позиции
        new_total_price = cart_item.product.selling_price * cart_item.quantity

        return JsonResponse({
            'success': True,
            'new_total_price': float(new_total_price),
            'new_quantity': cart_item.quantity  #  Возвращаем  новое  количество
        })
    except (ValueError, POSCartItem.DoesNotExist) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_POST
def delete_sale_item(request):
    item_id = request.POST.get('item_id')

    try:
        cart_item = POSCartItem.objects.get(pk=item_id)
        cart_item.delete()
        return JsonResponse({'success': True})
    except POSCartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Товар не найден в корзине'}, status=404)


@require_POST
@transaction.atomic
def complete_sale(request):
    cart = get_or_create_cart(request)
    if not cart.items.exists():
        return JsonResponse({'success': False, 'error': 'Корзина пуста!'})

    selected_warehouse_id = request.POST.get('warehouse_id')
    selected_warehouse = get_object_or_404(Warehouse, pk=selected_warehouse_id)

    try:
        with transaction.atomic():
            #  Создаем  заказ
            order = POSOrder.objects.create(
                warehouse=selected_warehouse
            )

            #  Создаем  позиции  заказа  и  обновляем  остатки
            for item in cart.items.all():
                POSOrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.selling_price
                )

                #  Получаем  остатки  на  складе
                stock = Stock.objects.select_for_update().get(
                    product=item.product,
                    warehouse=selected_warehouse
                )

                #  Проверяем  достаточно  ли  товара  на  складе
                if stock.quantity < item.quantity:
                    raise ValueError(f'Недостаточно  товара  "{item.product.name}"  на  складе!')

                #  Списываем  товар  со  склада
                stock.quantity -= item.quantity
                stock.save()

        #  Очищаем  корзину  после  успешного  завершения  транзакции
        cart.items.all().delete()
        request.session.pop('cart_id', None)
        return JsonResponse({'success': True})

    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)})

def search_products(request):
    query = request.GET.get('q', '')
    search_by = request.GET.get('search_by', 'name')  #  Параметр  для  выбора  поля  поиска

    if search_by == 'barcode':
        products = Product.objects.filter(barcode=query)
    else:
        products = Product.objects.filter(name__icontains=query)

    results = [{
        'id': product.id,
        'name': product.name,
        'barcode': product.barcode,
        'selling_price': float(product.selling_price),
        'quantity': Stock.objects.filter(product=product).values_list('quantity', flat=True).first() or 0
    } for product in products]

    return JsonResponse({'products': results})


@require_POST
def empty_cart(request):
    cart = get_or_create_cart(request)
    cart.items.all().delete()
    return JsonResponse({'success': True})
