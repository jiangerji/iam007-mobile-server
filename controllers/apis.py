import json
import time
import platform
import HTMLParser

MYSQL_HOST     = "iam007.cskkndpfwwgp.ap-northeast-1.rds.amazonaws.com"
MYSQL_USERNAME = "jiangerji"
MYSQL_PASSWORD = "eMBWzH5SIFJw5I4c"
MYSQL_DATABASE = "baidu"

if platform.system() == 'Windows':
    MYSQL_USERNAME = "root"
    MYSQL_PASSWORD = "123456"
    MYSQL_HOST = "localhost"
    MYSQL_DATABASE = "test"

PRODUCT_ARTICEL_URL = "http://iam007.cn/index.php/14-product-category/%s-%s"
NEWS_ARTICEL_URL = "http://iam007.cn/index.php/detail/%s-%s"
EVALUATION_ARTICEL_URL = "http://iam007.cn/index.php/evaluation/item/%s-%s"

PRODUCT_ARTICEL_URL = "http://iam007.cn:801/iam007/apis/article?contentid=%s"
if platform.system() == 'Windows':
    PRODUCT_ARTICEL_URL = "http://192.168.41.101:8000/iam007/apis/article?contentid=%s"

"""
select erji_content.id, erji_content.title, erji_tz_portfolio_xref_content.images, c.buy_url from erji_content, erji_tz_portfolio_xref_content, (select erji_content.id, products.buy_url from erji_content, products where erji_content.state=1 and erji_content.title = products.product_name and erji_content.catid=14) c where erji_content.id = erji_tz_portfolio_xref_content.id and erji_content.id = c.id;
"""

dal = None#DAL('sqlite://wanke.sqlite3.sqlite')
def _init():
    global dal, MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE
    if dal is None:
        """
        SQLite  sqlite://storage.db
        MySQL   mysql://username:password@localhost/test
        PostgreSQL  postgres://username:password@localhost/test
        """
        command = "mysql://%s:%s@%s/%s"%(MYSQL_USERNAME, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE)
        dal = DAL(command)

def convertBuyUrl(buyUrl):
    if buyUrl is None:
        buyUrl = ""
    try:
        if buyUrl.find("item.jd.com") != -1:
            endIndex = buyUrl.rfind('.')
            startIndex = buyUrl.rfind('/')
            itemId = buyUrl[startIndex+1:endIndex]
            buyUrl = "http://m.jd.com/product/%s.html"%itemId
    except Exception, e:
        pass

    html_parser = HTMLParser.HTMLParser()
    return html_parser.unescape(buyUrl)

"""
获取当前最新的产品列表，最多返回4个
"""
def latest():
    global dal
    preTime = time.time()
    _init()
    print "init cost:", (time.time() - preTime)
    preTime = time.time()

    parseRequest()

    limit = int(request.vars.get("limit", 4))
    pn = int(request.vars.get("pn", 0))
    catType = request.vars.get("cat", "product")
    catids = ["14"]
    if catType == "all":
        catids = ["8", "14", "15"]
    elif catType == "news":
        catids = ["8"]

    command = 'select a.id, a.title, a.alias, c.buy_url, b.images, a.catid, a.hits, a.introtext from erji_content a join erji_tz_portfolio_xref_content b on a.state=1 and a.catid in (%s) and a.id=b.contentid left join products c on c.product_title = a.title order by a.created desc limit %d, %d;'%(",".join(catids), pn*limit, (pn+1)*limit)

    lastestProducts = dal.executesql(command)

    result = {}
    result["e"] = 0

    jsonProducts = []
    for product in lastestProducts[0:limit]:
        jsonProduct = {}
        jsonProduct["i"] = product[0] # content id
        jsonProduct["n"] = product[1] # product name
        # 文章的连接
        jsonProduct['u'] = PRODUCT_ARTICEL_URL%(str(product[0]))
        jsonProduct["b"] = convertBuyUrl(product[3]) # product buy url
        jsonProduct["t"] = os.path.basename(product[4]) # product thumbnail
        jsonProduct["c"] = product[5] # content category id
        jsonProduct["h"] = product[6] # content hits
        jsonProduct["it"] = product[7] # content introduction
        
        jsonProducts.append(jsonProduct)

    result["d"] = jsonProducts

    print "lastest cost:", (time.time() - preTime)
    return json.dumps(result)

