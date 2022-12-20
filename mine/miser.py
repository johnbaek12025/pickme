import random
import time
import requests
from bs4 import BeautifulSoup as bf
import json
import numpy
import re
import logging
logger = logging.getLogger(__name__)

class Miser:
    def __init__(self, **kwargs) -> None:                
        self.session = None        
        self.main_url = 'https://www.coupang.com/'
        self.product_url = kwargs['product_url']
        self.wtime = numpy.arange(0.5, 2, 0.5)
        self.item_id = kwargs['item_id']
        self.product_price = None
        self.update_url = 'https://api.wooriq.com/cp/cp_price.php?purl={product_url}&price={product_price}'

    def set_headers(self):
        self.session = requests.session()
        header = {            
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
        }
        self.session.headers.update(header)
        self.session.cookies.set(**{"domain": ".coupang.com", 
                    "value": "51829479347949486589994", 
                    "path": "/",                 
                    "name": "PCID",
                    "rest": {"httpOnly": False, "sameSite": False},})
        self.session.cookies.set(**{ "name": "MARKETID",
                    "value": "51829479347949486589994",
                    "path": "/",   
                    "domain": ".coupang.com", 
                    "rest": {"httpOnly": True, "sameSite": None, "secure": True},})            
        self.session.cookies.set(**{"name": "sid",
                    "value": "a0438b4751a84b55838f254724e60773d89f10e0",            
                    "path": "/",   
                    "domain": ".coupang.com", 
                    "rest": {"httpOnly": False, "sameSite": '', "secure": False},})    
        self.session.cookies.set(**{"name": "x-coupang-origin-region", "value": "	KOREA", "domain": ".coupang.com", 
                        "path": "/","rest": {"httpOnly": False, "sameSite": '', "secure": False}})

    def main(self):        
        self.set_headers()
        self.status_validation(self.main_url)
        self.set_product_price()        
        if not self.product_price:
            return 'Fail'
        logging.info(f'url: {self.product_url}\nprice:{self.product_price}')
        self.status_validation(self.update_url.format(product_url=self.product_url, product_price=self.product_price))
        return 'Success'
        
            
    def set_product_price(self):
        res = self.status_validation(self.product_url)
        data = bf(res, 'html.parser')        
        first_div_tag = data.find('div', {"class": "prod-price-onetime"})        
        try:
            second_div_tag = first_div_tag.find('div', {"class": "prod-coupon-price prod-major-price"})
            price_tag = second_div_tag.find('span', {'class': 'total-price'})
        except AttributeError:
            self.product_price = None
        else:
            self.product_price = re.sub(r'[^0-9]+', '',price_tag.text)
            
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
    header_list_path = {"path":  '../cfg/android_samsung.json'}
    keyword = '도시락통'
    residue = '5937488068?itemId=10570345011'
    vendoritemid = '77851693275'
    c = Miser(**{"header_list_path": header_list_path, "keyword":keyword, "residue":residue, "vendoritemid":vendoritemid})
    res = c.main()
    print(res)