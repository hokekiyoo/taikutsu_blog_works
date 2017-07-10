from argparse import ArgumentParser
from urllib import request 
from urllib import error
from bs4 import BeautifulSoup
import os
import csv
import json
import datetime
import time
import matplotlib.pyplot as plt
import requests

def extract_urls(args):
    sitemap = "{}/sitemap.xml".format(args.url)
    r = requests.get(sitemap)
    data = r.text
    soup = BeautifulSoup(data, "lxml")
    url_list = []
    for page in soup.findAll("loc"):
        try:
            r = request.urlopen(page.text)
        except error.HTTPError as e:
            print("\t HTTPError:", e.reason)
        except error.URLError as e: 
            print("\t URLError:",  e.reason)
        soup = BeautifulSoup(r, "lxml")
        for url in soup.findAll("loc"):
            try:
                html = request.urlopen(url.text)
                soup = BeautifulSoup(html,"lxml")
                class_ = soup.find("body").get("class")
                # print(url.text, soup.find("title"). text, class_)
                if class_ != None and "single" in class_:
                    if url.text not in url_list:
                        print(url.text)
                        # if "hoge" in url.text:#階層構造にしている人
                        url_list.append(url.text)                    
            except error.HTTPError as e:
                print("\t HTTPError:", e.reason)
            except error.URLError as e: 
                print("\t URLError:", e.reason)
    return url_list

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
    count = 0
    article_dir = os.path.join(args.directory+"/imgs", name)
    if not os.path.exists(article_dir):
        os.mkdir(article_dir)

    entry = soup.select(".entry-content")[0]
    imgs = entry.find_all("img")
    filenames = []
    for i,img in enumerate(imgs):
        filename = img.get("src")
        # lazy-load対策
        if "lazy-load" in filename:
            filename = img.get("data-lazy-src")
        if "ssl-images-amazon" in filename:
            continue
        # 重複避ける
        if filename in filenames:
            continue
        # 拡張子チェック
        extensions = [".jpg", ".png", ".gif", ".jpeg"]
        for ext in extensions:
            if ext in filename:
                print("\t IMAGE:", filename)
                extension = ext
            else:
                print("\t IMAGE:", filename)
                extension = "jpg"
                continue
        try:
            image_file = request.urlopen(filename)
        except error.HTTPError as e: 
            print("\t HTTPERROR:", e.reason)
            continue
        except error.URLError as e: 
            print("\t URLERROR:", e.reson)
            continue
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
        filenames.append(filename)
        with open(os.path.join(article_dir,"{}.{}".format(i,extension)),"wb") as f:
            f.write(image_file.read())
            count+=1

def make_network(G, args, url, urls, soup):
    entry_url = args.url
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
    #amazon
    flag3 = "www.amazon.co.jp" not in url and "http://amzn.to/" not in url
    #rakuten
    flag4 = "rakuten.co.jp" not in url
    #もしも
    flag5 = "af.moshimo" not in url
    #affiliate B
    flag6 = "track.affiliate-b.com" not in url
    flag = flag1 and flag2 and flag3 and flag4 and flag5 and flag6
    return flag
    

def check_invalid_link(args, urls, url, soup, writer):
    import re
    from urllib.parse import quote_plus
    regex = r'[^\x00-\x7F]' #正規表現    
    entry_url = args.url
    try:
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
    except IndexError:
        print(IndexError)
        
def get_timestamps(args, url, name):
    """
    はてブのタイムスタンプを取得
    """ 
    plt.figure()
    data = request.urlopen("http://b.hatena.ne.jp/entry/json/{}".format(url)).read().decode("utf-8")
    info = json.loads(data.strip('(').rstrip(')'), "r")
    timestamps = list()
    if info != None and "bookmarks" in info.keys(): # 公開ブックマークが存在する時に、それらの情報を抽出
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
    nx.draw_networkx(G, pos, with_labels=False, alpha=0.4,font_size=0.0,node_size=10) 
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
                name = url.replace(args.url,"").replace("/","-")
                G.add_node(name)
        for i, url in enumerate(urls):
            name = url.replace(args.url,"").replace("/","-")
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
                    name = str(i) #日本語対応
                articles_to_img(args, url, soup, name)
            if args.graph:
                make_network(G, args, url, urls, soup)
            if args.invalid_url:
                check_invalid_link(args, urls, url, soup, writer_invalid)
            if args.hatebu:
                if "%" in name:
                    name = str(i) #日本語対応
                get_timestamps(args, url, name)
            # time.sleep(3)
        if args.invalid_url:
            f.close()
        if args.graph:
            graph_visualize(G, args)


if __name__ == '__main__':
    main()