"""
获取当前最热的产品列表，最多返回10个
"""
def hotest():
    global dal
    preTime = time.time()
    _init()
    parseRequest()

    limit = int(request.vars.get("limit", 4))

    command = 'select a.id, a.title, a.alias, c.buy_url, b.images, a.catid, a.hits from erji_content a join erji_tz_portfolio_xref_content b on a.state=1 and a.catid = 14 and (a.created > date_sub(sysdate(), INTERVAL 14 DAY)) and a.id=b.contentid join products c on c.product_title = a.title order by a.hits desc limit 0, 10 ;'

    hotestProducts = dal.executesql(command)

    result = {}
    result["e"] = 0

    jsonProducts = []
    for product in hotestProducts[0:limit]:
        jsonProduct = {}
        jsonProduct["i"] = product[0] # content id
        jsonProduct["n"] = product[1] # product title
        # 文章的连接
        jsonProduct['u'] = PRODUCT_ARTICEL_URL%(str(product[0]))
        jsonProduct["b"] = convertBuyUrl(product[3]) # product buy url
        jsonProduct["t"] = os.path.basename(product[4]) # product thumbnail
        jsonProduct["c"] = product[5]
        jsonProduct["h"] = product[6]
        
        jsonProducts.append(jsonProduct)

    result["d"] = jsonProducts

    print "lastest cost:", (time.time() - preTime)
    return json.dumps(result)

"""
获取推荐页顶部互动的广告信息
http://54.64.105.44/iam007/apis/ads
"""
def ads():
    global dal

    preTime = time.time()

    _init()
    parseRequest()
    limit = int(request.vars.get("limit", 4))

    command = 'select a.id, a.title, a.alias, c.buy_url, b.images, a.catid, a.hits from erji_content a join erji_tz_portfolio_xref_content b on a.state = 1 and a.id = b.contentid left join products c on c.product_title = a.title order by hits desc limit 0, 10;'

    allAds = dal.executesql(command)
    result = {}
    result["e"] = 0

    jsonAds = []
    for ad in allAds[0:limit]:
        jsonProduct = {}
        jsonProduct["i"] = ad[0] # content id
        jsonProduct["n"] = ad[1] # content title

        categoryId = int(ad[5])
        jsonProduct["c"] = categoryId # category id
        if categoryId == 8:
            jsonProduct['u'] = NEWS_ARTICEL_URL%(str(ad[0]), ad[2])
        elif categoryId == 14:
            jsonProduct['u'] = PRODUCT_ARTICEL_URL%(str(ad[0]))
        elif categoryId == 15:
            jsonProduct['u'] = EVALUATION_ARTICEL_URL%(str(ad[0]), ad[2])
        else:
            continue

        jsonProduct["b"] = convertBuyUrl(ad[3]) # content buy url
        jsonProduct["t"] = os.path.basename(ad[4]) # product thumbnail
        jsonProduct["h"] = ad[6]
        
        jsonAds.append(jsonProduct)

    result["d"] = jsonAds
    print "ads cost:", (time.time() - preTime)
    return json.dumps(result)

"""
获取某个content的详细内容 TODO
"""
def detail():
    global dal

    preTime = time.time()

    _init()
    parseRequest()
    contentId = int(request.vars.get("contentid", -1))
    category = request.vars.get("catid", "")
    if contentId == -1 or len(category) == 0:
        return "参数错误"

    # 需要获取
    # content id
    # content category id
    # content thumbnails
    # content introduction
    command = ""
    if category == "14":
        command = 'select a.id, a.introtext, b.product_thumbnails from erji_content a join products b on a.id = %d and a.title = b.product_title;'%contentId

    result = {}
    if command is None or len(command) == 0:
        return json.dumps(result)

    products = dal.executesql(command)
    if len(products) > 0:
        product = products[0]
        
        result['i'] = product[0]
        result['it'] = product[1]
        result['ts'] = eval(product[2])

    return json.dumps(result)

