#encoding=utf-8
import os
import time
import logging
import logging.handlers  

logPath = "."
# logPath = os.path.join(logPath, "applications")
# logPath = os.path.join(logPath, "iam007")
logPath = os.path.join(logPath, "logs")
LOG_FILE = os.path.join(logPath, 'iam007_%s.log'%time.strftime("%Y_%m_%d"))
handler = logging.handlers.RotatingFileHandler(LOG_FILE) # 实例化handler   
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(message)s'  
formatter = logging.Formatter(fmt)   # 实例化formatter  
handler.setFormatter(formatter)      # 为handler添加formatter  
logger = logging.getLogger("iam007")    # 获取名为tst的logger  
logger.addHandler(handler)           # 为logger添加handler  
logger.setLevel(logging.DEBUG)