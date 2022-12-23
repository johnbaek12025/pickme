import asyncio
from datetime import datetime, timedelta
import json
import re
from typing import List
from urllib.parse import parse_qs
from cor.Errors import ServerError
from cor.ip import swap_ip
import random
from aiohttp import ClientSession


class Slot:

    def __init__(self, server_pk, keyword, product_id, item_id, vendor_item_id):
        self.server_pk = server_pk
        self.keyword = keyword
        self.product_id = product_id
        self.item_id = item_id
        self.vendor_item_id = vendor_item_id    


async def fetch_slots() -> List[Slot]:
    # todo: slot 정보를 불러와서 Slot 으로 객체화하여 리스트에 반환    
    slots = await get_data_set()
    object_list = []
    for i, s in enumerate(slots):
        residue = re.sub(r'.+vendorItemId=', '', s['p_url'])
        vendoritemid = re.sub(r'[^0-9]+', '', residue)
        residue = re.search(r'[0-9]+\?itemId\=[0-9]+', s['p_url'])
        if not residue:
            continue
        residue = residue.group(0)
        left = residue.split('?itemId=')
        if i % 5 == 0:
            object_list.append(Slot(server_pk='35574', product_id='1319235770', item_id='2339357717', keyword='1구 인덕션', vendor_item_id='77959174230'))
        object_list.append(Slot(server_pk=s['id'], product_id=left[0], item_id=left[1], keyword=s['Keyword'], vendor_item_id=vendoritemid))
    return object_list


async def get_data_set():
    session = ClientSession()
    url = 'https://api.wooriq.com/cp/cp_keysel.php'
    async with session.get(url) as res:
        # todo: res 가 정상적인지 쿠키는 받아와졌는지 검증(출력)
        if status := res.status == 200:
            print(f"get api cp_list {status}")
            result = await res.text()
            session.close()            
            return json.loads(result)
        else:
            raise ServerError(f'cp_list api error')