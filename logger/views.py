from django.shortcuts import render, redirect
from django.db.models import Q, F, Sum, Max

from .models import InstockNagornaya


def index(request):
    # перекинуть, т.к. проебал js заглушку
    return redirect('kant_main')


def brand_details(request, brand):
    data = dict()
    data[brand] = dict()
    q = Q(code_id__brand=brand) & ~Q(code_id__prices__price=0) & ~Q(count=0)
    prods = [i[0] for i in InstockNagornaya.objects.filter(q).values('code_id').order_by(F('rate').desc()). \
        annotate(rate=Max('rating')).values_list('code_id')[:50]
             ]
    for code in prods:
        # get last update sizes from item
        items = InstockNagornaya.objects.filter(code_id=code).values('size'). \
            order_by(F('rate').desc()).annotate(rate=Max('rating')). \
            values_list('size', 'code_id__model', 'code_id__prices__price', 'code_id__gender')
        sizes = [i[0] for i in items]

        # count of sizes in stock more or equal than 3
        is_count_gte_3_sizes = True if len(sizes) > 3 else False

        item = items[0]
        model = item[1]
        price = item[2]
        gender = item[3]

        popular_man = [9, 9.5, 10, 10.5, 11]
        popular_woman = [8, 8.5, 9, 9.5, 10]
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
        sizes_count = len(popular_sizes)
        content = [model, gender, price, is_count_gte_3_sizes, sizes_count]
        data[brand][code] = content

    return render(request, 'display/brand_details.html', context={'data': data})


def kant_main(request):
    data = dict()
    items_in_brand = 5

    # Most popular brands by sales
    brands_for_rating = [i[0] for i in InstockNagornaya.objects.values('code_id__brand').order_by(F('rate').desc()).\
        annotate(rate=Sum('rating')).values_list('code_id__brand')]
    for brand in brands_for_rating:
        # 10 most popular (for rating (last updates), than price) models
        q = Q(code_id__brand=brand) & ~Q(code_id__prices__price=0) & ~Q(count=0)
        prods = [i[0] for i in InstockNagornaya.objects.filter(q).values('code_id').order_by(F('rate').desc()).\
                    annotate(rate=Max('rating')).values_list('code_id')[:items_in_brand]
                 ]
        items_dict = dict()
        for code in prods:
            # get last update sizes from item
            items = InstockNagornaya.objects.filter(code_id=code).values('size').\
                order_by(F('rate').desc()).annotate(rate=Max('rating')).\
                values_list('size', 'code_id__model', 'code_id__prices__price', 'code_id__gender')
            sizes = [i[0] for i in items]
            # print(sizes)

            # count of sizes in stock more or equal than 3
            is_count_gte_3_sizes = True if len(sizes) > 3 else False

            item = items[0]
            model = item[1]
            price = item[2]
            gender = item[3]

            popular_man = [9, 9.5, 10, 10.5, 11]
            popular_woman = [8, 8.5, 9, 9.5, 10]
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
            sizes_count = len(popular_sizes)
            content = [model, gender, price, is_count_gte_3_sizes, sizes_count]
            items_dict[code] = content
        # set dict with key = code, sorted by price from max
        data[brand] = dict(sorted(items_dict.items(), key=lambda x: x[1][2], reverse=True))

    return render(request, 'display/kant_main.html', context={'data': data})


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
