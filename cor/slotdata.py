import asyncio
from collections import OrderedDict
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

from concurrent.futures import ThreadPoolExecutor
write_executor = ThreadPoolExecutor(max_workers=1)

def thread_json_dump(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False)

class Slot:
    count = 0
    previous_server_pk = None
    previous_date = None
    def __init__(self, server_pk, keyword, product_id, item_id, vendor_item_id, not_update=False):
        self.server_pk = int(server_pk)
        self.keyword = keyword
        self.product_id = product_id
        self.item_id = item_id
        self.vendor_item_id = vendor_item_id
        self.not_update = not_update
        if Slot.previous_server_pk != self.server_pk:
            Slot.count += 1
        Slot.previous_server_pk = self.server_pk

async def fetch_slots(CONCURRENCY_MAX) -> List[Slot]:    
    # todo: slot 정보를 불러와서 Slot 으로 객체화하여 리스트에 반환    
    def get_param_dict(url):
        params = parse_qs(urlsplit(url).query)
        return {k:v[0] if v else None for k,v in params.items()}
    data = await get_data_set(CONCURRENCY_MAX)        
    data = OrderedDict(sorted(data.items(), key=lambda x: len(x[1]), reverse=True))
    write_executor.submit(thread_json_dump, 'before_processing.json', data)
    object_list = []
    list_chunks = []
    test_chunk = []
    test_list_chunks = []
    i = 0    
    urls = list(data.keys())    
    while len(data.items()):
        url = urls[i]
        try:
            value = data[url]
        except KeyError:
            continue    
        if not value:
            del(data[url])
            if len(urls) - 1 == i:        
                i = 0
            else:
                i += 1
            i += 1
            continue
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
            test_list_chunks.append(test_chunk)
            test_chunk = []
            object_list = []
        
        val = data[url].pop()    
        id = list(val.keys())
        keyword = list(val.values())
        try:
            object_list.append(Slot(server_pk=id[0], product_id=res['productId'], item_id=res["itemId"], keyword=keyword[0], vendor_item_id=res["vendorItemId"]))
            test_chunk.append({"server_pk": id[0], "product_id": res['productId'], "item_id": res["itemId"], "vendor_item_id": res["vendorItemId"], "keyword": keyword[0]})
            print(id[0], keyword[0], res)
        except KeyError:            
            object_list.append(Slot(server_pk=id[0], product_id=res['productId'], item_id=res["vendorItemId"], keyword=keyword[0], vendor_item_id=res["vendorItemId"]))
            test_chunk.append({"server_pk": id[0], "product_id": res['productId'], "item_id": res["vendorItemId"], "vendor_item_id": res["vendorItemId"], "keyword": keyword[0]})
            print(id[0], keyword[0], res)
    test_list_chunks.append(test_chunk)
    list_chunks.append(object_list)
    write_executor.submit(thread_json_dump, 'after_processing.json', test_list_chunks)
    random.shuffle(list_chunks)
    return list_chunks


def preprocess(result):
    vendor_dict = {}
    #hard coding for 찰보리빵    
    result.append({'p_url': 'https://www.coupang.com/vp/products/7054578165?itemId=17475148376&vendorItemId=84642758010&isAddedCart=', 'Keyword': '찰보리빵', 'id': 9999999})
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