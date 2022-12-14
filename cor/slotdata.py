from typing import List


class Slot:

    def __init__(self, server_pk, keyword, product_id, item_id):
        self.server_pk = server_pk
        self.keyword = keyword
        self.product_id = product_id
        self.item_id = item_id


async def fetch_slots(slots) -> List[Slot]:
    # todo: slot 정보를 불러와서 Slot 으로 객체화하여 리스트에 반환
    object_list = []
    for s in slots:
        object_list.append(Slot(server_pk=s['server_pk'], product_id=s['product_id'], item_id=s['item_id'], keyword=s['keyword']))
    return object_list
    pass

