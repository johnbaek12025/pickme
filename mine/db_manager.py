import logging
# import pymysql
import pymysqlpool
logger = logging.getLogger(__name__)



class DBManager(object):
    def __init__(self):
        self.uri = None
        self.conn = None

    def connect(self, db_host, db_port, db_name, db_user, db_pass=None):        
        try:
            pool1 = pymysqlpool.ConnectionPool(size=2, maxsize=3, host=db_host, user=db_user,port=int(db_port), password=db_pass, db=db_name, charset='utf8')
            self.conn = pool1.get_connection()
            # self.conn = pymysql.connect(host=db_host, user=db_user,port=int(db_port), password=db_pass, db=db_name, charset='utf8')
        except Exception as err:
            logger.error(f"connection to {self.uri} failed : {err}")
            raise

    def disconnect(self):
        if self.conn:
            logger.info(f"disconnect from {self.uri}")
            self.conn.close()
            self.conn = None

    def get_all_rows(self, sql):
        try:
            cur = self.conn.cursor()
            logger.info("sql: %s" % sql)
            cur.execute(sql)
            return cur.fetchall()
        except Exception as err:
            logger.error(f"query {sql} failed: {err}")
            raise

    def modify_many(self, sql, rows, commit):
        try:
            cur = self.conn.cursor()
            logger.info("sql: %s" % sql)
            cur.prepare(sql)
            cur.executemany(None, rows)
            if commit:
                self.conn.commit()
        except Exception as err:
            logger.error(f"query {sql} failed: {err}")
            raise

    def modify(self, sql, commit):
        try:
            cur = self.conn.cursor()
            logger.info("sql: %s" % sql)
            cur.execute(sql)
            if commit:
                self.conn.commit()
        except Exception as err:
            logger.info(f"query {sql} failed: {err}")
            raise

    def commit(self):
        try:
            self.conn.commit()
        except Exception as err:
            logger.info(f"commit failed: {err}")
            raise