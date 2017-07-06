#coding: utf-8
from bs4 import BeautifulSoup
import urllib
from urllib import request
import csv
from argparse import ArgumentParser


def articles_to_csv(url, output):
    is_articles = True
    page = 1
    with open (output, "w") as f:
        writer = csv.writer(f, lineterminator='\n') # 改行コード（\n）を指定しておく
        while is_articles:
            try:
                html = request.urlopen("{}/archive?page={}".format(url, page))
            except urllib.error.HTTPError as e: 
                # HTTPレスポンスのステータスコードが404, 403, 401などの例外処理
                print(e.reson)
                break
            except urllib.error.URLError as e: 
                # アクセスしようとしたurlが無効なときの例外処理
                print(e.reson)
                break
            soup = BeautifulSoup(html, "html.parser")
            articles = soup.find_all("a",class_="entry-title-link")
            for article in articles:
                try:
                    writer.writerow([article.text, article.get("href")])
                except UnicodeEncodeError as e:
                    # ふざけた文字が入ってる場合はエラー吐くことも
                    print(e.reason)
                    print("この記事のタイトルに良くない文字が入ってます :",article.get("href"))
            if len(articles) == 0:
                # articleがなくなったら終了
                is_articles = False
            page += 1
    

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-u", "--url", type=str, required=True,help="input your url")
    parser.add_argument("-o", "--output", type=str, default="articles.csv", help="output csv name")
    args = parser.parse_args()
    articles_to_csv(args.url, args.output)