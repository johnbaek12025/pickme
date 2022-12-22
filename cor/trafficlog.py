import asyncio
import datetime
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from cor.common import make_coro, save_file

from cor.path import DATE_LOG_DIR, ERROR_LOG_DIR, PRODUCT_LOG_DIR, SLOT_LOG_DIR
from cor.slotdata import Slot

write_executor = ThreadPoolExecutor(max_workers=1)


def thread_json_dump(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False)


def add_count_date_log(now, num):
    today_date = now.strftime('%Y%m%d')
    log_file_path = os.path.join(DATE_LOG_DIR, f'{today_date}.txt')
    if os.path.isfile(log_file_path):
        with open(log_file_path, 'r') as f:
            future = write_executor.submit(json.load, f)
            today_count = future.result()
    else:
        today_count = 0
    today_count += num
    
    write_executor.submit(thread_json_dump, log_file_path, today_count)


def product_log(now, slot: Slot):
    today_date = now.strftime('%Y%m%d')
    today_time = now.strftime('%H%M')

    product_log_file_path = os.path.join(PRODUCT_LOG_DIR, f'{slot.product_id}.txt')

    if os.path.isfile(product_log_file_path):
        with open(product_log_file_path, 'r') as f:
            product_log = json.load(f)
    else:
        product_log = {'date_count': {today_date: 0}, 'details': {today_date: []}}

    try:
        c = product_log['date_count'][today_date]
    except KeyError:
        c = 0
    c += 1
    product_log['date_count'][today_date] = c

    try:
        details = product_log['details'][today_date]   # 주의: KeyError 가 details 에서 나는 경우에 따른 에러 처리도 보강해야 함
    except KeyError:
        details = list()
    details.append(today_time)  # todo: 차후에는 쿠키값과 아이피값을 함께 추가
    product_log['details'][today_date] = details
    write_executor.submit(thread_json_dump, product_log_file_path, product_log)


def slot_log(now, slot: Slot):
    today_date = now.strftime('%Y%m%d')
    today_time = now.strftime('%H%M')

    slot_log_file_path = os.path.join(SLOT_LOG_DIR, f'{slot.server_pk}.txt')

    if os.path.isfile(slot_log_file_path):
        with open(slot_log_file_path, 'r') as f:            
            slot_log = json.load(f)            
    else:
        slot_log = {'date_count': {today_date: 0}, 'details': {today_date: []}}

    try:
        c = slot_log['date_count'][today_date]
    except KeyError:
        c = 0
    c += 1
    slot_log['date_count'][today_date] = c

    try:
        details = slot_log['details'][today_date]  # 주의: KeyError 가 details 에서 나는 경우에 따른 에러 처리도 보강해야 함
    except KeyError:
        details = list()
    details.append(today_time)  # todo: 차후에는 쿠키값과 아이피값을 함께 추가
    slot_log['details'][today_date] = details
    write_executor.submit(thread_json_dump, slot_log_file_path, slot_log)


async def error_log(slot: Slot, error_msg):
    _now = datetime.datetime.now()
    error_log_file_path = os.path.join(ERROR_LOG_DIR, f'{slot.server_pk}_{slot.product_id}_{slot.item_id}.txt')
    if os.path.isfile(error_log_file_path):
        loop = asyncio.get_running_loop()
        with open(error_log_file_path, 'r') as f:            
            # error_log = json.load(f)
            error_log = f.read()
            # future = await loop.run_in_executor(None, , data)
            # task = asyncio.create_task(make_coro(future))
            # await task
            # data = task.result()
    else:
        error_log = ""
    error_log += f"[{_now}] {slot.product_id}itemId={slot.item_id} {error_msg}\n"
    write_executor.submit(save_file, error_log, error_log_file_path)