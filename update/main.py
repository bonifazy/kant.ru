#!/usr/bin/env python

import time
import asyncio
import sys
from aiohttp import ClientConnectionError

from db import SQLite
from parser import Parser
from settings import DEBUG, RATING, ALL, BRANDS_URLS, SHOPS
# support print to testing for full app, include 'db' и 'parser' modules
if DEBUG:
    tic = lambda: time.time()
    now = tic()
    tac = lambda: '{:.2f}sec'.format(time.time() - now)
    print('Debug is on.')
else:
    print('Debug is off.')


class Main:

    def __init__(self):
        self.url_list = ALL + BRANDS_URLS  # all used running shoes urls to parsing
        self.brand = None  # need to test part of database with full work process (operate by all methods)
        self.products = list()  # cached solution items
        self.from_parse_main = list()  # cached, if disconnect cases is often
        self.finish_num_page = 30  # max pagination of each brand
        self.db = SQLite()  # connect to db
        self.loop = asyncio.get_event_loop()  # connect to event loop

    def update_products_table(self):
        # create new items to 'products' table and update rating to items, which doesn't in stock

        # support to develop, if True
        if DEBUG:
            now = tic()
            tac = lambda: '{:.2f}sec'.format(time.time() - now)
            print('\r\n> Start update_products_table..')
        # load urls from www.kant.ru
        if not self.from_parse_main:
            self.from_parse_main = self.loop.run_until_complete(Parser.parse_main(self.url_list, self.finish_num_page))
        unic_urls = set(self.from_parse_main)  # unic urls, exclude doubles items from list
        # this if/ else construction need to test all module without load all database and parsing from www.kant.ru site
        # test and refactoring feature
        # update one brand, not all table
        if not self.brand:
            url_from_db = set(self.db.get_last_update_products())
        else:
            url_from_db = set(self.db.get_last_update_products_by_brand(self.brand))
        check_urls = unic_urls - url_from_db  # check urls, not in stock, or min rating from 'products' table
        urls_not_instock = url_from_db - unic_urls # out of stock urls
        url_from_db_small_rate = set(self.db.get_products_urls_rating_to_normal())  # get only small rate
        urls_to_normal_rate = url_from_db_small_rate & check_urls  # update to normal rate: RATING
        new_urls = list(check_urls - url_from_db_small_rate)  # set new rate: RATING
        # get key by url, key == code
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
        return True  # if all ok

    def update_prices_table(self):
        # set new prices to new items in 'prices' from new items in 'products' and update prices 'prices' if chanched

        #support dev
        if DEBUG:
            now = tic()
            tac = lambda: '{:.2f}sec'.format(time.time() - now)
            print('\r\n> Start update_prices_table..')
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # time to update stamp
        products = self.db.get_products_code_url()  # get code and url from 'products'
        if not products:
            if DEBUG: print('No items in products table!')
            return False
        prod_codes = [code for code, url in products]
        # get prices by codes in 'products' from 'prices' table with max rate
        prices_from_db = self.db.get_last_update_prices()  # [(code, price, timestamp, rating), (code, ...]
        prices_codes = [code for (code, price, time_, rating) in prices_from_db]  # only codes
        # new codes set to 'prices': code, price, timestamp, RATING
        new = set(prod_codes) - set(prices_codes)  # new shoes, prices not define, need parse
        if new:
            new_codes_urls = [(code, url) for (code, url) in products if code in new]  # get pairs code: url for parsing
            new_codes_prices = self.loop.run_until_complete(Parser.parse_price(new_codes_urls))  # code: price for items
            # if price == 0, set rate == 1.
            # starting rate for new normal price == RATING
            solution_new_list = [(code, price, timestamp, (lambda i: RATING if i > 0 else 1)(price))
                                 for (code, price) in new_codes_prices
                                 ]
            if solution_new_list:
                self.db.to_prices(solution_new_list)
                if DEBUG: print('new prices to db: ', len(solution_new_list), *solution_new_list, timestamp)
        # if item was not in stock and now update yet, rate 1+1 = 2
        old = set(prices_codes) & set(prod_codes)  # check existing or update for new price find, increment rate +1
        if old:
            old_codes_urls = [(code, url) for (code, url) in products if code in old]
            updated_codes_prices = self.loop.run_until_complete(Parser.parse_price(old_codes_urls))
            solution_old_list = list()
            for upd_code, upd_price in updated_codes_prices:  # iterate for loaded db from site
                for db_code, db_price, time_, rating in prices_from_db:   # check equal prices from db and site
                    if upd_code == db_code and upd_price != db_price:  # code is equal and price is updated?
                        if upd_price != 0:  # item in stock and price real is update
                            solution_old_list.append((upd_code, upd_price, timestamp, rating+1))  # set new price toitem
                        else:  # price is 0 or price column not found in prices card
                            solution_old_list.append((upd_code, upd_price, timestamp, 1))  # set not in stock price
                        break
            if solution_old_list:  # set new price and rate conditions-- update existing items
                self.db.to_prices(solution_old_list)
                if DEBUG: print('\tupdate prices in db: ', len(solution_old_list), *solution_old_list, timestamp)
        if DEBUG: print('> End update_prices_table on {}.'.format(tac()))
        return True  # if all ok

    def update_instock_table(self):
        # set new instock availability of each size of each item, update existing availability and set to 0 not in stock
        # items. Working table: 'instock_nagornaya'
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
    if hasattr(page, 'db'):  # normal connect to db
        for i in range(3):
            try:
                if load_prods:
                    load_prods = not page.update_products_table()
                if load_prices:
                    load_prices = not page.update_prices_table()
                if load_instock:
                    load_instock = not page.update_instock_table()
            except ClientConnectionError as err:  # as usual in LTE connection from phone
                print('ConnectionError. Reconnect..')
                time.sleep(20)


if __name__ == "__main__":
    if DEBUG:
        now = tic()
    main()
    if DEBUG:
        print(tac(), 'worked app.')
