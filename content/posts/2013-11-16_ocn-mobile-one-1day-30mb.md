+++
date = "2013-11-16"
title = "OCNモバイルONEを1日30MBプランに変更"
tags = [ "MVNO", "OCN", "OCN mobile ONE" ]
slug = "ocn-mobile-one-1day-30mb"
+++

前回の更新からだいぶ経ちましたが・・・

今月からOCNモバイルONEのプラン変更を行ったので、2週間ほど使用した感想を簡単に記します。

<!--more-->

先月まで契約していたのは通信速度が500kbps一定で、1ヶ月7GB利用できるタイプ。500kbpsと低速であることに加え、au
Wi-Fi Walker
LTEを使っていた頃から速度制限を恐れるあまり大容量の通信をしない癖がついていたので、なかなか月末までに7GBを使い切ることができませんでした。そのため、無理矢理ソフトウェアアップデートなどで消費するという顛末になりました。

これではもったいないと、実験的な意味も込めて料金の安い1日30MBプランに変更することに。このプランは1日当たり30MB分だけ高速通信を行えますが、それを超えると200kbpsに制限されるというものです。毎日0時になると制限はリセットされ、再び30MB分高速で通信できるようになります。料金は月980円と500kbps/7GBプランの1980円に比べると半額程度でお得感があります。

プランの変更方法
================