"""
获取某个article的页面
"""
def article():
    global dal

    preTime = time.time()

    _init()
    parseRequest()
    contentId = int(request.vars.get("contentid", -1))
    print contentId
    if contentId == -1:
        return ""

    command = 'select a.`fulltext` from erji_content a where a.id=%s;'%contentId
    products = dal.executesql(command)
    if len(products) > 0:
        html_parser = HTMLParser.HTMLParser()
        articleDetail = html_parser.unescape(products[0][0])
        startIndex = articleDetail.find('jiangerji')
        if startIndex >= 0:
            startIndex = articleDetail.find('</p>')
            if startIndex >= 0:
                articleDetail = articleDetail[startIndex+len('</p>'):]
        return dict(content=XML(articleDetail))

    return "error"
    

import os
"""
http://iam007.cn:801/iam007/apis/version?type=android
获取当前版本更新信息
type: ios或者android

"""
def version():
    parseRequest()

    platform = request.vars.get("type", "")
    version = request.vars.get("version", "")

    result = {}
    result["state"] = 0

    if len(platform) == 0:
        result['state'] = 1
        return json.dumps(result)

    # TODO
    # 判断version是否需要更新

    result["state"] = 1 # 1表示需要更新， 0表示不需要更新，其他表示错误
    result["version"] = "1.0.1"                              # 版本号
    result["forceUpdate"] = False                            # 是否为强制更新
    result["updateShortLog"] = "这是一次假的更新。\nhaha ~~" # 此次更新的简要描述
    result["updateDetailLog"] = "http://www.baidu.com"       # 此次更新的详细描述的网页地址
    result["downUrl"] = "http://www.baidu.com"               # APK文件的下载地址

    return json.dumps(result)

"""
关注某个content
"""
def collect():
    _init()
    parseRequest()
    contentid = int(request.vars.get("contentid", -1))
    uid = request.vars.get("uid", "")

    result = {}
    result["state"] = 0

    if len(uid) == 0 or contentid == -1:
        result["state"] = -1
        return json.dumps(result)

    return json.dumps(result)


"""
取消关注某个content
"""
def uncollect():
    _init()
    parseRequest()
    contentid = int(request.vars.get("contentid", -1))
    uid = request.vars.get("uid", "")

    result = {}
    result["state"] = 0

    if len(uid) == 0 or contentid == -1:
        result["state"] = -1
        return json.dumps(result)

    return json.dumps(result)






#############################################################################
############################下面的接口都是无效的#############################
#############################################################################


"""
获取当前支持直播的游戏列表
http://54.64.105.44/wanketv/live/games
"""
def games():
    db = DAL('sqlite://wanke.sqlite3.sqlite')
    allGames = db.executesql("select * from games order by gameIndex")
    result = {}
    result["error"] = 0
    jsonGames = []
    for game in allGames:
        jsonGame = {}
        jsonGame["gameId"] = game[1]
        jsonGame["gameName"] = game[2]
        jsonGame["gameCover"] = game[4]
        jsonGames.append(jsonGame)

    result["data"] = jsonGames
    return json.dumps(result)

