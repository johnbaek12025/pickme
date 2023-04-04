import asyncio
import datetime
import json
import logging
import os
import random
import re
import time
from urllib.parse import quote, parse_qs, urlencode
from multidict import CIMultiDict
from aiohttp import ClientSession, ClientTimeout
from clientsession import CoupangClientSession
from bs4 import BeautifulSoup as bf
import requests
import traceback
from cor.Errors import NotFoundProducts, NotParsedSearchId, NotSearchedProductPrice, ServerError, WrongData
from cor.slotdata import Slot, increment_count
from asyncio.exceptions import TimeoutError
from aiohttp.client_exceptions import ClientConnectorError
from cor.trafficlog import add_count_date_log, save_cookies, update_cookies_to, error_log, product_ip_log, slot_log, vendor_item_log
from cor.common import *
from http import cookies
bundle_ID = "11"
C_APP_V = "3.8.8"
file_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
timeout = ClientTimeout(total=10)
retry_max = 3

async def create_dir(path):
    if os.path.isdir(path):
        return
    if os.path.isfile(path):
        return
    os.makedirs(path)


async def set_headers(session: CoupangClientSession, header):
    session._default_headers.update(CIMultiDict(header))
    #print(f"headers validation: {session.headers}")
    

async def retry_get(session: CoupangClientSession, retry_max, *args, **kwargs):    
    for i in range(retry_max):
        await asyncio.sleep(0.5)
        async with session.get(*args, **kwargs) as res:
            if status := res.status == 200:
                try:
                    result = await res.text()
                    cookies = res.cookies
                except TimeoutError:
                    #print(f"{i+1}번째 시도-----------------------------------\n-----------------------------------\n-------------------------------------------------------------")
                    continue                
                else:
                    if i >= 1:
                        #print(f"{i+1}번째 성공-----------------------------------\n-----------------------------------\n-------------------------------------------------------------")                    
                        pass
                    return result, cookies
            else:
                status = status
                #print(status)
                continue
    raise ServerError(f"{status}")
    


async def go_main_page(session):
    url = 'https://m.coupang.com'    
    try:
        info, cookies = await retry_get(session, retry_max=retry_max, url=url)                
    except ServerError as e:
        raise ServerError(f"coudn't get cookies from main_page")
    
        
        
        
    
            
async def search(session: CoupangClientSession, slot: Slot):
    url = f"https://m.coupang.com/nm/search?q={quote(slot.keyword)}"
    #print(f"search url {url}")
    try:
        info, cookies = await retry_get(session, retry_max=retry_max, url=url)
    except ServerError as e:
        raise(f"{slot.keyword} couldn't find searchId")
    # todo: res 가 정상적인지 쿠키는 받아와졌는지 검증(출력)
    # todo: search_id 파싱 후 session.search_id = 할당 및 검증(출력)   
    #print('cookies in search_function:----------------------------\n', cookies)
    data = bf(info, 'html.parser')
    li_tags = data.find_all('li', {'class': "plp-default__item"})
    if len(li_tags) == 0:
        raise NotFoundProducts(f"notfoundproducts list in search: {url}")
    try:
        product_links = [a['href'] for li_tag in li_tags if (a := li_tag.find('a', href=True)) is not None]
    except AttributeError:                
        raise NotParsedSearchId(f'href not found in a tag in search function {li_tags}')
    except Exception as e:
        raise e
    product_link_href = product_links[0]
    qs = parse_qs(product_link_href)
    search_id = qs['searchId'][0]
    session.search_id = search_id
    #print(f'session.search_id = {search_id}')
    

    # 검증
    if _l := len(session.search_id) != 32:
        #print(f'search_id 자리수가 32가 아닙니다({_l})({session.search_id})')
        pass
    if re_search := re.search('[^a-z0-9]', session.search_id):
        #print(f'파싱이 잘못되었거나 갑의 형식이 바뀌었을 수 있습니다. 소문자와 숫자가 아닌 문자({re_search.group()})가 삽입되어 있습니다.({search_id.search_id})')
        pass


async def click(session: CoupangClientSession, slot: Slot, header):
    url1 = f"https://m.coupang.com/vm/products/{slot.product_id}?itemId={slot.item_id}&q={quote(slot.keyword)}&searchId={session.search_id}&filterKey="
    try:
        int(slot.item_id), int(slot.product_id), int(slot.vendor_item_id)
    except ValueError as e:
            #print('item_id 또는 product_id, vendor_item_id의 값에 이상이 있습니다.')
        raise WrongData('item_id 또는 product_id, vendor_item_id의 값에 이상이 있습니다.')
        
    try:
        info, cookie_set = await retry_get(session, retry_max=retry_max, url=url1)
    except ServerError as e:
        raise(f"{url1} couldn't click")
    #await save_traffic_log(info, f'{slot.vendor_item_id}.html')    
    url2 = f"https://m.coupang.com/vm/v4/enhanced-pdp/products/{slot.product_id}?bundleId={bundle_ID}&vendorItemId={slot.vendor_item_id}&appVer={C_APP_V}&applyReconciliation=true&applyPddStandizing=true&threePlBadge=true&newGlobalBadge=true&priceGuaranteeBadge=true&applyNps=true"
    print(url2)
    print('\n')
    try:
        info, cookie_set = await retry_get(session, retry_max=retry_max, url=url2)
    except ServerError as e:
        raise(f"{url2} couldn't click")        
    url3 = f"https://m.coupang.com/vm/products/{slot.product_id}/recommendations/also-bought?itemId={slot.item_id}&vendorItemId={slot.vendor_item_id}&newPeopleAlsoBought=true&freshProduct=false&memberEligible=true"
    try:
        info, cookie_set = await retry_get(session, retry_max=retry_max, url=url3)
    except ServerError as e:
        raise(f"{url3} couldn't click")        
    else:      
        print(url3)
        print('\n')  
        return save_cookies(cookie_set, header)    

