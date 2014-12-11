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
import bayes
from jubatus.classifier.client import Classifier
from jubatus.classifier.types import LabeledDatum
from jubatus.common import Datum
import requests

reload(sys)
sys.setdefaultencoding("utf-8")


##################################################################
# フィールド
##################################################################

r = re.compile('"(http://cdn-ak.b.st-hatena.com/entryimage/.*?)"')
NO_IMAGE_URL = "http://images-jp.amazon.com/images/G/09/nav2/dp/no-image-no-ciu._SS200_.gif"
OFLD = "mynews/csv/train_data_"
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
    # ファイルの出力

    fout = open(OFLD + user + ".csv","w")
    writer = csv.writer(fout,delimiter=",")
    #writer.writerow(["id","url","user","count","title","imageurl"])
    for t in url_list:
        writer.writerow(t)
    fout.close()
    print 'anylaze finish'

##################################################################
# 分析結果読み込み
##################################################################

def data_reader(mybookmarkflg=False,usr=None):

    user = usr['display_name']
    print user

    path = OFLD + user + ".csv"
    print path
    if not os.path.exists(path):
        return get_rss_data(usr,'popular')

    f = open(path, 'rb')
    data_reader = csv.reader(f)
    temp_list = []
    ret = []
    random_set = Set([])

    cnt = 0
    for i,data in enumerate(data_reader):
        if (mybookmarkflg and data[1] != user):
            continue
        dic = {}
        dic["id"] = data[0]
        dic["uname"] = data[1]
        dic["category"] = data[2]
        dic["title"] = data[3]
        dic["link"] = data[4]
        dic["bookmarkcount"] = data[5]
        dic["imageurl"] = data[6]
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
# 最終更新日時
##################################################################
def get_last_upd_time(usr):
    user = usr['display_name']
    print user

    path = OFLD + user + ".csv"
    if not os.path.exists(path):
        return
    stat = os.stat(path)
    last_modified = stat.st_mtime
    dt = datetime.datetime.fromtimestamp(last_modified)
    print(dt.strftime("%Y-%m-%d %H:%M:%S"))  # Print 2011-05-30 17:48:12

    return dt.strftime("%Y-%m-%d %H:%M:%S")

##################################################################
# データ削除（テスト用）
##################################################################
def del_data(usr):
    user = usr['display_name']
    print user
    path = OFLD + user + ".csv"
    if os.path.exists(path):
        print "delete :" + path
        os.remove(path)
    else:
        print "already delete :" + path


##################################################################
# ユーザ判断追加
##################################################################
def decide_interest(usr,li):
    print 'hatena.decide_interest'

    user = usr['display_name']
    li.update({"id":99999 , "uname":user , "bookmarkcount":1})

    category = 'yes' if li['interestFlg'] == '1' else 'no'
    row = [99999,li['uname'],category,li['title'],li['link'],1,li['imageurl']]

    print row
    path = OFLD + user + ".csv"
    if not os.path.exists(path):
        return
    fout = open(path,"a")
    writer = csv.writer(fout,delimiter=",")
    writer.writerow(row)
    fout.close()
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
# ベイズ
##################################################################
def bayes_data(usr):
    user = usr['display_name']
    print user

    url_list = []
    feed_url = RSS_URL['popular']
    url_list = get_feed_list(feed_url)
    targets = [data["title"] for data in url_list]
    print "targets:%s" %(targets)
    ret = bayes.judge_target(targets)
    print "ret:%s" %(ret)

    ret1 = []
    ret2 = []
    for i in ret:
        print "i:%s" %(i)
        for j in url_list:
            if i[1] == j["title"]:
                if i[0] == 'yes':
                    j["title"] = '［興味あり］' + i[1]
                    ret1.append(j)
                else:
                    j["title"] = '［興味なし］' + i[1]
                    ret2.append(j)
    return ret1,ret2

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
    path = OFLD + user + ".csv"
    fb = open(path, 'rb')
    data_reader = csv.reader(fb)
    for i,data in enumerate(data_reader):
        label = data[2]
        dat = data[3]
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

    #test
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
# メイン
##################################################################

if __name__ == '__main__':
    #analyze_hatebu({"display_name":'junpei0029'})
    #data_reader()
    #get_last_upd_time({"display_name":'junpei0029'})
    bayes_data({"display_name":'junpei0029'})



