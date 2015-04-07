#encoding=utf-8
import os
import json
import time
import threading
import platform

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

rootDir = os.path.join(os.getcwd(), "applications")
rootDir = os.path.join(rootDir, "iam007")

def _handleThread(DAL):
    global _dal, MYSQL_PASSPORT, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE
    _info("============== Start Commit Thread ==============")

    try:
        if _dal is None:
            _dal = DAL("mysql://%s:%s@%s/%s"%(MYSQL_PASSPORT, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE))
            # print dir(_dal)
    except Exception, e:
        pass
    
    while True:
        if len(_apps_need_to_handle) == 0:
            _thread_lock.acquire()
            _info("Lock Handle Thread: no app need to handle!")
        else:
            while len(_apps_need_to_handle) > 0:
                appInfo = _apps_need_to_handle.pop(0)
                _info("--- Handle App ---")
                _info(appInfo)
                try:
                    _handleAppInfo(appInfo)
                except Exception, e:
                    print "_handleAppInfo exception:", e
                

            # _mysqlConn.commit()

_handle_thread = None

# 初始化数据库
MYSQL_HOST     = "jiangerji.mysql.rds.aliyuncs.com"
MYSQL_PASSPORT = "jiangerji"
MYSQL_PASSWORD = "eMBWzH5SIFJw5I4c"
MYSQL_DATABASE = "spider"

if platform.system() == 'Windows':
    MYSQL_HOST="localhost"
    MYSQL_PASSPORT="root"
    MYSQL_PASSWORD="123456"
    MYSQL_DATABASE="spider"

# APIS_HOST = "http://123.57.77.122:802/iam007"
# if platform.system() == 'Windows':
#     APIS_HOST = "http://192.168.54.9:8000/iam007"

# _mysqlConn=MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_PASSPORT, passwd=MYSQL_PASSWORD, db=MYSQL_DATABASE, charset="utf8")
# print "connect to", MYSQL_HOST
# _mysqlCur = _mysqlConn.cursor()
# print "db cursor", _mysqlCur

_dal = None

def _handleAppInfo(appInfo):
    global _dal

    trackid = appInfo.trackid
    schemesStr = ":".join(appInfo.schemes)
    _info("scheme is "+schemesStr)

    #"""
    # 是否在数据库中
    cmd = "select scheme from appstores where trackid='%s';"%trackid
    schemeResult = _dal.executesql(cmd)
    # _info(trackid + ":" + str(schemeResult))
    if len(schemeResult) > 0:
        # 已经在数据库中了，更新scheme
        _info("--- Update Scheme %s ---"%trackid)
        cmd = 'update appstores set scheme="%s", version=-2 where trackid="%s";'%(schemesStr,  trackid)
        _dal.executesql(cmd)
    else:
        # 不在数据库中
        _info("--- New AppInfo %s---"%trackid)

        icon60 = None
        icon512 = None
        try:
            icons = _getAppIcon(trackid)
            if icons is not None:
                icon60, icon512 = icons
        except Exception, e:
            pass

        cmd = 'insert into appstores (trackid, name, scheme, icon60, icon512, addtime, version) values ' + '("%s","%s","%s","%s","%s","%s",-2)'%(trackid, appInfo.name, schemesStr, icon60, icon512, time.strftime("%Y_%m_%d_%H"))
        _dal.executesql(cmd)

    _dal.commit()
    # print "Database Commit!"
    #"""

def _getUrlContent(url, cacheFile):
    target_path = cacheFile

    if not os.path.isfile(target_path):
        load_web_page_js_dir = os.path.join(rootDir, "bin")
        load_web_page_js = os.path.join(load_web_page_js_dir, "loadAnnie.js")
        command = 'phantomjs --load-images=false "%s" "%s" "%s"'%(load_web_page_js, url, target_path)

        state = os.system(command.encode("utf-8"))
        _info("Load Annie page state:%d"%state)

    return open(target_path).read()

def _getAppIcon(trackid):
    from lxml import etree

    if trackid is None:
        return None

    url = "https://itunes.apple.com/cn/app/id%s?mt=8"%trackid
    cacheDir = os.path.join(rootDir, "cache")
    cacheDir = os.path.join(cacheDir, "itunes")
    
    try:
        os.makedirs(cacheDir)
    except Exception, e:
        pass

    cacheFile = os.path.join(cacheDir, "itunes_%s.html"%trackid)
    content = None
    try:
        content = _getUrlContent(url, cacheFile)
        doc = etree.HTML(content)

        rows = doc.xpath("//div[@id='left-stack']//img[@class='artwork']")
        for row in rows:
            icon60 = row.get("src")
            icon512 = row.get("src-swap-high-dpi")

            return (icon60, icon512)
    except Exception, e:
        print "get url content exception:", e

    try:
        os.remove(cacheFile)
        _info("remove:"+cacheFile)
    except Exception, e:
        _info("remove:"+e)
    
    return None


def commit(content, DAL):
    global _handle_thread
    if _handle_thread is None:
        _handle_thread = threading.Thread(target=_handleThread, args=(DAL,))
        # _handle_thread.setDaemon(True)
        _handle_thread.start()

    appInfos = json.loads(content)
    _info(content)
    # _info("### Start Commit ###")

    trackids = appInfos.keys()
    for trackid in trackids:
        schemes = appInfos.get(trackid).get("schemes", None)
        name = appInfos.get(trackid).get("name", None)
        appInfo = _AppInfo(trackid, name, schemes)

        _info("--- Add to handle list ---")
        _info(appInfo)
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
    "434374726":{"schemes":["homelink"], "name":"掌上链家HD"}\
}'



def test(p):
    print p

def test2(func):
    func("af")

if __name__ == "__main__":
    # sinaweibosso.3677796771:tencent100273020:openapp.jdipad:wxe75a2e68877315fb
    rootDir = "."
    # print _getAppIcon("434374726")
    # commit(content)
    # test2(test)

# import time
# for i in range(10):
#     print "================", i
#     commit(content)
#     time.sleep(1)