"""
获取某款游戏的热门直播列表

http://54.64.105.44/wanketv/live/recommend?gameId=2&offset=0&limit=4
http://54.64.105.44/wanketv/live/recommend?offset=1&limit=20

recommend?gameId=2&offset=0&limit=4
    获取room id的第offset页，每页4个
    limit  默认值为20
    offset 默认值为0
    gameId 如果没有，不按照游戏进行分类返回
"""
def recommend():
    parseRequest()
    gameId = request.vars.get("gameId", "")
    limit = int(request.vars.get("limit", 20))
    offset = int(request.vars.get("offset", 0))

    debug = request.vars.get("debug", "")
    if len(debug) > 0:
        gameId = ""

    db = DAL('sqlite://wanke.sqlite3.sqlite')
    allRooms = []
    if len(gameId) == 0:
        # 返回所有游戏中最热门的直播频道
        allRooms = db.executesql("select * from live_channels order by _id")
    else:
        sql = "select * from live_channels where gameId=%s order by _id"%gameId
        allRooms = db.executesql(sql)

    result = {}
    result["error"] = 0

    index = 0
    jsonRooms = []
    for room in allRooms:
        if index < limit*offset:
            index += 1
            continue

        if index >= limit*(offset+1):
            break

        jsonRoom = {}
        jsonRoom["roomId"] = room[1]
        jsonRoom["roomName"] = room[2]
        jsonRoom["roomCover"] = room[3]
        jsonRoom["gameId"] = room[5]
        jsonRoom["gameName"] = room[6]
        jsonRoom["ownerNickname"] = room[11]
        jsonRoom["online"] = room[12]
        jsonRoom["fans"] = room[13]
        jsonRooms.append(jsonRoom)

        index += 1

    result["data"] = jsonRooms
    return json.dumps(result)

"""
获取某个房间的详细信息

http://54.64.105.44/wanketv/live/channel?roomId=7
http://54.64.105.44/wanketv/live/channel?roomId=7&uid=1

channel?roomId=7&uid=1
    roomId: 如果没有，返回空
    uid: 如果有，在返回结果中加入该用户是否订阅了该房间的字段
"""
def channel():
    parseRequest()
    roomId = request.vars.get("roomId", "")
    uid = request.vars.get("uid", "")

    db = DAL('sqlite://wanke.sqlite3.sqlite')
    allRooms = []

    result = ""
    if len(roomId) > 0:
        sql = "select * from live_channels where roomId=%s order by _id"%roomId
        allRooms = db.executesql(sql)

    room = None
    if len(allRooms) >= 1:
        room = allRooms[0]

    if room != None:
        jsonRoom = {}
        jsonRoom["roomId"] = room[1]
        jsonRoom["roomName"] = room[2]
        jsonRoom["roomCover"] = room[3]
        jsonRoom["gameId"] = room[5]
        jsonRoom["gameName"] = room[6]
        jsonRoom["ownerUid"] = room[9]
        jsonRoom["ownerNickname"] = room[11]
        jsonRoom["online"] = room[12]
        jsonRoom["fans"] = room[13]
        jsonRoom["detail"] = room[14]

        if len(uid) > 0:
            sql = "select subscribes from subscribe where uid=%s"%uid
            subscribes = db.executesql(sql)
            subscribe = None
            if len(subscribes) >= 1:
                subscribe = subscribes[0][0]

            if subscribe != None:
                sset = set(subscribe.split(":"))
                if roomId in sset:
                    jsonRoom["subscribed"] = True
                else:
                    jsonRoom["subscribed"] = False

        result = json.dumps(jsonRoom)
    return result

"""
取消对房间的订阅
http://54.64.105.44/wanketv/live/unsubscribe?roomId=7&uid=1

unsubscribe?roomId=7&uid=1
    roomId: 需要取消订阅的房间号
    uid:    用户uid，不能为空
    roomIds: 使用;对roomId进行分割，同时取消订阅多个房间号使用，优先级高于roomId
    all:    true or false, 这个优先级高于roomIds, 如果该值被设置为true, 删除该用户的所有订阅消息
"""
def unsubscribe():
    
    parseRequest()
    uid = request.vars.get("uid", "")
    roomId = request.vars.get("roomId", "")
    roomIds = request.vars.get("roomIds", "").split(":")
    unsubscribeAll = request.vars.get("all", "false")

    print roomIds

    result = {}
    result["error"] = 1

    if unsubscribeAll.lower() == "true":
        # 删除所有的订阅
        try:
            sql = 'update subscribe set subscribes="%s" where uid=%s'%("", uid)
            dal.executesql(sql)
            result["error"] = 0
        except Exception, e:
            result["msg"] = e.message
    else:
        if len(roomIds) == 0:
            roomIds.add(roomId)

        sql = "select subscribes from subscribe where uid=%s"%uid

        subscribes = dal.executesql(sql)

        subscribe = None
        if len(subscribes) >= 1:
            subscribe = subscribes[0][0]

        if subscribe != None:
            sset = set(subscribe.split(":"))
            try:
                for tempId in roomIds:
                    try:
                        sset.remove(tempId)
                    except Exception, e:
                        pass

                # update
                sql = 'update subscribe set subscribes="%s" where uid=%s'%(":".join(list(sset)), uid)
                dal.executesql(sql)
                result["error"] = 0
            except Exception, e:
                result["msg"] = e.message

    return json.dumps(result)

