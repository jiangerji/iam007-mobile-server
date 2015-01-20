#encoding=utf-8
from __future__ import unicode_literals
import sys
import os
import platform
import time
import json
import re
import codecs
import hashlib


"""
在log目录下创建filename.创建日期.log的日志文件
如果为None, filename默认为调用该接口的python文件名
"""
def openLogFile(filename=None):
    if filename == None:
        filename = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    currentDate = time.strftime("%Y-%m-%d",time.localtime()) 

    filename += "-" + currentDate + ".log"

    logDir = "log"
    if not os.path.isdir(logDir):
        os.makedirs(logDir)

    return codecs.open("log"+os.path.sep+filename, "w", "utf-8")

import MySQLdb
host    = "iam007.cskkndpfwwgp.ap-northeast-1.rds.amazonaws.com"
user    = "jiangerji"
passwd  = "eMBWzH5SIFJw5I4c"
db      = "baidu"
charset = 'utf8'

if platform.system() == 'Windows':
    host    = "localhost"
    user    = "root"
    passwd  = "123456"
    db      = "baidu"

def md5(source):
    result = hashlib.md5(source).hexdigest()
    return result

def parsePlugin(pluginDir, mysqlCur):
    print "=======Parse", pluginDir
    pluginConfig = os.path.join(pluginDir, "plugin.config")

    values = eval(open(pluginConfig).read())
    pluginId = values['id']
    pluginName = values['name']
    pluginDesc = values['desc']
    pluginIcon = values['icon']
    pluginMD5  = values['md5']
    pluginUrl  = values['url']
    pluginMD5 = md5(open(os.path.join(pluginDir, pluginUrl)).read())
    pluginType = values['type']
    pluginForceUpdate = values['forceUpdate']
    pluginVersion = values['version']
    print "plugin id:", pluginId
    print "plugin name:", pluginName
    print "plugin desc:", pluginDesc
    print "plugin icon:", pluginIcon
    print "plugin md5:", pluginMD5
    print "plugin url:", pluginUrl
    print "plugin type:", pluginType
    print "plugin force update:", pluginForceUpdate
    print "plugin version:", pluginVersion

    command = "insert into plugins_android (`id`, `name`, `description`, `icon`, `url`, `md5_value`, `force_update`, `version`, `type`) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    value = (pluginDir, pluginName, pluginDesc, pluginIcon, pluginUrl, pluginMD5, pluginForceUpdate, pluginVersion, pluginType)

    try:
        mysqlCur.execute(command, value)
    except Exception, e:
        pass
    
def main():
    mysqlConn = None
    mysqlCur = None
    try:
        mysqlConn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset=charset)
        mysqlCur  = mysqlConn.cursor()
    except MySQLdb.Error,e:
         print "Mysql Error %d: %s" % (e.args[0], e.args[1])
         exception = e

    command = 'TRUNCATE `plugins_android`;'
    mysqlCur.execute(command)

    for i in os.listdir("."):
        if os.path.isdir(i):
            configFile = os.path.join(i, "plugin.config")
            if os.path.isfile(configFile):
                parsePlugin(i, mysqlCur)

    mysqlConn.commit()



if __name__=="__main__":
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # workDir = os.path.dirname(os.path.realpath(sys.argv[0]))
    # os.chdir(os.path.dirname(workDir)) # 保证spider cache目录一致

    logFile = openLogFile()

    oldStdout = sys.stdout  
    sys.stdout = logFile

    print "============================================"
    # print "change work direcotory to workDir", workDir
    print "Start Parse Plugin Spider:", time.asctime()

    main()

    logFile.close()  
    if oldStdout:  
        sys.stdout = oldStdout