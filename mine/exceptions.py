class ConfigError(Exception):
    def __init__(self, error_msg):
        super().__init__(error_msg)


class LogInsertError(Exception):
    def __init__(self, error_msg):
        super().__init__(error_msg)
        

class IPChangeError(Exception):
    def __init__(self, error_msg):
        super().__init__(error_msg)