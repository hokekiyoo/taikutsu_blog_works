#coding: utf-8
from bs4 import BeautifulSoup
import urllib
from urllib import request
import time
import csv
import os
from argparse import ArgumentParser
import datetime
import json
import numpy as np

def extract_urls(root_url):
    """
    トップページを指定すると、ブログ内に存在するurlをすべて抜き出してくれる
    """
    is_articles = True
    page = 1
    urls = []
    # writer = csv.writer(f, lineterminator='\n') # 改行コード（\n）を指定しておく
    while is_articles:
        try:
            html = request.urlopen("{}/archive?page={}".format(root_url, page))
        except urllib.error.HTTPError as e: 
            # HTTPレスポンスのステータスコードが404, 403, 401などの例外処理
            print(e.reason)
            break
        except urllib.error.URLError as e: 
            # アクセスしようとしたurlが無効なときの例外処理
            print(e.reason)
            break
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.find_all("a",class_="entry-title-link")
        for article in articles:
            urls.append(article.get("href"))
        if len(articles) == 0:
            # articleがなくなったら終了
            is_articles = False
        page += 1
    return urls

def get_bookmarks(url):
    """
    はてブのタイムスタンプを取得
    """ 
    data = request.urlopen("http://b.hatena.ne.jp/entry/json/{}".format(url)).read().decode("utf-8")
    info = json.loads(data.strip('(').rstrip(')'))
    n = 10
    # info = json.loads(bytes(data).strip(b'(').rstrip(b')'), "r")
    try:
        return info["bookmarks"]
    except:
        return 0

def draw_heatmap(data):
    import matplotlib.pyplot as plt
    """
    :param data:二次元配列．入力するデータ
    :param min_value:カラーバーの最小値
    :param max_value:カラーバーの最大値
    """
    # 描画する
    fig, ax = plt.subplots(figsize=(100,100))
    heatmap = ax.pcolor(data, cmap=plt.cm.Blues)
    # ax.set_xticks(np.arange(data.shape[0])+0.5, minor=False)
    # ax.set_yticks(np.arange(data.shape[1])+0.5, minor=False)    
    # ax.invert_yaxis()
    # ax.xaxis.tick_top()
    plt.show()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-u", "--url", type=str, required=True,help="input your url")
    parser.add_argument("-r", "--rank", type=int, required=True,help="input num of related articles")
    parser.add_argument("-s", "--save_matrix", action="store_true", default=False, help="save matrix")
    parser.add_argument("-m", "--heatmap", action="store_true", default=False, help="show heatmap")
    args = parser.parse_args()
    save = args.save_matrix
    heatmap = args.heatmap
    n = args.rank
    urls = extract_urls(args.url)
    # userリスト作成
    users = []
    for url in urls:
        bookmarks = get_bookmarks(url)
        if bookmarks != 0:
            for bookmark in bookmarks:
                user = bookmark["user"]
                if user not in users:
                    users.append(user)
    # bookmark_matrix作成
    M = np.zeros((len(urls),len(users)))
    for i, url in enumerate(urls):
        bookmarks = get_bookmarks(url)
        if bookmarks != 0:
            for bookmark in bookmarks:
                j = users.index(bookmark["user"])
                M[i][j] += 1
    # 保存したければする
    if save:
        with open("data.csv","w") as f:
            writer = csv.writer(f, lineterminator='\n')
            a = ["USER"]
            a.extend(urls)
            writer.writerow(a)
        MT = M.T
        for i, user  in enumerate(users): 
            m = [user]
            m.extend(MT[i])
            with open("data.csv","a") as f:
                writer = csv.writer(f, lineterminator='\n')
                writer.writerow(m)
    # ブクマ一回勢を消す
    MT = M.T
    print(MT.shape)
    MT_filter = []
    for e in MT:
        if e.sum() > 1:
            e /= e.sum()
            MT_filter.append(e)
    MT_filter = np.array(MT_filter)
    M_filter = MT_filter.T
    print(MT_filter.shape)
    # csvにする
    with open("related_articles.csv","w") as f:
        writer = csv.writer(f, lineterminator='\n')
        a = ["original"]
        a.extend(range(n))
        writer.writerow(a)
    confidence = np.zeros(len(M_filter))
    for i, article0 in enumerate(M_filter):
        for j, article1 in enumerate(M_filter):
            a0a1 = np.zeros(len(article0))
            for k,(u0, u1) in enumerate(zip(article0, article1)):
                a0a1[k] = u0*u1
            if article0.sum() == 0:
                confidence[j] = 0
            else:
                confidence[j] = a0a1.sum()/article0.sum() 
        index = confidence.argsort()[::-1]
        print(urls[i])
        related_article = [urls[i]]
        related_num = ["#"]
        # 追加
        for i in index[1:n]:
            related_article.append(urls[i])
            related_num.append(confidence[i])
            print("\t",confidence[i], urls[i])
        with open("related_articles.csv","a") as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(related_article)
            writer.writerow(related_num)
    # confidence heatmap作る
    if heatmap:
        confidences = np.zeros((len(M_filter),len(M_filter)))
        for i, article0 in enumerate(M_filter):
            for j, article1 in enumerate(M_filter):
                a0a1 = np.zeros(len(article0))
                for l,(u0, u1) in enumerate(zip(article0, article1)):
                    a0a1[l] = u0*u1
                if article0.sum() == 0 or i==j:
                    confidences[i][j] = 0
                else:
                    confidences[i][j] = a0a1.sum()/article0.sum() 
        draw_heatmap(confidences)
        print(confidences)
