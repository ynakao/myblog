+++
Tags = [ 'nextcloud', 'selfhost' ]
date = "2016-12-10"
slug = "nextcloud-upgrade"
title = "Nextcloudをアップグレードする"
lastmod = "2017-02-27"
+++

Nextcloudから新しいバージョンが[リリース](https://nextcloud.com/blog/nextcloud-updates-10.0.2-and-9.0.55-are-available-time-to-update/)され、アップグレードしたのでその際の手順です。管理者ページからウィザード形式で行う方法もありますが、上手くいかないことが多く手動で行いました。

<!--more-->

前提として、ウェブサーバーにはNginx、データベースにはPostgreSQLを利用し、HTTPユーザは`www-data`、サードパーティのアプリに[Calendar](https://github.com/nextcloud/calendar/)と[Contacts](https://github.com/nextcloud/contacts)をインストールしています。また、Nextcloudのルートディレクトリは`/var/www/`に、`data`ディレクトリは`/var/www/nextcloud/`内に配置しています。その他詳細はひとつ前の[ポスト](https://blog.yujinakao.com/2016/07/05/nextcloud-installation/)を確認ください。基本的にはドキュメントの通りに進めます。cf: [Manual Nextcloud Upgrade](https://docs.nextcloud.com/server/10/admin_manual/maintenance/manual_upgrade.html)

まず、管理者アカウントで`https://example.com/settings/apps`にアクセスしサードパーティアプリ(Calendar, Contacts)を無効化します。

次に`occ`コマンドを用いNextcloudをメンテナンスモードに切り替えます。cf: [Using the occ Command](https://docs.nextcloud.com/server/10/admin_manual/configuration_server/occ_command.html)

```nohighlight
$ su
# cd /var/www/nextcloud
# sudo -u www-data php occ maintenance:mode --on
```

[Backing up Nextcloud](https://docs.nextcloud.com/server/10/admin_manual/maintenance/backup.html)を参考にバックアップを作成します。データベースのバックアップの際にはデータベース名、サーバー、データベースのユーザ名、パスワードを適宜指定します。ex: `[db_name]`: nextclouddb, `[server]`: localhost, `[username]`: nextcloud

```nohighlight
# cd ..
// Nextcloud backup
# rsync -Aax nextcloud/ nextcloud-dirbkp_`date +"%Y%m%d"`/
// Databese backup
# PGPASSWORD="password" pg_dump [db_name] -h [server] -U [username] -f nextcloud-sqlbkp_`date +"%Y%m%d"`.bak
```

Nextcloudの[ダウンロードページ](https://nextcloud.com/install/#instructions-server)からアーカイブファイルをダウンロードし、`/var/www/`以外の場所で展開します。`/var/www/`には旧バージョンのNextcloudディレクトリが残っており、名前が衝突するためです。

```nohighlight
# cd ~
// x.y.z is version number
# wget https://download.nextcloud.com/server/releases/nextcloud-x.y.z.tar.bz2
# tar -xjf nextcloud-x.y.z.tar.bz2
```

ウェブサーバーを停止します。

```nohighlight
# systemctl stop nginx
```

旧バージョンのNextcloudディレクトリを`nextcloud-old`のようにリネームします。

```nohighlight
# mv /var/www/nextcloud /var/www/nextcloud-old-`date +"%Y%m%d"`
```

先ほど展開した新しいNextcloudを配置します。

```nohighlight
# mv ~/nextcloud /var/www/
```

旧Nextcloudディレクトリから`config.php`, `data`, `calendar`, `contacts`を移行します。

```nohighlight
# cd /var/www
# cp nextcloud-old-`date +"%Y%m%d"`/config/config.php nextcloud/config/
# cp -r nextcloud-old-`date +"%Y%m%d"`/data/ nextcloud/
# cp -r nextcloud-old-`date +"%Y%m%d"`/apps/calendar/ nextcloud/apps/
# cp -r nextcloud-old-`date +"%Y%m%d"`/apps/contacts/ nextcloud/apps/
```

ウェブサーバーを起動させます。

```nohighlight
# systemctl start nginx
```

アップグレードはHTTPユーザで行うので、`nextcloud`ディレクトリ以下全ての所有権を一時的に`www-data`に与えます。

```nohighlight
# chown -R www-data:www-data /var/www/nextcloud/
```

`occ`コマンドを用いNextcloudのアップグレードを行います。
```nohighlight
# cd nextcloud
# sudo -u www-data php occ upgrade
```

アップグレードが始まりしばらく待ちます。問題がなければ`Update successful`と表示されます。

[Setting Strong Directory Permissions](https://docs.nextcloud.com/server/10/admin_manual/installation/installation_wizard.html#setting-strong-directory-permissions)のスクリプトを実行し、各ファイルの権限を変更します。

```nohighlight
# ~/nextcloud_permission.sh
```

最後にNextcloudのメンテナンスモードを解除します。

```nohighlight
# sudo -u www-data php occ maintenance:mode --off
```

再び`https://example.com/settings/apps`に管理者アカウントでアクセスし、サードパーティアプリ(Calendar, Contacts)を有効にすればアップグレードは完了です。
