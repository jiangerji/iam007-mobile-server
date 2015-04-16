import json
import os
import time
import platform
import HTMLParser
import subprocess
import urllib
from logutil import logger

import threading

MYSQL_HOST     = "jiangerji.mysql.rds.aliyuncs.com"
MYSQL_PASSPORT = "jiangerji"
MYSQL_PASSWORD = "eMBWzH5SIFJw5I4c"
MYSQL_DATABASE = "spider"

APIS_HOST = "http://123.57.77.122:802/iam007"
if platform.system() == 'Windows' and False:
    APIS_HOST = "http://192.168.54.9:8000/iam007"
    MYSQL_HOST="localhost"
    MYSQL_PASSPORT="root"
    MYSQL_PASSWORD="123456"
    MYSQL_DATABASE="spider"

    
dal = None#DAL('sqlite://wanke.sqlite3.sqlite')
def _init():
    global dal, MYSQL_PASSPORT, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE
    if dal is None:
        """
        SQLite  sqlite://storage.db
        MySQL   mysql://username:password@localhost/test
        PostgreSQL  postgres://username:password@localhost/test
        """
        command = "mysql://%s:%s@%s/%s"%(MYSQL_PASSPORT, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE)
        dal = DAL(command)

def _getTagsStaticFile(filename, mode="r", returnMode="content"):
    filePath = os.path.join(os.getcwd(), "applications")
    filePath = os.path.join(filePath, "iam007")
    filePath = os.path.join(filePath, "static")
    filePath = os.path.join(filePath, filename)

    if returnMode == "path":
        return filePath

    return open(filePath, mode)

def update():
    # 更新app scheme, trackid=1111&scheme=com.a.a.a.a:com.a.a.a
    global dal, APIS_HOST
    preTime = time.time()
    _init()
    print "init cost:", (time.time() - preTime)
    preTime = time.time()
    parseRequest()

    trackid = request.vars.get("trackid")
    scheme = request.vars.get("scheme")

    logger.info("update")
    logger.info("\t%s"%str(request.vars))

    if trackid is None or scheme is None:
        return "parameter error!"

    # 必须是scheme为空
    cmd = 'select scheme from appstores where trackid="%s"'%trackid
    schemeIn = dal.executesql(cmd)[0][0]
    isExist = (schemeIn is None) or (len(schemeIn.strip()) == 0)
    
    if isExist:
        cmd = 'update appstores set scheme="%s" where trackid=%s;'%(scheme, trackid)
        print cmd
        dal.executesql(cmd)
        print "commit", dal.commit()

    logger.info("\t%s"%str(isExist))
    return json.dumps({"result":isExist})

def getUnhandleApps():
    # 获取没有处理的应用信息
    global dal, APIS_HOST
    preTime = time.time()
    _init()
    print "init cost:", (time.time() - preTime)
    preTime = time.time()
    parseRequest()

    # limit=20&index=1
    limit = 20
    index = 0
    if request.vars.has_key("index"):
        try:
            index = int(request.vars.get("index"))
        except Exception, e:
            pass

        if index < 0:
            index = 0
        
    cmd = "select trackid, name, icon60, icon512 from appstores where scheme is null limit %d offset %d;"%(limit, index*limit)
    result = dal.executesql(cmd)
    apps = []
    for app in result:
        trackid, name, icon60, icon512 = app
        appInfo = {}
        appInfo["trackid"] = trackid
        appInfo["name"] = name
        appInfo["icon60"] = icon60
        appInfo["icon512"] = icon512
        appInfo["url"] = "https://itunes.apple.com/app/id%s?mt=8"%trackid
        apps.append(appInfo)
    return json.dumps({"data":apps})

