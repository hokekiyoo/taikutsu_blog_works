from argparse import ArgumentParser
from urllib import request 
from urllib import error
from bs4 import BeautifulSoup
import os
import csv
import json
import datetime
import matplotlib.pyplot as plt

def extract_urls(args):
    page = 1
    is_articles = True
    urls = []
    while is_articles:
        try:
            html = request.urlopen("{}/archive?page={}".format(args.url, page))
        except error.HTTPError as e: 
            # HTTPレスポンスのステータスコードが404, 403, 401などの例外処理
            print(e.reason)
            break
        except error.URLError as e: 
            # アクセスしようとしたurlが無効なときの例外処理
            print(e.reason)
            break
        soup = BeautifulSoup(html, "html.parser")
        articles = soup.find_all("a", class_="entry-title-link")
        for article in articles:
            urls.append(article.get("href"))
        if len(articles) == 0:
            # articleがなくなったら終了
            is_articles = False
        page += 1
    return urls

def make_directories(args):
    directory = args.directory
    if not os.path.exists(directory):
        os.mkdir(directory)
    if args.image:
        if not os.path.exists(directory+"/imgs"):
            os.mkdir(directory+"/imgs")
    if args.graph:
        if not os.path.exists(directory+"/graph"):
            os.mkdir(directory+"/graph")
    if args.hatebu:
        if not os.path.exists(directory+"/hatebu"):
            os.mkdir(directory+"/hatebu")

def articles_to_img(args, url, soup, name):
    """
    各記事内の画像を保存
    - gif, jpg, jpeg, png
    - 記事ごとにフォルダ分けして保存される
    - imgs/{urlの最後の部分}/{0-99}.png
    """
    # ディレクトリの作成
    article_dir = os.path.join(args.directory+"/imgs", name)
    if not os.path.exists(article_dir):
        os.mkdir(article_dir)
    entry = soup.select(".entry-content")[0]
    imgs = entry.find_all("img")
    count=0
    
    
    for img in imgs:
        filename = img.get("src")
        if "ssl-images-amazon" in filename:
            # print("amazon img")
            continue
        # 拡張子チェック
        if filename[-4:] == ".jpg" or filename[-4:] == ".png" or filename[-4:] == ".gif":
            extension = filename[-4:]
            print("\t IMAGE:",filename)
        elif filename[-5:] == ".jpeg":
            extension = filename[-5:]
            print("\t IMAGE:",filename,extension)
        else: 
            continue
        try:
            image_file = request.urlopen(filename)
        except error.HTTPError as e: 
            print("\t HTTPERROR:", e.reason)
            continue
        except error.URLError as e: 
            print("\t URLERROR:", e.reson)
            continue
        # ValueErrorになった場合に試す(httpで始まらないリンクも貼れるっぽい？)
        except ValueError:
            http_file = "http:"+filename
            try: 
                image_file = request.urlopen(http_file)
            except error.HTTPError as e: 
                print("\t HTTPERROR:", e.reason)
                continue
            except error.URLError as e: 
                print("\t URLERROR:", e.reason)
                continue
        # 画像ファイルの保存
        with open(os.path.join(article_dir,str(count)+extension), "wb") as f:
            f.write(image_file.read())
        count+=1

def make_network(G, args, url, urls, soup):
    entry_url = args.url + "/entry/"
    article_name = url.replace(entry_url,"").replace("/","-")
    entry = soup.select(".entry-content")[0]
    links = entry.find_all("a")
    for link in links:
        l = link.get("href")
        if l in urls:
            linked_article_name = l.replace(entry_url,"").replace("/","-")
            print("\t NETWORK: 被リンク！{} -> {}".format(article_name, linked_article_name))
            j = urls.index(l)
            G.add_edge(article_name, linked_article_name)
        else: 
            continue

def url_checker(url, urls):
    #変なリンクは除去したい
    flag1 = "http" in url[:5]     
    #ハテナのキーワードのリンクはいらない
    flag2 = "d.hatena.ne.jp/keyword/" not in url    
    #amazonリンクはダメ
    flag3 = "http://www.amazon.co.jp" not in url and "http://amzn.to/" not in url
    return flag1 and flag2 and flag3


def check_invalid_link(args, urls, url, soup, writer):
    import re
    from urllib.parse import quote_plus
    regex = r'[^\x00-\x7F]' #正規表現    
    entry_url = args.url + "/entry/"
    entry = soup.select(".entry-content")[0]
    links = entry.find_all("a")
    for link in links:
        l = link.get("href")
        if l == None:
            continue
        #日本語リンクは変換
        matchedList = re.findall(regex,l)
        for m in matchedList:
            l = l.replace(m, quote_plus(m, encoding="utf-8"))
        check = url_checker(l, urls)
        if check:
            #リンク切れ検証
            try:
                html = request.urlopen(l)
            except error.HTTPError as e:
                print("\t HTTPError:", l, e.reason)
                if e.reason != "Forbidden":
                    writer.writerow([url,  e.reason, l])
            except error.URLError as e: 
                writer.writerow([url, e.reason, l])                        
                print("\t URLError:", l, e.reason)
            except TimeoutError as e:
                print("\t TimeoutError:",l, e)
            except UnicodeEncodeError as e:
                print("\t UnicodeEncodeError:", l, e.reason)

