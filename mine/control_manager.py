from datetime import datetime, timedelta

from itertools import product
import json
import logging
import random
import re
import sys
import time
import requests
from mine.ip_util import switchIp2
from mine.pickme import PickMe
from mine.common import to_int, to_bool
from mine.exceptions import ConfigError, IPChangeError, LogInsertError
from .db_manager import DBManager
logger = logging.getLogger(__name__)
import timeit
import ast


class ControlManager(object):
    def __init__(self, test_data=False):
        # config info        
        self.interval = None
        self.wooriq_db = None
        self.header_list_path = None
        self.now_datetime = datetime.today()
        self.ten_hours_ago = self.now_datetime - timedelta(hours=10)        
        self.sleep_interval = None
        self.db_sleep_interval = None
        self.ins_url = "https://api.wooriq.com/cp/searchlog_ins.php?keyword={ip_address}&ip=&productid={vendoritemid}"
        self.sel_url = "https://api.wooriq.com/cp/searchlog_sel.php?keyword=&ip={ip_address}&productid={ProductID}"
                
    def check_config(self, config_dict):                
        self.data_database = config_dict.get("data_database")        
        if not self.data_database:
            ConfigError("check config file: [data_database]")        
        self.header_list_path = config_dict.get("header_list_path")
        if not self.header_list_path:
            ConfigError("check config file: [header_list_path]")
        self.interval = config_dict.get("interval")
        if not self.interval:
            self.db_sleep_interval = float(10)
            self.sleep_interval = float(600)
        else:
            self.db_sleep_interval = float(self.interval.get('db_sleep_interval'))
            self.sleep_interval = float(self.interval.get('sleep_interval'))
        
    def connect_to_db(self):
        logger.info("connect to databases")
        self.wooriq_db = DBManager()
        self.wooriq_db.connect(**self.data_database)

    def disconnect_from_db(self):
        logger.info("disconnect from databases")
        if self.wooriq_db:
            self.wooriq_db.disconnect()

    def initialize(self, config):        
        self.check_config(config)

    def get_swapped_ip(self, num, ProductID, ip_address=None):
        if ip_address == None or num % 5 == 0:
            try:
                ip_address = switchIp2()        
            except IPChangeError:
                print('테더링 확인 바랍니다.~~!!!')
                time.sleep(self.sleep_interval)
                self.get_swapped_ip(num, ProductID, ip_address)
        time.sleep(self.db_sleep_interval)
        # self.connect_to_db()
        log = {'ProductID': ProductID, 'ip_address': ip_address}
        if self.check_ip_address(log):
            return ip_address
        else:
            ip_address = self.get_swapped_ip(num, ProductID, None)
            return ip_address
    
    def run(self):        
        logger.info("run_method")
        self.disconnect_from_db()
        ip_address = None        
        try:            
            while True:                      
                self.connect_to_db()
                for num, data_dict in enumerate (self.preprocess()):
                    print(data_dict)
                    ip_address = self.get_swapped_ip(num, data_dict['vendoritemid'], ip_address=ip_address)
                    logging.info(f"current ip_address: {ip_address}")      
                    residue = re.search(r'[0-9]+\?itemId\=[0-9]+', data_dict['url'])
                    if not residue:
                        continue                    
                    residue = residue.group(0)
                    left = residue.split('?itemId=')                    
                    pm = PickMe(item_id=left[1], product_id=left[0], vendoritemid=data_dict['vendoritemid'], keyword=data_dict['keyword'], header_list_path=self.header_list_path)                    
                    if pm.main() == 'traffic fails':
                        logging.info(f'result of pm.main(): traffic fails')
                        continue                    
                    self.postprocess({"id": data_dict['id'], "ip_address": ip_address, "vendoritemid": data_dict['vendoritemid']})
                    # print()
        except KeyboardInterrupt as err:
            logger.info(f"key interruption")        
        except LogInsertError as err:
            logging.info(f'LogInsertError: {err}')
        except ConfigError as err:
            logger.info(err)        
        finally:
            self.disconnect_from_db()
            
            
    def preprocess(self):
        sql = f"""
        SELECT  cp.ID,
                cp.p_url,
                cp.ProductID,
                cp.Keyword
        FROM    wooriq.cp_keywordlist as cp,
                wooriq.memberwork as mw
        where mw.UID = cp.UID
        and   mw.KeywordState in ('1', '2')
        and	  cp.Keyword is not NULL
        and   cp.Keyword != ''
        and	  cp.p_url regexp 'https.+'
        and	  cp.mobile_yn in (0, 1)
        """
        got_data = self.wooriq_db.get_all_rows(sql)
        data_list = list()
        for d in got_data:
            data_list.append({"id": d[0], "url": d[1], 'vendoritemid': d[2], 'keyword': d[3]})        
        random.shuffle(data_list)
        return data_list
    
    def postprocess(self, log):                
        # sql = f"""
        # Insert into wooriq.cp_searchlog (IP_Address, ProductID) values ("{log['ip_address']}", "{log['vendoritemid']}")
        # """
        # self.wooriq_db.modify(sql, commit=True)
        logging.info(f"postprocess log: {log}")        
        self.connect_to_db()
        sql = f"""
        update cp_keywordlist set TotalWorkCount = TotalWorkCount + 1 , 
                                  WorkCount = WorkCount + 1, 
                                  LastWorkdt = now() 
        where ID ={log['id']}
        """
        self.wooriq_db.modify(sql, commit=True)        
        result = requests.get(url=self.ins_url.format(vendoritemid = log['vendoritemid'],  ip_address=log['ip_address']))
        if result.status_code == 200:
            logging.info(f"{log} insert succeed")
        else:
            raise LogInsertError (f"{log}")
        
            
        
        
    
            
    def check_ip_address(self, log):
        # sql = f"""
        # select  *
        # from 	wooriq.cp_searchlog
        # where   ProductID = "{log['ProductID']}"
        # and     IP_Address = "{log['ip_address']}"
        # and     date(regdate) > "{self.ten_hours_ago}"
        # """
        # got_data = self.wooriq_db.get_all_rows(sql)
        # if not got_data:
        #     return True
        # else:
        #     return False
        data = requests.get(url=self.sel_url.format(ip_address=log['ip_address'], ProductID=log['ProductID']))
        logging.info(self.sel_url.format(ip_address=log['ip_address'], ProductID=log['ProductID']))
        if data.status_code == 200:
            try:
                info = data.json()
            except json.JSONDecodeError:
                print(data.content)
            else:
                if not info:
                    return True
                else:
                    regdate = info[-1]['regdate']
                    logging.info(f"regdate: {regdate}, type: {type(regdate)}")
                    regist_time = datetime.strptime(regdate, '%Y-%m-%d %H:%M:%S')
                    if self.ten_hours_ago > regist_time:
                        return True
                    return False
        return False