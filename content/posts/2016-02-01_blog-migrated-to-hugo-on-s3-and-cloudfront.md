+++
Tags = [ "hugo", "aws", ]
date = "2016-02-01"
slug = "blog-migrated-to-hugo-on-s3-and-cloudfront"
title = "HugoをS3+CloudFront上にSSLでホストする"
lastmod = "2017-04-25"
+++

### はじめに

随分と更新を放置していましたが、今回ブログの構築方法を大幅に刷新したので備忘録も兼ねて変更点などを記します。

<!--more-->

最初にこのブログを始めたときはVPS上で[WordPress](https://wordpress.org/)を使っていましたが、しばらくしてPHPとMySQLの管理が面倒になったので[Ghost](https://ghost.org/)を試しました。WordPressもそうですが、基本的に両者ともブラウザ上で下書きを作成するためレスポンスがあまり良くない場合があります。また当時Ghostは開発初期だったので機能が乏しくカスタマイズも難しいところがありました。

そんなとき耳にしたのが静的サイトジェネレーターです。MarkdownなどのテキストファイルからHTMLを生成しインターネット上に公開するだけなのでデータベースの作成も必要ありません。さらに、プレーンテキストで下書きが保存されるためGitなどを用いたバージョン管理も容易です。

そうしてしばらく[Pelican](http://blog.getpelican.com/)を使っていましたが、それでもWebサーバーの保守は避けられません。なにか楽な方法はないものかと調べていると[Amazon S3](https://aws.amazon.com/s3/)を使って静的サイトをホスティングできるという記事[[1](https://bryce.fisher-fleig.org/blog/setting-up-ssl-on-aws-cloudfront-and-s3/), [2](http://knightlab.northwestern.edu/2015/05/21/implementing-ssl-on-amazon-s3-static-websites/)]を目にしました。また、[CloudFront](https://aws.amazon.com/cloudfront/)を併用することで自分の用意したSSL証明書を使ってセキュアな通信も可能とあり魅力的です。

そして先日、Amazonから無料でSSL証明書を発行できるサービスが発表されました([Amazon Web Services ブログ: AWS Certificate Manager – AWS上でSSL/TLSベースのアプリケーションを構築](http://aws.typepad.com/aws_japan/2016/01/new-aws-certificate-manager-deploy-ssltls-based-apps-on-aws.html))。[Let's Encrypt](https://letsencrypt.org/)を利用して無料で証明書を入手することも可能ですが、[AWS Certificate Manager(ACM)](https://aws.amazon.com/certificate-manager/)の優れた点は、証明書の有効期限が近づくと自動で更新してくれるということです。これでサーバーの管理や証明書の更新といった煩わしさから開放されます。

こうしてAWS Certificate Managerの発表がきっかけとなりブログ環境を改めることにしました。また今回、静的サイトジェネレーターとしてPelicanではなく、高速な記事の生成速度で評判のある[Hugo](http://gohugo.io/)を使うことにしました。

### 移行手順

注: 以下は2017年4月25日時点での操作方法です。AWSの仕様変更などにより手順が変わる場合が予想されます。

#### ソフトウェアのインストール

まず必要となるソフトウェアをインストールします。環境はMac OS Xで行い、[Homebrew](http://brew.sh/)を使っています。他OSでも各ディストリビューションのパッケージマネージャーやバイナリなどから適宜インストールできます。

```nohighlight
$ brew install hugo pandoc git awscli
```

hugoはサイトジェネレーターです。Pelicanでは原稿をreStructuredText形式(.rst)で書いていたため、Hugoを利用するにあたりMarkdown形式(.md)に変換する用途に[pandoc](http://pandoc.org/)を使いました。gitはバージョン管理やテーマのインストールの際に必要です。[awscli](https://aws.amazon.com/cli/)はAmazon Web Seviceの各サービスにコマンドラインからアクセスするためのツールで、hugoで生成されたファイルをS3にアップロードするときに使います。

#### Hugoを使った静的サイトの作成

続いてローカル環境でブログを構築します。ref: [Hugo Quickstart Guide](https://gohugo.io/overview/quickstart/)

```nohighlight
$ hugo new site path/to/blog
$ cd path/to/blog 
$ tree .
.
├── archetypes
├── config.toml
├── content
├── data
├── layouts
└── static
```

Pandocを使ってMarkdown形式に変換した原稿を`content`ディレクトリ内にコピーします。画像などのツリー関係はリンクが切れないように元の状態を維持しておきます。PelicanとHugoでは原稿の日付やタイトルといったメタデータの書き方が異なるため、それらは手動で書き換えました。ref: 
[Pandoc - Getting started with pandoc](http://pandoc.org/getting-started.html#step-6-converting-a-file), [Hugo - Front Matter](https://gohugo.io/content/front-matter/)

```nohighlight
// .rstを.mdに変換。.rstファイルのあるディレクトリにて
$ pandoc input.rst -f rst -t markdown -s -o output.md

// コピー後のcontentディレクトリ(一例)
$ tree content/
content/
├── images
│   ├── 2013
│   │   ├── 09
│   │   │   ├── 20130924-1.jpg
...            ...
│ 
└── posts
    ├── 2013-09-16_hello-world.md
...
```

テーマをインストールします。[テーマ一覧](http://themes.gohugo.io/)があるのでそこから自分の好きなテーマを選びます。[Vienna](https://github.com/keichi/vienna)というテーマが良さそうだったので今回はこれに決めました。

Hugoのトップディレクトリにて、

```nohighlight
$ mkdir themes
$ cd themes
$ git clone https://github.com/keichi/vienna
```
テーマがインストールされました。

Hugoの基本的な設定を指定する`config.toml`を編集します。このファイルはYAML形式やJSON形式にも対応していますが、デフォルトのTOML形式で記述しました。ref: [Hugo - Configuring Hugo](https://gohugo.io/overview/configuration/)

```nohighlight
$ cd ..
$ cat config.toml
baseurl = "https://blog.yujinakao.com/"
languageCode = "ja-jp"
title = "UGarchive"
theme = "vienna"

[permalinks]
  posts = "/:year/:month/:day/:slug/"

[params]
  twitter = "nakaoyuji"
  github = "ynakao"
  ...
```

上に自分の設定した`config.toml`の一部を示します。ほとんどは設定項目の名称からどのような内容か推察できると思います。`[permalinks]`の項目は記事URLの表示形式を決めるもので、`content/posts/`以下の原稿のメタデータと対応します。

例えば、`content/posts/2013-09-16_hello-world.md`のメタデータは以下のようになっています。

```nohighlight
$ cat content/posts/2013-09-16_hello-world.md 
+++
date = "2013-09-16"
title = "なにか書く"
tags = [ "announcement" ]
slug = "hello-world"
+++
...
```

これにより`:year`は2013、`:month`は09、`:day`は16、`:slug`はhello-worldとなり、この記事のURLは`baseurl`と合わせて`https://blog.yujinakao.com/2013/09/16/hello-world/`となります。

`[params]`の項目群はテーマによって設定できる値が変わるので注意が必要です。テーマのREADMEなどをよく読みましょう。

`config.toml`の編集が終わったらいよいよHTMLファイルを生成します。

```nohighlight
$ hugo
```

新たに`public`ディレクトリが作られ、その中にHTMLファイルなどが入っています。これらを丸ごとインターネット上に公開するとサイトが表示されます。

#### S3の設定

`public`ディレクトリ内のファイルをS3にアップロードするため、まずアップロード先となるS3のバケットを準備します。ref: [例: 独自ドメインを使用して静的ウェブサイトをセットアップする - Amazon Simple Storage Service](http://docs.aws.amazon.com/ja_jp/AmazonS3/latest/dev/website-hosting-custom-domain-walkthrough.html)

- [S3コンソール](https://console.aws.amazon.com/s3/home)に適切な権限を持つユーザーでログインし、`Create Bucket`をクリック。
- ここで言う「適切な権限を持つユーザー」とはS3へのアクセスやバケットの作成、設定の変更が許可されたユーザーのことである。AWSではユーザーごとに与えられる権限を細かく決めることが可能なためこのような表現をとっている。全権限を付与されたadminユーザーならば権限の有無を考慮する必要はないが、セキュリティの観点からAWSでは特定のサービス毎に必要最低限の権限を持ったユーザーの作成が推奨されている。この後も同様の表現をとった箇所があり、意味は同じである。ref: [IAM のベストプラクティス - AWS Identity and Access Management](http://docs.aws.amazon.com/ja_jp/IAM/latest/UserGuide/best-practices.html)
- ポップアップウインドウが現れるので`Bucket Name`にはブログのドメイン名を入力(今回は`blog.yujinakao.com`)。適当な`Region`を選択、`Copy settings from an existing bucket`は空欄のまま`Next`をクリック。
- `Set properties`では特に変更を加えず`Next`をクリック。
- `Set permissions`でも同様に変更を加えず`Next`をクリック。
- `Review`で設定した項目を確認し、`Create bucket`をクリック。
- バケット一覧に作成したバケットが表示される。作成したバケットを選択し、`Properties`のエリアをクリックし内容を編集していく。
- `Bucket Policy`のボックスをクリック。
- `Bucket policy editor`のテキストエリアに以下の内容をペーストする。`blog.yujinakao.com`の箇所は運用するサイトURLに合わせて適宜変更する。

```nohighlight
{
  "Version":"2012-10-17",
  "Statement":[{
    "Sid":"AddPerm",
        "Effect":"Allow",
      "Principal": "*",
      "Action":["s3:GetObject"],
      "Resource":["arn:aws:s3:::blog.yujinakao.com/*"
      ]
    }
  ]
}
```

- `Save`をクリック。
- 次に`Properties`のタブをクリック、`Static website hosting`の項目をクリックし内容を編集する。
- `Use this bucket to host a website`のラジオボタンをクリック。`Index document`には`index.html`、`Error document`には`404.html`を入力し`Save`をクリックする。
- `Static website hosting`に表示される`Endpoint`のURL(http://{バケット名}.s3-website-{バケットのリージョン}.amazonaws.com)にアクセスすることでウェブサイトのテストが可能。今回の場合は`http://blog.yujinakao.com.s3-website-ap-northeast-1.amazonaws.com`。

続いてS3にコマンドラインからアクセスするための設定を行います。まず、アクセスキーを発行します。ref: [IAM ユーザーのアクセスキーの管理 - AWS Identity and Access Management](http://docs.aws.amazon.com/ja_jp/IAM/latest/UserGuide/id_credentials_access-keys.html)

- 適切な権限を持つユーザーで[IAMコンソール](https://console.aws.amazon.com/iam/home)にログインする。
- `User`をクリックし、S3にアクセス権限を持つユーザー→`Security Credentials`→`Create Access Keys`の順にクリック。
- 鍵の作成に成功の旨のポップアップウインドウが表示されたら、`Secret access key`の項目内の`Show`をクリックし、`Access Key ID`と`Secret Access Key`の内容をメモしておく。`Download .csv file`からダウンロードすることも可能。ウインドウを閉じると`Secret Access Key`は二度と見ることができなくなる。また、忘れると再発行しなければならないことに注意。
- ローカル環境のコマンドラインでIDとKeyの設定を行う。ref: [configure — AWS CLI 1.10.1 Command Reference](http://docs.aws.amazon.com/cli/latest/reference/configure/index.html)

```nohighlight
$ aws configure
AWS Access Key ID [None]: "Access Key ID"
AWS Secret Access Key [None]: "Secret Access Key"
Default region name [None]: ap-northeast-1
Default output format [None]:
```

- 対話形式のウィザードが始まるので先程のIDとKeyを入力する。`Default region name`には自分の利用しているAWSのリージョンを指定する。日本のユーザーであればほとんどが`ap-northeast-1`。`Default output format`は何も入力せずエンターキーを押した。

一通りの準備が整ったのでCloudFrontの設定を行う前に、S3のみでサイトがホストされるか確認しました。`public`ディレクトリ内のファイルを作成したS3のバケットにアップロードします。下の`blog.yujinakao.com`には作成したバケットの名前を指定します。ref: [sync — AWS CLI 1.10.1 Command Reference](http://docs.aws.amazon.com/cli/latest/reference/s3/sync.html)

```nohighlight
$ aws s3 sync public/ s3://blog.yujinakao.com
```

バケットを`Enable website hosting`に設定した際の`Endpoint`のURL(http://{バケット名}.s3-website-{バケットのリージョン}.amazonaws.com)にアクセスしてサイトが表示されれば成功しています。ただし、HTMLヘッダ内のスタイルシートなどのリンクがこのURLだとアクセスできずレイアウトが崩れている場合もあります。

#### ACMにて証明書の発行

AWS Certificate Managerで自分のドメインのSSL証明書を発行します。ref: [Request a Certificate - AWS Certificate Manager](https://docs.aws.amazon.com/ja_jp/acm/latest/userguide/gs-acm-request.html)

- [ACMコンソール](https://console.aws.amazon.com/acm/home)に適切な権限を持つユーザーでログイン。`Get started`をクリックする。
- `Domain name`のテキストフィールドに証明書を発行したいドメインを入力する。ワイルドカードも使用可能で`*.yujinakao.com`とすれば`yujinakao.com`以下すべてのサブドメインで証明書が有効となる。ここでは`blog.yujinakao.com`と入力した。
- `Review and request`をクリックすると確認画面に遷移する。
- 確認画面で`Confirm and request`をクリックすると、申請したドメインの正式な保有者であるか確認のメールが送られてくる。自分の場合は、admin, webmaster, postmasterとWhois情報に載っているアドレス宛にメールが届いた。
- メール内のリンクを開くと最終確認の画面が表示される。内容をよく読み、`I Approve`をクリックする。
- ACMコンソールに戻ると申請したドメインが一覧に加わっている。

#### CloudFrontの設定

CloudFrontを使ってSSL通信に対応したコンテンツデリバリーの設定を行います。

- [CloudFrontコンソール](https://console.aws.amazon.com/cloudfront/home)に適切な権限を持つユーザーでログイン。`Create Distribution`をクリックする。
- デリバリー方式の選択を求められるので、`Web`の項目の`Get Started`をクリックする。
- 各種項目を以下のように設定した。特に明記していなければ空白のままか、もしくは変更を行ってない場合である。
  - **Origin Domain Name**: S3 `Endpoint` URLのドメイン箇所のみ({バケット名}.s3-website-{バケットのリージョン}.amazonaws.com)を入力(http://は入力しない)。テキストエリアをクリックするとプルダウンにリージョン名を含まない候補({バケット名}.s3.amazonaws.com)がサジェストされることがあるが、これを選択するとうまく動作しない。必ずリージョン名を含んだエンドポイントを入力するよう注意する。
  - **Origin ID**: 上のOrigin Domain Nameを入力すると自動で割り振られる。
  - **Viewer Protocol Policy**: `Redirect HTTP to HTTPS`を選択。HTTPでアクセスしてもHTTPSのサイトにリダイレクトされるようにする。
  - **Alternate Domain Names(CNAMEs)**: `blog.yujinakao.com`を入力。
  - **SSL Certificate**: `Custom SSL Certificate`を選択。さらにプルダウンから先に作成したblog.yujinakao.comのSSL証明書を選択する。
  - **Custom SSL Client Support**: `Only Clients that Support Server Name Indication (SNI)`を選択。
- `Create Distribution`をクリックして設定を終了。ディストリビューション一覧で`Status`が`Progess`から`Deploy`に変わるまで15分ほどかかる。
- リストから作成したディストリビューションを選択し、`Distribution Settings`をクリック。`General`タブ内の`Domain Name`の値(******.cloudfront.net)をメモしておく。
- [Amazon Route 53](https://aws.amazon.com/route53/)で`blog.yujinakao.com`が`******.cloudfront.net`をCNAMEで参照するようにDNSを設定した。

これで`https://blog.yujinakao.com/`にアクセスするとHugoで生成したブログが表示されるようになりました。セキュアな通信を示す緑の鍵マークもアドレス欄で確認でき、証明書の詳細を見るとAmazonが発行していることが分かります。

### さいごに

他にもHugoのテーマのCSSをいじったりバージョン管理の設定を行ったりと瑣末な点はありましたがおおまかな手順は以上の通りです。AWSにおけるユーザー・グループの作成やRoute 53の細かな操作は少し本題から離れそうでしたので軽く触れる程度にとどめました。

セキュリティ的な不備やもっとこうした方が良いといった改善点などあればご教授ください。ブログが新しくなったことで更新回数が増えればいいなと自分のことながら思います。

### 追記(2016/07/05)

参考までに[次のエントリ](https://blog.yujinakao.com/2016/02/17/mocos-kitchen-twitter-bot-on-aws-lambda/)の末尾にAWSで実際にかかった料金について触れています。上記のような運用でだいたい月$0.15-0.2くらいでした。ただ、アクセス数や通信量、S3に占めるファイルの容量が増えるとその分料金も上がります。
