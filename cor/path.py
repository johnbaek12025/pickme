
import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
# CONFIG_DIR = os.path.join(BASEDIR, 'config')
# INFO_DIR = os.path.join(BASEDIR, 'info')
# MOBILE_FAKER_PLUGIN_DIR = os.path.join(BASEDIR, 'plugin_mobile_faker')
# MODIFY_HEADERS_PLUGIN_DIR = os.path.join(BASEDIR, 'plugin_modify_headers')
# USERDATA_DIR = os.path.join(BASEDIR, 'chrome_userdata', 'mobile')
_LOG_DIR = os.path.join(BASEDIR, 'traffic_log')
PRODUCT_LOG_DIR = os.path.join(_LOG_DIR, 'products')
SLOT_LOG_DIR = os.path.join(_LOG_DIR, 'slots')
DATE_LOG_DIR = os.path.join(_LOG_DIR, 'date')

os.makedirs(_LOG_DIR, exist_ok=True)
os.makedirs(PRODUCT_LOG_DIR, exist_ok=True)
os.makedirs(SLOT_LOG_DIR, exist_ok=True)
os.makedirs(DATE_LOG_DIR, exist_ok=True)
