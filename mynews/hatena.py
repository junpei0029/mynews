# -*- coding: utf-8 -*-
from urllib import urlencode
import urllib2
import feedparser
import json
import sys,re,time
import csv
from xml.etree.ElementTree import XML
import random
from sets import Set
import os
import datetime
from jubatus.classifier.client import Classifier
from jubatus.classifier.types import LabeledDatum
from jubatus.common import Datum
import MySQLdb
from MySQLdb.cursors import DictCursor

reload(sys)
sys.setdefaultencoding("utf-8")

#DATABASE_HOST = 'www8079up.sakura.ne.jp'
#DATABASE_HOST = '153.121.74.93'
DATABASE_HOST = 'localhost'

##################################################################
# フィールド
##################################################################

r = re.compile('"(http://cdn-ak.b.st-hatena.com/entryimage/.*?)"')
NO_IMAGE_URL = "http://images-jp.amazon.com/images/G/09/nav2/dp/no-image-no-ciu._SS200_.gif"
user = "junpei0029"
RSS_URL = {'popular':'http://feeds.feedburner.com/hatena/b/hotentry',
            'it':'http://b.hatena.ne.jp/hotentry/it.rss',
            'knowledge':'http://b.hatena.ne.jp/hotentry/knowledge.rss',
            'life':'http://b.hatena.ne.jp/hotentry/life.rss',
            'social':'http://b.hatena.ne.jp/hotentry/social.rss',
            'fun':'http://b.hatena.ne.jp/hotentry/fun.rss',
            'entertainment':'http://b.hatena.ne.jp/hotentry/entertainment.rss',
            'game':'http://b.hatena.ne.jp/hotentry/game.rss',
            }


##################################################################
# データ分析
##################################################################

def analyze_hatebu(usr=None):

    user = usr['display_name']

    # Web情報取得の準備
    opener = urllib2.build_opener()

    # はてなブックマークのfeed情報の取得
    url_list = []
    id = 0
    for i in range(0,300,20):
        feed_url = "http://b.hatena.ne.jp/" + user + "/rss?of=" + str(i) # はてなAPIに渡すクエリの作成
        try:
            response = opener.open(feed_url) # urlオープン
        except:
            continue
        content = response.read() # feed情報の取得
        feed = feedparser.parse(content) # feedパーサを用いてfeedを解析
        # entriesがない場合break
        if feed["entries"] == []:
            break
        # urlリストの作成
        for e in feed["entries"]:
            try:
                m = r.search(e["content"][0]["value"])
                imageurl = m.group(1) if m.group(1) else NO_IMAGE_URL
                url_list.append([id,user,'yes',re.sub("[,\"]","",e["title"]),e["link"],e["hatena_bookmarkcount"],imageurl]) # url_listの作成（titleのカンマとダブルクォーテーションを置換）
                id += 1
            except:
                pass
        time.sleep(0.03) # アクセス速度の制御


    # 対象urlをブックマークしているユーザの抽出
#    user_list = []
#    for i, url in enumerate(url_list):
#        response = opener.open("http://b.hatena.ne.jp/entry/jsonlite/" + url[1]) # はてなAPIによるブックマーク情報の取得
#        content = response.read()
#        tmp = json.loads(content) # jsonの解析
#        # userリストの作成
#        if tmp.get("bookmarks"):
#            for b in tmp.get("bookmarks"):
#                user_list.append([url[0],b["user"]])
#            time.sleep(0.05) # アクセス速度の制御
#
#    # 自分と同じurlをブックマークしている数を集計
#    count_user = {}
#    for i, (id,uname) in enumerate(user_list):
#        if count_user.has_key(uname):
#            count_user[uname] += 1
#        else:
#            count_user[uname] = 1
#
#    # ブックマーク数上位のユーザのブックマークurl情報を取得
#    for uname, count in sorted(count_user.items(), key=lambda x:x[1],reverse=True):
#        print uname, count
#        if uname == user: continue # 自分のidは除く
#        # 直近200件のブックマークurlを取得
#        for i in range(0,200,20):
#            try:
#                feed_url = "http://b.hatena.ne.jp/" + uname + "/rss?of=" + str(i) # feed取得用クエリ
#            except:
#                continue
#            response = opener.open(feed_url) # feed情報の取得
#            content = response.read()
#            feed = feedparser.parse(content) # feed情報の解析
#            if feed["entries"] == []:
#                break
#            for e in feed["entries"]:
#                if [e["link"],uname] in [ [tmp[1],tmp[2]] for tmp in url_list]: continue # 過去に取得した情報は除く
#                try:
#                    m = r.search(e["content"][0]["value"])
#                    imageurl = m.group(1) if m.group(1) else ""
#                    url_list.append([id,e["link"],uname,e["hatena_bookmarkcount"],re.sub("[,\"]","",e["title"]),imageurl])
#                    id += 1
#                except:
#                    pass
#            time.sleep(0.05) # アクセス速度の制御
#        if count < 80: break # 同じブックマーク数が100より少ない場合break

    print len(url_list)
    
    #DB登録
    batchinsert_interrest_blog(url_list)
    print 'anylaze finish'

