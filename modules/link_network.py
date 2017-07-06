from bs4 import BeautifulSoup
import urllib
from urllib import request
import time
import csv
import os
import numpy as np
import time
from argparse import ArgumentParser
import networkx as nx
import matplotlib.pyplot as plt

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

def make_network(root_url, urls):
    entry_url = root_url + "/entry/"
    G = nx.Graph()
    for url in urls:
        article_name= url.replace(entry_url,"").replace("/","-")
        G.add_node(article_name)
    for i,url in enumerate(urls):
        print(i+1,"/",len(urls))
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
            if l in urls:
                linking_article_name = url.replace(entry_url,"").replace("/","-")
                linked_article_name = l.replace(entry_url,"").replace("/","-")
                print("被リンク！{} -> {}".format(linking_article_name, linked_article_name))
                j = urls.index(l)
                G.add_edge(linking_article_name, linked_article_name)
            else: 
                continue
    return G

def visualize(G, savename, savegml):
    pos = nx.spring_layout(G) # グラフ形式を選択。ここではスプリングモデルでやってみる
    nx.draw(G, pos, with_labels=True,alpha=0.3,font_size=0.0,node_size=10) # グラフ描画。 オプションでノードのラベル付きにしている
    plt.savefig(savename+".png")
    plt.show()
    if savegml:
        nx.write_gml(G,savename+".gml")

    
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-u", "--url", type=str, required=True,help="input your url")
    parser.add_argument("-o", "--savename", type=str, default="network", help="output name")
    parser.add_argument('-g', "--savegml", action="store_true", default=False)
    args = parser.parse_args()
    
    urls = extract_url(args.url)
    G = make_network(args.url, urls)
    visualize(G, args.savename, args.savegml)