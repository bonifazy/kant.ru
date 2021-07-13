#!/usr/bin/env python

import time
import asyncio
import sys
from aiohttp import ClientConnectionError

from db import SQLite
from parser import Parser
from settings import DEBUG, RATING, ALL, BRANDS_URLS, SHOPS
# дополнительный лог с помощью print по всему приложению, включая модули 'db' и 'parser'
if DEBUG:
    tic = lambda: time.time()
    now = tic()
    tac = lambda: '{:.2f}sec'.format(time.time() - now)
    print('Debug is on.')
else:
    print('Debug is off.')


class Main:

    def __init__(self):
        self.url_list = ALL + BRANDS_URLS
        self.products = list()
        self.from_parse_main = list()
        self.finish_num_page = 30
        self.db = SQLite()
        self.loop = asyncio.get_event_loop()

    def __del__(self):  # ну мало ли чё..
        if hasattr(self, 'db'):
            self.db.close()

    def update_products_table(self):
        # обновляем базу 'products'
        if DEBUG:
            now = tic()
            tac = lambda: '{:.2f}sec'.format(time.time() - now)
            print('\r\n> Start update_products_table..')
        # загружаем базу urls страниц товаров с сайта
        if not self.from_parse_main:
            self.from_parse_main = self.loop.run_until_complete(Parser.parse_main(self.url_list, self.finish_num_page))
        unic_urls = set(self.from_parse_main)  # уникальные ссылки на продукты с сайта
        url_from_db = set(self.db.get_last_update_products())
        check_urls = unic_urls - url_from_db  # urls, которых нет, либо низкий рейтинг в базе 'products',нужно проверить
        urls_not_instock = url_from_db - unic_urls # urls, которые закончились в магазине
        url_from_db_small_rate = set(self.db.get_products_urls_rating_to_normal())
        urls_to_normal_rate = url_from_db_small_rate & check_urls  # изменить на RATING
        new_urls = list(check_urls - url_from_db_small_rate)  # записать впервые рейтинг RATING
        # по urls находим ключ == code
        if urls_not_instock:
            self.db.update_products_rating_to_1(urls_not_instock)
        if urls_to_normal_rate:
            self.db.update_products_rating_to_normal(urls_to_normal_rate)
        if new_urls:
            self.products = self.loop.run_until_complete(Parser.parse_details(new_urls))
            if self.products:
                self.db.to_products(self.products)
            else:
                if DEBUG:
                    print('without call parse_details')
        if DEBUG:
            print('\tfrom db, rate {}: {}'.format(RATING, len(url_from_db)))
            print('\tfrom kant.ru: ', len(unic_urls))
            print('\tNot in stock:', urls_not_instock)
            print('\tUpdate rate 1 to normal:', urls_to_normal_rate)
            print('\tNew:', len(self.products))
            print('> End update_product_table {}.'.format(tac()))
        return True  # если все ок

    def update_prices_table(self):
        # обновление базы 'prices'
        if DEBUG:
            now = tic()
            tac = lambda: '{:.2f}sec'.format(time.time() - now)
            print('\r\n> Start update_prices_table..')
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # время для вставки обновления колонок
        products = self.db.get_products_code_url()  # загружаем коды и url с базы данных
        if not products:
            if DEBUG: print('No items in products table!')
            return False
        prod_codes = [code for code, url in products]
        # загружаем цены из базы
        prices_from_db = self.db.get_last_update_prices()  # [(code, price, timestamp, rating), (code, ...]
        prices_codes = [code for (code, price, time_, rating) in prices_from_db]  # коды из базы данных
        # новые коды закинуть в таблицу с ценой, временем обновления и рейтингом RATING
        new = set(prod_codes) - set(prices_codes)  # new = появившиеся кроссовки, для которых еще не определена цена
        if new:
            new_codes_urls = [(code, url) for (code, url) in products if code in new]
            # найдены цены на товар с www.kant.ru
            new_codes_prices = self.loop.run_until_complete(Parser.parse_price(new_codes_urls))
            # рейтинг для новых кроссовок в базе с 0 стоимостью == 1.
            # начальный рейтинг для новых кроссовок == RATING
            solution_new_list = [(code, price, timestamp, (lambda i: RATING if i > 0 else 1)(price))
                                 for (code, price) in new_codes_prices
                                 ]
            if solution_new_list:
                self.db.to_prices(solution_new_list)
                if DEBUG: print('new prices to db: ', len(solution_new_list), *solution_new_list, timestamp)
        # для моделей вышедших из магазина, но появившихся снова, рейтинг 1+1 = 2
        old = set(prices_codes) & set(prod_codes)  # проверите, уже имеющиеся, обновить, если новая цена, увеличить рейтинг +1
        if old:
            old_codes_urls = [(code, url) for (code, url) in products if code in old]
            updated_codes_prices = self.loop.run_until_complete(Parser.parse_price(old_codes_urls))
            solution_old_list = list()
            for upd_code, upd_price in updated_codes_prices:  # бегаем по загруженной с инета базе цен
                for db_code, db_price, time_, rating in prices_from_db:   # ищем эти же цены по коду товара из базы данных
                    if upd_code == db_code and upd_price != db_price:  # код найден и цены различны
                        if upd_price != 0:  # если товар в продаже и изменилась стоимость
                            solution_old_list.append((upd_code, upd_price, timestamp, rating+1))
                        else:  # если стоимость обнулилась либо не найдена графа стоимости в карточке товара
                            solution_old_list.append((upd_code, upd_price, timestamp, 1))
                        break
            if solution_old_list:
                self.db.to_prices(solution_old_list)
                if DEBUG: print('\tupdate prices in db: ', len(solution_old_list), *solution_old_list, timestamp)
        if DEBUG: print('> End update_prices_table on {}.'.format(tac()))
        return True  # если все ок

    def update_instock_table(self):
        # обновление базы 'instock_nagornaya'
        if DEBUG:
            now = tic()
            tac = lambda: '{:.2f}sec'.format(time.time() - now)
            print('\r\n> Start update_instock_tables..')
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # now time to update db timestamps
        codes_urls = self.db.get_products_code_url()
        if not codes_urls:
            if DEBUG: print('No items in products table!')
            return False
        codes = [i[0] for i in codes_urls]
        instock_codes = [int(i[1].split('/')[5]) for i in codes_urls]
        pair_codes = list(zip(codes, instock_codes))
        loaded = self.loop.run_until_complete(Parser.parse_available(pair_codes))
        loaded_instock = dict()
        shop = SHOPS[0]
        loaded_instock[shop] = dict()
        for code, instock in loaded:
            if shop in instock.keys():
                loaded_instock[shop][code] = list()
                for sizes in instock[shop]:
                    loaded_instock[shop][code].append((float(sizes[0]), sizes[1], timestamp, RATING))
        last_update_instock = dict()
        last_update_instock[shop] = dict()
        for code, size, count, time_, rate in self.db.get_instock_nagornaya_last_update():
            if code not in last_update_instock[shop].keys():
                last_update_instock[shop][code] = list()
            last_update_instock[shop][code].append((float(size), count, time_, rate))

        # Абсолютно новые кроссовки добавить сразу без проверок, т.к. их еще нет в базе
        new = list()
        for code in loaded_instock[shop].keys():
            if code not in last_update_instock[shop].keys():
                new.extend([(code, *i) for i in loaded_instock[shop][code]])

        # Проверить уже имеющиеся на консистентность данных
        updated = list()
        not_instock = list()

        for code in last_update_instock[shop].keys():
            if code in loaded_instock[shop].keys():  # если коды из инета и из базы совпадают
                for size, count, timestmp, rate in last_update_instock[shop][code]:  # бегаем по базе
                    for size_, count_, timestmp_, rate_ in loaded_instock[shop][code]:  # бегаем по загруж из инета
                        if size == size_ and count != count_:  # если размер из базы совпадает с загруж из инета
                            updated.append((code, size_, count_, timestamp, rate + 1))
                            break
                last_update_sizes = set(map(lambda x: float(x[0]), last_update_instock[shop][code]))
                loaded_sizes = set(map(lambda x: float(x[0]), loaded_instock[shop][code]))
                not_instock_sizes = last_update_sizes - loaded_sizes
                new_sizes = loaded_sizes - last_update_sizes
                not_instock.extend([(code, value[0], 0, timestamp, value[3]+1)
                                    for value in last_update_instock[shop][code] if value[0] in not_instock_sizes])
                new.extend([(code, value[0], value[1], timestamp, RATING)
                            for value in loaded_instock[shop][code] if value[0] in new_sizes])
        # коды в базе с размерами, у которых 0 количество
        not_instock_codes =  [i[0] for i in self.db.get_instock_codes_with_0_count()]
        # уникальные полученные размеры с 0 количеством, которых еще нет в базе
        not_instock = [item for item in not_instock if item[0] not in not_instock_codes]
        if new:
            self.db.to_instock_nagornaya(new)
        if updated:
            self.db.to_instock_nagornaya(updated)
        if not_instock:
            self.db.to_instock_nagornaya(not_instock)
        if DEBUG:
            print('\tnew: ', len(new), *new)
            print('\tupdated: ', len(updated), *updated)
            print('\tnot in stock: ', len(not_instock), *not_instock)
            print('> End update_instock_tables on {}.'.format(tac()))
        return True  # если все ок


def main(load_prods=False, load_prices=False, load_instock=False):
    load_prods = load_prods
    load_prices = load_prices
    load_instock = load_instock
    args = sys.argv
    if len(args) > 1:
        for argv in args:
            if argv.lower() == 'products':
                load_prods = True
            if argv.lower() == 'prices':
                load_prices = True
            if argv.lower() == 'instock':
                load_instock = True
    page = Main()
    # page.finish_num_page = 30
    # page.url_list = [BRANDS_URLS[0]]
    if hasattr(page, 'db'):  # if normal connect to db
        for i in range(3):
            try:
                if load_prods:
                    load_prods = not page.update_products_table()
                if load_prices:
                    load_prices = not page.update_prices_table()
                if load_instock:
                    load_instock = not page.update_instock_table()
            except ClientConnectionError as err:
                print('ConnectionError. Reconnect..')
                time.sleep(20)


if __name__ == "__main__":
    if DEBUG:
        now = tic()
    main()
    if DEBUG:
        print(tac(), 'worked app.')
