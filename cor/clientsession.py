from aiohttp import ClientSession, ClientTimeout


class CoupangClientSession(ClientSession):
    def __init__(self, *args, **kwargs):
        super(CoupangClientSession, self).__init__(*args, **kwargs)
        search_id = None