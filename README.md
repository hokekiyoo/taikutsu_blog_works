# ほけきよのかんがえたさいきょうのブログ最適化補助ツール

## Function
1. 記事とURLの一覧表をcsvにする : リライトのチェック用に
1. 自サイトのネットワーク構造を知る : 内部リンク最適化に
1. 画像を抜き出して出力する : 画像圧縮をして高速化する用に
1. はてブがつく初動(2日分)をグラフ化する : 記事のインパクト等の参考に
1. リンク切れを拾う : SEO対策のために

## Requirement
### python
- python3.x (2系ではurllib, エンコードの関係で動かないです)
### libraries

|ライブラリ|用途|
|---|---|
|bs4|スクレイピング|
|numpy|数値計算|
|networkx|グラフ構造作成|
|matplotlib|グラフ出力|

なお、めんどい人はあまり考えずAnacondaでOKです。

WindowsでのAnaconda環境構築はコチラ

[Windows10でちょっとしたpythonコードを使う環境を作る、その① AnacondaとPycharm](http://www.procrasist.com/entry/2016/10/04/200000)

### optional
グラフ描画ソフトがあればなお良し

## How to Use
### 実行
基本的には`all_in_one.py`で上記機能を網羅しています。全部使いたいときは、下記のように入力してください。

```
python all_in_one.py --url http://procrasist.com --directory procrasist --network --image --hatebu --invalid_link
```

または

```
python all_in_one.py -u http://procrasist.com -d procrasist -n -i -b -l
```

それぞれの引数の説明は、`python all_in_one.py -h`と入力すると出てきます。
|引数|意味|
|---|---|
|-u, --url |input your url|
|-d, --directory |output directory|
|-i, --image|extract image file from articles|
|-g, --graph|visualize internal link network|
|-l, --invalid_url|detect invalid links|
|-b, --hatebu|visualize analyzed hatebu graph |

- ※urlとdirectoryは必須です。
- ※その他のオプションは、必要なときにつけるという感じです。

### 出力
下記の様な出力になっている
```
├─taikutsu_blog_works
    ├─all_in_one.py
    └─procrasist
        ├─articles.csv
        ├─invalid_url_list.csv
        ├─graph
        ├─hatebu
        └─imgs
```

### 注意点
- HTTPエラーForbiddenはUser Agentを使えばなんとかなるらしいけど非推奨とかかれていたので省く
    - コンソールにだけだして出力はしない
- amazonリンクはcertificateがいるので省く
- 楽天リンクはAPIの仕様(?)上かなりアクセスに時間がかかる
- はてブ初動解析は、非公開の人のはてブは反映されていないので、実際よりも少ない
- 