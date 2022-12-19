class ServerError(Exception):
    pass


class ClientError(Exception):
    pass


class DataNotFound(ClientError):
    pass


class WrongData(ClientError):
    pass

class NotParsedSearchId(DataNotFound):
    pass

class ConfigError(Exception):
    def __init__(self, error_msg):
        super().__init__(error_msg)

class NotSearchedProductPrice(DataNotFound):
    pass