async def slot_update(slot):
    await asyncio.sleep(0.5)
    url = f"https://api.wooriq.com/cp/cp_keyup.php?id={slot.server_pk}"
    async with ClientSession(timeout=timeout) as session:
        async with session.get(url) as res:
            if status := res.status == 200:
                result = await res.text()
                print(f"slot_update result: {result}")            
            else:            
                print('fail update of the slot')
                pass

async def save_traffic_log(data, file_name):    
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(str(data))


# product_price search
def status_validation(url, session):        
        try:
            res = session.get(url)
        except Exception as e:
            #print(f'url: {url} {e}')
            raise (e)
        if res.status_code == 200:            
            try:                
                return res.json()
            except json.JSONDecodeError:                
                return res.text
        else:
            raise ServerError('price_url: not 200')


async def product_price_search(**kwargs):
    session = requests.Session()
    headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
                }
    session.headers.update(headers)
    session.cookies.set(**{"domain": ".coupang.com",
                    "value": "51829479347949486589994",
                    "path": "/",
                    "name": "PCID",
                    "rest": {"httpOnly": False, "sameSite": False},}
                        )
    loop = asyncio.get_running_loop()    
    future = loop.run_in_executor(None, status_validation, kwargs['product_url'], session)
    task = asyncio.create_task(make_coro(future))
    await task
    res = task.result()
    data = bf(res, 'html.parser')
    price_tag = data.find_all('span', {'class': 'total-price'})    
    try:
        product_price = [price for p in price_tag if (price := re.sub(r"[^0-9]+", "", p.text))][-1]    
    except IndexError:
        raise ('There is no price information')
    else:        
        update_url = f"https://api.wooriq.com/cp/cp_price.php?purl={kwargs['product_url']}&price={product_price}"
        future = loop.run_in_executor(None, status_validation, update_url, session)
        task = asyncio.create_task(make_coro(future))
        await task
        session.close()
        

async def work(slot, headers_list, COOKIE_REUSE_INTERVAL, COOKIE_MAX_REUSE, current_ip=None):
    # header = random.choice(headers_list)
    # cookies = await update_cookies_to(header, COOKIE_REUSE_INTERVAL, COOKIE_MAX_REUSE)
    ## print(type(cookies))
    pcid1 = None
    _now = datetime.datetime.now()    
    async with CoupangClientSession(timeout=timeout) as ses:
        try:
            header = random.choice(headers_list)
            pcid1 = await update_cookies_to(ses,header, COOKIE_REUSE_INTERVAL, COOKIE_MAX_REUSE)                        
            #print('헤더 세팅을 시작합니다')            
            await set_headers(session=ses, header=header)  
            #print('헤더 세팅 완료')
            #print('메인 페이지를 접속합니다')
            await go_main_page(session=ses)
            # print('메인 페이지를 접속 완료')
            # print(f'검색을 시도합니다({slot.keyword})')
            await search(session=ses, slot=slot)
            print(f'검색 완료({slot.keyword})')
            print('클릭을 시도합니다')
            pcid2 = await click(session=ses, slot=slot, header=header)
            print('클릭 완료')            
            if current_ip:                
                await product_ip_log(slot, current_ip, pcid1) if pcid1 else await product_ip_log(slot, current_ip, pcid2)                
            if not slot.not_update:
                await slot_update(slot)
            
        except NotFoundProducts as e:
            await error_log(slot, e)
            #print(f"{slot.keyword}, {slot.product_id}_{slot.item_id}_{slot.vendor_item_id}: {e}")
        except WrongData as e:
            await error_log(slot, e)
            #print(f"{slot.keyword}, {slot.product_id}_{slot.item_id}_{slot.vendor_item_id}: {e}")
        except NotParsedSearchId as e:
            await error_log(slot, e)
            #print(f"{slot.keyword}, {slot.product_id}_{slot.item_id}_{slot.vendor_item_id}: {e}")
        except ServerError as e:
            await error_log(slot, e)
            #print(f"{slot.keyword}, {slot.product_id}_{slot.item_id}_{slot.vendor_item_id}: {e}")
        except FileNotFoundError as e:
            await error_log(slot, e)
            #print(f"{slot.keyword}, {slot.product_id}_{slot.item_id}_{slot.vendor_item_id}: {e}")
        except ValueError as e:
            await error_log(slot, e)
            #print(f"{slot.keyword}, {slot.product_id}_{slot.item_id}_{slot.vendor_item_id}: {e}")
        except Exception as e:
            tb_str = traceback.format_exc()        
            await error_log(slot, tb_str)
        finally:
            await increment_count(slot)    
    # 기록    
    add_count_date_log(_now, 1)
    # vendor_item_log(_now, slot)
    # slot_log(_now, slot)
