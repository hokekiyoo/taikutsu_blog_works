#coding: utf-8

from bs4 import BeautifulSoup
import urllib
from urllib import request
import time
import csv
import os
from argparse import ArgumentParser

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

def articles_to_img(root_url, urls):
    """
    各記事内の画像を保存
    - gif, jpg, jpeg, png
    - 記事ごとにフォルダ分けして保存される
    - imgs/{urlの最後の部分}/{0-99}.png
    """
    rootdir = "imgs2"
    if not os.path.exists(rootdir):
        os.mkdir(rootdir)
    for i, url in enumerate(urls):
        try:
            html = request.urlopen(url)
        except urllib.error.HTTPError as e: 
            print(e.reason)
        except urllib.error.URLError as e: 
            print(e.reason)
        soup = BeautifulSoup(html, "html.parser")
        # ディレクトリの作成
        dirname = url.replace(root_url+"/entry/","").replace("/","-")
        print(i, dirname)
        article_dir = os.path.join(rootdir, dirname)
        if not os.path.exists(article_dir):
            os.mkdir(article_dir)
        entry = soup.select(".entry-content")[0]
        imgs = entry.find_all("img")
        count=0
        for img in imgs:
            filename = img.get("src")
            # 拡張子チェック
            if filename[-4:] == ".jpg" or filename[-4:] == ".png" or filename[-4:] == ".gif":
                extension = filename[-4:]
                print("\t",filename)
            elif filename[-5:] == ".jpeg":
                extension = filename[-5:]
                print("\t",filename,extension)
            else: 
                continue
            try:
                image_file = request.urlopen(filename)
            except urllib.error.HTTPError as e: 
                print(e.reason)
                continue
            except urllib.error.URLError as e: 
                print("ERROR", e.reson)
                continue
            # 画像ファイルの保存
            with open(os.path.join(article_dir,str(count)+extension), "wb") as f:
                f.write(image_file.read())
            count+=1
        time.sleep(3)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-u", "--url", type=str, required=True,help="input your url")
    args = parser.parse_args()
    urls =  extract_urls(args.url)
    articles_to_img(args.url, urls)