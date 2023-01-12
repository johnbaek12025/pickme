import asyncio
import datetime
import datetime
import json
import re
from typing import List
from urllib.parse import parse_qs, urlsplit
from cor.Errors import ServerError
from cor.ip import swap_ip
import random
from aiohttp import ClientSession
import asyncio


class Slot:
    def __init__(self, server_pk, keyword, product_id, item_id, vendor_item_id):
        self.server_pk = int(server_pk)
        self.keyword = keyword
        self.product_id = product_id
        self.item_id = item_id
        self.vendor_item_id = vendor_item_id
        self.count = 0
        self.lock = asyncio.Lock()
        self.previous_date = datetime.date.today()
        
        
async def increment_count(obj):    
    async with obj.lock:        
        obj.count += 1


async def fetch_slots(CONCURRENCY_MAX) -> List[Slot]:    
    # todo: slot 정보를 불러와서 Slot 으로 객체화하여 리스트에 반환    
    def get_param_dict(url):
        params = parse_qs(urlsplit(url).query)
        return {k:v[0] if v else None for k,v in params.items()}
    slots = await get_data_set(CONCURRENCY_MAX)
    print(f"갯수 {len(slots)}")
    object_list = []
    random.shuffle(slots)
    for i, s in enumerate(slots):
        residue = re.sub(r'.+products/', '', s['p_url'])        
        res = get_param_dict(s['p_url'])
        try:
            product_id = re.sub(f'\?itemId={res["itemId"]}&vendorItemId={res["vendorItemId"]}.*', '', residue)
        except KeyError:
            product_id = re.sub(f'\?vendorItemId={res["vendorItemId"]}.*', '', residue)
        res['productId'] = product_id
        try:
            object_list.append(Slot(server_pk=s['id'], product_id=res['productId'], item_id=res["itemId"], keyword=s['Keyword'], vendor_item_id=res["vendorItemId"]))
        except KeyError:
            object_list.append(Slot(server_pk=s['id'], product_id=res['productId'], item_id=res["vendorItemId"], keyword=s['Keyword'], vendor_item_id=res["vendorItemId"]))
    return object_list


async def get_data_set(CONCURRENCY_MAX):
    semaphore = asyncio.Semaphore(CONCURRENCY_MAX)    
    url = 'https://api.wooriq.com/cp/cp_keysel.php'
    async with semaphore:
        async with ClientSession() as session:
            async with session.get(url) as res:
                if status := res.status == 200:
                    print(f"get api cp_list {status}")
                    result = await res.text()
                    return json.loads(result)
                else:
                    raise ServerError(f'cp_list api error')