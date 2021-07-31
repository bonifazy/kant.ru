from django.shortcuts import render
from django.db.models import Max, Q

from update.settings import BRANDS
from .models import Products, Prices, InstockNagornaya

"""
# Главная страница отображения аналитики продаж

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


def index(request):
    templates = 'display/index.html'

    return render(request, templates)


def brand_details(request, brand):
    context = dict()
    if brand in BRANDS:
        prods = InstockNagornaya.objects.filter(code_id__brand=brand).order_by('-rating').distinct().values_list('code')
        if prods:
            context = {
                'brand': brand,
                'codes': prods,
            }
        return render(request, 'display/brand_details.html', context)


def kant_main(request):
    data = dict()
    for brand in BRANDS:
        # вывести самые популярные по обновлению наличия модели брендов, первые 10
        prods = InstockNagornaya.objects.filter(code_id__brand=brand).order_by('-rating').distinct().values_list('code')[:10]
        if prods:
            data[brand] = dict()
            for item in prods:
                code_ = item[0]
                details = InstockNagornaya.objects.filter(~Q(count=0), code=code_).values_list('code_id__model', 'code_id__prices__price')
                #print(details[0])
                data[brand][item[0]] = [details[0][0], details[0][1]]
                instock = details.order_by('size', '-rating').values_list('size', 'count', 'rating')
                while instock:
                    size_ = instock[0][0]
                    rating_ = instock[0][2]
                    instock = instock.exclude(size=size_)
                    data[brand][item[0]].append((size_, rating_))

    return render(request, 'display/kant_main.html', {'data': data})

"""
SELECT  p.code, p.brand, p.model, i.size, i.rating
FROM instock_nagornaya AS i
JOIN products AS p
ON code=code_id
WHERE p.code=1599734 AND i.count <> 0
GROUP BY i.size
HAVING MAX(i.rating);
"""
