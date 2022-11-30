__appname__ = "pick_me"
__version__ = "1.0"


import optparse
import os
import random
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from mine.ip_util import switchIp2
from mine import common
from mine.control_manager import ControlManager


if __name__ == "__main__":
    usage = """%prog [options]"""
    parser = optparse.OptionParser(usage=usage, description=__doc__)    
    common.add_basic_options(parser)
    (options, args) = parser.parse_args()
    config_dict = common.read_config_file(options.config_file)
    config_dict["app_name"] = __appname__
    log_dict = config_dict.get("log", {})
    log_file_name = "pickme.log"    
    common.setup_logging(
        appname=__appname__,
        appvers=__version__,
        filename=log_file_name,
        dirname=options.log_dir,
        debug=options.debug,
        log_dict=log_dict,
        emit_platform_info=True,
    )

    control_manager = ControlManager()
    control_manager.initialize(config_dict)    
    control_manager.run()
    
