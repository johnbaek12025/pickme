from msilib.schema import Error
import os
import random
import sys
import time
import requests
from bs4 import BeautifulSoup as bf
from lxml import etree
import json
import numpy
import re
import logging
from urllib import parse
from mine.ip_util import switchIp2
from mine.common import create_dir, save_file


class PickMe:
    def __init__(self, **kwargs) -> None:
        
        self.keyword = kwargs["keyword"]
        self.query_string = parse.quote_plus(self.keyword)
        self.session = None        
        self.wtime = numpy.arange(0.5, 2, 0.5)
        self.vendoritemid = kwargs['vendoritemid']
        self.headers_path = kwargs['header_list_path']['path']
        self.main_url = 'https://m.coupang.com/nm/'
        self.search_url = f"https://m.coupang.com/nm/search?q={self.query_string}"
        self.target_url = f"https://m.coupang.com/vm/products/{kwargs['product_id']}?itemId={kwargs['item_id']}&q={self.keyword}&searchId="
        self.file_path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
        self.searchId = None

    def set_headers(self):
        with open(os.path.join(os.getcwd(), self.headers_path), 'rt', encoding='utf-8-sig') as f:
            data = f.read()
            data_list = json.loads(data)      
        headers = random.choice(data_list)
        del headers['Num']
        self.session = requests.Session()
        logging.info(f"headers in file: {headers}")
        self.session.headers = headers
        logging.info(f"current header: {self.session.headers}")

    def main(self):        
        self.set_headers()
        self.status_validation(self.main_url)
        self.set_searchId()        
        if not self.searchId:
            logging.info(f"searchid of {self.keyword}, {self.vendoritemid} could not find~!!")
            return 'traffic fails'
        logging.info(f"searchID: {self.searchId}")        
        logging.info(f"targeturl: {self.target_url+self.searchId}")
        res = self.status_validation(self.target_url+self.searchId)
        create_dir(f'{self.file_path}\etc')
        save_file(res, f'{self.file_path}\\etc\\{self.vendoritemid}_{self.keyword}.html')
        return 'traffic success'
            
    def set_searchId(self):
        res = self.status_validation(self.search_url)
        data = bf(res, 'html.parser')
        save_file(res, f'{self.file_path}\\etc\\{self.vendoritemid}_{self.keyword}.html')
        li_tag = data.find('li', {'class': "plp-default__item"})
        product_link = li_tag.find('a', href=True)
        residue = re.sub(r'.+searchId\=','', product_link['href'])
        self.searchId = re.sub(r'\&clickEventId\=.+', '', residue)
        
            
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
    c = PickMe(**{"header_list_path": header_list_path, "keyword":keyword, "residue":residue, "vendoritemid":vendoritemid})
    res = c.main()
    print(res)