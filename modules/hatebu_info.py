#coding:utf-8
from argparse import ArgumentParser
from urllib import request 
import urllib
from bs4 import BeautifulSoup
import json
import datetime
import matplotlib.pyplot as plt

def get_timestamps(url):
    """
    はてブのタイムスタンプを取得
    """ 
    data = request.urlopen("http://b.hatena.ne.jp/entry/json/{}".format(url)).read().decode("utf-8")
    # print(bytes(data).strip(b'(').rstrip(b')'))
    info = json.loads(data.strip('(').rstrip(')'), "r")
    # info = json.loads(bytes(data).strip(b'(').rstrip(b')'), "r")
    timestamps = list()
    if info != None: # 公開ブックマークが存在する時に、それらの情報を抽出
        bookmarks=info["bookmarks"]
        title = info["title"]
        for bookmark in bookmarks:
            timestamp = datetime.datetime.strptime(bookmark["timestamp"],'%Y/%m/%d %H:%M:%S')
            timestamps.append(timestamp)
        timestamps = list(reversed(timestamps)) # ブックマークされた時間を保存しておく
    return info, timestamps

# ページカテゴリ取得
def get_category(url):
    try:
        html = request.urlopen("http://b.hatena.ne.jp/entry/{}".format(url))
        soup = BeautifulSoup(html,"lxml")
        return soup.find("html").get("data-category-name")
    except request.HTTPError as e:
        print(e.reason)
    except request.URLError as e:
        print(e.reason)

#はてブのエントリリストの順位チェック
def rank_checker(url,hatebu_url):
    try:
        html = request.urlopen(hatebu_url)
    except request.HTTPError as e:
        print(e.reason)
    except request.URLError as e:
        print(e.reason)
    soup = BeautifulSoup(html,"lxml")
    a = soup.find("a",href=url)
    if a == None:
        rank = None
    else:
        rank = a.get("data-entryrank")
    return rank

# はてなブログのトップページに乗っているか
def is_hatenatop(url):
    try:
        html = request.urlopen("http://hatenablog.com/")
    except urllib.HTTPError as e:
        print(e.reason)
    except urllib.URLError as e:
        print(e.reason)
    soup = BeautifulSoup(html,"lxml")
    a = soup.find("a",href=url)
    if a is None:
        return False
    return url == a.get("href")

def getdata(url):
    category = get_category(url)
    # カテゴリ新着エントリ
    category_entrylist = "http://b.hatena.ne.jp/entrylist/"+category 
    new_cate = rank_checker(url,category_entrylist) 
    # カテゴリホットエントリ
    category_hotentry = "http://b.hatena.ne.jp/hotentry/"+category 
    hot_cate = rank_checker(url,category_hotentry)
    # 総合新着エントリ
    entrylist = "http://b.hatena.ne.jp/entrylist"
    new_all  = rank_checker(url,entrylist)
    # 総合ホットエントリ
    hotentry = "http://b.hatena.ne.jp/hotentry/"      
    hot_all  = rank_checker(url,hotentry)
    # はてなトップ
    hatena_top = is_hatenatop(url)
    # データまとめ
    string  = "hatebu category entrylist rank  : {}\nhatebu category hotentry rank  : {}\nhatebu overall entrylist rank   : {}\nhatebu overall hotentry rank   : {}\nlisted up to hatenablog toppage : {}"\
    .format(rank_checker(url,category_entrylist),rank_checker(url,category_hotentry),
            rank_checker(url,entrylist),rank_checker(url,hotentry),is_hatenatop(url))
    print(string)
    return string

# プロット
def visualize(info, timestamp, data, label="", dayrange=2,annotate=True):
    plt.xkcd()
    count = len(timestamp)
    number = range(count)
    submit = timestamp[0]
    plt.plot(timestamp,number,"-",lw=3,label=label)
    plt.xlim(submit,submit+datetime.timedelta(days=dayrange))
    if annotate:
        plt.annotate(data,xy=(timestamp[-1], number[-1]), arrowprops=dict(arrowstyle='->'), xytext=(timestamp[-1],5))

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-u", "--url", type=str, required=True,help="input your url")
    args = parser.parse_args()
    # plt.figure(figsize=(10,7))
    entry_info = getdata(args.url)
    hatebu_info, timestamps = get_timestamps(args.url)
    visualize(hatebu_info, timestamps, entry_info, label="optimization")
    plt.legend()
    plt.show()