from urllib.parse import quote

from aiohttp import ClientSession


class CoupangClientSession(ClientSession):
    
    def __init__(self, *args, **kwargs):
        super(CoupangClientSession, self).__init__(*args, **kwargs)
        self.search_id = None

async def work(keyword, product_id, item_id):
    ses = CoupangClientSession()
    await set_headers(session=ses)


async def set_headers(session: CoupangClientSession):
    print(f"session: {session}")
    pass


async def go_main_page(session: CoupangClientSession):
    url = 'https://m.coupang.com/nm/'
    async with session.get(url) as res:
        # todo: res 가 정상적인지 쿠키는 받아와졌는지 검증(출력)
        pass


async def search(session: CoupangClientSession, keyword):
    url = f"https://m.coupang.com/nm/search?q={quote(keyword)}"
    async with session.get(url) as res:
        # todo: res 가 정상적인지 쿠키는 받아와졌는지 검증(출력)
        # todo: search_id 파싱 후 session.search_id = 할당 및 검증(출력)
        pass


async def click(session: CoupangClientSession, keyword, product_id, item_id):
    url = f"https://m.coupang.com/vm/products/{product_id}?itemId={item_id}&q={quote(keyword)}&searchId={session.search_id}"
    async with session.get(url) as res:
        # todo: res 가 정상적인지 쿠키는 받아와졌는지 검증
        pass


async def save_traffic_log():
    pass



    