OCNモバイルONEのプラン変更は[OCNマイページ](https://mypage.ocn.ne.jp/procedure/ocn/wireless/charge/index.do)から行うことができます（要ログインID）。

![20131116-1.jpg](/images/2013/11/20131116-1.jpg)

プルダウンから変更したいプラン内容を選択すると、

![20131116-2.jpg](/images/2013/11/20131116-2.jpg)

確認画面で変更が反映されていることが分かります。プラン変更は前月の最終日1日前までに申請しないと、翌月から反映されないので注意が必要です。

30MBで運用可能なのか
====================

問題は高速通信分の30MBでどれくらい使えるのかということでした。SIMを挿しているルーターのBF-01Bには通信量のログを取る機能がないので、どれくらい使ったのか把握できません。

そこで、[DataWiz](https://itunes.apple.com/jp/app/datawiz-free-mobile-data-management/id544544238)という通信ログアプリを導入し、iPhoneで日々どれくらい利用しているのか確認しました。

![20131116-3.jpg](/images/2013/11/20131116-3.jpg)

グラフの突出している箇所は、公衆無線LANに接続しているため通信量が多くなっています。ログがSSIDで区別されず、Wi-Fiであれば十把一絡げに記録されるようです。それらを除いてグラフを見ると、全体を通して50MB以下に収まっていることが分かります。通常の使い方であれば高速通信が30MBでも支障はなさそうです。

実際はこれに加え、ルーターに接続するPCやタブレットの通信分も考慮しなければなりませんが、自分の使い方ではもっぱらiPhoneからのWeb閲覧が主なので十分です。

速度の実測値はどれくらいか
--------------------------

### 高速時

最大速度112.5Mbpsを謳っていますが、そこは便利な言葉「ベストエフォート」。そんな数値が出ることはありません。本当にそんな速度だったら一瞬で30MBを消費してしまいます。3G専用Wi-Fiルーター経由のiPhoneでの測定ですが、どんな値になるのでしょうか。

![<http://www.speedtest.net/my-result/i/674515285>](/images/2013/11/20131116-4.png)

![<http://www.speedtest.net/my-result/i/674717319>](/images/2013/11/20131116-5.png)

上が回線の混み合っていないであろう早朝6時頃、下がMVNOの鬼門とされる平日昼休みの時間帯12時半過ぎに測定したものです。

回線が空いている時間帯はコンスタントに1−2Mbpsの速度が出て快適です。混雑しているときはレスポンスが遅いことがあり速度低下も見られますが、500kbps/7GBプランを思えばそれなりの速度が出ています。

### 低速時

低速時の挙動は、500kbps/7GBプランの制限時の200kbpsと同じでしたので先月末に測定したもので代用します。横着です。

![<http://www.speedtest.net/my-result/i/668301697>](/images/2013/11/20131116-6.png)

混雑していないときの200kbpsモードではきちんと額面通りの数値となっています。しかし…

![20131116-7.jpg](/images/2013/11/20131116-7.jpg)

平日昼間になると回線が不安定で測定もままなりません。ですが、テキストベースの通信ならば十二分に事足りますし、WebページもOpera
Miniなどデータ圧縮機能の付いたブラウザを介すれば許容の範囲内です。何より、980円という価格でどんなに遅くてもすべてを許せてしまいます。おかねのちからってすげー。

200kbpsでできること・できないこと
=================================

ここ数日の経験からiPhoneのみの運用であれば1日当たり30MBで十分でしたが、PCに接続すると高速分はすぐに使いきってしまします。ですので、いっそのこと200kbpsの速度一定プランと割りきって考えると良いかもしれません。正直に言って200kbpsは遅いですが、リッチコンテンツを避ければ低速でも運用できないことはありません。この速度で何が出来るのか色々と試した結果を並べてみます。

-   できること
    -   Webページの閲覧
    -   Twitterなど文字情報中心のやりとり

これらは楽勝です。PCではブラウザの画像表示や各種プラグインの設定をオフにするとさらに快適です。iPhoneでは先にも述べたOpera
Miniを使っています。大幅にデータを圧縮してくれるので30MB分をかなり延命できます。

-   できないことはないがストレスを感じる
    -   アプリやソフトウェアの簡単なアップデート
    -   キャッシュを溜めることのできる短い動画・音源の視聴

10MB前後のアプリのダウンロードやアップデートならば辛抱強く待てば可能です。動画や楽曲も短時間のものであれば何とかいけます。

-   できないこと
    -   システムの更新など大容量のアップデート
    -   ストリーミング系動画の視聴（iTunesの試聴含む）

この辺りになるとどうあがいても不可能です。100MBオーバーのアップデートを試みようとすると丸一日はかかるでしょう。また、ストリーミングは再生と読み込みがつっかえつっかえで、とても視聴に耐えうるものではありません。500kbpsの時は問題なかったiTunesの試聴も200kbpsでは出来ませんでした。iTunesの配信ビットレートは256kbpsなので数字的にも無理そうです。

それでも、数日試行錯誤するうちにストリーミングでも再生可能なケースをいくつか見つけました。iPhoneなどモバイル機器から画質・音質を落として見る方法です。YouTubeアプリは最低画質の144pを選択することで、品質は良くないですが内容確認程度には使えます。また、48kbpsという低いビットレートで配信されているradikoであれば難なく聞くことが出来ました。

さらに、iTunesの試聴もPCからではなく、iPhoneから行うと可能なことが分かりました。PCでは試聴の方式が完全なストリーミング様なのですが、iPhoneの場合は少しバッファを溜めることができるようです。そのため、再生ボタンを押してすぐに一時停止し、しばらく待ってから再生を始めると滞りなく聞けました。書いていてとてもせこい感じがします。

さいごに
========

MVNOのSIMを選ぶにあたり、OCNが候補となった理由の一つに3日で366MB規制がない点が挙げられます。他のMVNO各社は、200kbpsの低速状態でも直近3日間の通信料の合計が366MB以上になるとさらなる速度制限を設けており、そうなった場合50kbps以下にまで落ち込むと言われています。

OCNでは明言こそされていませんが、366MB規制は事実上確認されていないようです。バックグラウンドでの意図しないアップデートなどで大量の通信をしてしまったとしても、2段階目の制限を受ける心配がありません。モバイルWi-FiルーターでPCからも利用する身としては、これがOCNを選択する決め手となりました。

とは言うものの、低速とはいえ大量に通信を行っては周辺の回線に迷惑がかかってしまう可能性もあるので、無闇に乱用することは避け、節度を守った使い方を心がける必要はあると思います。