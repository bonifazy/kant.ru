#!/usr/bin/env python

from lxml import html as lxml_html
import requests
import time
import sqlite3
import asyncio
import aiohttp
from aiohttp.client_exceptions import ClientConnectionError

# Global to main
DEBUG = True
print('Debug is', 'on.' if DEBUG else 'off.')
DJANGO_DB = '../db.sqlite3'
SHOP = "nagornaya"
ALL = ['https://www.kant.ru/catalog/shoes/running-shoes/',]
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
ADIDAS = ['http://www.kant.ru/catalog/shoes/running-shoes/brand-adidas/',]
BROOKS = ['http://www.kant.ru/brand/brooks/products/']
CACHE = r"data/"

tic = lambda: time.time()
tac = lambda: '{:.2f}sec'.format(time.time() - now)

# Global to Parse
TIMEOUT = 0.2
CHUNK_PARSE_MAIN = 5
CHUNK = 5
RATING = 10

class Main:

    available_url = "http://www.kant.ru/ajax/loadTableAvailability.php"
    cache_type = "sqlite"  # "sqlite " or "json"

    def __init__(self, urls):
        self.url_list = urls
        self.products = list()
        self.finish_num_page = 25

    def update_products_table(self, loop):
        # обновляем базу 'nagornaya.products'
        if DEBUG:
            now = tic()
            print('\r\n>> start update_products_table')
        db = SQLite()
        urls = loop.run_until_complete(Parser.parse_main(self.url_list, self.finish_num_page))  # загружаем базу urls страниц товаров с сайта
        unic_urls = set(urls)  # уникальные ссылки на продукты с сайта
        url_from_db = set(db.get_urls())
        check_urls = list(unic_urls - url_from_db)  # urls, которых нет в базе 'products', нужно проверить
        urls_not_in_stock = list(url_from_db - unic_urls)  # urls, которые закончились в магазине
        # по urls находим ключ == code
        codes_not_in_stock = db.exe("select code from products where url in ('{}')".format("','".join(urls_not_in_stock)))
        if len(check_urls) > 0:
            self.products = loop.run_until_complete(Parser.parse_details(check_urls))
        else:
            self.products = list()
            if DEBUG:
                print('without call parse_details')
        if self.products:
            SQLite().to_products(self.products)
        if DEBUG:
            print('>> end update_product_table: ', tac())
            print('from db: ', len(url_from_db), '\nfrom kant.ru: ', len(unic_urls))
            print('Not in stock :', codes_not_in_stock)
            if self.products:
                print('New: ')
                for item in self.products:
                    print(item)
        db.close()
        return True  # если все ок

    def update_prices_table(self, loop):
        if DEBUG:
            now = tic()
            print('\r\n>> start update_prices_table')
        db = SQLite()
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # now time to update db timestamps
        products = db.get_products_code_url()
        if not products:
            if DEBUG: print('No items in products table!')
            return False
        prod_codes = [code for code, url in products]
        prices_from_db = db.get_last_prices()  # [(code, price, timestamp, rating), (code, ...]
        prices_codes = [code for (code, price, time_, rating) in prices_from_db]  # коды из базы
        # новые коды закинуть в таблицу с ценой, временем обновления и рейтингом 1
        new = set(prod_codes) - set(prices_codes)  # new = появившиеся кроссовки, для которых еще не определена цена

        if new:
            new_codes_urls = [(code, url) for (code, url) in products if code in new]
            new_codes_prices = loop.run_until_complete(Parser.parse_price(new_codes_urls))
            # обнулить рейтинг для новых кроссовок в базе с 0 стоимостью
            # начальный рейтинг для новых кроссовок == 10
            solution_new_list = [(code, price, timestamp, (lambda i: RATING if i > 0 else 0)(price)) for (code, price) in new_codes_prices]
            if solution_new_list:
                db.to_prices(solution_new_list)
                if DEBUG: print('new prices to db: ', len(solution_new_list), timestamp)
        # для моделей вышедших из магазина, но появившихся снова, рейтинг 0+1=1
        old = set(prices_codes) & set(prod_codes)  # проверите, уже имеющиеся, обновить, если новая цена, увеличить рейтинг +1
        if old:
            old_codes_urls = [(code, url) for (code, url) in products if code in old]
            updated_codes_prices = loop.run_until_complete(Parser.parse_price(old_codes_urls))
            solution_old_list = list()
            for upd_code, upd_price in updated_codes_prices:
                for db_code, db_price, time_, rating in prices_from_db:
                    if upd_code == db_code and upd_price != db_price:
                            solution_old_list.append((upd_code, upd_price, timestamp, rating+1))
            if solution_old_list:
                db.to_prices(solution_old_list)
                if DEBUG: print('update prices in db: ', len(solution_old_list), timestamp)
        db.close()
        if DEBUG: print('>> end update_product_table: ', tac())
        return True  # если все ок

    def sync_update_prices_table(self):
        products = {code: url for (code, url) in SQLite().get_products_code_url()}
        prod_codes = [i for i in products.keys()]
        prices = {code: [price, timestamp, rating] for (code, price, timestamp, rating) in SQLite().get_prices()}
        prices_codes = [i for i in prices.keys()]
        new = set(prod_codes) - set(prices_codes)  # новые коды закинуть в таблицу с ценой и временем обновления
        old = [i for i in prices_codes if i in prod_codes]  # обновить, если новая цена
        to_update = dict()  # коды для обновления цены
        all = len(old)
        for i, code in enumerate(old):
            print('\r{}, {}/ {}: {} old codes\r'.format(TAC(), i+1, all, code), end='')  # progress bar
            table_price = prices[code][0]
            actual_price = Parser.parse_price(url=products[code])
            if table_price != actual_price:
                to_update[code] = actual_price
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        prices_to_db = [(code, price, timestamp, prices[code][2]+1) for code, price in to_update.items()]
        all = len(new)
        for i, code in enumerate(new):
            print('\r{}, {}/ {}: {} new codes\r'.format(TAC(), i+1, all, code), end='')  # progress bar
            url_ = products[code]
            actual_price = Parser.parse_price(url_)
            prices_to_db.append((code, actual_price, timestamp, 1))
        if prices_to_db:
            SQLite().to_prices(prices_to_db)
            print('to db: ', len(prices_to_db), timestamp)
            for item in prices_to_db:
                print(item)
        # info
        if new:
            print('new:', len(new), new)
        if old:
            print('old:', len(old))
        pass


