# -*- coding: utf-8 -*-
import urllib
import urllib2
import os
from BeautifulSoup import BeautifulSoup


APPID = 'dj0zaiZpPU04TDh6WHptblN1QiZzPWNvbnN1bWVyc2VjcmV0Jng9MDQ-'
PAGEURL = "http://jlp.yahooapis.jp/MAService/V1/parse"

# Yahoo!形態素解析の結果をリストで返します。
def split(sentence, appid=APPID, results="ma", filter="9|10"):
  sentence = sentence.encode("utf-8")
  params = urllib.urlencode({'appid':appid, 'results':results, 'filter':filter,'sentence':sentence})
  results = urllib2.urlopen(PAGEURL, params)
  soup = BeautifulSoup(results.read())

  return [w.surface.string for w in soup.ma_result.word_list]

