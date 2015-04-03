#encoding=utf-8
import os
import json
import time
import threading

# 第三方依赖库
import MySQLdb

import logutil
# 记录日志对象
_logger = logutil.getLogger("commit")

# 打印info级别日志
def _info(message):
    _logger.info(message)

# 用于保存需要进行处理的应用的信息
_apps_need_to_handle = []

# 启动处理线程
_handle_thread = None
_thread_lock = threading.Lock()

def _handleThread():
    while True:
        if len(_apps_need_to_handle) == 0:
            _thread_lock.acquire()
            _info("Lock Handle Thread: no app need to handle!")
        else:
            while len(_apps_need_to_handle) > 0:
                appInfo = _apps_need_to_handle.pop(0)
                # _info("--- Handle App ---")
                # _info(appInfo)
                _handleAppInfo(appInfo)

_handle_thread = threading.Thread(target=_handleThread)
_handle_thread.setDaemon(True)
_handle_thread.start()

# 初始化数据库
MYSQL_HOST     = "jiangerji.mysql.rds.aliyuncs.com"
MYSQL_PASSPORT = "jiangerji"
MYSQL_PASSWORD = "eMBWzH5SIFJw5I4c"
MYSQL_DATABASE = "spider"

# APIS_HOST = "http://123.57.77.122:802/iam007"
# if platform.system() == 'Windows':
#     APIS_HOST = "http://192.168.54.9:8000/iam007"

_mysqlConn=MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_PASSPORT, passwd=MYSQL_PASSWORD, db=MYSQL_DATABASE, charset="utf8")
_mysqlCur = _mysqlConn.cursor()

def _handleAppInfo(appInfo):
    trackid = appInfo.trackid
    schemesStr = ":".join(appInfo.schemes)

    # 是否在数据库中
    cmd = "select scheme from appstores where trackid='%s'"%trackid
    _mysqlCur.execute(cmd)
    schemeResult = _mysqlCur.fetchone()
    if schemeResult is not None and schemeResult[0] is not None:
        # 已经在数据库中了，更新scheme
        _info("--- Update Scheme ---")
        _info(appInfo)
    else:
        # 不在数据库中
        _info("--- New AppInfo ---")
        _info(appInfo)
        pass


def commit(content):
    appInfos = json.loads(content)
    _info(content)
    # _info("### Start Commit ###")

    trackids = appInfos.keys()
    for trackid in trackids:
        schemes = appInfos.get(trackid).get("schemes", None)
        name = appInfos.get(trackid).get("name", None)
        appInfo = _AppInfo(trackid, name, schemes)

        # _info("--- Add to handle list ---")
        # _info(appInfo)
        _apps_need_to_handle.append(appInfo)

    _thread_lock.release()

class _AppInfo():
    def __init__(self, trackid, name, schemes):
        self.trackid = trackid
        self.name = name
        # schemes is a list
        self.schemes = schemes

    def __str__(self):
        result = ["AppInfo:"]
        result.append("%9s: %s"%("trackid", self.trackid))
        result.append("%9s: %s"%("name", self.name))
        result.append("%9s: %s"%("schemes", self.schemes))

        return "\n".join(result)

content = '{\
    "932389062":["fb266828356856324asdas", "haha"],\
    "584246550":["fb266828356856324", "haha1"]\
}'

if __name__ == "__main__":
    commit(content)
# import time
# for i in range(10):
#     print "================", i
#     commit(content)
#     time.sleep(1)