"""
订阅某个房间
http://54.64.105.44/wanketv/live/subscribe?roomId=7&uid=1

subscribe?roomId=7&uid=1
    roomId: 需要订阅的房间号
    uid:    用户uid
"""
def subscribe():
    parseRequest()
    uid = request.vars.get("uid", "")
    roomId = request.vars.get("roomId", "")
    if len(uid) == 0 or len(roomId) == 0:
        return ""

    db = DAL('sqlite://wanke.sqlite3.sqlite')
    sql = "select subscribes from subscribe where uid=%s"%uid

    subscribes = db.executesql(sql)

    subscribe = None
    if len(subscribes) >= 1:
        subscribe = subscribes[0][0]

    if subscribe != None:
        sset = set(subscribe.split(":"))
        sset.add(roomId)

        # update
        sql = 'update subscribe set subscribes="%s" where uid=%s'%(":".join(list(sset)), uid)
    else:
        # insert
        sql = 'insert into subscribe (uid, subscribes) VALUES (%s, "%s")'%(uid, roomId)
    
    db.executesql(sql)

    result = {}
    result["error"] = 0

    return json.dumps(result)

"""
登录操作
http://54.64.105.44/wanketv/live/login?username=root&password=1

login?username=root&password=1
    username: 注册用户名
    passwrod: 登录密码
"""
def login():
    time.sleep(2)

    parseRequest()
    username = request.vars.get("username", "")
    password = request.vars.get("password", "")

    """
    返回值:
        0:  登录成功
        1:  用户名或密码错误
    """
    result = {}
    result["error"] = 1
    result["msg"] = "用户名或密码错误"
    if len(username) > 0 and len(password) > 0:
        try:
            sql = 'select password, uid from account where username="%s"'%username
            selectResults = dal.executesql(sql)
            if len(selectResults) > 0:
                dbPassword = selectResults[0][0]
                if dbPassword == password:
                    result["error"] = 0
                    result["msg"] = ""
                    result["username"] = username
                    result["uid"] = selectResults[0][1]
                    result["avatar"] = "album_"+str(selectResults[0][1])+'.png'
        except Exception, e:
            result["error"] = 1

    return json.dumps(result)


"""
注册新用户
http://54.64.105.44/wanketv/live/register?username=2121&password=1&email=123123@gmail.com

register?username=2121&password=1&email=123123@gmail.com
    username: 注册用户名
    passwrod: 登录密码
    email:    注册邮箱
"""
def register():
    time.sleep(2)

    parseRequest()

    username = request.vars.get("username", "")
    password = request.vars.get("password", "")
    email = request.vars.get("email", "")
    
    """
    返回值:
        0:  注册成功
        1:  参数格式错误
        2:  用户名已存在
    """
    result = {}
    if len(username) == 0 or len(password) == 0 or len(email) == 0:
        result["error"] = 1
        result["msg"] = "参数格式错误！"
    else:
        try:
            sql = 'insert into account (username, password, email) VALUES ("%s", "%s", "%s")'%(username, password, email)
            dal.executesql(sql)
            result["error"] = 0
            result["msg"] = ""
        except Exception, e:
            result["error"] = 2
            result["msg"] = "用户名已存在！"

    return json.dumps(result)