def checkUpdate():
    global dal, APIS_HOST
    preTime = time.time()
    _init()
    print "init cost:", (time.time() - preTime)
    preTime = time.time()
    parseRequest()

    maxVersion = -1
    command = "select max(version) from appstores where version > 0;"

    maxVersion = dal.executesql(command)[0][0]

    appSchemeJsonVersion = None
    if request.vars.has_key("schemeJsonVersion"):
        appSchemeJsonVersion = int(request.vars.get("schemeJsonVersion"))


    if appSchemeJsonVersion == None or appSchemeJsonVersion > maxVersion:
        appSchemeJsonVersion = 0

    if appSchemeJsonVersion == maxVersion:
        # 不需要更新
        return json.dumps({"result":False})
    elif appSchemeJsonVersion == 0:
        # return os.getcwd()
        # 返回全部的scheme json数据
        content = json.load(_getTagsStaticFile("extSchemeApps.json"))
        result = {"result":True, "data":content, "schemeJsonVersion":maxVersion}
        return json.dumps(result)
    else:
        # 返回更新增量数据
        content = json.load(_getTagsStaticFile("scheme/extSchemeApps_%d_%d.json"%(int(maxVersion), int(appSchemeJsonVersion))))
        result = {"result":True, "data":content, "schemeJsonVersion":maxVersion}
        return json.dumps(result)

def _commitThread(content):
    filePath = _getTagsStaticFile(".update"+os.path.sep+"commit_%d.json"%long(time.time()), returnMode="path")
    commitFile = open(os.path.abspath(filePath), "w")
    commitFile.write(content)
    commitFile.close()
    
    spiderPath = "E:\\git\\iam007-spider\\AppStore\\AppStoreSpider.py"
    cmd = 'python "%s" update "%s"'%(spiderPath, filePath)
    # os.system(cmd.encode("utf-8"))
    
    # global dal
    # _init()
        
    # for trackid in content.keys():
    #     try:
    #         schemes = ":".join(content.get(trackid))
    #         cmd = 'select count(*) from appstores where trackid="%s";'%trackid
    #         if dal.executesql(cmd)[0][0] > 0:
    #             # 已经存在，更新
    #             cmd = 'update appstores set scheme="%s" where trackid="%s";'%(schemes, trackid)
    #             dal.executesql(cmd)
    #             logger.info("update %s scheme to %s"%(trackid, schemes))
    #             print "update %s scheme to %s"%(trackid, schemes)
    #         else:
    #             # 不存在，获取应用名称和icon，一并插入
    #             logger.info("insert %s scheme to %s"%(trackid, schemes))
    #             print "insert %s scheme to %s"%(trackid, schemes)
    #     except Exception, e:
    #         pass

    #     dal.commit()

def commit():
    parseRequest()
    result = True

    # t1 = threading.Thread(target=_commitThread, args=(request.vars.keys()[0],))
    # t1.setDaemon(True)
    # t1.start()

    import tempfile
    filepath = tempfile.mktemp()
    fp = open(filepath, "w")
    fp.write(request.vars.keys()[0])
    fp.close()

    try:
        commitScriptPath = ["applications", "iam007", "modules", "Commit.py"]
        commitScriptPath = os.path.sep.join(commitScriptPath)
        cmd = 'python "%s" "%s"'%(commitScriptPath, filepath)
        # os.system(cmd)

        params = urllib.urlencode({"file":filepath})
        cmd = 'wget -q http://127.0.0.1:9156/commitWithFile?%s'%(params)
        subprocess.Popen(cmd, shell=True)

    except Exception, e:
        print e

    # t1 = threading.Thread(target=_commitExecute, args=(filepath,))
    # t1.setDaemon(True)
    # t1.start()

    return json.dumps({"result":result})

