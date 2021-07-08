import sqlite3
import os.path
from pathlib import Path

from settings import DB_NAME, RATING


class SQLite:

    def __init__(self):
        parent_dir = Path(__file__).resolve().parent.parent  # to real path to 'db.sqlite3' file
        db = os.path.join(parent_dir, DB_NAME)  # path + file with any OS
        print()
        if os.path.isfile(db):
            self.conn = sqlite3.connect(db)
            self.cur = self.conn.cursor()
        else:
            print('no access to db.sqlite3 :-(\nEdit DB_NAME in kant/update/settings.py')

    def to_products(self, products:list):
        sql = 'insert into products (code, brand, model, url, img, age, gender, year, use, pronation, article, ' \
              'season, rating, timestamp) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
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

    def get_products_code_url_test(self):
        self.cur.execute("select code, url from products where brand = 'Brooks'")
        codes = self.cur.fetchall()
        return codes

    def get_last_update_products(self):
        self.cur.execute("select url from products where rating >= {}".format(RATING))
        urls = [i[0] for i in self.cur.fetchall()]
        return urls

    def get_last_update_prices(self):
        sql="select code_id, price, timestamp, rating from prices group by code_id order by -max(rating);"
        self.cur.execute(sql)
        return self.cur.fetchall()

    def get_instock_nagornaya_last_update(self):
        sql = "select code_id, size, count, timestamp, rating from instock_nagornaya where rating >= {} " \
              "group by code_id, size order by -max(rating);"
        self.cur.execute(sql.format(RATING))
        return self.cur.fetchall()

    def get_instock_codes_with_0_count(self):
        self.cur.execute("select code_id from instock_nagornaya where count = 0 group by code_id")
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
        if hasattr(SQLite, 'cur') and hasattr(SQLite, 'conn'):
            self.cur.close()
            self.conn.close()
            print('db close ok')
