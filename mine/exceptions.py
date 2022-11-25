class ConfigError(Exception):
    def __init__(self, error_msg):
        super().__init__(error_msg)


class ContentsError(Exception):
    def __init__(self, error_msg):
        super().__init__(error_msg)