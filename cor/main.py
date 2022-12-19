__appname__ = "cor_pickme"
__version__ = "1.1"

import asyncio
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from ip import swap_ip
from slotdata import fetch_slots
from traffic import work
import optparse
from Errors import *
from common import *
from cor.db_manager import DBManager



def list_chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]


async def main(config_dict):
    data_base_info = config_dict.get("data_database")
    if not data_base_info:        
        raise ConfigError('config파일 확인 [data_database]')
    header_list_path = config_dict.get("header_list_path")
    if not header_list_path:
        raise ConfigError('config파일 확인 [header_list_path]')
    etc = config_dict.get('etc')
    if not etc:
        raise ConfigError('config파일 확인 [etc]')
    concurrency_max = int(etc.get('concurrency_max'))
    ip_swap = bool(etc.get('ip_swap', False))
    header_list = await read_json(header_list_path.get('path'))    
    while True:
        slots = await fetch_slots(data_base_info)  #db에서 리스트를 가져옴        
        slot_chunks = list_chunk(slots, concurrency_max)# 리스트를
        for slot_chunk in slot_chunks: #리스트를 for loop            
            if not ip_swap: # ip 변경여부 config
                await swap_ip()                
            work_tasks = list()
            for slot in slot_chunk:
                work_tasks.append(asyncio.create_task(work(slot=slot, headers_list=header_list)))
            await asyncio.gather(*work_tasks) #coroutine 실행
            #db_update
            server_pk_list = [slot.server_pk for slot in slot_chunk]
            try:
                update_keywordlist(server_pk_list, data_base_info)
            except ServerError:
                print(f"{server_pk_list}, update_keywordlist error")
            else:
                print('update success')

def update_keywordlist(server_pk_list, data_base_info):
    sql = f"""
        update cp_keywordlist set TotalWorkCount = TotalWorkCount + 1 , 
                                  WorkCount = WorkCount + 1, 
                                  LastWorkdt = now() 
        where ID = %s
        """
    wooriq_db = DBManager()    
    wooriq_db.connect(**data_base_info)    
    try:
        wooriq_db.modify_many(sql, server_pk_list,commit=True)
    except Exception as e:
        raise ServerError (f'{server_pk_list} update error {e}')


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