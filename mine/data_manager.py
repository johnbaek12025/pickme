class NewsInfo:
    def __init__(self, **kwargs):
        self.news_seq = kwargs.get("news_seq")
        self.now_date = kwargs.get("now_date")
        self.now_time = kwargs.get("now_time")
        self.news_code = kwargs.get("news_code")
        self.stock_code = kwargs.get("stock_code")
        self.news_title = kwargs.get("news_title")
        self.request_type = kwargs.get("request_type")
        self.is_manual = kwargs.get("is_manual")
        self.is_reserved = kwargs.get("is_reserved")
        self.org_news_seq = kwargs.get("org_news_seq")
        self.org_now_date = kwargs.get("org_now_date")

    def print(self):
        var_dict = vars(self)
        print("------------------------------------------------")
        print(f"* {self.__class__.__name__} *")
        for i in var_dict:
            var = var_dict[i]
            print(f"[{i}]: {var}")


class NewsContent:
    def __init__(self, **kwargs):
        self.news_seq = kwargs.get("news_seq")
        self.now_date = kwargs.get("now_date")
        self.now_time = kwargs.get("now_time")
        self.contents_type = kwargs.get("contents_type")
        self.news_cnts = kwargs.get("news_cnts")
        self.news_code = kwargs.get("news_code")
        self.rep_image = kwargs.get("rep_image")

    def print(self):
        var_dict = vars(self)
        print("------------------------------------------------")
        print(f"* {self.__class__.__name__} *")
        for i in var_dict:
            var = var_dict[i]
            print(f"[{i}]: {var}")


class NewsCom:
    def __init__(self, **kwargs):
        self.news_seq = kwargs.get("news_seq")
        self.now_date = kwargs.get("now_date")
        self.info_seq = kwargs.get("info_seq")
        self.info_code = kwargs.get("info_code")

    def print(self):
        var_dict = vars(self)
        print("------------------------------------------------")
        print(f"* {self.__class__.__name__} *")
        for i in var_dict:
            var = var_dict[i]
            print(f"[{i}]: {var}")
