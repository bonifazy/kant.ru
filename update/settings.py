
#            для модуля 'main', 'parser', 'db'
#
# дополнительный лог с помощью print по всему приложению, включая модули 'db' и 'parser'
DEBUG = True

# начальный рейтинг для таблиц products, prices, instock_nagornaya
RATING = 4

#            для модуля 'main'
#
# одинаковый формат записи, как в выгрузке размеров с AVAILABLE запроса
SHOP = "Nagornaya"

# ссылки на беговые модели кроссовок на заполнение и обновление базы данных
ALL = ['https://www.kant.ru/catalog/shoes/running-shoes/']
BRANDS = ['Asics', 'Saucony', 'Mizuno', 'Hoka', 'Adidas', 'Salomon', 'Brooks', 'On', '361°', 'Raidlight']
BRANDS_URLS = [
    'http://www.kant.ru/catalog/shoes/running-shoes/brand-asics/',
    'http://www.kant.ru/catalog/shoes/running-shoes/brand-saucony/',
    'http://www.kant.ru/catalog/shoes/running-shoes/brand-mizuno/',
    'http://www.kant.ru/catalog/shoes/running-shoes/brand-hoka/',
    'http://www.kant.ru/catalog/shoes/running-shoes/brand-adidas/',
    'http://www.kant.ru/catalog/shoes/running-shoes/krossovki/brand-salomon/',
    'http://www.kant.ru/brand/brooks/products/',
    'http://www.kant.ru/brand/on/products/',
    'https://www.kant.ru/brand/361/products/',
]
BROOKS = ['http://www.kant.ru/brand/brooks/products/']

#
#            для модуля 'db'
#
# полный путь к базе данных либо с bash шаблоном, т.к все равно после обрабатывается os.path
DB_DIR = '/Users/dim/kant/db.sqlite3'  # True dir to db or '../db.sqlite3'

#
#            для модуля 'parser'
#
# таймаут между порциями параллельных загрузок, сек
TIMEOUT = 0.2
# количество параллельных GET- запросов за 1 порцию
CHUNK = 5
# ссылка для загрузки размерной линейки, приходит json с размерами и количеством во всех магазинах сети
AVAILABLE = "http://www.kant.ru/ajax/loadTableAvailability.php"
