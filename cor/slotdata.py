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
    def __init__(self, server_pk, keyword, product_id, item_id, vendor_item_id, not_update=False):
        self.server_pk = int(server_pk)
        self.keyword = keyword
        self.product_id = product_id
        self.item_id = item_id
        self.vendor_item_id = vendor_item_id
        self.not_update = not_update

async def fetch_slots(CONCURRENCY_MAX) -> List[Slot]:    
    # todo: slot 정보를 불러와서 Slot 으로 객체화하여 리스트에 반환    
    def get_param_dict(url):
        params = parse_qs(urlsplit(url).query)
        return {k:v[0] if v else None for k,v in params.items()}
    data = await get_data_set(CONCURRENCY_MAX)
    # print(f"갯수 {len(slots)}")
    object_list = []
    list_chunks = []
    i = 0
    while i < len(data):
        url, val = list(data.items())[i]
        try:
            re.match(r'https.+', url).group()
        except AttributeError:
            continue
        residue = re.sub(r'\?.+', '', url)
        res = get_param_dict(url)
        product_id = re.sub(r'[^0-9]+', '', residue)
        res['productId'] = product_id        
        if len(object_list) >= CONCURRENCY_MAX:
            list_chunks.append(object_list)
            object_list = []
        val = val.pop()
        id = list(val.keys())
        keyword = list(val.values())
        try:
            object_list.append(Slot(server_pk=id[0], product_id=res['productId'], item_id=res["itemId"], keyword=keyword[0], vendor_item_id=res["vendorItemId"]))
            print(id[0], keyword[0], res)
        except KeyError:            
            object_list.append(Slot(server_pk=id[0], product_id=res['productId'], item_id=res["vendorItemId"], keyword=keyword[0], vendor_item_id=res["vendorItemId"]))
            print(id[0], keyword[0], res)
        i += 1
    random.shuffle(list_chunks)
    return list_chunks


def preprocess(result):
    vendor_dict = {}
    for item in result:
        try:
            item['p_url'] = re.sub(r' + ', '', item['p_url'])
            re.match(r'\S*.*https://.+', item['p_url']).group()
        except AttributeError:            
            continue
        try:
            item['p_url'] = re.search(r'https://.+', item['p_url']).group()
        except AttributeError:
            continue
        item['p_url'] = re.sub('&isAddedCart=', '', item['p_url'])    
        try:
            vendor_dict[item['p_url']]
        except KeyError:
            vendor_dict[item['p_url']] = []        
        vendor_dict[item['p_url']].append({item['id']: item['Keyword']})
    return vendor_dict   
    

async def get_data_set(CONCURRENCY_MAX):
    semaphore = asyncio.Semaphore(CONCURRENCY_MAX)    
    url = 'https://api.wooriq.com/cp/cp_keysel.php'
    async with semaphore:
        async with ClientSession() as session:
            async with session.get(url) as res:
                if status := res.status == 200:
                    print(f"get api cp_list {status}")
                    result = await res.text()
                    return preprocess(json.loads(result))
                else:
                    raise ServerError(f'cp_list api error')