class Parser:

    @staticmethod
    async def parse_main(urls: list, finish: int) -> list:

        async def main_page_urls(url: str) -> list:
            urls = list()
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
                    if "kant__catalog__item" in html:  # найти urls всех товаров
                        # Если на странице есть сетка с товаром, то проверяем каждый товар, ищем его url
                        tree = lxml_html.fromstring(html)
                        a_tags = tree.xpath("//div[@class='kant__catalog__item']//a")
                        for item in a_tags:
                            name = item.values()[1].lower()
                            if 'кроссовки' in name or 'марафонки' in name:
                                item_url = "http://kant.ru{}".format(item.values()[0])
                                urls.append(item_url)
                    else:  # это вообще не страница с кроссовками, остановить корутины!
                        return list()
            return urls

        if DEBUG:
            now = tic()
        chunk = CHUNK_PARSE_MAIN
        solution_urls = list()
        all_urls = len(urls)
        for i, url in enumerate(urls):
            tasks = list()
            do_search = True
            for page_num in range(finish+1):  # бегаем по страницам каждого url
                if DEBUG:
                    print('\r{}, {}/ {} progress. Now {} page of {}\r'.format(tac(), i+1, all_urls, page_num+1, url), end='')  # progress bar
                page_url = "{}?PAGEN_1={}".format(url, str(page_num+1))  # начинаются с 1й страницы!
                tasks.append(asyncio.create_task(main_page_urls(page_url)))
                if len(tasks) == chunk:
                    new = await asyncio.gather(*tasks)
                    for urls in new:
                        if urls:
                            solution_urls.extend(urls)
                        else:
                            do_search = False
                    tasks = list()
                    await asyncio.sleep(TIMEOUT)
                if not do_search:  # выходим из листания страниц, если дальше ничего нет
                    break
        if DEBUG:
            print('{} worked parse_main. Find {} urls'.format(tac(), len(solution_urls)))
        return solution_urls

    @staticmethod
    async def parse_details(urls: list) -> list:

        async def parse(url: str) -> tuple:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
                    tree = lxml_html.fromstring(html)
                    running = False  # Точно ли это кроссовки?
                    brand = None
                    # commons attrs from xpath objs: values, text, xpath, text_content, keys, label, items, base, attrib
                    for item in tree.xpath("//div[@class='kant__product__detail-item']"):  # карточка описания товара
                        column = item.xpath("span[1]/text()")[0]
                        if len(item.xpath("span[2]/text()")) > 0:
                            value = item.xpath("span[2]/text()")[0]
                            if (column == 'Назначение' and 'бег' in value) or \
                                    (column == 'Тип' and 'кроссовки' in value or 'марафонки' in value):
                                running = True
                            if column == 'Бренд':
                                brand = value.lower()
                    if running:  # это точно карточка кроссовки!
                        age = gender = year = article = season = use = pronation = ''
                        name = tree.xpath("//div[@id='kantMainCardProduct']/h1/text()")[0].lower()
                        if brand is None:
                            if 'кроссовки' in name or 'марафонки' in name:
                                temp_brands = [i.lower() for i in BRANDS]
                                temp = [i for i in name.split() if i in temp_brands]
                                if temp:
                                    brand = temp[0]
                        model = name.partition(brand)[2].strip()
                        brand = brand.title()
                        code = tree.xpath("//div[@class='kant__product__code']/strong/text()")[0]
                        code = int(code) if code.isdecimal() else 0
                        if tree.xpath("//div[@class='kant__product__color__thumbs']//img"):
                            img = 'http://kant.ru' + tree.xpath("//div[@class='kant__product__color__thumbs']//img")[0].values()[0]
                        else:
                            img = 'http://kant.ru'
                        for item in tree.xpath("//div[@class='kant__product__detail-item']"):
                            column = item.xpath("span[1]/text()")[0]
                            if len(item.xpath("span[2]/text()")) > 0:
                                value = item.xpath("span[2]/text()")[0]
                                if column == 'Возраст':
                                    age = value
                                if column == 'Пол':
                                    gender = value
                                if column == 'Модельный год':
                                    year = value
                                if column == 'Покрытие':
                                    use = value
                                if column == 'Пронация':
                                    pronation = value
                                if column == 'Артикул':
                                    article = value
                                if column == 'Сезон':
                                    season = value
                        # special to Saucony brand:
                        if brand == 'Saucony' and model.startswith('s-'):
                            age = 'junior' if age == '' else age
                        # end special Saucony
                        # special to Hoka brand:
                        if brand == 'Hoka':
                            if model.startswith('m '):
                                gender = 'man' if gender == '' else gender
                            elif model.startswith('w '):
                                gender = 'woman' if gender == '' else gender
                            model = model[2:]
                        # end special Hoka
                        # TODO
                        rating = RATING
            return code, brand, model, url, img, age, gender, year, use, pronation, article, season, rating

        if DEBUG:
            now = tic()
        products = list()
        all_urls = len(urls)
        tasks = list()
        chunk = CHUNK
        for i, url in enumerate(urls):
            tasks.append(asyncio.create_task(parse(url)))
            if len(tasks) == chunk or i+1 == all_urls:
                new = await asyncio.gather(*tasks)
                products.extend(new)
                tasks = list()
                await asyncio.sleep(TIMEOUT)
            if DEBUG:
                print('\r{} sec, {}/ {}: {}\r'.format(tac(), i+1, all_urls, url), end='')  # progress bar
        if DEBUG:
            print('{} worked parse_details. Parsed {} items.'.format(tac(), len(products)))
        return products

    @staticmethod
    def sync_parse_price(url):
        html = requests.get(url)
        tree = lxml_html.fromstring(html.text)
        if tree.xpath("//div[@class='kant__product__price']/span[2]/text()"):
            price = ''.join(tree.xpath("//div[@class='kant__product__price']/span[2]/text()")[0].split(' '))
            price = int(price) if price.isdecimal() else 0
        else:
            price = 0
        return price

    @staticmethod
    async def parse_price(codes_urls: list) -> list:

        async def get_and_parse(code, url: str) -> tuple:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    html = await response.text()
                    tree = lxml_html.fromstring(html)
                    if tree.xpath("//div[@class='kant__product__price']/span[2]/text()"):
                        price = ''.join(tree.xpath("//div[@class='kant__product__price']/span[2]/text()")[0].split(' '))
                        price = int(price) if price.isdecimal() else 0
                    else:
                        price = 0
                    return code, price

        chunk = CHUNK  # count get requests per 1 asyncio session with timeout
        timeout = TIMEOUT  # add value, if you banned from kant.ru: timeout to between async get requests
        tasks = list()
        products = list()  # general solution list
        all_urls = len(codes_urls)
        if DEBUG:
            now = tic()
        for i, (code, url) in enumerate(codes_urls):
            tasks.append(asyncio.create_task(get_and_parse(code, url)))
            if len(tasks) == chunk or i+1 == all_urls:
                if DEBUG:
                    print('\r{} sec, {}/ {}: {}\r'.format(tac(), i+1, all_urls, url), end='')
                new = await asyncio.gather(*tasks)
                products.extend(new)
                await asyncio.sleep(TIMEOUT)  # uncomment if you banned from kant.ru
                tasks = list()
        if DEBUG:
            print(tac(), 'get urls and parsing prices')

        return products  # [(code, price), (code, price)...]

    @staticmethod
    def append_ajax_available(url_, id_):
        shops = ("Nagornaya", "Timiryazevskaya", "TeplyStan", "Altufevo")
        in_stock = dict()
        html = requests.get(url_, params={"ID": id_})
        tree = lxml_html.fromstring(html.text)
        popur_row_div = tree.xpath("//div[@data-tab='tab958']/div")  # div class = popur__row
        for shop, div in zip(shops, popur_row_div):
            div_content = div.text_content().strip()
            if "наличии" not in div_content:  # not in stock
                in_stock[shop] = list()
            # print(shop, self.in_stock.keys())
        shop_index = 0  # Nagorn:1, Timiryaz: 2, TStan: 3, Altuf: 4
        for i in range(4):  # В Москве (div:data-tab=tab958) всего 4 магазина
            rows = tree.xpath("//div[@data-tab='tab958']/table[{}]/tr".format(i+1))
            for row in rows:
                row_list = row.text_content().split()
                if len(row_list) == 3:  # нашли размеры и наличие
                    instock = row_list[0], int(row_list[2])
                    if shop_index == 1 and "Nagornaya" in in_stock.keys():
                        in_stock["Nagornaya"].append(instock)
                    elif shop_index == 2 and "Timiryazevskaya" in in_stock.keys():
                        in_stock["Timiryazevskaya"].append(instock)
                    elif shop_index == 3 and "TeplyStan" in in_stock.keys():
                        in_stock["TeplyStan"].append(instock)
                    elif shop_index == 4 and "Altufevo" in in_stock.keys():
                        in_stock["Altufevo"].append(instock)
                    else:
                        shop_index += 1
                elif len(row_list) == 6:  # Нашли описание колонки
                    shop_index += 1
        return in_stock


