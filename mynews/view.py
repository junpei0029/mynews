# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template
import sys,os
import hatena as htn

app = Flask(__name__)

@app.route('/')
def index():
    url_list = htn.data_reader()
    return render_template('index.html' ,url_list=url_list)

@app.route('/analyze')
def analyze():
    htn.analyze_hatebu()
    url_list = htn.data_reader()
    return render_template('index.html' ,url_list=url_list)

@app.route('/singleproject.html')
def single():
    return render_template('singleproject.html')

if __name__ == '__main__':
    #app.run(port=8090,debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)



