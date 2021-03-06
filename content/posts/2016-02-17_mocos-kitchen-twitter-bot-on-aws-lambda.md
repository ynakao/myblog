+++
Tags = [ 'aws', 'python', 'twitter' ]
date = "2016-02-17"
slug = "mocos-kitchen-twitter-bot-on-aws-lambda"
title = "AWS LambdaでMOCO'Sキッチンの更新情報をつぶやくTwitter Botを動かす"
lastmod = "2018-03-05"
+++

### 2018/03/05 更新

MOCO'sキッチンのサイトの仕様が変更されたため、以下のコードでは動作しなくまりました。bot箇所については[新しい記事](https://blog.yujinakao.com/2018/03/05/mocos-kitchen-twitter-bot-update/)を参考にしてください。AWS Lambdaでの設定はインターフェースの変更などが見受けられますが、おおまかな手順は変わっていません。

---

### はじめに

平日の朝8時頃にMOCO'Sキッチンの本日のメニューをツイートするのが日課です。数年前、オリーブオイルの使い方が奇抜だと注目された時期に見始めたことがきっかけだと思います。

<!--more-->

最近ではブームも一段落してネット上での盛り上がりも落ち着いてきましたが、その頃の名残なのか毎日のメニューを確認することで1日の始まりにリズムが付くような気がします。

日々のつぶやきは開始以来ずっと手動で行っていました。これが意外と面倒です。ブラウザを開いてサイトにアクセス、料理名をコピーしてTwitterアプリを開きツイート作成画面にペースト、ハッシュタグを付けてようやく送信です。この一連の流れを自動化できたら便利だなと今回のTwitter Bot作りを思い立ちました。

特定のサイトから情報を取得してツイートするにはどうすればいいのか思案していると、サーバーでスクリプトを書いてcronで定期的に実行するのが最適ではとの考えに至りました。スクリプトはWebスクレイピングやTwitter関連のライブラリが豊富なPythonで書くのが良さそうです。

