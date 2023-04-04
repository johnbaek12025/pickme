import asyncio
import datetime
import datetime
import json
import re
from typing import List
from urllib.parse import parse_qs
from cor.Errors import ServerError
from cor.ip import swap_ip
import random
from aiohttp import ClientSession
import asyncio
from common import get_param_dict

class Slot:    
    def __init__(self, server_pk, keyword, product_id, item_id, vendor_item_id, not_update=False):
        self.server_pk = str(server_pk)
        self.keyword = keyword
        self.product_id = product_id
        self.item_id = item_id
        self.vendor_item_id = vendor_item_id
        self.not_update = not_update
        self.count = 0
        self.lock = asyncio.Lock()

async def increment_count(obj):
    async with obj.lock:
        obj.count += 1


async def fetch_slots(CONCURRENCY_MAX) -> List[Slot]:
    # todo: slot 정보를 불러와서 Slot 으로 객체화하여 리스트에 반환    

    slots = await get_data_set(CONCURRENCY_MAX)
    
    test_chunk = []    
    random.shuffle(slots)
    for i, s in enumerate(slots):
        try:
            s['p_url'] = re.sub(r' + ', '', s['p_url'])
            re.match(r'\S*.*https://.+', s['p_url']).group()
        except AttributeError:            
            continue
        try:
            s['p_url'] = re.search(r'https://.+', s['p_url']).group()
        except AttributeError:
            continue
        s['p_url'] = re.sub('&isAddedCart=', '', s['p_url'])
        try:
            re.match(r'https.+', s['p_url']).group()
        except AttributeError:
            continue
        residue = re.sub(r'\?.+', '', s['p_url'])
        res = get_param_dict(s['p_url'])
        product_id = re.sub(r'[^0-9]+', '', residue)
        res['productId'] = product_id        
        try:
            test_chunk.append({"server_pk": s['id'], "product_id": res['productId'], "item_id": res["itemId"], "vendor_item_id": res["vendorItemId"], "keyword": s['Keyword']})                
        except KeyError:
            try:
                test_chunk.append({"server_pk": s['id'], "product_id": res['productId'], "item_id": res["vendorItemId"], "vendor_item_id": res["vendorItemId"], "keyword": s['Keyword']})
            except KeyError:
                try:
                    test_chunk.append({"server_pk": s['id'], "product_id": res['productId'], "item_id": res["itemId"], "vendor_item_id": res["itemId"], "keyword": s['Keyword']})
                except KeyError:
                    continue
        random.shuffle(test_chunk)
    return test_chunk


async def get_data_set(CONCURRENCY_MAX):
    url = 'https://api.wooriq.com/cp/cp_keysel.php'
    semaphore = asyncio.Semaphore(CONCURRENCY_MAX)
    async with semaphore:
        async with ClientSession() as session:
            async with session.get(url) as res:
                if status := res.status == 200:
                    print(f"get api cp_list {status}")
                    result = await res.text()                    
                    return json.loads(result)
                else:
                    raise ServerError(f'cp_list api error')
    
