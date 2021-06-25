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

def test_update_products_table(url_):
    page = kant.Main(kant.ALL)
    page.url_list = [url_]
    # page.finish_num_page = 1
    page.update_products_table()

def test_get_for_id(id_):
    db = kant.SQLite()
    data = db.exe('select id, url from products where id={}'.format(id_))
    print(data)

def test_to_products(products: list):
    db = kant.SQLite()
    db.to_products(products)
    db.close()

def parse_available(codes: list, loop) -> list:
    data = loop.run_until_complete(kant.Parser.parse_available(codes))
    print(data)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    # parse_available([(1599205, 2780445)], loop=loop)
    # test_async_parse_price(['https://www.kant.ru/catalog/product/2906145/', 'https://www.kant.ru/catalog/product/2780445/'], loop=loop)
    # test_parser_parse_main('https://www.kant.ru/catalog/shoes/womans/marafonki/')
    test_parse_details('https://www.kant.ru/catalog/product/2780445/', loop=loop)  # https://www.kant.ru/catalog/product/2906145/, https://www.kant.ru/catalog/product/2780445/
    # test_update_products_table('https://www.kant.ru/catalog/shoes/womans/krossovk/')  # https://www.kant.ru/catalog/shoes/womans/krossovk/, https://www.kant.ru/catalog/shoes/womans/marafonki/
    # test_get_for_id(2445929)
    # test_to_products([(1599205, 'Saucony', 's-ride 13 black/green', 'https://www.kant.ru/catalog/product/2780445/',
    #                   'http://www.google.com/', 'детский', 'унисекс', '2021', 'асфальт', 'нейтральная', 'SK264329',
    #                   'лето', 1])
