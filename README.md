# GADGET Highlight

ガジェットの値下げ、クーポン、価格履歴だけを表示する静的メディアです。レビュー文章を生成せず、取得元の構造化データと確認済みの事実だけを掲載します。

## 対応カテゴリ

メカニカルキーボード、ポータブル電源、PC周辺機器、オーディオ、スマートホーム、DIY電子工作、SaaS/AIツールなどを `config.yml` から追加できます。

## 収集方式

- 楽天市場商品検索API（認証情報を設定すると自動取得）
- Amazon Creators API（利用資格と認証情報の取得後に有効化）
- メーカー公式セール／クーポンの確認済み手動カタログ
- 非公式なAmazon商品ページのスクレイピングは行いません

Amazonの現行Creators APIは、Amazonアソシエイトの最終承認と直近30日間の適格販売10件以上が利用条件です。それまではSiteStripe等で作成したAmazonリンクを手動カタログへ登録し、楽天APIと公式ストアの価格で運用を開始します。条件達成後は認証情報を設定するだけでAmazon検索を有効化できます。

楽天市場商品検索APIは2026-07-01版に対応し、アプリIDとアクセスキーを使用します。

## 初期設定

`.env.example` を `.env` の参考にして必要な値を設定します。

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python collector.py
.venv\Scripts\python builder.py
```

ローカル確認は `docs/index.html` を開きます。認証情報がない場合でも、安全なデモデータから画面を生成できます。

## 自動通知

値下げ通知は `data/notifications.json` に生成されます。`DISCORD_WEBHOOK_URL` またはX API認証情報を設定した場合だけ外部送信します。`NOTIFY_DRY_RUN=true` の間は送信しません。
