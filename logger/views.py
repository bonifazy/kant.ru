from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, F, Sum, Max
from django.http import Http404
from django.contrib.auth.models import User

from .models import Products, Prices, InstockNagornaya


def not_found(request, exception):
    context = {
        'request': exception
    }
    return render(request, 'errors/404.html', context=context, status=404)


def index(request):

    # searching form
    items = None
    q = request.GET.get('q')
    if q is not None:
        q = q.strip()
        if q.isdigit():
            code = int(q)
            if 1_000_000 < code < 2_500_000:
                item = get_object_or_404(Products, code=code)
                return single_item(request, item)
        if len(q) < 20:
            brand = q.lower().title()
            items = Products.objects.filter(brand=brand)
            if len(items) > 0:
                return brand_details(request, brand=brand)
        model = q
        items = Products.objects.filter(model__icontains=model)
        if len(items) > 0:
            return items_list(request, items)
        return not_found(request, exception=q)
    return redirect('/kant/')


def single_item(request, item):
    user = User.objects.first().username

    return render(request, 'display/views_single_item.html', {'item': item, 'user': user})


def brand_details(request, brand):

    brand = brand.lower().title()
    items_in_list = 50
    data = dict()
    # условия фильтрации: поиск по бренду, товар точно в наличии, смотреть размеры в наличии
    q = Q(code_id__brand=brand) & ~Q(code_id__prices__price=0) & ~Q(count=0)
    items = InstockNagornaya.objects.filter(q).values('code_id').order_by(F('rate').desc()).\
                annotate(rate=Max('rating')).values_list('code_id')[:items_in_list]
    prods = [i[0] for i in items]
    if not prods:
        return not_found(request, 'brand')

    for code in prods:
        item = Products.objects.get(code=code)
        model = item.model
        gender = item.gender
        price = item.prices_set.values('price').order_by(F('rate').desc()).annotate(rate=Max('rating')).\
            values_list('price').first()[0]

        # последние обновленные размеры товара в наличии
        sizes = InstockNagornaya.objects.filter(code_id=code).values('size').order_by(F('rate').desc()).\
            annotate(rate=Max('rating')).values_list('size')
        sizes = list(map(lambda x: float(x[0]), sizes))

        # размерная сетка в наличии по данному товару (по коду товара), шт, больше 3, да/ нет
        is_count_gte_3_sizes = True if len(sizes) > 3 else False

        popular_man = [9, 9.5, 10, 10.5, 11]
        popular_woman = [8, 8.5, 9, 9.5, 10]
        popular_sizes = list()
        if gender in ('мужской', 'man', 'унисекс'):
            gender = 'man'
        elif gender in ('женский', 'woman'):
            gender = 'woman'
        else:
            gender = None
        if gender == 'man':
            popular_sizes = [i for i in sizes if i in popular_man]
        elif gender == 'woman':
            popular_sizes = [i for i in sizes if i in popular_woman]
        sizes_count = len(popular_sizes)

        data[code] = [model, gender, price, is_count_gte_3_sizes, sizes_count]
        user = User.objects.first().username

    return render(request, 'display/views_brand_details.html', context={'brand': brand, 'data': data, 'user': user})


def items_list(request, content):
    q = Q(rating=1) &Q(prices__price__gt=0)  # фильтр: выводить только в наличии

    items = content.filter(q).order_by(F('rate').desc()).annotate(rate=Max('instocknagornaya__rating'))
    data = {item.code: item for item in items}
    user = User.objects.first().username

    return render(request, 'display/views_items_list.html', context={'data': data, 'user': user})


