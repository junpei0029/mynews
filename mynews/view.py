# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
import sys,os
import hatena as htn
from multiprocessing import Process
from oauth2 import Token,Consumer,Client
from flask import request,session,redirect,url_for,g,jsonify
import urlparse
import json
from functools import wraps

import smtplib
from email.MIMEText import MIMEText
from email.Header import Header
from email.Utils import formatdate
from smtplib import SMTP_SSL
from datetime import datetime as dt

app = Flask(__name__)
app.secret_key = 'why would I tell you my secret key?'

import config
app.config.from_object("config.DevelopConfig")
CONSUMER_KEY = app.config['CONSUMER_KEY']
CONSUMER_SECRET = app.config['CONSUMER_SECRET']
FROM_MAIL_ADDRESS = app.config['FROM_MAIL_ADDRESS']
FROM_MAIL_PASSWORD = app.config['FROM_MAIL_PASSWORD']

#hatenaOauth
REQUEST_TOKEN_URL = 'https://www.hatena.com/oauth/initiate'
ACCESS_TOKEN_URL = 'https://www.hatena.com/oauth/token'
AUTHENTICATE_URL = 'https://www.hatena.ne.jp/oauth/authorize'
SCOPE = 'read_public'

consumer = Consumer(CONSUMER_KEY, CONSUMER_SECRET)

##################################################################
# 認証
##################################################################
def login_required(f):
    @wraps(f)
    def decorated_view(*args,**kwargs):
        print 'login_required'
        if not g.user:
            return redirect(url_for('login'))
        return f(*args,**kwargs)
    return decorated_view

@app.before_request
def load_user():
    user = get_user_inf()
    if user:
        g.user = user
    else :
        g.user = None


# リクエストトークン取得から認証用URLにリダイレクトするための関数
@app.route('/login')
def login():
    # リクエストトークンの取得
    client = Client(consumer)
    print "client : %s" %client
    resp, content = client.request('%s?scope=%s&oauth_callback=%s%s' % \
            (REQUEST_TOKEN_URL, SCOPE, request.host_url,'on-auth'))
    # セッションへリクエストトークンを保存しておく
    session['request_token'] = dict(urlparse.parse_qsl(content))
    # 認証用URLにリダイレクトする
    return redirect('%s?oauth_token=%s' % (AUTHENTICATE_URL, session['request_token']['oauth_token']))

# セッションに保存されたトークンを破棄しログアウトする関数
@app.route('/logout')
def logout():
    if session.get('access_token'):
        session.pop('access_token')
    if session.get('request_token'):
        session.pop('request_token')
    return redirect(url_for('login'))
 
# 認証からコールバックされ、アクセストークンを取得するための関数
@app.route('/on-auth')
def on_auth():
    # リクエストトークンとverifierを用いてアクセストークンを取得
    request_token = session['request_token']
    token = Token(request_token['oauth_token'], request_token['oauth_token_secret'])
    token.set_verifier(request.args['oauth_verifier'])
    client = Client(consumer, token)
    resp, content = client.request(ACCESS_TOKEN_URL)
    # アクセストークンをセッションに記録しておく
    session['access_token'] = dict(urlparse.parse_qsl(content)) 
    return redirect(url_for('index'))

##################################################################
# url_routing
##################################################################
@app.route('/')
@login_required
def index():
    print "index start"
    user = g.user
    last_upd_time = htn.get_last_upd_time(user)
    url_list = htn.data_reader(usr=user)
    return render_template('index.html' ,url_list=url_list,user=user,last_upd_time=last_upd_time)

@app.route('/analyze')
@login_required
def analyze():
    print "analyze start"
    #非同期実行
    user = g.user
    process = Process(target=htn.analyze_hatebu,args=(user,))
    process.start()
    last_upd_time = htn.get_last_upd_time(user)
    url_list = htn.data_reader(usr=user)
    return render_template('index.html' ,url_list=url_list,user=user,last_upd_time=last_upd_time)

@app.route('/bookmark')
@login_required
def bookmark():
    print "bookmark start"
    user = g.user
    last_upd_time = htn.get_last_upd_time(user)
    url_list = htn.data_reader_bookmark(usr=user)
    return render_template('index.html' ,url_list=url_list,user=user,last_upd_time=last_upd_time)

