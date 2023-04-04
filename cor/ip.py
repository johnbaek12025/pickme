import asyncio
import os
import socket
import requests
import queue
import threading
import random
import time
import re
import concurrent.futures

async def get_myip(wait_seconds=180, proxy=None):
    servers = [        
        'http://ifconfig.me/ip',
        'http://ipecho.net/plain',
        'http://myexternalip.com/raw',
        'http://www.trackip.net/',
        'http://icanhazip.com/',
        'http://formyip.com/',
        'http://httpbin.org/ip',
        'https://v4.ident.me',
        'https://haribo.ai/devops/api/check/my/ip',
        'http://ifconfig.me/ip',
        'http://ipecho.net/plain',
        'http://2shop.co.kr/getip.php']

    def try_get(proxy=proxy):
        myip = ''
        try:
            if proxy:
                re_search = re.search('https?://(.*)', proxy)
                if re_search:
                    proxy = re_search.group(1)
                proxies = {'http': 'http://' + proxy,
                           'https': 'http://' + proxy}
                res = requests.get(random.choice(servers), timeout=9, proxies=proxies)
            else:
                res = requests.get(random.choice(servers), timeout=9)
            res.raise_for_status()
            page_text = res.text
            myip = re.search('\d+\.\d+\.\d+\.\d+', page_text).group()
        except:
            pass
        return myip

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(try_get): url for url in servers}
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                myip = future.result()
                if re.search('\d+\.\d+\.\d+\.\d+', myip):
                    return myip
            except:
                continue
    return 'failure'


def change_process():
    path = os.path.abspath(os.path.dirname(__file__))    
    if not os.path.isfile(f"{path}\\"+'adb.exe'):
        print('테더링 확인')
    os.system(f"{path}\\" + 'adb shell svc data disable')
    time.sleep(1.0)
    os.system(f"{path}\\" + 'adb shell svc data enable')


def command_reset_tethering():
    path = os.path.abspath(os.path.dirname(__file__))    
    if not os.path.isfile(f"{path}\\"+'adb.exe'):
        print('테더링 확인')
    #os.system(f"{path}\\" + 'adb kill-server')
    #time.sleep(0.5)
    os.system(f"{path}\\" + 'adb shell am start -n com.android.settings/.TetherSettings')
    time.sleep(0.8)
    os.system(f"{path}\\" + 'adb shell input keyevent 20')
    time.sleep(0.8)
    os.system(f"{path}\\" + 'adb shell input keyevent 20')
    time.sleep(0.8)
    os.system(f"{path}\\" + 'adb shell input keyevent KEYCODE_ENTER')
    time.sleep(0.8)
    os.system(f"{path}\\" + 'adb shell input keyevent KEYCODE_ENTER')
    
    
async def swap_ip():
    ##안드로이드 버전 높은 경우
    n = 1    
    while True:                
        print('아이피 변경 시도(' + str(n) + '회)')
        lastIp = await get_myip()
        change_process()        
        currentIp = await get_myip()                
        print(f'before:{lastIp}, after:{currentIp}')
        n += 1
        if lastIp != currentIp and re.search('\d+\.\d+\.\d+\.\d+', currentIp):
            return currentIp
        else:
            print('2s waiting ...')
            await asyncio.sleep(2)
            if n > 20:
                print('`````````````````````````````````````\n\n\n\n``````````````````````')
                command_reset_tethering()
            continue
        
            
        
if __name__ == '__main__':
    x = asyncio.run(swap_ip())
    print(x)