簡単なスクリプトですのでわざわざサーバーを使うのは大仰だなと調べていると、去年の10月に[AWS Lambda](https://aws.amazon.com/lambda/)がPythonに対応したとの発表を目にしました([Amazon Web Services ブログ: 【AWS発表】AWS Lambdaのアップデート – Python, VPC, 実行時間の延長, スケジュールなど](http://aws.typepad.com/aws_japan/2015/10/aws-lambda-update-python-vpc-increased-function-duration-scheduling-and-more.html))。さらに[CloudWatch](https://aws.amazon.com/cloudwatch/)と連携させることでcronのような動作も可能とのことです。

せっかくの新機能なので早速利用することにします。~~残念なのはAWS Lambdaの対応するPythonのバージョンが2.7のみだという点で、日本語文字列の処理などに気を使わねばなりません。~~ (17/04/19 追記) 2017年4月18日からPython 3.6が[利用できるよう](https://aws.amazon.com/releasenotes/5198208415517126)になりました。以下、Python 3に対応するよう記述をアップデートしています。Python 2では動作しません。過去の履歴をご覧になりたい場合は[レポジトリ](https://github.com/ynakao/myblog/commits/master/content/posts/2016-02-17_mocos-kitchen-twitter-bot-on-aws-lambda.md)を確認ください。

以上を踏まえて、

- Webページをrequestsで取得
- BeautifulSoupでメニュー名を抜き出す
- Tweepyを使ってそれをつぶやく

という流れのスクリプトをAWS LambdaにアップロードしてCloudWatchで定期的に実行するという方針を取りました。


### 作業手順

#### Bot用のスクリプトを書く

まず、Twitter Botがアカウントにアクセスするためのトークンを取得しておきます。

- [Twitter Application Management](https://apps.twitter.com/)のページを開き適当なTwitterアカウントでログインする。
- `Create New App`をクリックし、アプリ名など必要事項を記入、`Developer Agreement`に同意し、`Create your Twitter application`をクリックする。
- 作成したアプリのステータスページが現れるので、`Keys and Access Tokens`のタブを開く。
- `Consumer Key (API Key)`と`Consumer Secret (API Secret)`をメモしておく。
- ページ下部の`Create my access token`をクリックし、`Access Token`と`Access Token Secret`を発行する。`Accsess Level`が`Read and write`以上になっていることを確認しておく。
- 以上4つのKeyを取得したら、`twitterTokens.py`にディクショナリー形式でスクリプト本体とは別ファイルとして保存する。スクリプトに直接書くとセキュリティがおろそかになることや、取り回しが不便になるためである。

```python
tokens = dict(
    consumer_key =          '******************',
    consumer_secret =       '******************',
    access_token =          '******************',
    access_token_secret =   '******************',
)
```

スクリプト`mocotwi.py`の全容は以下のようになりました。

```python
import requests
import bs4
import datetime
import re
# Load twitter tokens from the external twitterTokens.py file.
# Tokens are in the dictionary named "tokens".
from twitterTokens import tokens
import tweepy

url = 'http://www.ntv.co.jp/zip/mokomichi/index.html'
res = requests.get(url)
moco = bs4.BeautifulSoup(res.text.encode(res.encoding), "html.parser")


# Are there any updates?
def isUpdate():
    utcDelta = 9  # JST timezone
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=utcDelta)
    date = moco.select('.recently time')
    return date[0].attrs['datetime'] == now.strftime('%Y-%m-%d')


def getMenu():
    menuHTML = moco.select('.recently h3')
    menu = menuHTML[0].getText().strip()
    # remove prefix if exists
    remove = re.compile('もこみち流[\s　]+')
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

上から順番に補足します。

```python
from twitterTokens import tokens
```

各モジュールをインポートする際に先ほどのトークンを記述したファイルも読み込みます。

```python
moco = bs4.BeautifulSoup(res.text.encode(res.encoding), "html.parser")
```

`requests`で取得したサイトを`BeautifulSoup`に渡す時に、文字コードが正しくエンコードされていないと後の処理がうまくいきませんでした。ref: [pythonとBeautifulsoupとrequests - adragoonaの日記](http://d.hatena.ne.jp/adragoona/20131109/1383984774)

```python
def isUpdate():
    utcDelta = 9  # JST timezone
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=utcDelta)
    date = moco.select('.recently time')
    return date[0].attrs['datetime'] == now.strftime('%Y-%m-%d')
```

MOCO'Sキッチンのサイトが更新されているか確認します。AWS Lambdaで`datetime.datetime.now()`するとどうやらUTCで動いているようなので、JSTになるよう9時間分進めています。サイト内の日付がスクリプト実行時の日付と同じであれば`True`を返します。

```python
def getMenu():
    menuHTML = moco.select('.recently h3')
    menu = menuHTML[0].getText().strip()
    # remove prefix if exists
    remove = re.compile('もこみち流[\s　]+')
    if remove.match(menu):
        menu = remove.sub('', menu)
    return menu
```

料理名の箇所を抜き出します。HTML要素から`getText()`すると改行の`\n`が付いてきたので`strip()`で削っています。また、頭の「もこみち流　(全角スペース)」の部分を取り除くため続けて削っています。(16/11/07 追記) 全角スペースだけでなく半角が混ざることもあるので正規表現で対応します。さらに、特別企画の際には「もこみち流」が付かない場合もあるので、その表記が含まれているのかどうかも確認します。

そして`tweetMenu()`でトークンを読み込み認証を行い、抽出した料理名にハッシュタグを付けてつぶやかせます。ref: [Authentication Tutorial — tweepy 3.5.0 documentation](http://docs.tweepy.org/en/latest/auth_tutorial.html)

```python
def lambda_handler(event, context):
    if isUpdate():
        tweetMenu()
```

`main`となる関数部分には`lambda_handler(event, context)`というAWS Lambdaが識別できるような関数名をつけます。名称自体は任意に設定可能ですがここでは分かりやすくこのような名前にしました。ref: [Lambda 関数ハンドラー (Python) - AWS Lambda](http://docs.aws.amazon.com/ja_jp/lambda/latest/dg/python-programming-model-handler-types.html)

#### AWS Lambdaを設定する

スクリプトが用意できたのでAWS Lambdaにアップロードします。Lambdaドキュメントにしたがってzipファイルを作ります。ref: [デプロイパッケージの作成 (Python) - AWS Lambda](https://docs.aws.amazon.com/ja_jp/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html)

まず作業用ディレクトリを作り、そこに必要なファイルを置きます。

```nohighlight
$ mkdir mocotwi
$ cd mocotwi
$ tree .
.
├── mocotwi.py
└── twitterTokens.py
```

サードパーティー製のPythonモジュールはAWS Lambdaには用意されていないので、zipファイル内に同梱しなければなりません。`pip`を使って必要なモジュールをカレントディレクトリ内にインストールします。ドキュメントにも記載されていますがMacでHomebrewから導入したPythonを使っている場合、正常にインストールされないので次のファイルを用意しておきます。

```nohighlight
$ cat setup.cfg
[install]
prefix=
// 上のファイルがあるとHomebrew環境下でも正常にインストールされる
$ pip3 install -t . requests beautifulsoup4 tweepy 
// -tオプションでカレントディレクトリ内にインストールするよう指定
```

必要なものが揃ったのでzipファイルを生成します。

```nohighlight
$ zip -r ~/mocotwi.zip *
```

ホームディレクトリに`monotwi.zip`ができました。

ここからAWS Lambdaのコンソール上での作業です。

- [Lambda Management Console](https://console.aws.amazon.com/lambda/home)にログインし、`Get Started Now`(2回目以降は`Create a Lambda function`)をクリック。
- テンプレート一覧が表示される。`Blank Function`を選択する。`Configure triggers`の画面が表示されるが次項で設定するので、ここでは`Next`をクリックし次へ進む。
- `Configure function`内の項目を埋める。`Name`には作成するLambda functionの名前(mocotwiなど)、`Description`にはその説明を入力、`Runtime`ではプルダウンから`Python 3.6`を選択。
- `Lambda function code`の`Code entry type`では`Upload a .ZIP file`を選択する。`Upload`ボタンをクリックし、先ほどの`mocotwi.zip`を指定する。
- `Lambda function handler and role`の`Handler`には`mocotwi.lambda_handler`と入力。トリガーとなるmain関数を呼び出し、`ファイル名.main関数名`の形式をとる。`Role`にはプルダウンから適当なロールを選択するが、初めて利用する場合は存在しない。`Create new role`の`Basic execution role`を選択すれば必要最小限の権限を持ったロールを作成してくれる。
- `Advanced settings`は特に変更せず`Next`をクリック。
- 最終確認の画面が表示されるので確認して`Create function`をクリック。

最後にcronの設定を行います。

- 先の`Create function`後Lambda functionのステータス画面に遷移するので`Triggers`
のタブをクリック。
- `Add trigger`をクリック、さらに空欄になったアイコンをクリックし、プルダウンから`CloudWatch Events - Schedule`を選択。
- `Rule name`、`Rule description`に名前と説明を入力し、`Schedule expression`の項目ではプルダウンメニューから`cron`を選択する。
- 選択した`cron`は書き換えることが可能で、内容を`cron(2 23 ? * SUN-THU *)`に変更する。MOCO'Sキッチン放送後の平日朝8:02(JST)に実行するようにしたいので9時間分巻き戻して、日曜から木曜の23:02(UTC)と設定した。cronの書き方は以下を参照。ref: [スケジュールされたイベントでの AWS Lambda の使用 - AWS Lambda](http://docs.aws.amazon.com/ja_jp/lambda/latest/dg/with-scheduled-events.html)
- `Enable trigger`にチェックが入っていることを確認し`Submit`をクリックする。

以上で全ての作業は終了です。

### さいごに

このBotを今週の初めから動かしていますが今のところ順調に動作しています。つぶやき元となっているTwitterクライアントが表示されるTwitterクライアント(紛らわしい)を持っている方は、ここ数日のMOCO'Sキッチンツイートを見ると`from mocotwi`のようになっているのが確認できると思います。

ただページが更新されなかった場合やメニューの書き方が突然変わった場合など、不測の事態に備えたエラーハンドリングを全くとっていないので、そういうケースに遭遇したら手動で確認しなければなりません。なにかうまく対処できればよいのですが対応策が思い浮かびません。

また気になるお値段ですが、AWS Lambdaの[料金ページ](https://aws.amazon.com/jp/lambda/pricing/)を見ると、

- リクエストのうち毎月最初の 1,000,000 件は無料
- 1 GB/秒の使用につき 0.00001667 USD の料金

とあります。このスクリプトは平日に1回呼び出すだけなので月20回くらいとなり、リクエストに関しては余裕で無料の範囲内に収まると思われます。実行時間にかかる料金は、ログを見たところmocotwiスクリプトの実行時間は700ミリ秒でメモリは128MBの環境で行っているので、

```nohighlight
合計コンピューティング(秒)= 20 × 0.7 = 14秒
合計コンピューティング(GB/秒)= 14 × 128 MB / 1024 = 1.75 GB/秒
1か月のコンピューティング料金= 1.75 × 0.00001667 USD = 0.0000291725 USD
```

となり、これお金かかるのかなという試算になります。どこかに見落としがないか不安ですが、具体的な請求が来たらご報告します。また前回書き忘れていましたが、AWS S3 + CloudFrontでのブログのホスト料金も安く抑えられるはずですので合わせてお知らせできればと思います。

#### 追記(2016/07/05)

遅くなりましたが、2月から6月まで5ヶ月分の請求が来たので内訳をお知らせします。表中の単位は`$`です。また、請求は来ましたが、以前AWSのアンケートに答えて$25分のクーポンを貰っていたので実際に支払った金額はゼロで済みました。定期的にアンケートが行われるので、ひょっとしてずっと貰い続けられるのではと淡く期待しています。

```nohighlight
|          |Feb |Mar |Apr |May |Jun |
|----------|----|----|----|----|----|
|S3        |0.05|0.02|0.02|0.03|0.03|
|CloudFront|0.12|0.16|0.13|0.12|0.15|
|Route 53  |0.51|0.51|0.51|0.51|0.51|
|Total     |0.68|0.69|0.66|0.66|0.69|
```

予想通りAWS Lambdaの料金はかかりませんでした。S3 + CloudFrontを利用したブログのホスト代はだいたい$0.15-0.2くらいでしょうか。Route 53はDNSサービスとして利用しており、1つのドメインにつき1ヶ月$0.5とDNSクエリ代が$0.01かかっていました。信頼性や豊富な機能からAWSのDNSサービスを利用していますが、ドメインを購入する際にレジストラが無料で提供しているところも多いので、それを利用すればさらに費用は抑えられるでしょう。
