import os
import sys
import time
import random
import re
import requests
import queue
import threading


def get_myip(wait_seconds=180, proxy=None):

    st = time.time()

    servers = [
        'http://ip.dnsexit.com',
        'http://ifconfig.me/ip',
        'http://ipecho.net/plain',
        'http://checkip.dyndns.org/plain',
        'http://myexternalip.com/raw',
        'http://www.trackip.net/',
        'http://icanhazip.com/',
        'http://formyip.com/',
        'https://check.torproject.org/',
        'http://checkip.dyndns.com/',
        'http://httpbin.org/ip',
        'https://api.ipify.org',
        'https://v4.ident.me']



    q = queue.Queue()

    def try_get(que, proxy=proxy):
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

        que.put(myip)

        return myip

    while True:
        thrd = threading.Thread(target=try_get, args=(q,))
        thrd.start()
        print('아이피 추출을 위해 아이피 체커 사이트 접속 중')
        time.sleep(1)
        qget = q.get()
        if re.search('\d+\.\d+\.\d+\.\d+', qget):
            return qget
        else:
            if time.time() -st > wait_seconds:
                return 'Failure'
            time.sleep(1)


def switchIp2():

    ##안드로이드 버전 높은 경우
    n = 1

    while True:        
        path = os.path.abspath(os.path.dirname(__file__))       
        if not os.path.isfile(f"{path}\\"+'adb.exe'):
            return
        print('아이피 변경 시도(' + str(n) + '회)')
        latestIp = get_myip()
        os.system(f"{path}\\" + 'adb shell svc data disable')
        time.sleep(0.5)
        os.system(f"{path}\\" + 'adb shell svc data enable')
        currentIp = get_myip()
        print(f'before:{latestIp}, after:{currentIp}')
        n += 1
        if latestIp != currentIp and re.search('\d+\.\d+\.\d+\.\d+', currentIp):
            return currentIp
        else:
            print('2s waiting ...')
            time.sleep(2)
            if n >= 3:
                return False


if __name__ == "__main__":
    ip = switchIp2()
    print(ip)