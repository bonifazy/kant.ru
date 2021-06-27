#!/usr/bin/env python
import os.path

from lxml import html as lxml_html
import time
import sqlite3
import asyncio
import aiohttp

# Global to main
DEBUG = True
print('Debug is', 'on.' if DEBUG else 'off.')
DJANGO_DB = '../db.sqlite3'
SHOP = "Nagornaya"  # одинаковый формат записи, как в выгрузке размеров с AVAILABLE запроса
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
ADIDAS = ['http://www.kant.ru/catalog/shoes/running-shoes/brand-adidas/']
BROOKS = ['http://www.kant.ru/brand/brooks/products/']
CACHE = r"data/"

tic = lambda: time.time()
now = tic()
tac = lambda: '{:.2f}sec'.format(time.time() - now)

# Global to Parse
TIMEOUT = 0.2
CHUNK_PARSE_MAIN = 5
CHUNK = 5
RATING = 4  # Normal rating to items to db.
AVAILABLE = "http://www.kant.ru/ajax/loadTableAvailability.php"


class Main:

    def __init__(self):
        self.url_list = ALL + BRANDS_URLS
        self.products = list()
        self.finish_num_page = 25
        self.db = SQLite()
        self.loop = asyncio.get_event_loop()

    def __del__(self):
        self.db.close()

    def update_products_table(self):
        # обновляем базу 'nagornaya.products'
        if DEBUG:
            now = tic()
            print('\r\n>> start update_products_table')
        urls = self.loop.run_until_complete(Parser.parse_main(self.url_list, self.finish_num_page))  # загружаем базу urls страниц товаров с сайта
        unic_urls = set(urls)  # уникальные ссылки на продукты с сайта
        # unic_urls.remove('http://kant.ru/catalog/product/3004861/')
        url_from_db = set(self.db.get_last_update_products())
        check_urls = unic_urls - url_from_db  # urls, которых нет, либо низкий рейтинг в базе 'products', нужно проверить
        urls_not_instock = url_from_db - unic_urls # urls, которые закончились в магазине
        url_from_db_small_rate = set(self.db.get_products_urls_rating_to_normal())
        urls_to_normal_rate = url_from_db_small_rate & check_urls  # изменить на 10 рейтинг
        new_urls = check_urls - url_from_db_small_rate  # записать впервые рейтинг 10
        # по urls находим ключ == code
        if urls_not_instock:
            self.db.update_products_rating_to_1(urls_not_instock)
        if urls_to_normal_rate:
            self.db.update_products_rating_to_normal(urls_to_normal_rate)
        if new_urls:
            self.products = self.loop.run_until_complete(Parser.parse_details(list(new_urls)))
            self.db.to_products(self.products)
        else:
            if DEBUG:
                print('without call parse_details')
        if DEBUG:
            print('from db, rate {}: {}'.format(RATING, len(url_from_db)))
            print('from kant.ru: ', len(unic_urls))
            print('Not in stock:', urls_not_instock)
            print('Update rate 1 to normal:', urls_to_normal_rate)
            print('New:', new_urls)
            print('>> end update_product_table: ', tac())
        return True  # если все ок

    def update_prices_table(self):
        if DEBUG:
            now = tic()
            print('\r\n>> start update_prices_table')
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # now time to update db timestamps
        products = self.db.get_products_code_url()
        if not products:
            if DEBUG: print('No items in products table!')
            return False
        prod_codes = [code for code, url in products]
        prices_from_db = self.db.get_last_update_prices()  # [(code, price, timestamp, rating), (code, ...]
        prices_codes = [code for (code, price, time_, rating) in prices_from_db]  # коды из базы
        # новые коды закинуть в таблицу с ценой, временем обновления и рейтингом RATING
        new = set(prod_codes) - set(prices_codes)  # new = появившиеся кроссовки, для которых еще не определена цена

        if new:
            new_codes_urls = [(code, url) for (code, url) in products if code in new]
            new_codes_prices = self.loop.run_until_complete(Parser.parse_price(new_codes_urls))
            # обнулить рейтинг для новых кроссовок в базе с 0 стоимостью
            # начальный рейтинг для новых кроссовок == RATING
            solution_new_list = [(code, price, timestamp, (lambda i: RATING if i > 0 else 0)(price)) for (code, price) in new_codes_prices]
            if solution_new_list:
                self.db.to_prices(solution_new_list)
                if DEBUG: print('new prices to db: ', len(solution_new_list), timestamp)
        # для моделей вышедших из магазина, но появившихся снова, рейтинг 0+1=1
        old = set(prices_codes) & set(prod_codes)  # проверите, уже имеющиеся, обновить, если новая цена, увеличить рейтинг +1
        if old:
            old_codes_urls = [(code, url) for (code, url) in products if code in old]
            updated_codes_prices = self.loop.run_until_complete(Parser.parse_price(old_codes_urls))
            solution_old_list = list()
            for upd_code, upd_price in updated_codes_prices:
                for db_code, db_price, time_, rating in prices_from_db:
                    if upd_code == db_code and upd_price != db_price:
                        if upd_price != 0:
                            solution_old_list.append((upd_code, upd_price, timestamp, rating+1))
                        else:
                            solution_old_list.append((upd_code, upd_price, timestamp, 1))
            if solution_old_list:
                self.db.to_prices(solution_old_list)
                if DEBUG: print('update prices in db: ', len(solution_old_list), timestamp)
        if DEBUG: print('>> end update_product_table: ', tac())
        return True  # если все ок

    def update_instock_table(self):
        if DEBUG:
            now = tic()
            print('\r\n>> start update_instock_tables')
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # now time to update db timestamps
        codes_urls = self.db.get_products_code_url()
        if not codes_urls:
            if DEBUG: print('No items in products table!')
            return False
        codes = [i[0] for i in codes_urls]
        instock_codes = [i[1].split('/')[5] for i in codes_urls]
        codes = list(zip(codes, instock_codes))
        loaded = self.loop.run_until_complete(Parser.parse_available(codes))
        loaded_instock = dict()
        loaded_instock[SHOP] = dict()
        for code, instock in loaded:
            if SHOP in instock.keys():
                loaded_instock[SHOP][code] = list()
                for sizes in instock[SHOP]:
                    """ for test
                    if code == 1648580:
                        if sizes[0] == 9.0:
                            continue
                        if float(sizes[0]) == 8.5:
                            loaded_instock[SHOP][code].append((8.5, 1, timestamp, 10))
                            continue
                    if code == 1648581:
                        if sizes[0] == 9.0:
                            continue
                        if float(sizes[0]) == 8.5:
                            loaded_instock[SHOP][code].append((8.5, 1, timestamp, 10))
                            continue
                    """
                    loaded_instock[SHOP][code].append((float(sizes[0]), sizes[1], timestamp, RATING))

        last_update_instock = dict()
        last_update_instock[SHOP] = dict()
        for code, size, count, time_, rate in self.db.get_last_update_instock_nagornaya():
            if code not in last_update_instock[SHOP].keys():
                last_update_instock[SHOP][code] = list()
            last_update_instock[SHOP][code].append((float(size), count, time_, rate))

        # Абсолютно новые кроссовки добавить сразу без проверок, т.к. их еще нет в базе
        new = list()
        for code in loaded_instock[SHOP].keys():
            if code not in last_update_instock[SHOP].keys():
                new.extend([(code, *i) for i in loaded_instock[SHOP][code]])

        # Проверить уже имеющиеся на консистентность данных
        updated = list()
        not_instock = list()

        for code in last_update_instock[SHOP].keys():
            if code in loaded_instock[SHOP].keys():  # если коды из инета и из базы совпадают
                for size, count, timestmp, rate in last_update_instock[SHOP][code]:  # бегаем по базе
                    for size_, count_, timestmp_, rate_ in loaded_instock[SHOP][code]:  # бегаем по загруж из инета
                        if size == size_ and count != count_:  # если размер из базы совпадает с загруж из инета
                            updated.append((code, size_, count_, timestamp, rate + 1))
                            break
                last_update_sizes = set(map(lambda x: float(x[0]), last_update_instock[SHOP][code]))
                loaded_sizes = set(map(lambda x: float(x[0]), loaded_instock[SHOP][code]))
                not_instock_sizes = last_update_sizes - loaded_sizes
                new_sizes = loaded_sizes - last_update_sizes
                not_instock.extend([(code, value[0], 0, timestamp, 1) for value in last_update_instock[SHOP][code] if value[0] in not_instock_sizes])
                new.extend([(code, value[0], value[1], timestamp, RATING) for value in loaded_instock[SHOP][code] if value[0] in new_sizes])
        if new:
            self.db.to_instock_nagornaya(new)
        if updated:
            self.db.to_instock_nagornaya(updated)
        if not_instock:
            self.db.to_instock_nagornaya(not_instock)
        if DEBUG:
            print('new: ', len(new), *new)
            print('updated: ', len(updated), *updated)
            print('not in stock: ', len(not_instock), *not_instock)
            print('>> end update_product_table: ', tac())
        return True  # если все ок


