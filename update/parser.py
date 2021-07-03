import time
import asyncio
import aiohttp
from lxml import html as lxml_html

from settings import DEBUG, CHUNK, TIMEOUT, AVAILABLE

if DEBUG:
    tic = lambda: time.time()

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
            tac = lambda: "{:.2f}sec".format(time.time() - now)
            print('\r\n>>> Start parse_main at ', time.strftime('%H:%M:%S', time.localtime()))
        chunk = CHUNK
        solution_urls = list()
        all_urls = len(urls)
        for i, url in enumerate(urls):
            tasks = list()
            do_search = True
            for page_num in range(1, finish+1):  # бегаем по страницам каждого url
                if DEBUG:
                    # progress bar
                    print('\r{}, {}/ {} progress. Now {} page of {}\r'.format(tac(), i+1, all_urls, page_num, url), end='')
                tasks.append(asyncio.create_task(main_page_urls(url, page_num)))
                if len(tasks) == chunk or page_num == finish:
                    new = await asyncio.gather(*tasks)
                    for urls_ in new:
                        if urls_:
                            solution_urls.extend(urls_)
                        else:
                            do_search = False
                    tasks = list()
                    await asyncio.sleep(TIMEOUT)
                if not do_search:  # выходим из листания страниц, если дальше ничего нет
                    break
        if DEBUG:
            print('>>> End parse_main on {} sec. Find {} urls.\n'.format(tac(), len(solution_urls)))
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
                            img = 'http://kant.ru' + \
                                  tree.xpath("//div[@class='kant__product__color__thumbs']//img")[0].values()[0]
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
                        #
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
            tac = lambda: '{:.2f}sec'.format(time.time() - now)
            print('\r\n>>> Start parse_details at ', time.strftime('%H:%M:%S', time.localtime()))
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
                print('\r{} sec, {}/ {}: {}\r'.format(tac(), i+1, all_urls), end='')  # progress bar
        if DEBUG:
            print('>>> End parse_details on {} sec. Parsed {} items.\n'.format(tac(), len(products)))
        return products  # [(code, brand, model, url, img, age), (code, brand, model, ..), ...,]

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
            tac = lambda: "{:.2f}sec".format(time.time() - now)
            print('\r\n>>> Start parse_price at ', time.strftime('%H:%M:%S', time.localtime()))
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
            print('>>> End parse_price on {} sec. Parsed {} items.\n'.format(tac(), len(products)))

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
            tac = lambda: "{:.2f}sec".format(time.time() - now)
            print('\r\n>>> Start parse_available at ', time.strftime('%H:%M:%S', time.localtime()))
        for i, (code, instock_code) in enumerate(codes):
            tasks.append(asyncio.create_task(parse_instock(code, instock_code)))
            if len(tasks) == chunk or i+1 == count_codes:
                if DEBUG:
                    print('\r{} sec, {}/ {}: {}\r'.format(tac(), i+1, count_codes, code), end='')
                new = await asyncio.gather(*tasks)
                products.extend(new)
                await asyncio.sleep(TIMEOUT * 0.5)  # приходит чистый json без html, уменьшаем таймаут
                tasks = list()
        if DEBUG:
            print('>>> End parse_available on {} sec. Parsed {} items.\n'.format(tac(), len(products)))

        return products