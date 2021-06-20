import kant
import time
import asyncio
import aiohttp

# kant.ALL, kant.BRANDS, kant.MAIN, kant.PARSER

def test_async_parse_price(urls, loop):
    data = kant.Parser.async_parse_price(urls, loop)
    print(data)

def test_parser_parse_main(url_):
    data = kant.Parser.parse_main([url_,], 1)
    print(data)

def test_parse_details(url_):
    data = kant.Parser.parse_details([url_,])
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

HTTPBIN = 'http://httpbin.org/get'

"""
async def fetch(url, params):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            text = await resp.text()
            print(text)

async def hello(url, loop):
    reader, writer = await asyncio.open_connection(host=url, port=7777, loop=loop)
    data = await reader.read(100)
    print(data.decode())
    writer.write('q')
    writer.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(hello('127.0.0.1', loop))
loop.close()
"""

def main():

    async def fetch(session, url):
        async with session.get(url) as response:
            return await response.text()

    async def main(urls_, products):
        urls = urls_
        tasks = []
        async with aiohttp.ClientSession() as session:
            for url in urls:
                tasks.append(fetch(session, url))
            htmls = await asyncio.gather(*tasks)
            for html in htmls:
                print(html[:10], '\n')
        products = htmls

    prods = list()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(kant.BRANDS_URLS, prods))
    print(len(prods))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    test_async_parse_price(['https://www.kant.ru/catalog/product/2906145/', 'https://www.kant.ru/catalog/product/2780445/'], loop=loop)
    # test_parser_parse_main('https://www.kant.ru/catalog/shoes/womans/marafonki/')
    # test_parse_details('https://www.kant.ru/catalog/product/2780445/')  # https://www.kant.ru/catalog/product/2906145/, https://www.kant.ru/catalog/product/2780445/
    #test_update_products_table('https://www.kant.ru/catalog/shoes/womans/krossovk/')  # https://www.kant.ru/catalog/shoes/womans/krossovk/, https://www.kant.ru/catalog/shoes/womans/marafonki/
    # test_get_for_id(2445929)
    #test_to_products([(1599205, 'Saucony', 's-ride 13 black/green', 'https://www.kant.ru/catalog/product/2780445/',
    #                   'http://www.google.com/', 'детский', 'унисекс', '2021', 'асфальт', 'нейтральная', 'SK264329',
    #                   'лето', 1])
