import enum
from msilib.schema import Error
import os
import random
import sys
import time
import requests
from bs4 import BeautifulSoup as bf
import json
import numpy
import re
import logging
from urllib import parse
from mine.ip_util import switchIp2
from mine.common import create_dir, save_file


class PickMe:
    def __init__(self, **kwargs) -> None:
        self.pick_item_id = kwargs["itemid"]
        self.keyword = kwargs["keyword"]
        self.query_string = parse.quote_plus(self.keyword)
        self.session = None        
        self.wtime = numpy.arange(0.5, 2, 0.5)
        self.headers_path = kwargs['header_list_path']['path']
        self.main_url = 'http://www.coupang.com'        
        self.search_url = "https://www.coupang.com/np/search?q={query_string}&channel=auto&component=&eventCategory=SRP&trcid=&traid=&sorter=scoreDesc&minPrice=&maxPrice=&priceRange=&filterType=&listSize=&filter=&isPriceRange=false&brand=&offerCondition=&rating=0&page={page}&rocketAll=false&searchIndexingToken=1=6&backgroundColor="        
        self.search_url_price = "https://www.coupang.com/np/search?rocketAll=false&q={query_string}&brand=&offerCondition=&filter=&availableDeliveryFilter=&filterType=&isPriceRange=true&priceRange={price}&minPrice={price}&maxPrice={price}&page={page}&trcid=&traid=&filterSetByUser=true&channel=user&sorter=scoreDesc"
        self.file_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    
    def set_headers(self):
        with open(os.path.join(os.getcwd(), self.headers_path), 'rt', encoding='utf-8-sig') as f:
            data = f.read()
            data_list = json.loads(data)        
        headers = random.choice(data_list)
        del headers['Num']
        self.session = requests.Session()
        self.session.headers = headers        
            
    def set_cookies(self):        
        self.status_validation(self.main_url)        
        self.session.cookies.set(**{"name": "searchKeyword", "domain": ".coupang.com", 
                                    "value": self.query_string,
                                    "rest": {"httpOnly": False, "sameSite": '', "secure": False},  "path": "/",})
        self.session.cookies.set(**{"name": "searchKeywordType", "domain": ".coupang.com", 
                                    "value": self.query_string,
                                    "rest": {"httpOnly": False, "sameSite": '', "secure": False},  "path": "/",})
            
    def main(self):        
        self.set_headers()
        self.set_cookies()   
        product_price = self.bring_info()        
        logging.info(f"picked_product_price: {product_price}")
        product_link = self.bring_info(product_price)
        logging.info(f"picked_product_link: {product_link}")
        target_url = self.main_url + product_link
        res = self.status_validation(target_url)
        create_dir(f'{self.file_path}\etc')
        save_file(res, f'{self.file_path}\\etc\\{self.pick_item_id}.html')
        
        
    
    def bring_info(self, price=None):
        flag = False
        for p in range(1, 100):
            if not price:
                url = self.search_url.format(query_string=self.query_string, page=f'{p}')
            else:
                url = self.search_url_price.format(query_string=self.query_string, page=f"{p}", price=f"{price}")
            info = self.status_validation(url)
            data = bf(info, 'html.parser')
            ul = data.find('ul')
            li_tags = ul.find_all('li')
            a_tags = [li.find('a', href=True) for li in li_tags]            
            if flag:
                break
            for a in a_tags:                
                try:
                    itemid = re.search(r'itemId=\d+', a['href'])[0]
                except TypeError:                    
                    continue        
                else:
                    itemid = re.sub('[^0-9]', '', itemid)
                    price_tag = a.find('div', {"class": "discount-price"})                                        
                    if itemid == self.pick_item_id:
                        if not price:
                            return re.sub('[^0-9]','',price_tag.text)
                        else:
                            return a['href']
                    
            
    def status_validation(self, url, func_name=None):
        _name = "status_validation"
        time.sleep(random.choice(self.wtime))       
        try:
            res = self.session.get(url)
        except:
            time.sleep(10)
            res = self.session.get(url)
        status = res.status_code
        if status == 200:            
            try:                
                return res.json()
            except json.JSONDecodeError:                
                return res.text
        else:
            return None
                
        
        
            
            

    
if __name__ == "__main__":
    c = TestCoupang()    
    c.main()
        