from django.shortcuts import render
# from .models import Products, Prices, InstockNagornaya

"""
# Самые продаваемые модели бренда Asics, первые 20 шт.
SELECT DISTINCT p.code, p.brand, p.model, i.rating 
FROM instock_nagornaya AS i 
JOIN products AS p
ON code_id=code
WHERE p.brand="Asics"
ORDER BY i.rating DESC
LIMIT 20;

# Актуальный размерный ряд модели по коду товара с учетом рейтинга, 
  даже если при обновленном состоянии размера нет в наличии
SELECT  p.code, p.brand, p.model, i.size, i.rating
FROM instock_nagornaya AS i
JOIN products AS p
ON code=code_id
WHERE p.code=1599734
GROUP BY i.size
HAVING MAX(i.rating) AND i.count<>0;

# Приоритет выставления брендов в пагинатор, относительно суммы рейтингов последних обновлений наличия
SELECT SUM(rate)
FROM (
    SELECT i.rating as rate
    FROM instock_nagornaya AS i 
    JOIN products AS p
    ON code_id=code
    WHERE p.brand="Adidas"
    ORDER BY -i.rating
    LIMIT 20
    );

# Актуальная стоимость товара
SELECT price
FROM prices 
WHERE code_id="1270586"
ORDER BY rating DESC
LIMIT 1;
"""


def index(request):
    templates = 'display/index_with_js.html'

    return render(request, templates, dict())
