+++
Tags = [ 'aws', 'python', 'twitter' ]
date = "2018-03-05"
slug = "mocos-kitchen-twitter-bot-update"
title = "MOCO'SキッチンのTwitter Botをサイトの仕様変更に伴いアップデートする"
+++

[以前の記事](https://blog.yujinakao.com/2016/02/17/mocos-kitchen-twitter-bot-on-aws-lambda/)も参考にしてください。

MOCO'Sキッチンのサイトに仕様変更が行われ、今までのBotでは動作しなくなったため一部を書き換えました。新しいサイトでは更新情報にJSON形式でアクセスできるので、わさわざBeautiful Soupでスクレイピングする必要がなくなりました。

<!--more-->

```python
# twitterTokens.py
tokens = dict(
    consumer_key =          '******************',
    consumer_secret =       '******************',
    access_token =          '******************',
    access_token_secret =   '******************',
)
```

```python
# mocotwi.py
import requests
import json
import datetime
import re
from twitterTokens import tokens
import tweepy

url = 'http://www.ntv.co.jp/zip/mocos/json/latest.json'
res = requests.get(url)
parsed_json = json.loads(res.text)


def isUpdate():
    utcDelta = 9  # JST timezone
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=utcDelta)
    return parsed_json[0]['date'] == now.strftime('%Y.%m.%d')


def getMenu():
    menu = parsed_json[0]['title']
    # remove prefix if exists
    # \s: whitespace and \u3000: fullwidth whitespace
    remove = re.compile('もこみち流[\s\u3000]+')
    if remove.match(menu):
        menu = remove.sub('', menu)
    return menu


def tweetMenu():
    # set tokens
    CONSUMER_KEY = tokens['consumer_key']
    CONSUMER_SECRET = tokens['consumer_secret']
    ACCESS_TOKEN = tokens['access_token']
    ACCESS_TOKEN_SECRET = tokens['access_token_secret']
    # auth process
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    # send tweet
    api.update_status(getMenu() + ' #mocos_kitchen ')


def lambda_handler(event, context):
    if isUpdate():
        tweetMenu()


if __name__ == '__main__':
    lambda_handler(None, None)
```

`http://www.ntv.co.jp/zip/mocos/json/latest.json`から直近数日分のデータを取得できます。日付やメニューを抽出するプロセスが変わっただけで、残りは以前のままです。

あとはAWS Lambdaにzipファイルをアップロードして、CloudWatchで実行するタイミングを設定すれば完了です。AWSもサイトの更新によりインターフェース等の変更がありますが、行うべき内容は変わらないので、そこでの手順は[以前の記事](https://blog.yujinakao.com/2016/02/17/mocos-kitchen-twitter-bot-on-aws-lambda/)をもって割愛します。 
```nohighlight
$ mkdir mocotwi
$ cd mocotwi
$ tee setup.cfg <<EOF
[install]
prefix=
EOF
$ tree .
.
├── mocotwi.py
├── twitterTokens.py
└── setup.cfg
$ pip3 install -t . requests tweepy
$ zip -r ~/mocotwi.zip *
```

AWSのインターフェースが新しくなるたびに操作方法を示すのは煩わしいので、このあたりの設定も将来的にコマンドラインから行えるようにできればと考えています。
