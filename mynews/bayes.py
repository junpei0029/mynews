#coding:utf-8
import numpy as np
import sys
import math
import csv
from collections import defaultdict
#yahoo!形態素解析
import morphological

class NaiveBayes:
    """Multinomial Naive Bayes"""
    def __init__(self):
        self.categories = set()     # カテゴリの集合
        self.vocabularies = set()   # ボキャブラリの集合
        self.wordcount = {}         # wordcount[cat][word] カテゴリでの単語の出現回数
        self.catcount = {}          # catcount[cat] カテゴリの出現回数
        self.denominator = {}       # denominator[cat] P(word|cat)の分母の値

    def train(self, data):
        """ナイーブベイズ分類器の訓練"""
        # 文書集合からカテゴリを抽出して辞書を初期化
        for d in data:
            cat = d[0]
            self.categories.add(cat)
        for cat in self.categories:
            self.wordcount[cat] = defaultdict(int)
            self.catcount[cat] = 0
        # 文書集合からカテゴリと単語をカウント
        for d in data:
            cat, doc = d[0], d[1:]
            self.catcount[cat] += 1
            for word in doc:
                self.vocabularies.add(word)
                self.wordcount[cat][word] += 1
        # 単語の条件付き確率の分母の値をあらかじめ一括計算しておく（高速化のため）
        for cat in self.categories:
            self.denominator[cat] = sum(self.wordcount[cat].values()) + len(self.vocabularies)

    def classify(self, doc):
        """事後確率の対数 log(P(cat|doc)) がもっとも大きなカテゴリを返す"""
        best = None
        max = -sys.maxint
        for cat in self.catcount.keys():
            p = self.score(doc, cat)
            if p > max:
                max = p
                best = cat
        return best

    def wordProb(self, word, cat):
        """単語の条件付き確率 P(word|cat) を求める"""
        # ラプラススムージングを適用
        # wordcount[cat]はdefaultdict(int)なのでカテゴリに存在しなかった単語はデフォルトの0を返す
        # 分母はtrain()の最後で一括計算済み
        return float(self.wordcount[cat][word] + 1) / float(self.denominator[cat])

    def score(self, doc, cat):
        """文書が与えられたときのカテゴリの事後確率の対数 log(P(cat|doc)) を求める"""
        total = sum(self.catcount.values())  # 総文書数
        score = math.log(float(self.catcount[cat]) / total)  # log P(cat)
        for word in doc:
            # logをとるとかけ算は足し算になる
            score += math.log(self.wordProb(word, cat))  # log P(word|cat)
        return score

    def __str__(self):
        total = sum(self.catcount.values())  # 総文書数
        return "documents: %d, vocabularies: %d, categories: %d" % (total, len(self.vocabularies), len(self.categories))

def getwords(doc):
    words = [s.lower() for s in morphological.split(doc)]
    return tuple(w for w in words)

def get_train_data():
    f = open('mynews/csv/traindata.csv', 'rb')
    data_reader = csv.reader(f)
    ret = []
    for i,data in enumerate(data_reader):
        li = [data[0], data[1]]
        ret.append(li)
    return ret

def convert_data(pre_data):
    retlist = []
    for li in pre_data:
        tmp = []
        tmp.append(unicode(li[0], 'utf_8'))
        tmp.extend(getwords(unicode(li[1], 'utf_8')))
        retlist.append(tmp)
    return retlist

def judge_target(targets):
    ret_list = []
    data = convert_data(get_train_data())
    # ナイーブベイズ分類器を訓練
    nb = NaiveBayes()
    nb.train(data)
    print nb

    for target in targets:
        temp_list = []
        test = getwords(target)
        temp_list.append(nb.classify(test))
        temp_list.append(target)
        ret_list.append(temp_list)

    for i in ret_list:
        print i[1]
        print  u"興味あり" if i[0] == 'yes' else u"興味なし"

    return ret_list

if __name__ == "__main__":
#    data2 = [["yes", "python", "java", "sql"],
#            ["yes", "java", "scala", "vim"],
#            ["yes", "shell", "python"],
#            ["yes", "python", "lisp", "vim"],
#            ["no", "go", "Ruby", "C#"],
#            ["no", "centos", "swift", "C#"]]

    # テストデータのカテゴリを予測
    targets = [u"Google ウェブマスター向け公式ブログ: HTTPS をランキング シグナルに使用します",u"コミュニケーション能力の鍛え方を教えて欲しい"]
    target = u"Google ウェブマスター向け公式ブログ: HTTPS をランキング シグナルに使用します"

    judge_target(targets)

