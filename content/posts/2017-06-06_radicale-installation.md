+++
Tags = [ 'radicale', 'selfhost' ]
date = "2017-06-06"
slug = "radicale-installation"
title = "RadicaleでCalDAV/CardDAVサーバーを構築する"
+++

以前の[ポスト](https://blog.yujinakao.com/2016/07/05/nextcloud-installation/)でNextcloudをインストールし、CalDAV/CardDAVサーバーとして利用していると書きました。ところが先日、Nextcloud 12が[リリース](https://nextcloud.com/blog/welcome-to-nextcloud-12/)されたので更新しようとしましたが[うまく行きません](https://twitter.com/nakaoyuji/status/870262354054754305)。次のマイナーアップデートで改善されるかもしれませんが、なんとなく居心地がよくない気がします。

<!--more-->

もともとNextcloudは、他のCalDAV/CardDAVサーバーが不安定であったため導入したもので、その多機能さゆえカレンダーや連絡帳の同期にのみ利用するのは少し大袈裟でした。また、Nextcloudのインストールには多くのPHPパッケージを必要とし、加えてデータベースも別途用意しなければならず煩雑な点があります。

そこでNextcloudがアップデートされなかったことを機に、先の試行ではきちんと動かすことができなかった[Radicale](http://radicale.org/)を再び試してみることにしました。すると、しばらく見ない間にバージョン2になっており、ドキュメントも以前より分かりやすく書かれています。実際にインストールしてみると正常に動作したのでその過程を記します。

---

前提として、Debian 8.8上でウェブサーバーにNginxを使用しています。[チュートリアル](http://radicale.org/tutorial/)によるとPython3.4以上とPythonパッケージ導入に`pip`が必要なのでインストールします。また、今回は[Virtualenv](https://virtualenv.pypa.io/en/stable/)を用い、環境を切り離してRadicaleを動かすことにしたので、それも同時にインストールしておきます。

```nohighlight
$ sudo apt install python3 python3-pip python3-virtualenv
```

#### Radicaleのインストール

`radicale`という名前の仮想環境を作り、Radicaleをインストールします。その際`python3`がデフォルトとなるよう指定しておきます。

```nohighlight
$ virtualenv --python=python3 radicale
$ cd radicale
$ source bin/activate
(radicale)$ python --version
Python 3.4.2
```

Radicaleやパスワード生成に必要なPythonパッケージをインストールします cf. [Basic Setup](http://radicale.org/setup/)。`bcrypt`をインストールする際、依存関係となるライブラリなどがないとエラーが出るので、 `bcrypt`の [ドキュメント](https://github.com/pyca/bcrypt/)にならい、先にインストールしておきます。

```nohighlight
$ sudo apt install build-essential libffi-dev python-dev
$ python -m pip install radicale passlib bcrypt
```

#### Radicaleの設定

ログインのためのパスワードを生成します cf. [Basic Setup](http://radicale.org/setup/)。`htpasswd`コマンドはDebianでは[apache2-utils](https://packages.debian.org/search?keywords=apache2-utils)に含まれるため、これもインストールします。`-B`オプションは`bcrypt`の暗号方式、`-c`オプションはパスワードファイルを生成することを意味します cf. [htpasswd](https://httpd.apache.org/docs/current/programs/htpasswd.html)。以下、`username`はRadicaleにログインする時のユーザーとして任意の名前を付けます。

```nohighlight
$ sudo apt install apache2-utils
$ htpasswd -B -c /path/to/file username
New password:
Re-type new password:
```

設定方法のページを参考に`config`ファイルを作成します cf. [Configuration](http://radicale.org/configuration/)。今回はそのままの設定にしました。パスワードファイルまでのパスは適宜変える必要があります。

```nohighlight
$ cat ~/.config/radicale/config
[server]
hosts = 0.0.0.0:5232

[auth]
type = htpasswd
htpasswd_filename = /path/to/file
htpasswd_encryption = bcrypt
[storage]
filesystem_folder = ~/.var/lib/radicale/collections
```

#### Systemdの設定

サーバーとして稼働されるためのsystemdファイルを作成します cf. [Basic Setup](http://radicale.org/setup/)。今回はシステムワイドではなく1ユーザー環境下でのsystemd initとしました。

```nohighlight
$ cat ~/.config/systemd/user/radicale.service
[Unit]
Description=A simple CalDAV (calendar) and CardDAV (contact) server

[Service]
ExecStart=/path/to/radicale/bin/python -m radicale
Restart=on-failure

[Install]
WantedBy=default.target
```

ドキュメントでは`ExecStart`の項目が`ExecStart=/usr/bin/env python3 -m radicale`となっていますが、今回はVirtualenv内に`python`実行ファイルが存在するのでその箇所を変更します。

ここでRadicaleを試しに稼働させてみます。`http://localhost:5232`にアクセスして`Radicale works!`と表示されれば、ローカルでRadicaleが動いていることが確認できます。

```nohighlight
$ systemctl --user start radicale.service
$ wget http://localhost:5232
$ cat index.html
Radicale works!
```

#### Proxyサーバーの設定

外部からもアクセスできるようNginxの設定を行います cf. [Reverse Proxy](http://radicale.org/proxy/)。まずHTTPSで通信を行うため、[Let's Encrypt](https://letsencrypt.org/)を利用して証明書を発行します。詳細は以前の[ポスト](https://blog.yujinakao.com/2016/07/05/nextcloud-installation/)を参考ください。

```nohighlight
$ sudo systemctl stop nginx
$ su
# certbot certonly -d radicale.example.com
How would you like to authenticate with the ACME CA?
-------------------------------------------------------------------------------
1: Place files in webroot directory (webroot)
2: Spin up a temporary webserver (standalone)
-------------------------------------------------------------------------------
Select the appropriate number [1-2] then [enter] (press 'c' to cancel): 2
...
- Congratulations! Your certificate and chain have been saved at ...
```

次にNginxの設定ファイルを作成します。

```nohighlight
# exit
$ cat /etc/nginx/sites-available/radicale.example.com
server {
    listen  80;
    server_name radicale.example.com;
    return 301 https://radicale.example.com;
}

server {
  listen 443 ssl;
  server_name radicale.example.com;

  ssl_certificate /etc/letsencrypt/live/radicale.example.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/radicale.example.com/privkey.pem;

  location / {
    proxy_pass http://127.0.0.1:5232/;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_pass_header Authorization;
  }
}
$ sudo ln -s /etc/nginx/sites-available/radicale.example.com /etc/nginx/sites-enabled
$ sudo systemctl restart nginx
```

これが最小の設定だと思います。[Mozilla SSL Configuration Generator](https://mozilla.github.io/server-side-tls/ssl-config-generator/)などを参考にセキュリティやその他の設定を追加しても良いでしょう。

`radicale.example.com`がサーバーのIPアドレスに向いていれば、ブラウザからアクセスすると`Radicale works!`と表示されるはずです。

最後にサーバーの再起動後もRadicaleが自動で立ち上がるようにしておきます。

```nohighlight
$ systemctl --user enable radicale.service
```

---

#### CalDAV/CardDAVクライアントの設定

サーバーが動作していることを確認できたので、各デバイスからの接続を行います cf. [Clients](http://radicale.org/clients/)。基本的にドキュメント通りですが躓いた箇所を補足します。

クライアントから接続した後、連絡先を追加すれば自動的にサーバー上にコレクションが作成されます。しかし、自動に任せると、コレクションの名前がハッシュ値のようなランダムな数字の配列になってしまいます。すると、[Thunderbird](https://www.mozilla.org/thunderbird/)などからサーバーに繋げる際、接続先のURLが` https://radicale.example.com/username/*************`と煩雑になり入力が面倒です。

そこでドキュメント終盤に書かれているように、まず手動でサーバー側にコレクションを作っておくとURLが簡潔になり覚えやすいです。

Radicaleの設定ファイル`~/.config/radicale/config`が上記のように設定されているなら、コレクションのルートディレクトリは`~/.var/lib/radicale/collections/collection-root/username/`となります。この下にカレンダーなら`calendar.ics`、連絡帳なら`addressbook.vcf`といった任意の名前をつけたディレクトリを作成します。

```nohighlight
$ mkdir -p ~/.var/lib/radicale/collections/collection-root/username/
$ cd ~/.var/lib/radicale/collections/collection-root/username/
$ mkdir calendar.ics
$ mkdir addressbook.vcf
```

そして、それぞれのディレクトリ配下に`.Raidicale.props`ファイルを作成します。

```nohighlight
$ cat calendar.ics/.Radicale.props
{"tag": "VCALENDAR"}
$ cat addressbook.vcf/.Radicale.props
{"tag": "VADDRESSBOOK"}
```

これでクライアントからコレクションを直接指定して接続しなければならない場合、カレンダーと連絡帳の接続先はそれぞれ`https://radicale.example.com/username/calendar.ics`、`https://radicale.example.com/username/addressbook.vcf`と記述できます。

自分の試した範囲では、macOS・iOSのカレンダー・連絡帳、Thunderbirdに登録する際にはこれらのURLが必要でしたが、[DAVdroid](https://davdroid.bitfire.at/)は`https://radicale.example.com`だけでCalDAV・CardDAVどちらも自動で認識してくれました。

また、macOS・iOSの設定方法はドキュメントに示されていませんが、macOSは`System Preferences` - `Internet Accounts` - `Add Other Account...` - `CalDAV account`もしくは`CardDav account` - `Account Type: Manual`、iOSは`Settings` - `Mail, Contacts, Calendars` - `Add Account` - `Other` - `Add CalDAV account`もしくは`Add CardDAV account`と進み、必要事項: `User name`、`Passward`、`Server address`を記入すると繋がりました。

---

今のところどのクライアントでも正常に動作しています。ドキュメントには、

> A future release of Radicale 2.x.x will come with a built-in web interface that lets you create and manage collections conveniently. 

> [Clients](http://radicale.org/clients/)

との記述もあり、将来的にブラウザ経由でのコレクションの管理が予定されているようなので、より簡単に設定が可能になると思われます。
