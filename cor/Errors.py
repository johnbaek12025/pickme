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