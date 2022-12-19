from datetime import datetime, timedelta
import json
import re
from typing import List
from cor.ip import swap_ip
from db_manager import DBManager
import random
from aiohttp import ClientSession

class Slot:

    def __init__(self, server_pk, keyword, product_id, item_id, vendor_item_id, ip_address):
        self.server_pk = server_pk
        self.keyword = keyword
        self.product_id = product_id
        self.item_id = item_id
        self.vendor_item_id = vendor_item_id
    
    # async def check_ip_address(self, ip_address):
    #     session = ClientSession()
    #     now_datetime = datetime.today()
    #     ten_hours_ago = now_datetime - timedelta(hours=10)
    #     url = f"https://api.wooriq.com/cp/searchlog_sel.php?keyword=&ip={ip_address}&productid={self.vendor_item_id}"
    #     async with session.get(url) as res:
    #         if res.status == 200:
    #             try:
    #                 info = await res.json()
    #             except json.JSONDecodeError:
    #                 return True
    #             else:
    #                 if not info:
    #                     return True
    #                 else:
    #                     regdate = info[-1]['regdate']                    
    #                     regist_time = datetime.strptime(regdate, '%Y-%m-%d %H:%M:%S')
    #                     if ten_hours_ago > regist_time:
    #                         return True
    #                     return False
    


async def fetch_slots(data_base_info) -> List[Slot]:
    # todo: slot 정보를 불러와서 Slot 으로 객체화하여 리스트에 반환    
    slots = get_data_set(data_base_info)
    object_list = []
    for s in slots:
        vendoritemid = re.sub(r'.+vendorItemId=', '', s['url'])
        residue = re.search(r'[0-9]+\?itemId\=[0-9]+', s['url'])
        if not residue:
            continue
        residue = residue.group(0)
        left = residue.split('?itemId=')
        object_list.append(Slot(server_pk=s['server_pk'], product_id=left[0], item_id=left[1], keyword=s['keyword'], vendor_item_id=vendoritemid))
    return object_list


def get_data_set(data_base_info):
        sql = f"""
        SELECT  cp.ID,
                cp.p_url,                
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
        wooriq_db = DBManager()
        wooriq_db.uri = data_base_info.get('db_name')
        wooriq_db.connect(**data_base_info)
        try:
            got_data = wooriq_db.get_all_rows(sql)
        except Exception as e:
            return None
        finally:
            if wooriq_db:
                wooriq_db.disconnect()            
        data_list = list()
        for d in got_data:
            data_list.append({"server_pk": d[0], "url": d[1],  'keyword': d[2]})        
        random.shuffle(data_list)
        return data_list