from datetime import datetime, timedelta

from itertools import product
import logging
import random
import re
import sys
import time
import requests
from mine.ip_util import switchIp2
from mine.pickme import PickMe
from mine.common import to_int, to_bool
from mine.exceptions import ConfigError, IPChangeError
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
        if not ip_address or num % 5 == 0:
            try:
                ip_address = switchIp2()        
            except IPChangeError:
                print('테더링 확인 바랍니다.~~!!!')
                time.sleep(self.sleep_interval)
                self.get_swapped_ip(ProductID)
        time.sleep(self.db_sleep_interval)
        self.connect_to_db()
        log = {'ProductID': ProductID, 'ip_address': ip_address}
        if self.check_ip_address(log):
            return ip_address
        else:
            self.get_swapped_ip(ProductID)
    
    def run(self):
        logger.info("run_method")        
        self.connect_to_db()                
        ip_address = None
        try:            
            while True:      
                for num, data_dict in enumerate (self.preprocess()):
                    print(num)
                    ip_address = self.get_swapped_ip(num, data_dict['vendoritemid'], ip_address=ip_address)
                    residue = re.search(r'[0-9]+\?itemId\=[0-9]+&vendorItemId\=', data_dict['url'])
                    if not residue:
                        continue
                    data_dict['residue'] = residue.group(0)
                    pm = PickMe(residue=data_dict['residue'], vendoritemid=data_dict['vendoritemid'], keyword=data_dict['keyword'], header_list_path=self.header_list_path)
                    if not pm.main():
                        continue
                    self.postprocess({"ip_address": ip_address, "vendoritemid": data_dict['vendoritemid']})
                time.sleep(self.sleep_interval)
                    
        except KeyboardInterrupt as err:
            logger.info(f"key interruption")        
        except ConfigError as err:
            logger.info(err)
        finally:
            self.disconnect_from_db()
            
            
    def preprocess(self):
        sql = f"""
        SELECT  cp.Keyword,
                cp.memo,
                cp.ProductID
        FROM    wooriq.cp_keywordlist as cp,
                wooriq.memberwork as mw
        where mw.UID = cp.UID
        and   mw.KeywordState in ('1', '2')
        and	  cp.Keyword is not NULL
        and   cp.Keyword != ''
        and	  cp.memo regexp 'https.+'        
        and	  cp.mobile_yn = 0
        """
        got_data = self.wooriq_db.get_all_rows(sql)
        data_list = list()
        for d in got_data:
            data_list.append({"url": d[1], 'vendoritemid': d[2], 'keyword': d[0]})
        random.shuffle(data_list)
        return data_list
    
    def postprocess(self, log):#FIXME API형식으로 
        sql = f"""
        Insert into wooriq.cp_searchlog (IP_Address, ProductID) values ("{log['ip_address']}", "{log['vendoritemid']}")
        """
        self.wooriq_db.modify(sql, commit=True)
    
            
    def check_ip_address(self, log):#FIXME API형식으로 
        
        sql = f"""
        select  *
        from 	wooriq.cp_searchlog
        where   ProductID = "{log['ProductID']}"
        and     IP_Address = "{log['ip_address']}"
        and     date(regdate) > "{self.ten_hours_ago}"
        """
        got_data = self.wooriq_db.get_all_rows(sql)            
        if not len(got_data):
            return True
        else:
            return False
            