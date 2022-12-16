import asyncio
import os
import random
import re
from urllib.parse import quote
from multidict import CIMultiDict
from aiohttp import ClientSession
from bs4 import BeautifulSoup as bf

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
                session.search_id = None
            else:
                residue = re.sub(r'.+searchId\=','', product_link['href'])
                session.search_id = re.sub(r'\&clickEventId\=.+', '', residue)
                print(f"cookies set validation after getting searchId: {res.cookies}")

async def click(session: CoupangClientSession, keyword, product_id, item_id):
    url = f"https://m.coupang.com/vm/products/{product_id}?itemId={item_id}&q={quote(keyword)}&searchId={session.search_id}"
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
    

async def work(keyword, product_id, item_id, headers_list):    
    ses = CoupangClientSession()    
    await set_headers(session=ses, headers_list=headers_list)
    await go_main_page(session=ses)
    await search(session=ses, keyword=keyword)
    await click(session=ses, keyword=keyword, product_id=product_id, item_id=item_id)
    await ses.close()