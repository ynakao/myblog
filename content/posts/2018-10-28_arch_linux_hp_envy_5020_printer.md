+++
Tags = [ 'arch', 'cups', 'hp']
date = "2018-10-28"
slug = "arch-linux-hp-envy-5020-printer"
title = "Arch LinuxでHP Envy 5020プリンターをセットアップする"
+++

これまで[HP Photosmart Premium C309g](http://jp.ext.hp.com/products/printers/inkjet/aio/c309g/)をプリンターとして使っていましたが、先日故障し動かなくなりました。購入してから9年経ってサポートが切れていることもあり、無理に修理するより新しく買った方が安く済むため思い切って新調することにしました。高性能な機能は求めていなかったので、検討した時点で一番安価だった[HP Envy 5020](http://jp.ext.hp.com/printers/personal/inkjet/envy5020/)を購入しました。今回はこのプリンターをArch Linuxから使用できるようにするための手順を書いていきます。

<!--more-->

#### 簡単なレビュー

新しいプリンターにHPを選んだのはLinuxのサポートに優れているからです。EpsonやCanon、BrotherなどもLinux向けのプリンタードライバーを配布していますが、自分の調べた限りではHPのみが[オープンソース](https://developers.hp.com/hp-linux-imaging-and-printing)のようです。そのため各Linuxディストリビューションの公式レポジトリからインストールすることができ、アップデートなどもパッケージマネージャから簡単に行えます。

またHP Envy 5020の気に入った点は、インクカートリッジが以前の5つから2つに削減されているところです。C309gではイエロー、マゼンダ、シアン、ブラック、フォトブラックと5つの独立インクで構成されていました。無くなったインクのみを交換可能で経済的との謳い文句でしたが、どれか1つが単独で空になるということは殆どなく、ほぼ毎回5つ全てを取り替えていました。さらに個々のインクカートリッジは1000円前後するため全部で5000〜6000円かかりインク代も馬鹿になりません。

Envy 5020ではカラーインクが1つにまとめられ、ブラックも1種類のみになっており交換が計2つで済みます。高価な大容量タイプもありますが、小さいカートリッジを選べばかかるお金も2000円ちょっとに抑えられます。使用頻度から考えると年に数回たまに印刷する程度なので、この形態は自分のユースケースに良く合っていると感じました。

ただ以前のモデルと変わらず使い辛いのは付属のタッチパネルの性能です。C309gの時と同様、反応がとても緩慢で操作のレスポンスが常にワンテンポ遅れる感じです。ワイヤレス設定の際には大変煩わしい思いをしました。一度設定が完了すればタッチパネルに触れる機会も殆ど無くなりますし、下位モデルなのでそういう部分でコストカットしているのだろうと割り切れば、必要十分な機能をひと通り揃えた満足度の高いプリンターだと思います。

#### Linuxとの接続

PCとプリンターとの接続はルーターのWi-Fiを介して行います。まずプリンターをルーターに接続しPCと同一ネットワーク下に置きます。これはHPの[ドキュメント](https://support.hp.com/jp-ja/document/c05822183)のステップ1, 2に沿って行います。この時ルーターのDHCP固定割当設定から、プリンターに常に同一のIPアドレスが割り当てられるようにしておきます。例として192.168.179.7で進めます。

続いてプリンターを利用するために必要なパッケージ、[CUPS](https://www.cups.org/)と[hplip](https://developers.hp.com/hp-linux-imaging-and-printing)をインストールします。`CUPS`はプリンターや印刷ジョブを管理する印刷全般に関与するプログラムで、`hplip`はHP製プリンター用のドライバーです。ArchWikiのそれぞれのページ([CUPS](https://wiki.archlinux.org/index.php/CUPS), [hplip](https://wiki.archlinux.org/index.php/CUPS/Printer-specific_problems#HP))にも詳しく書かれているのでそちらも参考にして下さい。

実際にパッケージをインストールし`CUPS`を起動させます。他のディストリビューションでも手順は同じだと思います。

```nohighlight
$ sudo pacman -S cups hplip
$ sudo systemctl start org.cups.cupsd.service
$ sudo systemctl enable org.cups.cupsd.service
```

ブラウザから`http://localhost:631/`にアクセスすると`CUPS`の管理画面が開きます。この状態で`Printers`のタブを開いても何も表示されません。ここにEnvy 5020をリストするための操作を行います。先に例に示したIPアドレスを指定し以下のコマンドを実行すると、ターミナル上で対話形式のプログラムが始まります。

```nohighlight
$ sudo hp-setup -i 192.169.179.7
...
Please enter a name for this print queue (m=use model name:'ENVY_5000'*, q=quit) ?m
// プリントキューの名前を訊かれる。ここではデフォルトのままにした。

Locating PPD file... Please wait.

Found PPD file: drv:///hp/hpcups.drv/hp-envy_5000_series.ppd
Description:

Note: The model number may vary slightly from the actual model number on the device.

Does this PPD file appear to be the correct one (y=yes*, n=no, q=quit) ? y
// プリンターを動かすために必要なPPDファイルが正しいか訊かれる。
// hplipパッケージの中身(https://www.archlinux.org/packages/extra/x86_64/hplip/files/)を見ると
// Envy 5020と全く同じファイル名はないが、一番近いものがenvy_5000_seriesなのでこれで正しいと思われる。

Enter a location description for this printer (q=quit) ?
Enter additonal information or notes for this printer (q=quit) ?
// 追加の情報があれば入力する。ここでは何も入力せずにエンター。

Adding print queue to CUPS:
Device URI: hp:/net/ENVY_5000_series?ip=192.168.179.7
Queue name: ENVY_5000
PPD file: drv:///hp/hpcups.drv/hp-envy_5000_series.ppd
Location:
Information:

---------------------
| PRINTER TEST PAGE |
---------------------

Would you like to print a test page (y=yes*, n=no, q=quit) ? y
warning: hp-testpage should not be run as root/superuser.
// 設定が完了したらテストページを印刷するか訊かれる。
// スーパーユーザーで実行するなとの警告が出たが、hp-setupはノーマルユーザーでもセットアップできたのだろうか。
...
Done.
```

テストページが印刷されれば成功です。`CUPS`の管理画面の`Printers`タブを再び訪れると新たにプリンターが追加されているはずです。今のところGIMPやLibreOfficeなどのプログラムから印刷を試みると`ENVY_5000`というプリンター名でリストされるので設定は上手くいっていると思われます。

![20181028-cups-envy-5000.jpg](/images/2018/10/20181028-cups-envy-5000.jpg)
