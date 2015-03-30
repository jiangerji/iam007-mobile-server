import json
import os
import time
import platform
import HTMLParser

MYSQL_HOST     = "jiangerji.mysql.rds.aliyuncs.com"
MYSQL_PASSPORT = "jiangerji"
MYSQL_PASSWORD = "eMBWzH5SIFJw5I4c"
MYSQL_DATABASE = "spider"

APIS_HOST = "http://123.57.77.122:802/iam007"
if platform.system() == 'Windows':
    APIS_HOST = "http://192.168.54.9:8000/iam007"

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

def _getTagsStaticFile(filename):
    filePath = os.path.join(os.getcwd(), "applications")
    filePath = os.path.join(filePath, "iam007")
    filePath = os.path.join(filePath, "static")
    filePath = os.path.join(filePath, filename)
    return open(filePath, "r")

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