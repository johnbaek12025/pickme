import asyncio

from cor.ip import swap_ip
from cor.slotdata import fetch_slots
from cor.traffic import work

concurrency_max = 5


def list_chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]


async def main():
    while True:
        slots = await fetch_slots()  #db에서 리스트를 가져옴

        slot_chunks = list_chunk(slots, concurrency_max)# 리스트를  
        for slot_chunk in slot_chunks: #리스트를 for loop
            await swap_ip()

            work_tasks = list()
            for slot in slot_chunk:
                work_tasks.append(asyncio.create_task(work(keyword=slot.keyword, residue=slot.product_id, item_id=slot.item_id)))
            await asyncio.gather(*work_tasks) #coroutine 실행



if __name__ == '__main__':
    asyncio.run(main())