##################################################################
# 分析結果読み込み
##################################################################

def data_reader(mybookmarkflg=False,usr=None):

    user = usr['display_name']
    print user

    temp_list = []
    ret = []
    random_set = Set([])

    data_reader = select_Interrest_Blog(user)
    if not data_reader:
        return get_rss_data(usr,'popular')

    cnt = 0
    for data in data_reader:
        if (mybookmarkflg and data["USER_NAME"] != user):
            continue
        dic = {}
        dic["id"] = data["INTERREST_ID"]
        dic["uname"] = data["USER_NAME"]
        dic["category"] = data["CATEGORY"]
        dic["title"] = data["TITLE"]
        dic["link"] = data["LINK"]
        dic["bookmarkcount"] = data["BOOKMARKCOUNT"]
        dic["imageurl"] = data["IMAGEURL"]
        temp_list.append(dic)
        cnt = cnt + 1

    print cnt

    while len(random_set) <= 30:
        random_set.add(random.randint(1, cnt-1))

    for i in random_set:
        if len(temp_list) > i:
            ret.append(temp_list[i])

    print random_set
    print ret
    return ret


##################################################################
# 分析結果読み込み(自分のお気に入り)
##################################################################
def data_reader_bookmark(usr):
    return data_reader(mybookmarkflg=True,usr=usr)


##################################################################
# ユーザ判断追加
##################################################################
def decide_interest(usr,li):
    print 'hatena.decide_interest'
    user = usr['display_name']
    category = 'yes' if li['interestFlg'] == '1' else 'no'
    insert_interrest_blog(user,category,li['title'],li['link'],1,li['imageurl'])

    return data_reader(usr=usr)

##################################################################
# rss記事取得
##################################################################
def get_rss_data(usr,category):
    user = usr['display_name']
    print user

    url_list = []
    id = 0
    feed_url = RSS_URL[category]
    url_list = get_feed_list(feed_url)

    return url_list


##################################################################
# rss記事取得(複数)
##################################################################
def get_rss_data_from_catlist(usr,category_list):
    url_list = []

    for cat in category_list:
        url_list.extend(get_rss_data(usr,cat))
        time.sleep(0.01) # アクセス速度の制御

    return url_list


##################################################################
# jubatus
##################################################################
def parse_args():
    from optparse import OptionParser, OptionValueError
    p = OptionParser()
    p.add_option('-s', '--server_ip', action='store',
                 dest='server_ip', type='string', default='127.0.0.1')
    p.add_option('-p', '--server_port', action='store',
                 dest='server_port', type='int', default='9199')
    p.add_option('-n', '--name', action='store',
                 dest='name', type='string', default='tutorial')
    return p.parse_args()

def get_most_likely(estm):
    ans = None
    prob = None
    result = {}
    result[0] = ''
    result[1] = 0
    for res in estm:
        if prob == None or res.score > prob :
            ans = res.label
            prob = res.score
            result[0] = ans
            result[1] = prob
    return result

def get_classify_data(usr):

    user = usr['display_name']
    print user

    options, remainder = parse_args()
    classifier = Classifier(options.server_ip,options.server_port, options.name, 10.0)

    #train
    data_reader = select_Interrest_Blog(user)
    for row in data_reader:
        label = row['CATEGORY']
        dat = row['TITLE']
        datum = Datum({"message": dat})
        classifier.train([LabeledDatum(label, datum)])


    url_list = []
    url_list = get_rss_data_from_catlist(usr,['social','fun','entertainment','game'])
    for data in url_list:
        title = data["title"]
        datum = Datum({"message": title})
        classifier.train([LabeledDatum('no', datum)])

#    print classifier.get_status()
#    print classifier.save("tutorial")
#    print classifier.load("tutorial")
#    print classifier.get_config()

    url_list = []
    ret1 = []
    ret2 = []
    url_list = get_rss_data_from_catlist(usr,['it','popular','life','knowledge'])
    for data in url_list:
        title = data["title"]
        datum = Datum({"message": title})
        ans = classifier.classify([datum])
        if ans != None:
            estm = get_most_likely(ans[0])
            if estm[0] == 'yes':
                ret1.append(data)
            else:
                ret2.append(data)

    print ret1
    print ""
    print ret2

    return ret1,ret2

