from __future__ import annotations

import html
from datetime import date
from pathlib import Path

OPERATOR = "GADGET Highlight運営事務局"
EMAIL = "daichiprojectwork@gmail.com"


def layout(title: str, body: str) -> str:
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}｜GADGET Highlight</title><style>
:root{{--bg:#080807;--panel:#11110f;--line:#343029;--ink:#f2eee4;--muted:#aaa297;--gold:#d0a35c}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Noto Sans JP","Yu Gothic",sans-serif}}header{{border-bottom:1px solid var(--line);padding:30px 5vw}}header a{{color:var(--ink);text-decoration:none;font-size:20px;font-weight:700;letter-spacing:.18em}}header b{{color:var(--gold)}}main{{max-width:900px;margin:auto;padding:65px 24px 100px}}h1,h2{{font-weight:500}}h1{{font-size:clamp(2.2rem,6vw,4.5rem);letter-spacing:-.04em;margin:0 0 55px}}h2{{font-size:1.35rem;border-top:1px solid var(--line);padding-top:28px;margin-top:48px}}p,li{{color:#d2cbc1;font-size:14px;line-height:2}}a{{color:var(--gold);text-underline-offset:4px}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:16px 8px;font-size:14px;line-height:1.8}}th{{width:180px;color:var(--muted)}}.note{{border:1px solid var(--line);padding:20px;margin-top:35px}}footer{{border-top:1px solid var(--line);padding:30px;text-align:center;color:var(--muted);font-size:11px}}@media(max-width:600px){{th,td{{display:block;width:100%}}}}
</style></head><body><header><a href="../">GADGET <b>Highlight</b></a></header><main><h1>{html.escape(title)}</h1>{body}</main><footer>GADGET Highlight</footer></body></html>'''


def build_content_pages(root: Path) -> list[str]:
    today = date.today().isoformat()
    pages = {
        "about": ("運営者情報", f'''<table><tr><th>サイト名</th><td>GADGET Highlight</td></tr><tr><th>運営者</th><td>{OPERATOR}</td></tr><tr><th>連絡先</th><td><a href="mailto:{EMAIL}">{EMAIL}</a></td></tr><tr><th>目的</th><td>Amazon、楽天市場、メーカー公式ストア等の価格、割引率、クーポン、価格履歴を探しやすい形で掲載すること</td></tr></table><h2>運営方針</h2><p>長文の商品評価や、確認できない推薦文を生成しません。価格、割引、仕様、販売先など購入判断に必要な事実を優先します。</p>'''),
        "privacy": ("プライバシーポリシー", f'''<p>{OPERATOR}は、問い合わせおよびアクセス解析等で取り扱う情報を適切に管理します。</p><h2>取得する情報</h2><p>お問い合わせ時の氏名または名称、メールアドレス、問い合わせ内容、ならびにアクセス解析で用いられる端末・閲覧情報を取得する場合があります。</p><h2>Cookieとアクセス解析</h2><p>アクセス状況の把握、広告効果測定、不正利用防止のためCookie等を使用する場合があります。Google Analyticsや広告サービスを導入する場合は、本方針と同意表示を更新します。</p><h2>広告・アフィリエイト</h2><p>Amazonアソシエイト、楽天アフィリエイトその他の広告サービスを利用する場合があります。外部リンク経由の購入等により当事務局が報酬を受け取ることがあります。</p><h2>第三者提供</h2><p>法令に基づく場合を除き、本人の同意なく問い合わせ情報を第三者へ提供しません。</p><p class="note">制定・最終更新日：{today}<br>連絡先：<a href="mailto:{EMAIL}">{EMAIL}</a></p>'''),
        "disclosure": ("広告・アフィリエイト表記", '''<p>本サイトにはアフィリエイト広告を含む場合があります。商品リンクを経由して購入・申込みが行われた場合、運営者が報酬を受け取ることがあります。利用者が支払う価格に追加料金が加算されるものではありません。</p><h2>価格表示</h2><p>価格、在庫、ポイント、送料、クーポン条件は変動します。購入を確定する前に販売ページの表示をご確認ください。</p><h2>Amazonについて</h2><p>Amazonのアソシエイトとして、GADGET Highlight運営事務局は適格販売により収入を得る予定です。AmazonおよびAmazon.co.jpはAmazon.com, Inc.またはその関連会社の商標です。</p><h2>観測最安値</h2><p>「観測最安値」は当サイトが保存した価格履歴の範囲内における最安値であり、市場全体または全期間の最安値を保証しません。</p>'''),
        "editorial-policy": ("編集・価格更新方針", '''<h2>取得元</h2><p>販売事業者の公式API、メーカー公式情報、確認済みの手動登録データを使用します。利用規約に反する商品ページの取得は行いません。</p><h2>事実データ</h2><p>商品名、通常価格、販売価格、割引率、主要仕様、クーポン、取得日時を掲載します。本文にない性能や評価を推測しません。</p><h2>更新</h2><p>原則として毎日2回更新します。API障害、在庫変動、販売元の仕様変更等により遅延または差異が生じる場合があります。</p><h2>訂正</h2><p>誤りは<a href="mailto:daichiprojectwork@gmail.com">メール</a>でご連絡ください。販売元の情報を確認して修正します。</p>'''),
        "disclaimer": ("免責事項", '''<p>掲載情報の正確性と最新性に配慮しますが、完全性、購入可能性、価格、在庫、クーポン適用、製品の品質を保証しません。</p><p>購入契約は利用者と販売事業者との間で成立します。商品、配送、返品、保証等は販売事業者の条件をご確認ください。本サイトの利用または外部サイトの利用によって生じた損害について、運営者は法令上認められる範囲で責任を負いません。</p>'''),
        "contact": ("お問い合わせ", f'''<p>価格・リンクの訂正、掲載・削除依頼、広告・取材等は、以下のメールアドレスへご連絡ください。</p><p class="note"><a href="mailto:{EMAIL}">{EMAIL}</a></p><p>商品名、掲載URL、確認した内容を添えていただくと確認がスムーズです。パスワード、決済情報などの機微情報は送信しないでください。</p>'''),
    }
    for path, (title, body) in pages.items():
        directory = root / path
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(layout(title, body), encoding="utf-8")
    return list(pages)

