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
from mine.exceptions import ConfigError, ContentsError
from .db_manager import DBManager
logger = logging.getLogger(__name__)
import timeit
import ast



class ControlManager(object):
    def __init__(self, test_data=False):
        # config info        
        self.sleep_interval = None
        self.wooriq_db = None
        self.header_list_path = None
        # self.now_datetime = datetime.datetime.today().strftime("%Y-%m-%d")
        # self.tomorrow_datetime = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime("%Y/%m/%d")
        self.now_datetime = '2021-04-05'                
        
        
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
        logger.info("main start")
        while True:
            try:                
                print(self.header_list_path)
                pm = PickMe(itemid="2339357717", keyword='1구 인덕션', header_list_path=self.header_list_path)
                pm.main()
                time.sleep(self.sleep_interval)
            except KeyboardInterrupt as err:
                logger.info(f"key interruption")
            except ConfigError as err:
                logger.info(err)
            # finally:
            #     self.disconnect_from_db()
            
    def preprocess(self):
        sql = f"""
                SELECT  keyword,
                        productid
                FROM    test.cp_keywordlist 
                where   DATE(regdate) = "{self.now_datetime}" 
                order by regdate desc;
        """
        got_data = self.wooriq_db.get_all_rows(sql)        
        for d in got_data:            
            print(d)