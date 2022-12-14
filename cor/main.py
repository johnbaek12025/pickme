import asyncio
import json

from ip import swap_ip
from slotdata import fetch_slots
from traffic import work

concurrency_max = 5


def list_chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]


async def main(list_slot, headers_list):
    
    while True:
        slots = await fetch_slots(list_slot)  #db에서 리스트를 가져옴

        slot_chunks = list_chunk(slots, concurrency_max)# 리스트를  
        for slot_chunk in slot_chunks: #리스트를 for loop
            # await swap_ip()        
            work_tasks = list()
            for slot in slot_chunk:
                work_tasks.append(asyncio.create_task(work(keyword=slot.keyword, product_id=slot.product_id, item_id=slot.item_id, headers_list=headers_list)))
            await asyncio.gather(*work_tasks) #coroutine 실행



if __name__ == '__main__':
    with open('list.json', encoding='utf-8') as f:
        list_slot = json.loads(f.read())
    with open('../cfg/android_samsung.json', encoding='utf-8') as f:
        headers = json.loads(f.read())
    asyncio.run(main(list_slot, headers))