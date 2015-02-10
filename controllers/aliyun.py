import json
import os
import time
import platform
import HTMLParser

MYSQL_HOST     = "jiangerji.mysql.rds.aliyuncs.com"
MYSQL_PASSPORT = "jiangerji"
MYSQL_PASSWORD = "eMBWzH5SIFJw5I4c"
MYSQL_DATABASE = "iam007"

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
    staticFileFormat = "%s/static/tags/%%s"%APIS_HOST
    return staticFileFormat%filename

# 获取所有的tags
def tags():
    global dal, APIS_HOST
    preTime = time.time()
    _init()
    print "init cost:", (time.time() - preTime)
    preTime = time.time()
    parseRequest()

    command = "select a.term_id, a.description, b.name, b.slug, a.count from wp_term_taxonomy a join wp_terms b on a.taxonomy='post_tag' and a.term_id=b.term_id order by a.count desc;"

    allTags = dal.executesql(command)

    result = {}
    result["error"] = 0

    jsonTags = []

    for tag in allTags:
        jsonTag = {}
        jsonTag["id"] = tag[0]      # tag id
        jsonTag["icon"] = tag[1]    # tag icon
        jsonTag["icon"] = _getTagsStaticFile(tag[1])#"http://123.57.77.122/static/wx_200.jpg"
        jsonTag["name"] = tag[2]    # tag readable name
        jsonTag["slug"] = tag[3]    # tag alias
        jsonTag["count"] = tag[4]   # tag 
        jsonTags.append(jsonTag)

    result["data"] = jsonTags

    print "tags cost:", (time.time() - preTime)
    return json.dumps(result)

def recommend():
    # 获取所有推荐列表
    global dal
    _init()
    print parseRequest()

    # 获取热门的tags
    hotTagsCommand = "select b.name from wp_term_taxonomy a join wp_terms b on a.taxonomy='post_tag' and b.term_id=a.term_id order by a.count desc limit 0, 5"
    _hotTags = list(dal.executesql(hotTagsCommand))
    _hotTags = map(lambda x: x[0], _hotTags)
    hotTags = []
    for i in _hotTags:
        hotTags.append(i.encode("utf8"))

    """
    select e.name, a.post_id, b.post_title, f.meta_value  from wp_postmeta a join wp_posts b on a.meta_key='hot' and a.meta_value='1' and b.ID=a.post_id join wp_term_relationships c on c.object_id=a.post_id join wp_term_taxonomy d on d.term_taxonomy_id=c.term_taxonomy_id join wp_terms e on d.term_id = e.term_id and e.name='智能客厅' join wp_postmeta f on f.post_id=b.ID and f.meta_key='focus_image_value';
    """
    commandFormat = "select e.name, a.post_id, b.post_title, f.meta_value, g.meta_value from wp_postmeta a join wp_posts b on a.meta_key='hot' and a.meta_value='1' and b.ID=a.post_id join wp_term_relationships c on c.object_id=a.post_id join wp_term_taxonomy d on d.term_taxonomy_id=c.term_taxonomy_id join wp_terms e on d.term_id = e.term_id and e.name='%s' join wp_postmeta f on f.post_id=b.ID and f.meta_key='focus_image_value' left join wp_postmeta g on g.post_id=b.ID and g.meta_key='referenceurl';"

    result = {}
    result['error'] = 0
    resultData = []
    for tag in hotTags:
        command = commandFormat%tag
        recommendSkus = dal.executesql(command)

        data = {}
        data['name'] = tag
        skuDatas = []
        for sku in recommendSkus:
            skuData = {}
            skuData['postId'] = sku[1]
            skuData['title'] = sku[2]
            skuData['icon'] = sku[3]
            skuData['ref'] = sku[4]
            skuDatas.append(skuData)
        data['data'] = skuDatas
        resultData.append(data)
    result['data'] = resultData

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