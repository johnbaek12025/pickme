import asyncio
import datetime
import glob
import json
import logging
import os
#from traffic import CoupangClientSession

from concurrent.futures import ThreadPoolExecutor
from cor.clientsession import CoupangClientSession
from cor.common import *

from cor.path import DATE_LOG_DIR, DETAIL_LOG_DIR, ERROR_LOG_DIR, SLOT_LOG_DIR, VENDOR_ITEM_LOG_DIR, COOKIE_UA_DIR
from cor.slotdata import Slot
import pickle
write_executor = ThreadPoolExecutor(max_workers=1)


def thread_json_dump(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False)


def extract_cookie(header_id, path):    
    path = path.replace('\\', '/')
    pcid = re.sub(f".+/{header_id}/", "", path)
    return pcid
    

async def update_cookies_to(session: CoupangClientSession, header, COOKIE_REUSE_INTERVAL, COOKIE_MAX_REUSE):
    header_cookie_dir = os.path.join(f"{COOKIE_UA_DIR}", header['Num'])
    os.makedirs(header_cookie_dir, exist_ok=True)
    ua_cookie_log = os.path.join(f"{COOKIE_UA_DIR}", "cookie_log.json")    
    cookie_files = list(filter(os.path.isfile, glob.glob(os.path.join(header_cookie_dir, "*"))))
    cookie_files.sort(key=lambda x: os.path.getmtime(x))
    get_success = False
    if os.path.isfile(ua_cookie_log):            
        with open(ua_cookie_log, 'r', encoding='utf-8') as f:
            cookie_log = json.load(f)
    else:
        cookie_log = {}        
    for cf in cookie_files:        
        pcid = extract_cookie(header['Num'], cf)        
        how_many_used, last_used_at = cookie_log.get(pcid, (0, None))
        if last_used_at is not None:
            last_used_at = datetime.datetime.strptime(last_used_at, '%Y-%m-%d %H:%M')
            if datetime.datetime.now() - last_used_at < datetime.timedelta(hours=COOKIE_REUSE_INTERVAL):
                print(pcid, '3시간 이내의 사용 이력으로 해당 쿠키를 건너 뜀------------------------')
                continue
        if how_many_used <= COOKIE_MAX_REUSE:
            cookie_log[pcid] = [how_many_used + 1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M')]
            with open(cf, 'rb') as f:
                cookies = pickle.load(f)            
            get_success = True
            break
        else:
            if how_many_used >= COOKIE_MAX_REUSE:
                del cookie_log[pcid]
                #todo: 파일 삭제
                os.remove(cf)
                write_executor.submit(thread_json_dump, ua_cookie_log, cookie_log)
                write_executor.submit(thread_json_dump, ua_cookie_log[:-3] + str('backup.json'), cookie_log)
            else:
                cookie_log[pcid] = [how_many_used + 1, datetime.datetime.now().strftime('%Y-%m-%d %H:%M')]
                with open(cf, 'rb') as f:
                    cookies = pickle.load(f)                
                get_success = True
                break
    if get_success:        
        c_cookies_before = session.cookie_jar.filter_cookies('http://coupang.com')
        print(f'update cookies before: {c_cookies_before}')
        session._cookie_jar.update_cookies(cookies)
        c_cookies_after = session.cookie_jar.filter_cookies('http://coupang.com')
        print(f'update cookies after: {c_cookies_after}')
        write_executor.submit(thread_json_dump, ua_cookie_log, cookie_log)
        write_executor.submit(thread_json_dump, ua_cookie_log[:-3] + str('backup.json'), cookie_log)    
    else:
        print('활용가능한 쿠키가 없어 사전 로드한 쿠키 없이 작업합니다.')
        
        
def save_cookies(session: CoupangClientSession, header):
    header_cookie_dir = os.path.join(f"{COOKIE_UA_DIR}", header['Num'])
    os.makedirs(header_cookie_dir, exist_ok=True)
    print(session.cookie_jar)
    c_cookies = session.cookie_jar.filter_cookies('http://coupang.com')
    print('c_cookies:', c_cookies)
    pcid_val = c_cookies['PCID'].value
    if not pcid_val:
        print('pcid 쿠키가 없습니다.(저장 생략)')
        return
    with open(f"{header_cookie_dir}/{pcid_val}", 'wb') as f:
        pickle.dump(c_cookies, f)


async def product_ip_log(slot:Slot, current_ip, used_cookie):
    _now = datetime.datetime.now()
    now_datetime = _now.strftime("%Y%m%d")
    today_time = _now.strftime('%H%M')    
    ip_log_folder_path = os.path.join(DETAIL_LOG_DIR, now_datetime)
    os.makedirs(ip_log_folder_path, exist_ok=True)
    ip_log_file_path = f"{ip_log_folder_path}\\{slot.vendor_item_id}.json"
    if os.path.isfile(ip_log_file_path):
        with open(ip_log_file_path, 'r', encoding='utf-8') as f:
            log_info = json.load(f)
    else:        
        log_info = {slot.vendor_item_id: {'ip_log': {current_ip: {slot.server_pk: {slot.keyword: []}}}, 'slot_count':{slot.server_pk: 0}, 'cookie_log': {used_cookie: []}}}
    try:
        log_info[slot.vendor_item_id]['ip_log']
    except KeyError:
        log_info[slot.vendor_item_id]['ip_log'] = {current_ip: {slot.server_pk: {slot.keyword: []}}}
    try:
        log_info[slot.vendor_item_id]['ip_log'][current_ip]
    except KeyError:
        log_info[slot.vendor_item_id]['ip_log'][current_ip] = {slot.server_pk: {slot.keyword: []}}
    try:
        log_info[slot.vendor_item_id]['ip_log'][current_ip][slot.server_pk]
    except KeyError:
        log_info[slot.vendor_item_id]['ip_log'][current_ip][slot.server_pk]= {slot.keyword: list()}
    try:
        log_info[slot.vendor_item_id]['ip_log'][current_ip][slot.server_pk][slot.keyword]
    except KeyError:
        log_info[slot.vendor_item_id]['ip_log'][current_ip][slot.server_pk][slot.keyword] = list()
    try:
        log_info[slot.vendor_item_id]['slot_count']
    except KeyError:
        log_info[slot.vendor_item_id]['slot_count'] = {slot.server_pk: 0}
    try:
        log_info[slot.vendor_item_id]['slot_count'][slot.server_pk]
    except KeyError:
        log_info[slot.vendor_item_id]['slot_count'][slot.server_pk] = 0
    try:
        log_info[slot.vendor_item_id]['cookie_log']
    except KeyError:
        log_info[slot.vendor_item_id]['cookie_log'] = {used_cookie: []}
    try:
        log_info[slot.vendor_item_id]['cookie_log'][used_cookie]
    except KeyError:
        log_info[slot.vendor_item_id]['cookie_log'][used_cookie] = []
    log_info[slot.vendor_item_id]['ip_log'][current_ip][slot.server_pk][slot.keyword].append(today_time)
    log_info[slot.vendor_item_id]['slot_count'][slot.server_pk] += 1
    log_info[slot.vendor_item_id]['cookie_log'][used_cookie].append(today_time)    
    write_executor.submit(thread_json_dump, ip_log_file_path, log_info)


def vendor_item_log(now, slot: Slot):
    today_date = now.strftime('%Y%m%d')
    today_time = now.strftime('%H%M')
    vendor_item_log = os.path.join(VENDOR_ITEM_LOG_DIR, today_date)
    os.makedirs(vendor_item_log, exist_ok=True)
    vendor_item_log_file_path = os.path.join(vendor_item_log, f'{slot.vendor_item_id}.json')
    if os.path.isfile(vendor_item_log_file_path):
        with open(vendor_item_log_file_path, 'r', encoding='utf-8') as f:
            product_log = json.load(f)    
    else:
        product_log = {slot.vendor_item_id: {'slot_count':0}}
    try:
        c = product_log[slot.vendor_item_id]['product_count']
    except KeyError:
        c = 0
    c += 1
    product_log[slot.vendor_item_id]['product_count'] = c

    try:
        product_log[slot.vendor_item_id]['detail']  # 주의: KeyError 가 details 에서 나는 경우에 따른 에러 처리도 보강해야 함
    except KeyError:
        product_log[slot.vendor_item_id]['detail'] = list()
    product_log[slot.vendor_item_id]['detail'].append(today_time)  # todo: 차후에는 쿠키값과 아이피값을 함께 추가    
    write_executor.submit(thread_json_dump, vendor_item_log_file_path, product_log)

        
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
    