def get_timestamps(args, url, name):
    """
    はてブのタイムスタンプを取得
    """ 
    plt.figure()
    data = request.urlopen("http://b.hatena.ne.jp/entry/json/{}".format(url)).read().decode("utf-8")
    info = json.loads(data.strip('(').rstrip(')'), "r")
    timestamps = list()
    if info != None: # 公開ブックマークが存在する時に、それらの情報を抽出
        bookmarks=info["bookmarks"]
        title = info["title"]
        for bookmark in bookmarks:
            timestamp = datetime.datetime.strptime(bookmark["timestamp"],'%Y/%m/%d %H:%M:%S')
            timestamps.append(timestamp)
        timestamps = list(reversed(timestamps)) # ブックマークされた時間を保存しておく
    count = len(timestamps) 
    number = range(count)
    if(count!=0):
        first = timestamps[0]
        plt.plot(timestamps,number,"-o",lw=3,color="#444444")
        # 3時間で3
        plt.axvspan(first,first+datetime.timedelta(hours=3),alpha=0.1,color="blue")
        plt.plot([first,first+datetime.timedelta(days=2)],[3,3],"--",alpha=0.9,color="blue",label="new entry")
        # 12時間で15
        plt.axvspan(first+datetime.timedelta(hours=3),first+datetime.timedelta(hours=12),alpha=0.1,color="green")
        plt.plot([first,first+datetime.timedelta(days=2)],[15,15],"--",alpha=0.9, color="green",label="popular entry")
        # ホッテントリ
        plt.plot([first,first+datetime.timedelta(days=2)],[15,15],"--",alpha=0.7, color="red",label="hotentry")        
        plt.xlim(first,first+datetime.timedelta(days=2))
        plt.title(name)
        plt.xlabel("First Hatebu : {}".format(first))
        plt.legend(loc=4)
        plt.savefig(args.directory+"/hatebu/{}.png".format(name))
        plt.close()

def graph_visualize(G, args):
    import networkx as nx
    import numpy as np
    # グラフ形式を選択。ここではスプリングモデルでやってみる
    pos = nx.spring_layout(G)
    # グラフ描画。 オプションでノードのラベル付きにしている
    plt.figure()
    nx.draw(G, pos, with_labels=False, alpha=0.4,font_size=0.0,node_size=10) 
    plt.savefig(args.directory+"/graph/graph.png")
    nx.write_gml(G, args.directory+"/graph/graph.gml")
    # 次数分布描画
    plt.figure() 
    degree_sequence=sorted(nx.degree(G).values(),reverse=True) 
    dmax=max(degree_sequence) 
    dmin =min(degree_sequence)
    kukan=range(0,dmax+2) 
    hist, kukan=np.histogram(degree_sequence,kukan)
    plt.plot(hist,"o-")
    plt.xlabel('degree') 
    plt.ylabel('frequency')
    plt.grid()
    plt.savefig(args.directory+'/graph/degree_hist.png') 
    
def main():
    parser = ArgumentParser()
    parser.add_argument("-u", "--url", type=str, required=True,help="input your url")
    parser.add_argument("-d", "--directory", type=str, required=True,help="output directory")
    parser.add_argument("-i", "--image", action="store_true", default=False, help="extract image file from articles")
    parser.add_argument("-g", "--graph", action="store_true", default=False, help="visualize internal link network")
    parser.add_argument("-l", "--invalid_url", action="store_true", default=False, help="detect invalid links")
    parser.add_argument("-b", "--hatebu", action="store_true", default=False, help="visualize analyzed hatebu graph")   
    args = parser.parse_args()

    urls = extract_urls(args)
    # 保存用ディレクトリ作成
    make_directories(args)
    # 記事リストを作る
    with open (args.directory+"/articles_list.csv", "w") as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(["Article TITLE", "URL","Hatebu COUNT"])
        if args.invalid_url:
            f = open(args.directory+'/invalid_url_list.csv', 'w')
            writer_invalid = csv.writer(f, lineterminator='\n')
            writer_invalid.writerow(["Article URL", "ERROR", "LINK"])        
        if args.graph:
            import networkx as nx
            G = nx.Graph()
            for i, url in enumerate(urls):
                name = url.replace(args.url+"/entry/","").replace("/","-")
                G.add_node(name)
        for i, url in enumerate(urls):
            name = url.replace(args.url+"/entry/","").replace("/","-")
            print("{}/{}".format(i+1,len(urls)), name)
            # 抽出したurlに対して各処理実行
            try:
                html = request.urlopen(url)
            except error.HTTPError as e: 
                print(e.reason)
            except error.URLError as e: 
                print(e.reason)
            soup = BeautifulSoup(html, "html.parser")
            # WordPressならいらない
            data = request.urlopen("http://b.hatena.ne.jp/entry/json/{}".format(url)).read().decode("utf-8")        
            info = json.loads(data.strip('(').rstrip(')'), "r")
            try:
                count = info["count"]
            except TypeError:
                count = 0
            # 記事の名前とurl、はてブを出力
            try:
                writer.writerow([soup.title.text, url, count])
            except UnicodeEncodeError as e:
                # ふざけた文字が入ってる場合はエラー吐くことも
                print(e.reason)
                print("\tArticleWriteWarning この記事のタイトルに良くない文字が入ってます :",url)
                continue
            if args.image:
                if "%" in name:
                    #日本語対応
                    name = str(i)
                articles_to_img(args, url, soup, name)
            if args.graph:
                make_network(G, args, url, urls, soup)
            if args.invalid_url:
                check_invalid_link(args, urls, url, soup, writer_invalid)
            if args.hatebu:
                if "%" in name:
                    #日本語対応
                    name = str(i)
                get_timestamps(args, url, name)
        if args.invalid_url:
            f.close()
        if args.graph:
            graph_visualize(G, args)


if __name__ == '__main__':
    main()