# -*- coding: utf-8 -*-
import urllib2
import feedparser
import json
import sys,re,time
import csv
from xml.etree.ElementTree import XML
import random
from sets import Set

reload(sys)
sys.setdefaultencoding("utf-8")


##################################################################
# フィールド
##################################################################

r = re.compile('"(http://cdn-ak.b.st-hatena.com/entryimage/.*?)"')
NO_IMAGE_URL = "http://images-jp.amazon.com/images/G/09/nav2/dp/no-image-no-ciu._SS200_.gif"
OFLD = "csv/"
user = "junpei0029"


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
                url_list.append([id,e["link"],user,e["hatena_bookmarkcount"],re.sub("[,\"]","",e["title"]),imageurl]) # url_listの作成（titleのカンマとダブルクォーテーションを置換）
                id += 1
            except:
                pass
        time.sleep(0.05) # アクセス速度の制御


    # 対象urlをブックマークしているユーザの抽出
    user_list = []
    for i, url in enumerate(url_list):
        response = opener.open("http://b.hatena.ne.jp/entry/jsonlite/" + url[1]) # はてなAPIによるブックマーク情報の取得
        content = response.read()
        tmp = json.loads(content) # jsonの解析
        # userリストの作成
        if tmp.get("bookmarks"):
            for b in tmp.get("bookmarks"):
                user_list.append([url[0],b["user"]])
            time.sleep(0.05) # アクセス速度の制御

    # 自分と同じurlをブックマークしている数を集計
    count_user = {}
    for i, (id,uname) in enumerate(user_list):
        if count_user.has_key(uname):
            count_user[uname] += 1
        else:
            count_user[uname] = 1

    # ブックマーク数上位のユーザのブックマークurl情報を取得
    for uname, count in sorted(count_user.items(), key=lambda x:x[1],reverse=True):
        print uname, count
        if uname == user: continue # 自分のidは除く
        # 直近200件のブックマークurlを取得
        for i in range(0,200,20):
            try:
                feed_url = "http://b.hatena.ne.jp/" + uname + "/rss?of=" + str(i) # feed取得用クエリ
            except:
                continue
            response = opener.open(feed_url) # feed情報の取得
            content = response.read()
            feed = feedparser.parse(content) # feed情報の解析
            if feed["entries"] == []:
                break
            for e in feed["entries"]:
                if [e["link"],uname] in [ [tmp[1],tmp[2]] for tmp in url_list]: continue # 過去に取得した情報は除く
                try:
                    m = r.search(e["content"][0]["value"])
                    imageurl = m.group(1) if m.group(1) else ""
                    url_list.append([id,e["link"],uname,e["hatena_bookmarkcount"],re.sub("[,\"]","",e["title"]),imageurl])
                    id += 1
                except:
                    pass
            time.sleep(0.05) # アクセス速度の制御
        if count < 80: break # 同じブックマーク数が100より少ない場合break

    print len(url_list)
    # ファイルの出力

    fout = open(OFLD + user + ".csv","w")
    writer = csv.writer(fout,delimiter=",")
    writer.writerow(["id","url","user","count","title","imageurl"])
    for t in url_list:
        writer.writerow(t)
    fout.close()


##################################################################
# 分析結果読み込み
##################################################################

def data_reader(myfav_flg=False,usr=None):

    user = usr['display_name']
    print user
    f = open(OFLD + user + ".csv", 'rb')
    data_reader = csv.reader(f)
    temp_list = []
    ret = []
    random_set = Set([])

    cnt = 0

    for i,data in enumerate(data_reader):
        if (myfav_flg and data[2] != user) or (not myfav_flg and data[2] == user):
            continue
        dic = {}
        dic["id"] = data[0]
        dic["link"] = data[1]
        dic["uname"] = data[2]
        dic["bookmarkcount"] = data[3]
        dic["title"] = data[4]
        dic["imageurl"] = data[5]
        temp_list.append(dic)
        cnt = cnt + 1

    while len(random_set) <= 30:
        random_set.add(random.randint(1, cnt))

    for i in random_set:
        ret.append(temp_list[i])

    print random_set
    print ret
    return ret

##################################################################
# 分析結果読み込み(自分のお気に入り)
##################################################################
def data_reader_favorite(usr):
    return data_reader(myfav_flg=True,usr=usr)

##################################################################
# メイン
##################################################################

if __name__ == '__main__':
    analyze_hatebu({"display_name":'junpei0029'})
    #data_reader()