class SQLite:

    def __init__(self):
        from os.path import isfile
        self.name = DJANGO_DB
        if isfile(self.name):
            self.conn = sqlite3.connect(self.name)
            self.cur = self.conn.cursor()
        else:
            print('no access to db.sqlite3 :-(')

    def to_products(self, products:list):
        sql = 'insert into products (code, brand, model, url, img, age, gender, year, use, pronation, article, season, rating) values (?,?,?,?,?,?,?,?,?,?,?,?,?)'
        self.cur.executemany(sql, products)
        self.conn.commit()
        return self.cur.rowcount

    def to_prices(self, prices:list):
        sql = 'insert into prices (code_id, price, timestamp, rating) values (?,?,?,?)'
        self.cur.executemany(sql, prices)
        self.conn.commit()
        return self.cur.rowcount

    def get_urls(self):
        self.cur.execute("select url from products")
        urls = [i[0] for i in self.cur.fetchall()]
        return urls

    def get_products_code_url(self):
        self.cur.execute("select code, url from products")
        codes = self.cur.fetchall()
        return codes

    def get_last_prices(self):
        self.cur.execute("select code_id, price, timestamp, rating from prices")
        return self.cur.fetchall()

    def select(self, sql):
        if sql:
            self.cur.execute("select " + sql + " from products")
        return(self.cur.fetchall())

    def exe(self, sql):
        if sql:
            self.cur.execute(sql)
        answer = self.cur.fetchall()
        self.conn.commit()
        return answer

    def close(self):
        self.cur.close()
        self.conn.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    now = tic()
    prods = False
    prices = False
    page = Main(urls=ALL+BRANDS_URLS)
    for i in range(2):
        try:
            if not prods:
                prods = page.update_products_table(loop=loop)
            if not prices:
                prices = page.update_prices_table(loop=loop)
        except ClientConnectionError:
            print('ConnectionError. Reconnect..')
            time.sleep(30)

    print(tac(), 'worked app.')
