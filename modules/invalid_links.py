from bs4 import BeautifulSoup
import urllib
from urllib import request
import time
from argparse import ArgumentParser
import csv


def extract_url(root_url):
    page = 1
    is_articles = True
    urls = []
    
    while is_articles:
        html = request.urlopen(root_url+"/archive?page={}".format(page))
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.find_all("a",class_="entry-title-link")
        for article in articles:
            urls.append(article.get("href"))
        if len(articles) == 0:
            # articleがなくなったら終了
            is_articles = False
        page += 1
    return urls

def url_checker(url, urls):
    #変なリンクは除去したい
    flag1 = "http" in url[:5]     
    #ハテナのキーワードのリンクはいらない
    flag2 = "d.hatena.ne.jp/keyword/" not in url    
    #amazonリンクはダメ
    flag3 = "http://www.amazon.co.jp" not in url and "http://amzn.to/" not in url
    return flag1 and flag2 and flag3

def check_invalid_link(root_url, urls, output):
    import re
    regex = r'[^\x00-\x7F]' #正規表現    
    entry_url = root_url + "/entry/"
    with open (output, "w") as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(["URL", "ERROR", "LINK", "STATUS"])
        for i,url in enumerate(urls):
            print(i+1,"/",len(urls),url)
            try:
                html = request.urlopen(url)
            except urllib.error.HTTPError as e: 
                print(e.reason)
            except urllib.error.URLError as e: 
                print(e.reason)
            soup = BeautifulSoup(html, "html.parser")
            entry = soup.select(".entry-content")[0]
            links = entry.find_all("a")
            for link in links:
                l = link.get("href")
                #日本語リンクは変換
                matchedList = re.findall(regex,l)
                for m in matchedList:
                    l = l.replace(m, urllib.parse.quote_plus(m, encoding="utf-8"))
                check = url_checker(l, urls)
                if check:
                    #リンク切れ検証
                    try:
                        html = request.urlopen(l)
                    except urllib.error.HTTPError as e: 
                        writer.writerow([url, "HTTP ERROR", l, e.reason])
                        print("HTTPError:", l, e.reason)
                    except urllib.error.URLError as e: 
                        writer.writerow([url, "URL ERROR", l, e.reason])                        
                        print("URLError:", l, e.reason)
                    except UnicodeEncodeError as e:
                        writer.writerow([url, "UNICODE ENCODE ERROR", l, e.reason])
                        print("UnicodeEncodeError:", l, e.reason)                        
            # time.sleep()

if __name__ == '__main__':
    """
    TODO
    - APIを叩いてなんとかなるやつ実装
        - amazon associateの対応
        - youtubeの削除された動画対応
    """
    parser = ArgumentParser()
    parser.add_argument("-u", "--url", type=str, required=True,help="input your url")
    parser.add_argument("-o", "--output", type=str, default="articles.csv", help="output csv name")
    args = parser.parse_args()
    urls = extract_url(args.url)
    check_invalid_link(args.url, urls, args.output)