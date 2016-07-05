+++
Tags = [ 'letsencrypt', 'nextcloud', 'selfhost' ]
date = "2016-07-05"
slug = "nextcloud-installation"
title = "Nextcloud(ownCloud)をインストールする"
+++

### はじめに

GoogleやAppleのiCloudなどのサービスを利用すれば、各デバイス間でカレンダーや連絡帳の同期が可能です。しかし、それらは各企業独自のコードベース下にあるため、バックエンドまでは自由にマネジメントできません。また、Googleなどの大企業に関してはほぼ考えられませんが、突然サービスが終了してしまうこともあり得ます。そこでCalDAV・CardDAVサーバーを立てて自身で管理してみようと思いました。色々言ってますが単なる好奇心というのが本音です。

<!--more-->

実際この1年ほど[ownCloud](https://owncloud.org/)を用いてきました。特に不具合もなく動作していたのですが、本来DropboxやGoogle Driveの代替として開発されたこのソフトウェアにとってCalDAV・CardDAVは付随的機能です。また、大人数での利用を想定されていることもあり機能が豊富すぎるところがあります。 余談ですがデバイス間でのファイル転送なら、iOSでは利用できませんが[Syncthing](https://syncthing.net/)がサーバーレスで動作し便利だと思います。 

もうすこしミニマルな解決策はないものかと調べていると、[Radicale](http://radicale.org/)や[Baïkal](http://sabre.io/baikal/)を見つけました。ところが、まずRadicaleはインストールが複雑でドキュメントも分かりやすいとは言えず、動かすところまでたどり着けませんでした。次にBaïkalはなんとかインストール出来たのですが、[同期がうまくいかず](https://github.com/fruux/Baikal/issues/559)動作が不安定でした。  

やはりownCloudで運用するべきかと思い直していると、[Nextcloud](https://nextcloud.com/)というプロジェクトがアナウンスされました。どうやらownCloud内で意見の相違があったようで、ownCloud創設者やコアディベロッパー達が新たに立ち上げたフォークとのことです[[1]](https://nextcloud.com/we-are-nextcloud-the-future-of-private-file-sync-and-share/), [[2]](https://osdn.jp/magazine/16/06/03/163000)。面白そうなので心機一転Nextcloudを新たにインストールすることとしました。

### 方針

[ドキュメント](https://docs.nextcloud.org/server/9/admin_manual/installation/deployment_recommendations.html)によると通常のLAMP構成が推奨されていますが、個人的にNginxとPostgreSQLが好きなのでそちらを使用します。また、各Linuxディストリビューションのレポジトリから提供されるNextcloud(ownCloud)だと、ApacheやMySQLが自動的にインストールされてしまう場合があるので、すべて手動で行います([Manual Installation on Linux](https://docs.nextcloud.org/server/9/admin_manual/installation/source_installation.html))。

さらにHTTPSでやり取りを行うよう[Let's Encrypt](https://letsencrypt.org/)を利用してSSL証明書を発行します。料金はかかりませんがEmailアドレスが必要です。先日、Let's Encryptは規約更新のお知らせを送信する際、誤って他人のメールアドレスを本文に貼り付けて送ってしまうという[事態](https://community.letsencrypt.org/t/email-address-disclosures-june-11-2016/17025)がありましたので留意しておきましょう。

以上を踏まえて、DebianサーバーにNginx, PostgreSQL, PHPという構成で、Let's Encryptを用いたSSL通信が可能なようNextcloudをインストールしていきます。

### 作業手順

#### 1, PHPのインストール

PHPとともに必要となる各種モジュールをインストールします。一覧がドキュメントに載っているので適当なものを選択します。ref: [Prerequisites](https://docs.nextcloud.org/server/9/admin_manual/installation/source_installation.html#prerequisites)

```nohighlight
$ sudo apt-get install php php5-fpm php5-gd php5-json php5-pgsql php5-curl\
                       php5-intl php5-mcrypt php5-gmp php5-apcu php5-imagick
```

PHPモジュールで特に明記していないものは[php5-fpm](https://packages.debian.org/jessie/php5-fpm)パッケージ内に含まれています。`$ php -m`でインストールされたか確認します。

#### 2, PostgreSQLのインストール・データベースの作成

PostgreSQLをインストールし、Nextcloud用のロールとデータベースを作成します。

```nohighlight
$ sudo apt-get install postgresql postgresql-contrib
$ su - postgres  // ユーザ変更

$ psql
postgres=# CREATE ROLE nextcloud;  // nextcloudというロールを作成
postgres=# \password nextcloud  // ロールのパスワード設定

postgres=# ALTER ROLE nextcloud WITH LOGIN;  // ロールにログイン権限を付与
postgres=# CREATE DATABASE nextclouddb WITH OWNER nextcloud;
// nextclouddbというデータベースを作成し、nextcloudに所有権を与える
```

nextcloudロールでデータベースにログインできるようPostgreSQLの認証設定を変更します。

```nohighlight
$ sudo vim /etc/postgresql/9.4/main/pg_hba.conf

// ファイル末尾付近のpeerをmd5に書き換える
# TYPE DATABASE USER ADDRESS METHOD  // before
local  all      all          peer

# TYPE DATABASE USER ADDRESS METHOD  // after
local  all      all          md5

$ sudo systemctl restart postgresql  // 設定を反映させる
```

#### 3, Let's Encryptを用いSSL証明書を取得する

Let's Encryptを扱うにはクライアントである[Certbot](https://certbot.eff.org/)をインストールする必要があります。トップページのプルダウンからウェブサーバーとOSの種類を選択すると、インストールに最適な方法を示してくれます。Debian Jessieの場合は[Debian Backports](https://backports.debian.org/)を利用します。

今回は一番簡単な証明書のみを手動で発行する方法を用います。事前準備として、自身の所有するドメインが、証明書を発行するサーバーに向けて名前解決されている必要があります。これは各種DNSサービスを利用して行います。また、既にウェブサーバーが稼働している場合は、認証時の妨げになるので停止させておきます。

まずDebian Backportsを有効にします。

```nohighlight
$ sudo vim /etc/apt/sources.list

// ファイル末尾に以下の行を追加する
deb http://ftp.debian.org/debian jessie-backports main

$ sudo apt-get update  // 設定を反映させる
```

次にCertbotをインストールします。

```nohighlight
$ sudo apt-get install certbot -t jessie-backports
```

証明書の発行を行います。ref: [User Guide](https://certbot.eff.org/docs/using.html)

```nohighlight
$ su  // ルートユーザに変更
# certbot certonly --manual  // 証明書のみ手動で発行するコマンド
```

ウィザードが現れ、メールアドレスの入力や利用規約への同意が求められます。続いてSSL証明書を発行したいドメイン名を入力します。現在Let's Encryptはマルチドメインやワイルドカードに対応していないため、複数のドメインに対応させたい場合はその都度発行する手続きが必要です。入力すると、発行を申請したサーバーのIPアドレスが記録される旨のお知らせが表示されるので`OK`を選択します。

するとPythonの簡易ウェブサーバー機能を用いた認証の段階に入り、`Press ENTER to continue`と表示され入力待ちの状態になります。画面に以下のような手順をルートユーザで進めるよう促されます。ウェブサーバーを稼働させるため、新しいターミナルウインドウを開いてそこで作業を行います。

```nohighlight
# mkdir -p /tmp/certbot/public_html/.well-known/acme-challenge
# cd /tmp/certbot/public_html
# printf "%s" xxxxxx(長い文字列) > .well-known/acme-challenge/xxxxxx(長い文字列)
# $(command -v python2 || command -v python2.7 || command -v python2.6) -c \
  "import BaseHTTPServer, SimpleHTTPServer; \
  s = BaseHTTPServer.HTTPServer(('', 80), SimpleHTTPServer.SimpleHTTPRequestHandler); \
  s.serve_forever()"
```

元のターミナルウインドウに戻って`Enter`を押すと認証手続きが始まり、成功すると`Congratulations!`等メッセージが表示されます。発行された証明書は`/etc/letsencrypt/live/`以下に生成されているので確認しましょう。ウェブサーバーを動かしていたウインドウでは`Ctrl-C`でサーバーを停止させます。

その他注意すべき点は、Let's Enctyptの証明書は有効期限が90日しかないため、1年から数年間有効な一般的な証明書に比べ頻繁に更新する必要があります。さらに、上記手法で証明書を発行した場合、更新は毎回手動で行わなければいけません(`certbot renew`など)。Certbotは開発段階なので今後容易に更新が行えるよう改善していくとのことですが[[1](https://github.com/certbot/certbot/issues/2782)], [[2](https://community.letsencrypt.org/t/problem-renewing-certonly/17130)] 、それまでは手作業かスクリプトを作って対処するしかなさそうです。

#### 4, Nextcloudのダウンロード

[ドキュメント](https://docs.nextcloud.org/server/9/admin_manual/installation/source_installation.html#ubuntu-installation-label)に倣ってNextcloudをダウンロードし、チェックサムやGPG signatureを確認します。

[ダウンロードページ](https://nextcloud.com/install/)の`1. Get Nextcloud Server`の項目の`More details`をクリックし、`.tar.bz2`とその`SHA256チェックサム`、`GPG Signature`、及びNextcloudの`GPG公開鍵`をダウンロードします。

```nohighlight
$ wget https://download.nextcloud.com/server/releases/nextcloud-x.y.z.tar.bz2
// x.y.zはバージョンナンバー
$ wget https://download.nextcloud.com/server/releases/nextcloud-x.y.z.tar.bz2.sha256
// tar.bz2のSHA256チェックサム
$ wget https://download.nextcloud.com/server/releases/nextcloud-x.y.z.tar.bz2.asc
// tar.bz2のGPG Signature
$ wget https://nextcloud.com/nextcloud.asc
// NextcloudのGPG公開鍵
```
SHA256チェックサムを検証します。

```nohighlight
$ sha256sum -c nextcloud-x.y.z.tar.bz2.sha256 < nextcloud-x.y.z.tar.bz2
nextcloud-9.0.51.tar.bz2: OK
```

OKが出ればファイルの同一性は確認できました。

続いてGPG Signatureを使って本当にNextcloudから提供されたものか検証します。

```nohighlight
$ gpg --import nextcloud.asc  // 公開鍵のインポート
$ gpg --verify nextcloud-9.0.51.tar.bz2.asc nextcloud-9.0.51.tar.bz2
```

`Good Signature`と表示されれば完了です。

最後に`tar.bz2`を展開し、ウェブサーバーのドキュメントルートとなる場所に配置します。ここでは例としてドキュメントルートを`/var/www/`としています。

```nohighlight
$ tar -xjf nextcloud-x.y.z.tar.bz2
$ sudo cp -r nextcloud /var/www
```

#### 5, Nginxの設定

Nginxをインストールし、ドキュメントを参考に設定ファイルを書いていきます。ref: [Nginx Configuration for the Nextcloud 9.x Branches](https://docs.nextcloud.org/server/9/admin_manual/installation/nginx_owncloud_9x.html)

```nohighlight
$ sudo apt-get install nginx
$ sudo touch /etc/nginx/sites-available/example.com
$ sudo vim /etc/nginx/sites-available/example.com
```

基本的にドキュメントの通りで良いですが、`server_name`やSSL証明書のパスなどを自分の環境に合わせて変更します。さらにセキュリティを高めたければ、Mozillaが提供する[Mozilla SSL Configuration Generator](https://mozilla.github.io/server-side-tls/ssl-config-generator/)を利用して強固にすることも可能です。サーバーの種類やバージョン入力すると適切な設定を提案してくれます。

以下に設定ファイルの内容を示します。長いですが、ほとんどコピペしたもので変更点には注釈を入れています。元々含まれていたコメントは削除していますので、各セクションの意味はドキュメントを参照ください。

```nohighlight
upstream php-handler {
    server unix:/var/run/php5-fpm.sock; 
    # Nextcloudへの接続方法をUNIXソケットに変更
}

server {
    listen 80;
    server_name example.com;
    # 自分の環境に合わせてドメイン名を変更。以下同様の箇所も同じ
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name example.com;

    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Robots-Tag none;
    add_header X-Download-Options noopen;
    add_header X-Permitted-Cross-Domain-Policies none;

    root /var/www/nextcloud/;

    location = /robots.txt {
        allow all;
        log_not_found off;
        access_log off;
    }

    location = /.well-known/carddav { return 301
     $scheme://$host/remote.php/dav; }
    location = /.well-known/caldav { return 301
     $scheme://$host/remote.php/dav; }

    location /.well-known/acme-challenge { }

    client_max_body_size 512M;
    fastcgi_buffers 64 4K;

    gzip off;

    error_page 403 /core/templates/403.php;
    error_page 404 /core/templates/404.php;

    location / {
        rewrite ^ /index.php$uri;
    }

    location ~ ^/(?:build|tests|config|lib|3rdparty|templates|data)/ {
        deny all;
    }
    location ~ ^/(?:\.|autotest|occ|issue|indie|db_|console) {
        deny all;
    }

    location ~
    ^/(?:index|remote|public|cron|core/ajax/update|status|ocs/v[12]|updater/.+|ocs-provider/.+|core/templates/40[34])\.php(?:$|/) {
        include fastcgi_params;
        fastcgi_split_path_info ^(.+\.php)(/.+)$;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param PATH_INFO $fastcgi_path_info;
        fastcgi_param HTTPS on;
        fastcgi_param modHeadersAvailable true;
        fastcgi_param front_controller_active true;
        fastcgi_pass php-handler;
        fastcgi_intercept_errors on;
        # fastcgi_request_buffering off; 
        # Debian Jessie標準のNginx v1.6.2では対応していないのでコメントアウト
        # v1.7.11から対応している
        # http://nginx.org/en/docs/http/ngx_http_fastcgi_module.html#fastcgi_request_buffering
    }

   location ~ ^/(?:updater|ocs-provider)(?:$|/) {
        try_files $uri/ =404;
        index index.php;
    }

    location ~* \.(?:css|js)$ {
        try_files $uri /index.php$uri$is_args$args;
        add_header Cache-Control "public, max-age=7200";
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options "SAMEORIGIN";
        add_header X-XSS-Protection "1; mode=block";
        add_header X-Robots-Tag none;
        add_header X-Download-Options noopen;
        add_header X-Permitted-Cross-Domain-Policies none;
        access_log off;
    }

    location ~* \.(?:svg|gif|png|html|ttf|woff|ico|jpg|jpeg)$ {
        try_files $uri /index.php$uri$is_args$args;
        access_log off;
    }

    # ここからSSLの設定
    # https://mozilla.github.io/server-side-tls/ssl-config-generator/
    # Mozilla SSL Configuration GeneratorでNginx v1.6.2, Modern, OpenSSL v1.0.1tの結果を参考
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    # SSL証明書のパスを自分の環境に合わせる
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    # ssl_session_tickets off;
    # ブラウザでSSL_ERROR_RX_UNEXPECTED_NEW_SESSION_TICKETエラーがでるのでコメントアウト
    # 少し調べたが原因がわからない
    
    # Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
    # https://weakdh.org/sysadmin.html 
    ssl_dhparam /etc/nginx/ssl/example.com/dhparams.pem;
    # 上記URLを参考にdhparams.pemを生成しパスを指定

    ssl_protocols TLSv1.2;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA256';
    ssl_prefer_server_ciphers on;

    add_header Strict-Transport-Security max-age=15768000;

    ssl_stapling on;
    ssl_stapling_verify on;

    ssl_trusted_certificate /etc/letsencrypt/live/example.com/chain.pem;
    # パスを変更
}
```

設定を有効にし、Nginxを起動します。

```nohighlight
$ sudo ln -s /etc/nginx/sites-available/example.com /etc/nginx/sites-enabled
$ sudo systemctl start nginx
```

#### 6, インストールウィザード

Nextcloudに必要な環境が整ったので、Webインターフェース経由のインストール作業を行います。ref: [Installation Wizard](https://docs.nextcloud.org/server/9/admin_manual/installation/installation_wizard.html)

まず、Nextcloudを置いたディレクトリ以下の所有権をHTTPユーザ(Debianなら`www-data`)に変更しておきます。

```nohighlight
$ sudo chown -R www-data:www-data /var/www/nextcloud/
```

次に、ブラウザから`https://example.com`にアクセスすると上記ドキュメントのようなインストールウィザードが現れます。`admin`アカウントのユーザ名とパスワードを入力し、用いるデータベースを選択します。SQLiteやMySQL、MariaDBがインストールされているとそれらも表示されますが、ここではPostgreSQLを選びます。

`Data Folder`の項目にはデフォルトで`/var/www/nextcloud/data`が入力されていますが、変更したければ別のディレクトリを指定します。さらに、先に作成したデータベースの情報に基づきロール名(nextcloud)とそのパスワード(******)、データベース名(nextclouddb)を入力します。接続先は`localhost`のままにします。`Finish setup`のボタンをクリックするとインストールが始まり、エラーなど出なければ完了です。

最後にこちら([Setting Strong Directory Permissions](https://docs.nextcloud.org/server/9/admin_manual/installation/installation_wizard.html#setting-strong-directory-permissions))を参考に、`www-data`に全権を付与した`/var/www/nextcloud`以下ディレクトリのパーミッションを変更しましょう。参考ページに書かれたスクリプトをルートユーザで実行します。変数は自分の環境に合わせて適宜設定します。

インストールが完了したら[ユーザーマニュアル](https://docs.nextcloud.org/server/9/user_manual/)などを参考にNextcloudを活用しましょう。Dropboxのようにデスクトップクライアントやモバイルアプリもありますが、Android以外はまだownCloudのものを流用しているようです。

これらの方法でインストールした場合、`https://example.com/settings/admin`の管理者設定ページを見ると`Security & setup warnings`に警告が2つ表示されていました。1つ目は`php-fpm`の設定に関することで、こちら([php-fpm Configuration Notes](https://docs.nextcloud.org/server/9/admin_manual/installation/source_installation.html#php-fpm-configuration-notes))を参考に設定し直します。`/etc/php5/fpm/pool.d/www.conf`を開いて次の5行のコメントアウトを外します。

```nohighlight
;env[HOSTNAME] = $HOSTNAME
;env[PATH] = /usr/local/bin:/usr/bin:/bin
;env[TMP] = /tmp
;env[TMPDIR] = /tmp
;env[TEMP] = /tmp
```

さらに`env[PATH]`の右辺を`$ printenv $PATH`で出力された値に書き換えます。

2つ目はキャッシュの設定がなされていない旨のメッセージで、こちら([Configuring Memory Caching](https://docs.nextcloud.org/server/9/admin_manual/configuration_server/caching_configuration.html))を参考にします。今回キャッシュの役割として`php-apcu`をインストールしているので、`/var/www/nextcloud/config/config.php`を開き`array`内に`'memcache.local' => '\OC\Memcache\APCu',`と追記します。

ブラウザを再読み込みすると注意を促すメッセージは消えました。

### さいごに

本来の目的であったCalDAVとCardDAVはこのページ([Contacts & Calendar](https://docs.nextcloud.org/server/9/user_manual/pim/index.html))を参考に各種クライアントで設定を行ったところ、何の問題もなく同期されました。ミニマルな環境にしようとしていましたが、結果としてWebDAVやその他豊富な機能の恩恵に与れるのでよしとします。

ownCloudと袂を分かったNextcloudが今後どうなるのかまだよく分かりませんが、両者の動向に注視したいと思います。