class Parser:

    @staticmethod
    async def parse_main(urls: list, finish: int) -> list:

        async def main_page_urls(url: str, params: int) -> list:
            urls = list()
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params={'PAGEN_1':params}) as response:
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
            for page_num in range(1, finish+1):  # бегаем по страницам каждого url
                if DEBUG:
                    print('\r{}, {}/ {} progress. Now {} page of {}\r'.format(tac(), i+1, all_urls, page_num, url), end='')  # progress bar
                tasks.append(asyncio.create_task(main_page_urls(url, page_num)))
                if len(tasks) == chunk or page_num == finish:
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

        async def parse(url: str, timestamp: str) -> tuple:
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
            return code, brand, model, url, img, age, gender, year, use, pronation, article, season, rating, timestamp

        if DEBUG:
            now = tic()
        products = list()
        all_urls = len(urls)
        tasks = list()
        chunk = CHUNK
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        for i, url in enumerate(urls):
            tasks.append(asyncio.create_task(parse(url, timestamp)))
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
                await asyncio.sleep(TIMEOUT)  # add value if you banned from kant.ru
                tasks = list()
        if DEBUG:
            print(tac(), 'get urls and parsing prices')

        return products  # [(code, price), (code, price)...]

    @staticmethod
    async def parse_available(codes: list)-> list:

        async def parse_instock(code: int, instock_code: int) -> tuple:

            async with aiohttp.ClientSession() as session:
                    async with session.get(AVAILABLE, params={'ID':instock_code}) as response:
                        html = await response.text()
                        tree = lxml_html.fromstring(html)
                        popur_row_div = tree.xpath("//div[@data-tab='tab958']/div")  # div class = popur__row
                        shops = ("Nagornaya", "Timiryazevskaya", "TeplyStan", "Altufevo")
                        in_stock = dict()
                        for shop, div in zip(shops, popur_row_div):
                            div_content = div.text_content().strip()
                            if "наличии" not in div_content:  # not in stock
                                in_stock[shop] = list()
                        shop_index = 0  # Nagorn:1, Timiryaz: 2, TStan: 3, Altuf: 4
                        for i in range(4):  # В Москве (div:data-tab=tab958) всего 4 магазина
                            rows = tree.xpath("//div[@data-tab='tab958']/table[{}]/tr".format(i+1))
                            for row in rows:
                                row_list = row.text_content().split()
                                if len(row_list) == 3:  # нашли размеры и наличие
                                    temp = row_list[0].lower()
                                    if temp.startswith('u'):
                                        size = '.'.join(temp.split(':')[1].split(','))
                                    if temp.startswith('eur'):
                                        size = '.'.join(temp.split(':')[1].split(','))
                                    if size.isdecimal():
                                        size = float(size)
                                    elif size.startswith('k'):
                                        size = size[1:] if size[1:].isdecimal() else 0
                                    instock = size, int(row_list[2])
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
            return code, in_stock

        chunk = CHUNK  # count get requests per 1 asyncio session with timeout
        timeout = TIMEOUT  # add value, if you banned from kant.ru: timeout to between async get requests
        tasks = list()
        products = list()  # general solution list
        count_codes = len(codes)
        if DEBUG:
            now = tic()
        for i, (code, instock_code) in enumerate(codes):
            tasks.append(asyncio.create_task(parse_instock(code, instock_code)))
            if len(tasks) == chunk or i+1 == count_codes:
                if DEBUG:
                    print('\r{} sec, {}/ {}: {}\r'.format(tac(), i+1, count_codes, code), end='')
                new = await asyncio.gather(*tasks)
                products.extend(new)
                await asyncio.sleep(0.1)  # add global timeout, if you banned from kant.ru
                tasks = list()
        return products


