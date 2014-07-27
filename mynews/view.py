# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
import sys,os
import hatena as htn
from multiprocessing import Process
from oauth2 import Token,Consumer,Client
from flask import request,session,redirect,url_for,g
import urlparse
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = 'why would I tell you my secret key?'

if os.environ.get('CONSUMER_KEY') and os.environ.get('CONSUMER_SECRET'):
    CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
    CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')
else:
    import config
    app.config.from_object("config.DevelopConfig")
    CONSUMER_KEY = app.config['CONSUMER_KEY']
    CONSUMER_SECRET = app.config['CONSUMER_SECRET']

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
        user = get_user_inf()
        if not user:
            return redirect(url_for('login'))
        return f(*args,**kwargs)
    return decorated_view

# リクエストトークン取得から認証用URLにリダイレクトするための関数
@app.route('/login')
def login():
    # リクエストトークンの取得
    client = Client(consumer)
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
    return redirect(url_for('index'))
 
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
    user = get_user_inf()
    url_list = htn.data_reader(usr=user)
    return render_template('index.html' ,url_list=url_list,user=user)

@app.route('/analyze')
@login_required
def analyze():
    #非同期実行
    process = Process(target=htn.analyze_hatebu)
    process.start()
#    user = get_user_inf()
#    url_list = htn.data_reader(usr=user)
#    return render_template('index.html' ,url_list=url_list,user=user)

@app.route('/favorite')
@login_required
def favorite():
    user = get_user_inf()
    url_list = htn.data_reader_favorite(usr=user)
    return render_template('index.html' ,url_list=url_list,user=user)


##################################################################
# methods
##################################################################
def get_user_inf():
    user = {}
    access_token = session.get('access_token')
    if access_token:
        # access_tokenなどを使ってAPIにアクセスする
        token = Token(access_token['oauth_token'], access_token['oauth_token_secret'])
        client = Client(consumer, token)
        resp, content = client.request('http://n.hatena.com/applications/my.json')
        print content
        print resp
        user = json.loads(content)
    return user

##################################################################
# メイン
##################################################################
if __name__ == '__main__':
    #app.run(port=8090,debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port,debug=True)
    #app.run(host='0.0.0.0', port=port)