def task():
    global dal, APIS_HOST
    preTime = time.time()
    _init()
    print "init cost:", (time.time() - preTime)
    preTime = time.time()
    parseRequest()

    action = request.vars.get("action")
    appleid = request.vars.get("id")
    trackid = request.vars.get("trackid")

    # debug
    # trackid = '9585078694'
    # appleid = "jiangerji"
    # action = 'get'

    print request.vars

    result = {}

    (_BLANK, _MY_OWNER, _OTHER_OWNER, _PARAMS_ERROR) = (0, 1, 2, -1)

    state = _BLANK
    if action is None or trackid is None or appleid is None:
        state = _PARAMS_ERROR
    elif action == "get":
        # action=get&trackid=111&appleid=111
        # 领取任务, 检查是否已经被自己领取了
        alreadyInTask = False
        cmd = 'select trackid, owner from taskstate where trackid=%s;'%trackid
        try:
            rr = dal.executesql(cmd)
            print rr
            if len(rr) > 0:
                # 任务已经被领取
                alreadyInTask = True

                # 是否被自己领取
                if rr[0][1] == appleid:
                    state = _MY_OWNER # 自己领取
                else:
                    state = _OTHER_OWNER # 别人领取
            else:
                # 无人领取
                state = _BLANK

        except Exception, e:
            pass

        if state == _BLANK:
            # 无人领取，
            cmd = 'insert into taskstate (trackid, state, owner, timestamp) VALUES ("%s", %s, "%s", "%s")'%(trackid, 1, appleid, time.strftime("%Y_%m_%d_%H_%M_%S"))
            dal.executesql(cmd)
    elif action == "complete":
        # action=complete&trackid=111&appleid=111&scheme=aaa.aaa.aaa:vv:vvs
        scheme = request.vars.get("scheme")
        print "scheme is ", scheme
        if (scheme is None) or (len(scheme.strip()) == 0):
            state = _PARAMS_ERROR # 参数错误
        else:
            # 完成任务
            # 从taskstate中删除
            cmd = 'delete from taskstate where trackid=%s'%trackid
            dal.executesql(cmd)
            print "delete from taskstate"

            # 插入到task表中
            cmd = 'insert into task (trackid, scheme, owner, timestamp) VALUES ("%s", "%s", "%s", "%s")'%(trackid, scheme, appleid, time.strftime("%Y_%m_%d_%H_%M_%S"))
            dal.executesql(cmd)
            print "insert into task"

            # 插入到appstores表中
            cmd = 'update appstores set scheme="%s" where trackid=%s;'%(scheme, trackid)
            dal.executesql(cmd)
            print "insert into appstores"

            dal.commit()

    result["result"] = state
    return json.dumps(result)


def unhandle():
    global dal
    preTime = time.time()
    _init()
    print "init cost:", (time.time() - preTime)
    preTime = time.time()
    parseRequest()

    cmd = 'select name, trackid, price from appstores where scheme is null;'
    result = dal.executesql(cmd)

    result = map(lambda x: (x[0], "https://itunes.apple.com/cn/app/id%s"%x[1], " %0.2f"%int(x[2])), result)
    return dict(appInfos=result)

def help():
    # 帮助页面
    global dal
    preTime = time.time()
    _init()
    print "init cost:", (time.time() - preTime)
    preTime = time.time()
    parseRequest()

    redirect("http://chuye.cloud7.com.cn/3014684")
    return ""

def about():
    # 帮助页面
    global dal
    preTime = time.time()
    _init()
    print "init cost:", (time.time() - preTime)
    preTime = time.time()
    parseRequest()

    redirect("http://chuye.cloud7.com.cn/3017283")
    return ""

def config():
    # 获取应用程序的配置信息
    content = ""
    try:
        content = json.load(_getTagsStaticFile("AppConfig.json"))
    except Exception, e:
        print e

    return json.dumps(content)

def guideInstallApp():
    # QQ，微信, 微博, YY, 陌陌
    # 网易新闻，
    # 爱奇艺、腾讯视频，
    # DOTA传奇，
    # QQ音乐, 百度音乐
    # 百度地图，高德地图
    # 美颜相机
    # 获取应用程序的配置信息
    content = ""
    try:
        content = json.load(_getTagsStaticFile("guideinstallapp.json"))
    except Exception, e:
        print e

    return json.dumps(content)


def parseRequest():
    # 发起请求客户端的操作系统类型
    platform = ""
    if request.vars.has_key("platform"):
        platform = request.vars.get("platform")

    # 发起请求客户端的操作系统版本
    os = ""
    if request.vars.has_key("os"):
        os = request.vars.get("os")

    # 发起请求客户端的版本
    version = ""
    if request.vars.has_key("version"):
        version = request.vars.get("version")

    token = ""
    if request.vars.has_key("token"):
        token = request.vars.get("token")

    return platform, os, version, token