class SQLite:

    def __init__(self):
        import os.path
        from os import getcwd
        name = os.path.join(os.path.split(getcwd())[0], 'db.sqlite3')
        if os.path.isfile(name):
            self.conn = sqlite3.connect(name)
            self.cur = self.conn.cursor()
        else:
            print('no access to db.sqlite3 :-(')

    def to_products(self, products:list):
        sql = 'insert into products (code, brand, model, url, img, age, gender, year, use, pronation, article, season, rating, timestamp) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
        self.cur.executemany(sql, products)
        self.conn.commit()
        return self.cur.rowcount

    def to_prices(self, prices:list):
        sql = 'insert into prices (code_id, price, timestamp, rating) values (?,?,?,?)'
        self.cur.executemany(sql, prices)
        self.conn.commit()
        return self.cur.rowcount

    def to_instock_nagornaya(self, instock:list):
        sql = 'insert into instock_nagornaya (code_id, size, count, timestamp, rating) values (?,?,?,?,?)'
        self.cur.executemany(sql, instock)
        self.conn.commit()
        return self.cur.rowcount

    def get_products_urls_rating_to_normal(self):
        self.cur.execute("select url from products where rating < {}".format(RATING))
        urls = [i[0] for i in self.cur.fetchall()]
        return urls

    def get_products_codes_for_urls(self, urls):
        self.cur.execute("select code from products where url in ('{}')".format("','".join(urls)))
        codes = self.cur.fetchall()
        return codes

    def get_products_code_url(self):
        self.cur.execute("select code, url from products")
        codes = self.cur.fetchall()
        return codes

    def get_last_update_products(self):
        self.cur.execute("select url from products where rating >= {}".format(RATING))
        urls = [i[0] for i in self.cur.fetchall()]
        return urls

    def get_last_update_prices(self):
        sql="select code_id, price, timestamp, rating from prices where rating >= {} group by code_id order by -max(rating);".format(RATING)
        self.cur.execute(sql)
        return self.cur.fetchall()

    def get_last_update_instock_nagornaya(self):
        self.cur.execute("select code_id, size, count, timestamp, rating from instock_nagornaya where rating >= {} group by code_id, size order by -max(rating);".format(RATING))
        return self.cur.fetchall()

    def update_products_rating_to_1(self, urls):
        for url in urls:
            sql="update products set rating = 1 where url = '{}'".format(url)
            self.cur.execute(sql)
            self.conn.commit()
        return self.cur.fetchall()

    def update_products_rating_to_normal(self, urls):
        for url in urls:
            sql="update products set rating = '{}' where url = '{}'".format(RATING, url)
            self.cur.execute(sql)
            self.conn.commit()
        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()


if __name__ == "__main__":
    now = tic()
    prods = False
    prices = False
    instock = False
    page = Main()
    page.url_list = ['http://www.kant.ru/brand/on/products/']
    for i in range(3):
        try:
            if not prods:
                prods = page.update_products_table()
            if not prices:
                prices = page.update_prices_table()
            if not instock:
                instock = page.update_instock_table()
        except aiohttp.ClientConnectionError:
            print('ConnectionError. Reconnect..')
            time.sleep(10)

    print(tac(), 'worked app.')
