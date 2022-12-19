import asyncio
import datetime
import os
import random
import re
from urllib.parse import quote, parse_qs
from multidict import CIMultiDict
from aiohttp import ClientSession
from bs4 import BeautifulSoup as bf

from cor.Errors import NotParsedSearchId, ServerError, WrongData
from cor.trafficlog import add_count_date_log, product_log, slot_log


async def create_dir(path):
    if os.path.isdir(path):
        return
    if os.path.isfile(path):
        return
    os.makedirs(path)


class CoupangClientSession(ClientSession):    
    def __init__(self, *args, **kwargs):
        super(CoupangClientSession, self).__init__(*args, **kwargs)
        self.search_id = None


async def set_headers(session: CoupangClientSession, headers_list: list):
    headers = random.choice(headers_list)
    session._default_headers.update(CIMultiDict(headers))    
    print(f"headers validation: {session.headers}")


async def go_main_page(session):
    url = 'https://m.coupang.com'
    async with session.get(url) as res:
        # todo: res 가 정상적인지 쿠키는 받아와졌는지 검증(출력)

        print(f"cookies set validation: {res.cookies}")


async def search(session: CoupangClientSession, keyword):
    url = f"https://m.coupang.com/nm/search?q={quote(keyword)}"
    async with session.get(url) as res:
        # todo: res 가 정상적인지 쿠키는 받아와졌는지 검증(출력)
        # todo: search_id 파싱 후 session.search_id = 할당 및 검증(출력)
        if res.status == 200:            
            info = await res.text()
            data = bf(info, 'html.parser')        
            li_tag = data.find('li', {'class': "plp-default__item"})
            try:
                product_link = li_tag.find('a', href=True)
            except AttributeError:
                raise NotParsedSearchId
            except Exception as e:
                raise e
#                print(product_link['href'])
#                residue = re.sub(r'.+searchId\=','', product_link['href'])
#                session.search_id = re.sub(r'\&clickEventId\=.+', '', residue)
#                print(f"cookies set validation after getting searchId: {residue}")
            try:
                product_link_href = product_link['href']
            except AttributeError:
                raise NotParsedSearchId('href not found in a tag')

            qs = parse_qs(product_link_href)
            search_id = qs['searchId'][0]
            session.search_id = search_id
            print(f'session.search_id = {search_id}')

        else:
            raise ServerError

        # 검증
        if _l := len(session.search_id) != 32:
            print(f'search_id 자리수가 32가 아닙니다({_l})({session.search_id})')
        if re_search := re.search('[^a-z0-9]', session.search_id):
            print(f'파싱이 잘못되었거나 갑의 형식이 바뀌었을 수 있습니다. 소문자와 숫자가 아닌 문자({re_search.group()})가 삽입되어 있습니다.({search_id.search_id})')


async def click(session: CoupangClientSession, keyword, product_id, item_id):
    url = f"https://m.coupang.com/vm/products/{product_id}?itemId={item_id}&q={quote(keyword)}&searchId={session.search_id}"
    try:
        int(item_id), int(product_id)
    except ValueError as e:
        print('item_id 또는 product_id의 값에 이상이 있습니다.')
        raise WrongData('item_id 또는 product_id의 값에 이상이 있습니다.')

    print(product_id, item_id, keyword, session.search_id)
    print('url:', url)
    async with session.get(url) as res:
        # todo: res 가 정상적인지 쿠키는 받아와졌는지 검증
        if res.status == 200:
            info = await res.text()
            file_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
            await create_dir(f'{file_path}\\coro_test')            
            await save_traffic_log(info, f"{file_path}\\coro_test\\{keyword}_{item_id}.html")


async def save_traffic_log(data, file_name):    
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(str(data))
        f.write(str(data))


async def work(slot, headers_list):
    ses = CoupangClientSession()
    print('헤더 세팅을 시작합니다')
    await set_headers(session=ses, headers_list=headers_list)
    print('헤더 세팅 완료')
    print('메인 페이지를 접속합니다')
    await go_main_page(session=ses)
    print('메인 페이지를 접속 완료')
    print(f'검색을 시도합니다({slot.keyword})')
    await search(session=ses, keyword=slot.keyword)
    print(f'검색 완료({slot.keyword})')
    print('클릭을 시도합니다')
    await click(session=ses, keyword=slot.keyword, product_id=slot.product_id, item_id=slot.item_id)
    print('클릭 완료')
    await ses.close()

    # 기록
    _now = datetime.datetime.now()
    add_count_date_log(_now, 1)
    product_log(_now, slot)
    slot_log(_now, slot)