"""
获取某人的资料信息
http://54.64.105.44/wanketv/live/userInfo?uid=2121


userInfo?uid=2121
    uid: 注册用户的uid
"""
def userInfo():

    parseRequest()

    uid = request.vars.get("uid", "")
    result = {}
    result["error"] = 0
    result["msg"] = ""

    if len(uid) == 0:
        result["error"] = 1
        result["msg"] = "参数格式错误！"
    else:
        try:
            sql = 'select * from account where uid="%s"'%uid
            selectResults = dal.executesql(sql)
            if len(selectResults) > 0:
                info = selectResults[0]

                result["uid"] = info[0]
                result["username"] = info[1]
                # result["password"] = info[2]
                result["email"] = info[3]
                result["exp"] = info[4]
                result["fans"] = info[5]
                result["gender"] = info[6]
        except Exception, e:
            result["error"] = 2
            result["msg"] = "用户名已存在！"

    return json.dumps(result)

"""
意见反馈接口
http://54.64.105.44/wanketv/live/feedback?uid=2121&content=fasfasfasfasfasdf

feedback?uid=2121&content=fasfasfasfasfasdf
    uid: 注册用户的uid，可选
    content: 用户反馈的意见，不能为空
"""
def feedback():
    parseRequest()

    uid = request.vars.get("uid", "")
    content = request.vars.get("content", "")

    result = {}
    result["error"] = 0
    result["msg"] = ""

    time.sleep(2)

    if len(content) < 10:
        result["error"] = 1
        result["msg"] = "意见字数太少！"
    else:
        pass

    return json.dumps(result)

"""
获取用户关注的直播频道数据
http://54.64.105.44/wanketv/live/fav?uid=1

fav?uid=2121
"""
def fav():
    parseRequest()

    uid = request.vars.get("uid", "")
    result = {}
    result["error"] = 0
    result["msg"] = ""

    if len(uid) > 0:
        try:
            sql = 'select subscribes from subscribe where uid="%s"'%uid
            selectResults = dal.executesql(sql)
            if len(selectResults) > 0:
                subscribesInfo = selectResults[0][0]
                data = []
                for roomId in subscribesInfo.split(":"):
                    subscribe = {}
                    subscribe["roomId"] = roomId
                    data.append(subscribe)
                    """
                    uid, avatar, username, fans
                    """

                    try:
                        sql = 'select ownerUid, ownerNickname, fans from live_channels where roomId=%s'%roomId
                        selectResults = dal.executesql(sql)
                        if len(selectResults) > 0:
                            subscribe["uid"] = selectResults[0][0]
                            subscribe["avatar"] = str(selectResults[0][0])+".png"
                            subscribe["username"] = selectResults[0][1]
                            subscribe["fans"] = selectResults[0][2]
                    except Exception, e:
                        raise e

                result["data"] = data

        except Exception, e:
            pass

    return json.dumps(result)



"""
获取当前弹幕热词
"""
def danmaku():
    global hotDanmakus
    parseRequest()

    sql = 'CREATE TABLE IF NOT EXISTS hot_danmakus (content TEXT NOT NULL )'
    dal.executesql(sql)

    result = {}
    result["error"] = 0
    result["msg"] = ""

    danmakuContent = request.vars.get("add", "")
    if len(danmakuContent) > 0:
        sql = 'insert into hot_danmakus (content) VALUES ("%s")'%danmakuContent
        dal.executesql(sql)
    else:
        sql = 'select * from hot_danmakus'
        selectResults = dal.executesql(sql)
        datas = []
        if len(selectResults) > 0:
            for i in selectResults:
                datas.append(i[0])

        result["data"] = datas

    return json.dumps(result)

"""
获取图片
"""
def imgfile():
    filename = request.vars.get("id", "")
    if len(filename) == 0:
        return ""

    print filename
    # redirect(URL("/static/images/cover/"+filename))
    filepath = os.path.join(os.getcwd(), "applications")
    filepath = os.path.join(filepath, "wanketv")
    filepath = os.path.join(filepath, "static")
    filepath = os.path.join(filepath, "images")
    filepath = os.path.join(filepath, "cover")
    filepath = os.path.join(filepath, filename)
    url = "http://192.168.41.101:9257/wanketv/static/images/cover/"+filename
    redirect(url)

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
