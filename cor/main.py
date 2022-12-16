__appname__ = "cor_pickme"
__version__ = "1.1"

import asyncio
import json

from ip import swap_ip
from slotdata import fetch_slots
from traffic import work
import optparse
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from cor import common


def list_chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]

async def make_coro(future):#2
    try:
        return await future
    except asyncio.CancelledError:
        return await future

async def main(config_dict):
    data_base_info = config_dict.get("data_database")
    if not data_base_info:
        return
    header_list_path = config_dict.get("header_list_path")
    if not header_list_path:
        return    
    etc = config_dict.get('etc')
    if not etc:
        return
    concurrency_max = int(etc.get('concurrency_max'))
    header_list = await read_json(header_list_path.get('path'))    
        
    while True:
        slots = await fetch_slots(data_base_info)  #db에서 리스트를 가져옴        
        slot_chunks = list_chunk(slots, concurrency_max)# 리스트를
        for slot_chunk in slot_chunks: #리스트를 for loop
            await swap_ip()
            work_tasks = list()
            for slot in slot_chunk:                
                work_tasks.append(asyncio.create_task(work(keyword=slot.keyword, product_id=slot.product_id, item_id=slot.item_id, headers_list=header_list)))
            await asyncio.gather(*work_tasks) #coroutine 실행

async def read_json(path):
    with open(path, 'rt', encoding='utf-8-sig') as f:
        data = f.read()
    data = json.loads(data)
    return data

if __name__ == '__main__':
    # with open('list.json', encoding='utf-8') as f:
    #     list_slot = json.loads(f.read())
    # with open('../cfg/android_samsung.json', encoding='utf-8') as f:
    #     headers = json.loads(f.read())
    usage = """%prog [options]"""
    parser = optparse.OptionParser(usage=usage, description=__doc__)    
    common.add_basic_options(parser)
    (options, args) = parser.parse_args()
    config_dict = common.read_config_file(options.config_file)
    # log_dict = config_dict.get("log", {})
    # log_file_name = "cor_pickme.log"
    # common.setup_logging(
    #     appname=__appname__,
    #     appvers=__version__,
    #     filename=log_file_name,
    #     dirname=options.log_dir,
    #     debug=options.debug,
    #     log_dict=log_dict,
    #     emit_platform_info=True,
    # )
    asyncio.run(main(config_dict))