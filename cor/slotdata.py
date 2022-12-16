import re
from typing import List
from db_manager import DBManager
import random

class Slot:

    def __init__(self, server_pk, keyword, product_id, item_id, vendor_item_id):
        self.server_pk = server_pk
        self.keyword = keyword
        self.product_id = product_id
        self.item_id = item_id
        self.vendor_item_id = vendor_item_id


async def fetch_slots(data_base_info) -> List[Slot]:
    # todo: slot 정보를 불러와서 Slot 으로 객체화하여 리스트에 반환
    wooriq_db = DBManager()
    wooriq_db.uri = data_base_info.get('db_name')
    wooriq_db.connect(**data_base_info)
    slots = preprocess(wooriq_db)
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


def preprocess(wooriq_db):
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