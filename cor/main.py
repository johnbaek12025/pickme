__appname__ = "cor_pickme"
__version__ = "1.1"

import asyncio
import json
import os
import sys
from datetime import timedelta, datetime
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from cor.common import *
from ip import swap_ip
from slotdata import fetch_slots, Slot
from traffic import work
import optparse
from Errors import *
from common import *
from cor.trafficlog import *




logger = logging.getLogger(__name__)


async def main(config_dict):
    HEADER_LIST_PATH = config_dict.get("header_list_path")
    if not HEADER_LIST_PATH:
        raise ConfigError('config파일 확인 [header_list_path]')
    ETC = config_dict.get('etc')
    if not ETC:
        raise ConfigError('config파일 확인 [etc]')
    CONCURRENCY_MAX = int(ETC.get('concurrency_max'))
    NO_IP_SWAP = to_bool(ETC.get('no_ip_swap', False))
    COOKIE_REUSE_INTERVAL = int(ETC.get('cookie_reuse_interval', 6))
    COOKIE_MAX_REUSE = int(ETC.get('cookie_max_reuse', 10))
    header_list = await read_json(HEADER_LIST_PATH.get('path'))
    print('CONFIG_SETTING')
    print(f"CONCURRENCY_MAX: {CONCURRENCY_MAX}")
    print(f"NO_IP_SWAP: {NO_IP_SWAP}")
    print(f"HEADER_LIST = {header_list}")    
    slots = await fetch_slots(CONCURRENCY_MAX)  #db에서 리스트를 가져옴        
    now_date = datetime.datetime.today()    
    criteria_date = config_dict['criteria_date']
    current_ip = None
    slot_dict = {}
    i = 0
    cnt = 0
    while True:
        print('cnt =================== ', cnt)               
        if cnt >= 5:            
            slots = await fetch_slots(CONCURRENCY_MAX)  #db에서 리스트를 가져옴
            cnt = 0
            print('-----------------------new slots brought-----------------------')            
        slot_chunks = list_chunk(slots, CONCURRENCY_MAX)
        for slot_chunk in slot_chunks: #리스트를 for loop            
            work_tasks = list()            
            if not NO_IP_SWAP: # ip 변경여부 config
                current_ip = await swap_ip()            
            if i <= 300:
                #result.append({'p_url': 'https://www.coupang.com/vp/products/7054578165?itemId=17475148376&vendorItemId=84642758010&isAddedCart=', 'Keyword': '찰보리빵', 'id': 9999999})
                work_tasks.append(asyncio.create_task(work(Slot(server_pk=999999, product_id="7054578165", item_id="17475148376",vendor_item_id="84642758010", keyword='찰보리빵', not_update=True), headers_list=header_list, COOKIE_REUSE_INTERVAL=COOKIE_REUSE_INTERVAL , COOKIE_MAX_REUSE=COOKIE_MAX_REUSE, current_ip=current_ip)))
                i += 1
            for slot in slot_chunk:                
                current_date = datetime.datetime.today().strftime('%Y%m%d')                
                try:
                    slot_dict[str(slot['server_pk'])]
                except KeyError:
                    slot_dict[str(slot['server_pk'])] = Slot(server_pk=slot['server_pk'], product_id=slot['product_id'], item_id=slot['item_id'], vendor_item_id=slot['vendor_item_id'], keyword=slot['keyword'])                    
                if criteria_date != current_date:
                    i = 0
                    slot_dict[str(slot['server_pk'])].count = 0
                    criteria_date = datetime.datetime.today().strftime('%Y%m%d')
                print(f"current count of {slot_dict[str(slot['server_pk'])].server_pk} of {slot_dict[str(slot['server_pk'])].keyword}  ====== {slot_dict[str(slot['server_pk'])].count}")
                work_tasks.append(asyncio.create_task(work(slot=slot_dict[slot['server_pk']], headers_list=header_list, COOKIE_REUSE_INTERVAL=COOKIE_REUSE_INTERVAL , COOKIE_MAX_REUSE=COOKIE_MAX_REUSE, current_ip=current_ip)))
            await asyncio.gather(*work_tasks) #coroutine 실행
        cnt += 1

async def read_json(path):
    with open(path, 'rt', encoding='utf-8-sig') as f:
        data = f.read()
    data = json.loads(data)
    return data


if __name__ == '__main__':    
    usage = """%prog [options]"""
    parser = optparse.OptionParser(usage=usage, description=__doc__)    
    add_basic_options(parser)
    (options, args) = parser.parse_args()
    config_dict = read_config_file(options.config_file)
    config_dict['criteria_date'] = datetime.datetime.today().strftime('%Y%m%d')
    asyncio.run(main(config_dict))
