from typing import List


class Slot:

    def __init__(self, server_pk, keyword, residue, item_id):
        self.server_pk = server_pk
        self.keyword = keyword
        self.product_id = residue
        self.item_id = item_id


async def fetch_slots() -> List[Slot]:
    # todo: slot 정보를 불러와서 Slot 으로 객체화하여 리스트에 반환
    pass

