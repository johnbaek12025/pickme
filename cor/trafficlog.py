import asyncio
import datetime
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from cor.common import *

from cor.path import DATE_LOG_DIR, ERROR_LOG_DIR, SLOT_LOG_DIR, PRODUCT_IP_DIR, VENDOR_ITEM_LOG_DIR
from cor.slotdata import Slot

write_executor = ThreadPoolExecutor(max_workers=1)


def thread_json_dump(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False)

async def product_ip_log(slot, current_ip):
    _now = datetime.datetime.now()
    now_datetime = _now.strftime("%Y%m%d")
    today_time = _now.strftime('%H%M')
    create_dir(f"{PRODUCT_IP_DIR}\\{now_datetime}")
    ip_log_file_path = os.path.join(f"{PRODUCT_IP_DIR}\\{now_datetime}", f'{slot.vendor_item_id}.json')
    if os.path.isfile(ip_log_file_path):
         with open(ip_log_file_path, 'r') as f:
            ip_list = json.load(f)
    else:
        ip_list = {current_ip: [today_time]}        
    try:
        ip_list[current_ip].append(today_time)    
    except KeyError:        
        ip_list[current_ip] = []
        ip_list[current_ip].append(today_time)
    write_executor.submit(thread_json_dump, ip_log_file_path, ip_list)
    
        
def add_count_date_log(now, num):
    today_date = now.strftime('%Y%m%d')
    log_file_path = os.path.join(DATE_LOG_DIR, f'{today_date}.json')
    if os.path.isfile(log_file_path):
        with open(log_file_path, 'r') as f:
            future = write_executor.submit(json.load, f)
            today_count = future.result()
    else:
        today_count = 0        
    today_count += num    
    write_executor.submit(thread_json_dump, log_file_path, today_count)


def vendor_item_log(now, slot: Slot):
    today_date = now.strftime('%Y%m%d')
    today_time = now.strftime('%H%M')

    vendor_item_log_file_path = os.path.join(VENDOR_ITEM_LOG_DIR, f'{slot.vendor_item_id}.json')

    if os.path.isfile(vendor_item_log_file_path):
        with open(vendor_item_log_file_path, 'r') as f:
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
    write_executor.submit(thread_json_dump, vendor_item_log_file_path, product_log)


def slot_log(now, slot: Slot):
    today_date = now.strftime('%Y%m%d')
    today_time = now.strftime('%H%M')

    slot_log_file_path = os.path.join(SLOT_LOG_DIR, f'{slot.server_pk}.json')

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
    now_datetime = _now.strftime("%Y%m%d")
    create_dir(f"{ERROR_LOG_DIR}\\{now_datetime}")
    error_log_file_path = os.path.join(f"{ERROR_LOG_DIR}\\{now_datetime}", f'{slot.server_pk}_{slot.product_id}_{slot.item_id}.txt')
    if os.path.isfile(error_log_file_path):
        with open(error_log_file_path, 'r', encoding='utf-8') as f:  
            error_log = f.read()                    
    else:
        error_log = ""
    error_log += f"[{_now}] {slot.product_id}itemId={slot.item_id} {error_msg}\n"
    write_executor.submit(save_file, error_log, error_log_file_path)
    
