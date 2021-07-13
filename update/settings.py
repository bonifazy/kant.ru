
#            для модуля 'main', 'parser', 'db'
#
# дополнительный лог с помощью print по всему приложению, включая модули 'db' и 'parser'
DEBUG = True

# начальный рейтинг для таблиц products, prices, instock_nagornaya
RATING = 4

#            для модуля 'main'
#
# одинаковый формат записи, как в выгрузке размеров с AVAILABLE запроса
SHOPS = ('Nagornaya', 'Timiryazevskaya', 'TeplyStan', 'Altufevo')

# ссылки на беговые модели кроссовок на заполнение и обновление базы данных
ALL = ['https://www.kant.ru/catalog/shoes/running-shoes/']
BRANDS = ['Asics', 'Saucony', 'Mizuno', 'Hoka', 'Adidas', 'Salomon', 'Brooks', 'On', '361°', 'Raidlight']
BRANDS_URLS = [
    'https://www.kant.ru/catalog/shoes/running-shoes/brand-asics/',
    'https://www.kant.ru/catalog/shoes/running-shoes/brand-saucony/',
    'https://www.kant.ru/catalog/shoes/running-shoes/brand-mizuno/',
    'https://www.kant.ru/catalog/shoes/running-shoes/brand-hoka/',
    'https://www.kant.ru/catalog/shoes/running-shoes/brand-adidas/',
    'https://www.kant.ru/catalog/shoes/running-shoes/krossovki/brand-salomon/',
    'https://www.kant.ru/brand/brooks/products/',
    'https://www.kant.ru/brand/on/products/',
    'https://www.kant.ru/brand/361/products/',
]

#
#            для модуля 'db'
#
DB_NAME = 'db.sqlite3'

#
#            для модуля 'parser'
#
# таймаут между порциями параллельных загрузок, сек
TIMEOUT = 0.2
# количество параллельных GET- запросов за 1 порцию
CHUNK = 5
# ссылка для загрузки размерной линейки, приходит json с размерами и количеством во всех магазинах сети
AVAILABLE = "http://www.kant.ru/ajax/loadTableAvailability.php"
