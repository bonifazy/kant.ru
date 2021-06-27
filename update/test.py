import kant
import asyncio

# kant.ALL, kant.BRANDS, kant.MAIN, kant.PARSER


def test_parse_price(urls, loop):
    data = kant.Parser.parse_price(urls, loop)
    print(data)


def test_parse_main(url_):
    data = kant.Parser.parse_main([url_,], 1)
    print(data)


def test_parse_details(url_, loop):
    data = loop.run_until_complete(kant.Parser.parse_details([url_,]))
    print(data)


def test_get_for_id(id_):
    db = kant.SQLite()
    data = db.exe('select id, url from products where id={}'.format(id_))
    print(data)


def test_to_products(products: list):
    db = kant.SQLite()
    db.to_products(products)
    db.close()


def test_parse_available(codes: list, loop) -> list:
    data = loop.run_until_complete(kant.Parser.parse_available(codes))
    print(data)


def test_update_products_table(url_):
    page = kant.Main()
    page.url_list = [url_]
    page.finish_num_page = 1
    page.update_products_table()


def test_update_prices_table():
    page = kant.Main()
    page.update_prices_table()


def test_update_instock_table():
    page = kant.Main()
    page.update_instock_table()


def test():
    # d from internet
    # d2 from db
    d = {
        'nimbus': [(10, 1), (11, 1), (12, 2)],
        'cumulus': [(8, 1), (9, 4), (10, 4)],
        'ravenna': [(9, 2), (10, 4), (11, 3)],
    }
    d2 = {
        'triumph': [(9, 1, 10)],
        'cumulus': [(8, 3, 10), (9, 5, 10), (10, 4, 10)],
        'ride': [(10, 1, 10), (11, 2, 10)],
        'nimbus': [ (9, 1, 10), (10, 2, 10), (12, 4, 10)],
        'freedom': [(7, 1, 10)]
    }
    updated = list()
    not_instock = list()
    new = list()
    for code in d2.keys():
        sizes = list()
        for size, count, rate in d2[code]:
            sizes.append(size)
            if code in d.keys():
                for size_, count_ in d[code]:
                    if size == size_:
                        sizes.remove(size)
                        d[code].remove((size_, count_))
                        if count != count_:
                            updated.append((code, size_, count_, rate + 1))
        for size in sizes:
            not_instock.append((code, size, 0, 1))
    for code, value in d.items():
        if value:
            new.extend([(code, size, count, 10) for size, count in value])
    print('new: ', new)
    print('updated: ', updated)
    print('not in stock: ', not_instock)

def test2():
    l = [(1, 10), (2, 20), (3, 30)]
    a = list()
    i = 1
    for one, two in l:
        a.append(one)
        if one in [1, 2, 3]:
            a.remove(one)
            i += 1
            pass
        b = a
    input()

if __name__ == '__main__':
    # test
    # test_update_products_table('http://www.kant.ru/brand/brooks/products/')  # https://www.kant.ru/catalog/shoes/womans/krossovk/, https://www.kant.ru/catalog/shoes/womans/marafonki/
    # test_update_prices_table()
     #test_update_instock_table()
    # test_parse_available([(1599205, 2780445)], loop=loop)
    # test_async_parse_price(['https://www.kant.ru/catalog/product/2906145/', 'https://www.kant.ru/catalog/product/2780445/'], loop=loop)
    # test_parser_parse_main('https://www.kant.ru/catalog/shoes/womans/marafonki/')
    # test_parse_details('https://www.kant.ru/catalog/product/2780445/', loop=loop)  # https://www.kant.ru/catalog/product/2906145/, https://www.kant.ru/catalog/product/2780445/
    # test_get_for_id(2445929)
    # test_to_products([(1599205, 'Saucony', 's-ride 13 black/green', 'https://www.kant.ru/catalog/product/2780445/',
    #                   'http://www.google.com/', 'детский', 'унисекс', '2021', 'асфальт', 'нейтральная', 'SK264329',
    #                   'лето', 1])
