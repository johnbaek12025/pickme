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
from slotdata import fetch_slots
from traffic import work
import optparse
from Errors import *
from common import *
from cor.trafficlog import *



logger = logging.getLogger(__name__)

def list_chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]

async def main(config_dict):
    HEADER_LIST_PATH = config_dict.get("header_list_path")
    if not HEADER_LIST_PATH:
        raise ConfigError('config파일 확인 [header_list_path]')
    ETC = config_dict.get('etc')
    if not ETC:
        raise ConfigError('config파일 확인 [etc]')
    CONCURRENCY_MAX = int(ETC.get('concurrency_max'))
    NO_IP_SWAP = to_bool(ETC.get('no_ip_swap', False))
    SLOT_MAX_COUNT = int(ETC.get('slot_max_count'))
    header_list = await read_json(HEADER_LIST_PATH.get('path'))
    print('CONFIG_SETTING')
    print(f"CONCURRENCY_MAX: {CONCURRENCY_MAX}")
    print(f"NO_IP_SWAP: {NO_IP_SWAP}")
    print(f"HEADER_LIST = {header_list}")
    print(f"max_slot_click {SLOT_MAX_COUNT}")
    slots = await fetch_slots(CONCURRENCY_MAX)  #db에서 리스트를 가져옴        
    now_datetime = datetime.datetime.today()
    one_hour_after = (now_datetime + timedelta(hours=1)).strftime('%H%M')
    now_datetime = now_datetime.strftime('%H%M')    
    while True:        
        if now_datetime > one_hour_after:            
            now_datetime = datetime.datetime.today()
            one_hour_after = (now_datetime + timedelta(hours=1)).strftime('%H%M')
            now_datetime = now_datetime.strftime('%H%M')
            slots = await fetch_slots(CONCURRENCY_MAX)  #db에서 리스트를 가져옴
            print('-----------------------new slots brought-----------------------')
        slot_chunks = list_chunk(slots, CONCURRENCY_MAX)# 리스트를
        # for slot_chunk in slot_chunks: #리스트를 for loop            
        #     if not NO_IP_SWAP: # ip 변경여부 config
        #         await swap_ip()
        #     work_tasks = list()
        #     semaphore = asyncio.Semaphore(CONCURRENCY_MAX)            
        #     async with semaphore:
        #         for slot in slot_chunk:
        #             work_tasks.append(asyncio.create_task(work(slot=slot, headers_list=header_list, slot_max_count=SLOT_MAX_COUNT)))
        #         await asyncio.gather(*work_tasks) #coroutine 실행        
        
        
            
            
            
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
    asyncio.run(main(config_dict))