def kant_main(request):

    data = dict()
    items_in_brand = 5  # список товаров в рамках одного бренда

    # популярность бренда относительно частоты продаж
    brands_for_rating = [i[0] for i in InstockNagornaya.objects.values('code_id__brand').order_by(F('rate').desc()).\
        annotate(rate=Sum('rating')).values_list('code_id__brand')]

    if not brands_for_rating:
        raise Http404

    for brand in brands_for_rating:
        # 10 most popular (for rating (last updates), than price) models
        q = Q(code_id__brand=brand) & ~Q(code_id__prices__price=0) & ~Q(count=0)
        prods = [i[0] for i in InstockNagornaya.objects.filter(q).values('code_id').order_by(F('rate').desc()).\
            annotate(rate=Max('rating')).values_list('code_id')[:items_in_brand]
                 ]
        items_dict = dict()
        for code in prods:
            # актуальная размерная сетка товара
            items = InstockNagornaya.objects.filter(code_id=code).values('size').\
                    order_by(F('rate').desc()).annotate(rate=Max('rating')).\
                values_list('size', 'code_id__model', 'code_id__prices__price', 'code_id__gender')
            sizes = [i[0] for i in items]
            # item.4 размерная линейка точно больше 3 размеров
            is_count_gte_3_sizes = True if len(sizes) > 3 else False

            item = items[0]
            model = item[1]
            price = item[2]  # TODO проверить точно ли актуальная стоимость?
            gender = item[3]

            popular_man = [9, 9.5, 10, 10.5, 11]
            popular_woman = [8, 8.5, 9, 9.5, 10]
            porular_unisex = [8.5, 9, 9.5, 10, 10.5]
            popular_sizes = list()
            if gender in ('мужской', 'man', 'унисекс'):
                gender = 'man'
            elif gender in ('женский', 'woman', 'унисекс'):
                gender = 'woman'
            else:
                gender = None
            if gender == 'man':
                popular_sizes = [i for i in sizes if i in popular_man]
            elif gender == 'woman':
                popular_sizes = [i for i in sizes if i in popular_woman]
            elif gender is None:
                popular_sizes = [i for i in sizes if i in porular_unisex]
            # item.4 количество размеров, подходящих под популярные
            sizes_count = len(popular_sizes)
            #            0     1       2          3                 4
            content = [model, gender, price, is_count_gte_3_sizes, sizes_count]
            items_dict[code] = content
        # словарь продуктов, сортировка по стоимости по убыванию
        # return desc popular brands by sales count
        data[brand] = dict(sorted(items_dict.items(), key=lambda x: x[1][2], reverse=True))
        user = User.objects.first().username

    return render(request, 'display/views_kant_main.html', context={'data': data, 'user': user})


"""
# Главная страница отображения аналитики продаж

SELECT SUM(rate)
FROM (
    SELECT i.rating as rate
    FROM instock_nagornaya AS i
    JOIN products AS p
    ON code_id=code
    WHERE p.brand="Adidas"
    ORDER BY i.rating DESC
    LIMIT 20
    );

# Самые продаваемые модели бренда Asics, первые 20 шт.
SELECT DISTINCT p.code, p.brand, p.model, i.rating
FROM instock_nagornaya AS i
JOIN products AS p
ON code_id=code
WHERE p.brand="Asics"
ORDER BY i.rating DESC
LIMIT 20;

# Актуальный размерный ряд модели по коду товара с учетом рейтинга, 
когда размер точно в наличии
SELECT  p.code, p.brand, p.model, i.size, i.rating
FROM instock_nagornaya AS i
JOIN products AS p
ON code=code_id
WHERE p.code=1599734 AND i.count <> 0
GROUP BY i.size
HAVING MAX(i.rating);

# Приоритет выставления брендов в пагинатор, относительно суммы рейтингов последних обновлений наличия
SELECT SUM(rate)
FROM (
    SELECT i.rating as rate
FROM instock_nagornaya AS i
JOIN products AS p
ON code_id=code
WHERE p.brand="Adidas"
ORDER BY i.rating DESC
LIMIT 20
);

# Актуальная стоимость товара
SELECT price
FROM prices
WHERE code_id="1270586"
ORDER BY rating DESC
LIMIT 1;

# Страница выбора товара. Нажимаем на кнопочку конкретной модели.

# Стоимость и дата обновления за период
SELECT p.price, p.timestamp, prod.brand, prod.model
FROM prices AS p
JOIN products AS prod
ON prod.code=p.code_id
WHERE prod.code="1270586"
ORDER BY p.timestamp DESC;

# Размер и его наличие на складе
# Актуальный размерный ряд модели по коду товара с учетом рейтинга, 
#   когда размер точно в наличии
SELECT  p.code, p.brand, p.model, i.size, i.rating
FROM instock_nagornaya AS i
JOIN products AS p
ON code=code_id
WHERE p.code=1599734
GROUP BY i.size
HAVING MAX(i.rating) AND i.count<>0;

# from Coursera.com
Lookups (поиск по полю)
будет указано в where
можно передавать в filter(), exclude(), get() в формате field__lookuptype = value

entries = Entry.objects.filter(blog_id__in[1, 2])

# товар, который менял цену хотя бы раз (изменение цены > 1 раза)
prods = Products.objects.filter(brand="Asics").annotate(prices_count=Count("prices")).filter(prices_count__gt=1)
SELECT  p.code, p.brand, p.model, i.size, i.rating
FROM instock_nagornaya AS i
JOIN products AS p
ON code=code_id
WHERE p.code=1599734
GROUP BY i.size
HAVING MAX(i.rating) AND i.count<>0;
"""