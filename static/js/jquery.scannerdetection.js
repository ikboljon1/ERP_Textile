$(document).ready(function() {

    //Обработка выбора товара
    $('.product-card').on('click', function() {
        var productId = $(this).data('product-id');
        var productName = $(this).data('product-name');
        var productPrice = $(this).data('product-price');

        // Добавление товара в корзину (AJAX запрос)
        $.ajax({
            url: '{% url "add_item_to_sale" %}',
            type: 'POST',
            data: {
                'product_id': productId,
                'quantity': 1,
                // Добавьте CSRF токен, если требуется
            },
            dataType: 'json',
            success: function(data) {
                if (data.success) {
                  console.log("Товар успешно добавлен");
                  updateCartTable(data);
                } else {
                  alert(data.error);
                }
            },
            error: function() {
                alert('Произошла ошибка при добавлении товара.');
            }
        });
    });

      // Функция для обновления таблицы корзины
    function updateCartTable(data) {
        var itemId = data.product_id;
        var existingRow = $('#cart-table tbody tr[data-item-id="' + itemId + '"]');

        if (existingRow.length) {
            // Обновляем существующую строку
            var quantityInput = existingRow.find('.quantity-input');
            var currentQuantity = parseInt(quantityInput.val());
            quantityInput.val(currentQuantity + 1);
            updateItemTotalPrice(existingRow);
        } else {
            // Добавляем новую строку
            var newRow = `
                <tr data-item-id="${data.product_id}">
                    <td>
                        ${data.product_name}
                    </td>
                    <td>
                        <div class="input-group">
                            <button class="btn btn-outline-secondary btn-sm decrease-quantity" data-item-id="${data.product_id}">-</button>
                            <input type="text" class="form-control form-control-sm quantity-input" data-item-id="${data.product_id}" value="1">
                            <button class="btn btn-outline-secondary btn-sm increase-quantity" data-item-id="${data.product_id}">+</button>
                        </div>
                    </td>
                    <td>${data.product_price}</td>
                    <td class="item-total-price">${data.product_price}</td>
                    <td>
                        <button class="btn btn-danger btn-sm delete-item" data-item-id="${data.product_id}">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </td>
                </tr>
            `;
            $('#cart-table tbody').append(newRow);
        }
        updateSaleTotal();
    }

    // Функция для обновления общей суммы товара в строке
    function updateItemTotalPrice(row) {
        var quantity = parseInt(row.find('.quantity-input').val());
        var price = parseFloat(row.find('td:nth-child(3)').text()); // Цена - третья ячейка
        var totalPrice = quantity * price;
        row.find('.item-total-price').text(totalPrice.toFixed(2)); // Обновляем сумму
    }

      // Обработка изменения количества в корзине
    $('#cart-table').on('change', '.quantity-input', function() {
        var itemId = $(this).data('item-id');
        var quantity = $(this).val();
        updateSaleItemQuantity(itemId, quantity);
    });


    // Функция для обновления количества товара в корзине
    function updateSaleItemQuantity(itemId, quantity) {
        $.ajax({
            url: '{% url "update_sale_item_quantity" %}',
            type: 'POST',
            data: {
                'item_id': itemId,
                'quantity': quantity,
                // Добавьте CSRF токен, если требуется
            },
            dataType: 'json',
            success: function(data) {
                if (data.success) {
                    // Обновляем отображение в корзине
                    var row = $('#cart-table tbody tr[data-item-id="' + itemId + '"]');
                    row.find('.item-total-price').text(data.new_total_price);

                    // Обновляем общую сумму
                    $('#sale-subtotal').text(data.sale_subtotal.toFixed(2));
                    $('#sale-total').text(data.sale_total.toFixed(2));
                } else {
                    alert(data.error);
                }
            },
            error: function() {
                alert('Произошла ошибка при обновлении количества.');
            }
        });
    }

      // Обработка удаления товара из корзины
    $('#cart-table').on('click', '.delete-item', function() {
        var itemId = $(this).data('item-id');
        deleteSaleItem(itemId);
    });

    // Функция для удаления товара из корзины (AJAX запрос)
    function deleteSaleItem(itemId) {
        $.ajax({
            url: '{% url "delete_sale_item" %}',
            type: 'POST',
            data: {
                'item_id': itemId,
                // Добавьте CSRF токен, если требуется
            },
            dataType: 'json',
            success: function(data) {
                if (data.success) {
                    // Удаляем строку из таблицы
                    $('#cart-table tbody tr[data-item-id="' + itemId + '"]').remove();
                    // Обновляем общую сумму в корзине
                    $('#sale-subtotal').text(data.sale_subtotal.toFixed(2));
                    $('#sale-total').text(data.sale_total.toFixed(2));
                } else {
                    alert(data.error);
                }
            },
            error: function() {
                alert('Произошла ошибка при удалении товара.');
            }
        });
    }


    function updateSaleTotal() {
      var subtotal = 0;
      $('.item-total-price').each(function () {
        subtotal += parseFloat($(this).text());
      });
      $('#sale-subtotal').text(subtotal.toFixed(2));

      var discount = parseFloat($('#discountInput').val()) || 0;
      var total = subtotal * (1 - discount / 100);
      $('#sale-total').text(total.toFixed(2));
    }

      // Сканирование штрихкода
    $(document).scannerDetection({
        timeBeforeScanTest: 200,
        avgTimeByChar: 40,
        onComplete: function(barcode, qty) {
            // Поиск товара по штрихкоду (AJAX)
            $.ajax({
                url: '{% url "search_products" %}',
                type: 'GET',
                data: {'q': barcode},
                dataType: 'json',
                success: function(data) {
                    if (data.products.length > 0) {
                        var product = data.products[0];
                        // Используйте product.id для поиска товара и добавления его в корзину
                        // ...
                        console.log("Найденный товар:", product);
                    } else {
                        alert('Товар с таким штрихкодом не найден.');
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Ошибка AJAX:", error);
                    alert('Произошла ошибка при поиске товара.');
                }
            });
        }
    });

      // Завершение продажи
    $('.complete-sale').click(function() {
        $.ajax({
            url: '{% url "complete_sale" %}',
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                if (data.success) {
                    // Очистка корзины
                    $('#cart-table tbody').empty();
                    $('#sale-subtotal').text('0.00');
                    $('#sale-total').text('0.00');
                    // Дополнительные действия (например, печать чека)
                    alert('Продажа успешно завершена!');
                } else {
                    alert(data.error);
                }
            },
            error: function() {
                alert('Произошла ошибка при завершении продажи.');
            }
        });
    });
});