##################################################################
# フィード取得
##################################################################
def get_feed_list(feed_url):

    url_list = []
    id = 0

    # Web情報取得の準備
    opener = urllib2.build_opener()
    response = opener.open(feed_url) # urlオープン
    content = response.read() # feed情報の取得
    feed = feedparser.parse(content) # feedパーサを用いてfeedを解析

    # urlリストの作成
    for e in feed["entries"]:
        try:
            m = r.search(e["content"][0]["value"])
            imageurl = m.group(1) if m.group(1) else NO_IMAGE_URL
            dic = {}
            dic["id"] = id
            dic["title"] = re.sub("[,\"]","",e["title"])
            dic["link"] = e["link"]
            dic["uname"] = user
            dic["bookmarkcount"] = e['hatena_bookmarkcount']
            dic["imageurl"] = imageurl
            url_list.append(dic)
            id += 1
        except:
            pass

    return url_list

##################################################################
# DB接続
##################################################################

def db_connect():
    con = MySQLdb.connect(host=DATABASE_HOST, db='mynews', user='root', passwd='root')
    return con

def db_close(con):
    con.close()

def select_Interrest_Blog(user):
    con = db_connect();
    sql = """
        SELECT
            *
        FROM INTERREST_BLOG IB
        WHERE IB.USER_NAME = '%s'
        ;
    """ % user
    try:
        cur = con.cursor(DictCursor)                       # connectionから取得したcursorからsqlを発行する
        print cur.execute(sql)                             # executeは行数を返却
        res = cur.fetchall()                               # fetchone, fetchmany, fetchallで結果取得
        return res
    finally:
        cur.close()
        db_close(con)
    return []

def insert_interrest_blog(user,category,title,link,bookmarkcount,imageurl):
    print_with_time('insert_interrest_blog start')
    con = db_connect();
    sql = u"""
        INSERT INTO INTERREST_BLOG (
            USER_NAME
            ,CATEGORY
            ,TITLE
            ,LINK
            ,BOOKMARKCOUNT
            ,IMAGEURL
            ,TOROKU_DATE
        )
        VALUES('%s','%s','%s','%s','%s','%s','%s')
        ;
    """ % (user,category,title,link,bookmarkcount,imageurl,datetime.datetime.now())
    with con as cur:
        cur.execute(sql)
    con = db_connect();
    print_with_time('insert_interrest_blog end')

def batchinsert_interrest_blog(feed_list):
    con = db_connect();

    try:
        for li in feed_list:
            cur = con.cursor()
            sql = """
                INSERT INTO INTERREST_BLOG (
                    USER_NAME
                    ,CATEGORY
                    ,TITLE
                    ,LINK
                    ,BOOKMARKCOUNT
                    ,IMAGEURL
                    ,TOROKU_DATE
                )
                VALUES('%s','%s','%s','%s','%s','%s','%s')
                ;
            """ % (li[1],li[2],li[3],li[4],li[5],li[6],datetime.datetime.now())
            cur.execute(sql)
            cur.close()
    finally:
        con.commit()
        cur.close()
        db_close(con)



##################################################################
# ブックマーク登録
##################################################################
def add_bookmark(feed_url,access_token):

    #url = u'http://api.b.hatena.ne.jp/1/my/bookmark'
    url = 'http://b.hatena.ne.jp/junpei0029/add.confirm'

    oauth_token = access_token['oauth_token']
    oauth_token_secret = access_token['oauth_token_secret']

    #post_data = {'url':feed_url, 'oauth_token':oauth_token,'oauth_token_secret':oauth_token_secret}
    post_data = {'url':feed_url}
    data = urlencode(post_data)

    return url + '?' + data

#    print data
#    r = requests.get(url, data=data)
#    #r.add_header('Authorization', 'Bearer %s' % access_token)
#    print r.text




    # Web情報取得の準備
#    params = urllib.urlencode({'url':feed_url, 'oauth_token':oauth_token,'oauth_token_secret':oauth_token_secret})
#    response = urllib.urlopen(url, params)
#    print response
#    the_page = response.read()
#    print the_page


##################################################################
# 標準出力（タイムスタンプ付き）
##################################################################
def print_with_time(content):
    print str(datetime.datetime.now()) + ' : '+ str(content)
    

##################################################################
# メイン
##################################################################

if __name__ == '__main__':
    #analyze_hatebu({"display_name":'junpei0029'})
    #data_reader()
    #get_last_upd_time({"display_name":'junpei0029'})
    bayes_data({"display_name":'junpei0029'})



