# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
import sys,os
import hatena as htn
from multiprocessing import Process


app = Flask(__name__)

@app.route('/')
def index():
    url_list = htn.data_reader()
    return render_template('index.html' ,url_list=url_list)

@app.route('/analyze')
def analyze():
    #非同期実行
    process = Process(target=htn.analyze_hatebu)
    process.start()
    url_list = htn.data_reader()
    return render_template('index.html' ,url_list=url_list)

@app.route('/favorite')
def favorite():
    url_list = htn.data_reader_favorite()
    return render_template('index.html' ,url_list=url_list)

if __name__ == '__main__':
    #app.run(port=8090,debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)



