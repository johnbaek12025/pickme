import asyncio
from collections import OrderedDict
import datetime
import datetime
import json
import re
from typing import List
from urllib.parse import parse_qs, urlsplit
from cor.Errors import ServerError
from common import get_non_duplicated_dict_list, preprocess
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
    def __init__(self, server_pk, keyword, product_id, item_id, vendor_item_id, not_update=False):
        self.server_pk = int(server_pk)
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
    def get_param_dict(url):
        params = parse_qs(urlsplit(url).query)
        return {k:v[0] if v else None for k,v in params.items()}
    data = await get_data_set(CONCURRENCY_MAX)        
    data = OrderedDict(sorted(data.items(), key=lambda x: len(x[1]), reverse=True))
    write_executor.submit(thread_json_dump, 'before_processing.json', data)
    list_chunks = get_non_duplicated_dict_list(data, CONCURRENCY_MAX)
    write_executor.submit(thread_json_dump, 'after_processing.json', list_chunks)
    random.shuffle(list_chunks)
    return list_chunks

   
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