@app.route('/favorite')
@login_required
def favorite():
    print "favorite start"
    user = g.user
    last_upd_time = htn.get_last_upd_time(user)
    #url_list,url_list_2 = htn.bayes_data(usr=user)
    url_list,url_list_2 = htn.get_classify_data(usr=user)
    print url_list_2
    return render_template('index.html' ,url_list=url_list,url_list_2=url_list_2,user=user,last_upd_time=last_upd_time)

@app.route('/del_data')
@login_required
def del_data():
    print "del_data start"
    user = g.user
    htn.del_data(usr=user)
    return render_template('index.html' ,user=user)

@app.route('/rss/<path:category>')
@login_required
def rss(category):
    print "rss start"
    user = g.user
    last_upd_time = htn.get_last_upd_time(user)
    url_list = htn.get_rss_data(usr=user,category=category)
    return render_template('index.html' ,url_list=url_list,user=user,last_upd_time=last_upd_time)

@app.route('/decide_interest',methods=['POST'])
@login_required
def decide_interest():
    print "decide_interest start"
    json_data = json.loads(request.data)
    interestFlg=json_data['interestFlg']
    title=json_data['title']
    link=json_data['link']
    imageurl=json_data['imageurl']
    user = g.user
    last_upd_time = htn.get_last_upd_time(user)
    url_list = htn.decide_interest(usr=user,li=json_data)
    return render_template('index.html' ,url_list=url_list,user=user,last_upd_time=last_upd_time)

@app.route('/favorite/<user_id>', methods=['GET'])
def read(user_id):

    print "favorite/%s start" % user_id
    user = {'display_name':user_id}
    url_list,url_list_2 = htn.get_classify_data(usr=user)
    mailtext = createMailText(url_list)

    tdatetime = dt.now()
    tstr = tdatetime.strftime('%Y/%m/%d')

    mailheader = u'Link %s'% (tstr)
    from_addr = "junpei.k.29@gmail.com"
    to_addr = "junpei.k.29@gmail.com"

    msg = create_message(from_addr, to_addr, mailheader, mailtext, 'UTF-8')
    print "create_message finish"
    send_via_gmail(from_addr, to_addr, msg)
    print "favorite/%s finish" % user_id

    response = jsonify({"url_list":url_list})
    response.status_code = 200
    return response

##################################################################
# methods
##################################################################
def get_user_inf():
    user = {}
    access_token = session.get('access_token')
    print access_token
    if access_token:
        # access_tokenなどを使ってAPIにアクセスする
        token = Token(access_token['oauth_token'], access_token['oauth_token_secret'])
        client = Client(consumer, token)
        resp, content = client.request('http://n.hatena.com/applications/my.json')
        if content != 'oauth_problem=token_rejected':
            user = json.loads(content)
    return user

def createMailText(url_list):
    text = u"""<h2>あなたのおすすめ記事</h2>
    """
    for i in url_list:
        text = text + (u"""<a href="%s"><p>%s</p></a>
            """) % (i["link"],i["title"])
    return text

def create_message(from_addr, to_addr, subject, body, encoding):
    # 'text/plain; charset="encoding"'というMIME文書を作ります
    msg = MIMEText(body, 'html', encoding)
    msg['Subject'] = Header(subject, encoding)
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Date'] = formatdate()
    return msg

def send_via_gmail(from_addr, to_addr, msg):
    print "send via SSL..."
    s = SMTP_SSL('smtp.gmail.com', 465)
    s.login(FROM_MAIL_ADDRESS, FROM_MAIL_PASSWORD)
    s.sendmail(from_addr, [to_addr], msg.as_string())
    s.close()
    print 'mail sent!'

##################################################################
# メイン
##################################################################
if __name__ == '__main__':
    #app.run(port=8090,debug=True)
    #port = int(os.environ.get("PORT", 5000))
    #app.run(host='0.0.0.0', port=port,debug=True)
    port = int(os.environ.get("PORT", 60000))
    app.run(host='153.121.74.93', port=port,debug=False)

