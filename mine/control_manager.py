import datetime

from itertools import product
import logging
import random
import re
import time
import requests
from mine.ip_util import switchIp2
from mine.pickme import PickMe
from mine.common import to_int, to_bool
from mine.exceptions import ConfigError, ContentsError, IPChangeError
from .db_manager import DBManager
logger = logging.getLogger(__name__)
import timeit
import ast
from pymysql.err import OperationalError, InterfaceError


class ControlManager(object):
    def __init__(self, test_data=False):
        # config info        
        self.sleep_interval = None
        self.wooriq_db = None
        self.header_list_path = None
        self.now_datetime = datetime.datetime.today()
        
    def check_config(self, config_dict):                
        self.data_database = config_dict.get("data_database")        
        if not self.data_database:
            ConfigError("check config file: [data_database]")        
        self.header_list_path = config_dict.get("header_list_path")
        if not self.header_list_path:
            ConfigError("check config file: [header_list_path]")
        self.sleep_interval = float(600)        
    
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

    def run(self):
        logger.info("run_method")        
        try:
            while True:
                ip_address = switchIp2()
                if not ip_address:
                    break
                # pm = PickMe(itemid='77959174230', keyword='1구 인덕션', header_list_path=self.header_list_path)
                # pm.main()
                self.connect_to_db()
                for i, data_dict in enumerate(self.preprocess(), start=1):                    
                    log = {'ip_address': ip_address, 'keyword': data_dict['keyword'], 'ProductID': data_dict['itemid']}
                    log['ip_address'] = self.check_log(log)                    
                    if i % 5 == 0:                        
                        ip_address = switchIp2()
                        self.connect_to_db()
                        log = {'ip_address': ip_address, 'keyword': data_dict['keyword'], 'ProductID': data_dict['itemid']}
                        log['ip_address'] = self.check_log(log)
                    pm = PickMe(itemid=data_dict['itemid'], keyword=data_dict['keyword'], header_list_path=self.header_list_path)
                    pm.main()
                    self.postprocess(log)            
                    time.sleep(10)
                time.sleep(self.sleep_interval)
        except KeyboardInterrupt as err:
            logger.info(f"key interruption")
        except IPChangeError as err:
            logger.info(f"{err}")
        except ConfigError as err:
            logger.info(err)
        finally:
            self.disconnect_from_db()
            
    def preprocess(self):
        sql = f"""
        SELECT  cp.ProductID,
                cp.Keyword
        FROM    wooriq.cp_keywordlist as cp,
                wooriq.memberwork as mw
        where mw.UID = cp.UID
        and   mw.KeywordState in ('1', '2')
        and	  Keyword is not NULL
        and   Keyword != ''
        and	  cp.mobile_yn = 0
        """
        got_data = self.wooriq_db.get_all_rows(sql)
        data_list = list()
        for d in got_data:
            data_list.append({'itemid': d[0], 'keyword': d[1]})
        random.shuffle(data_list)
        return data_list
    
    def postprocess(self, log):
        sql = f"""
        Insert into wooriq.cp_searchlog (IP_Address, Keyword, ProductID) values ("{log['ip_address']}", "{log['keyword']}", "{log['ProductID']}")
        """
        self.wooriq_db.modify(sql, commit=True)
        
    def check_log(self, log):   
        sql = f"""
        select  *
        from 	wooriq.cp_searchlog
        where   Keyword = "{log['keyword']}"
        and     ProductID = "{log['ProductID']}"
        and     IP_Address = "{log['ip_address']}"
        """
        got_data = self.wooriq_db.get_all_rows(sql)
            
        if not len(got_data):
            return log['ip_address']
        else:
            ip_address = switchIp2()
            self.connect_to_db()
            if not ip_address:
                raise IPChangeError
            log['ip_address'] = ip_address
            return self.check_log(log)