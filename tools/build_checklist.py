# -*- coding: utf-8 -*-
"""
chemical-compliance.html に定義された法令チェック項目から、
「法令・確認点・必要実施事項」の一覧を組む。

判定エンジンと同じ定義を読むため、アプリ・画面・紙が食い違わない。

  --mode print   A4印刷用のHTML。Chromium の --print-to-pdf でPDF化する
  --mode web     画面で読むためのHTML。検索・分類の絞り込み・法令への移動つき
"""
import io, json, re, sys, datetime

SRC = "chemical-compliance.html"

# 該当条件（内部フラグ）を日本語に直す
FLAG = {
 "ra":"リスクアセスメント対象物を製造・取り扱う",
 "skin":"皮膚等障害化学物質等を取り扱う",
 "cancer":"がん原性物質を取り扱う",
 "tokka":"特定化学物質を取り扱う",
 "tokkaS":"特別管理物質を取り扱う",
 "yuki":"有機溶剤等を取り扱う",
 "yuki12":"第1種・第2種有機溶剤等を取り扱う",
 "lead":"鉛またはその化合物を取り扱う",
 "dust":"粉じん作業がある",
 "measure":"作業環境測定の対象作業場がある",
 "localExhaust":"局所排気装置・プッシュプル型換気装置がある",
 "welding":"金属アーク溶接等の作業がある",
 "demolition":"建築物・工作物の解体または改修の予定がある",
 "josei":"女性則の就業制限対象物質を取り扱う",
 "kakan":"化管法の指定化学物質を取り扱う",
 "prtr":"PRTR届出の3要件（対象業種・従業員21人以上・取扱量）を満たす",
 "shipping":"化学品を他社へ出荷・販売している",
 "dokugeki":"毒物または劇物を取り扱う",
 "plating":"電気めっき業または金属熱処理業を営んでいる",
 "shAny":"消防法の危険物を貯蔵・取り扱っている",
 "shMinor":"指定数量の倍数が5分の1以上1未満",
 "shOver":"指定数量の倍数が1以上",
 "waste":"産業廃棄物を排出している",
 "spWaste":"特別管理産業廃棄物が生じる可能性がある",
 "wasteLarge":"多量排出事業者に該当する",
 "waterFacility":"水質汚濁防止法の特定施設がある",
 "hazardWater":"有害物質使用特定施設・有害物質貯蔵指定施設がある",
 "publicWater":"公共用水域へ排出している",
 "sewer":"公共下水道へ排除している",
 "vocFacility":"揮発性有機化合物（VOC）排出施設がある",
 "boiler":"ばい煙発生施設がある",
 "haz_air":"有害大気汚染物質（優先取組物質）を取り扱う",
 "area900":"土地の形質変更の届出規模に該当する敷地である",
 "freon":"第一種特定製品（業務用エアコン・冷凍冷蔵機器）がある",
 "freonLarge":"フロン類の年間漏えい量が1,000t-CO2以上",
 "pcb":"PCB含有機器を保管または使用している",
 "kashin1":"第一種特定化学物質を取り扱う",
 "manufacture":"化学物質を製造または輸入している",
 "gas":"高圧ガスを貯蔵・消費している",
 "ordinance":"自治体の化学物質適正管理条例の対象地域である",
 "unknown":"内容が確定していない成分がある",
 "anySub":"化学品を台帳に登録している",
 "emp21":"常時使用する従業員が21人以上",
}
CYC = {"once":"随時（1回）","1m":"毎月","3m":"3か月ごと","6m":"6か月ごと",
       "12m":"1年ごと","36m":"3年ごと","60m":"5年ごと","event":"事由発生時"}
def cyc_label(c):
    return "毎年 %s日まで" % c[2:].replace("-","月") if c.startswith("y:") else CYC.get(c, c)

def load_tasks():
    s = io.open(SRC, encoding="utf-8").read()
    blk = re.search(r'const TASKS = \[(.*?)\]\.map\(r=>\(\{id:r\[0\]', s, re.S).group(1)
    rows, depth, cur, instr, esc = [], 0, "", False, False
    for ch in blk:
        if instr:
            cur += ch
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': instr = False
            continue
        if ch == '"': instr = True; cur += ch; continue
        if ch == "[":
            depth += 1
            if depth == 1: cur = "["; continue
        if ch == "]":
            depth -= 1
            if depth == 0: rows.append(cur + "]"); cur = ""; continue
        if depth >= 1: cur += ch
    out = []
    for r in rows:
        v = json.loads(r)
        out.append(dict(id=v[0], law=v[1], art=v[2], title=v[3], cat=v[4],
                        cyc=v[5], when=v[6], keep=v[7], memo=v[8]))
    return out

def cond_text(when):
    parts = []
    for c in when:
        if isinstance(c, str):
            parts.append(FLAG.get(c, c))
        else:
            parts.append(" かつ ".join(FLAG.get(f, f) for f in c))
    return " または ".join(parts)

E = lambda s: (str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

def build_html(tasks):
    laws = []
    for t in tasks:
        if t["law"] not in laws: laws.append(t["law"])
    today = datetime.date.today().strftime("%Y年%m月%d日")
    cats = []
    for t in tasks:
        if t["cat"] not in cats: cats.append(t["cat"])

    body = []
    for i, law in enumerate(laws, 1):
        items = [t for t in tasks if t["law"] == law]
        body.append(f'''<section class="law">
  <h2><span class="ln">{i:02d}</span>{E(law)}<span class="cnt">{len(items)}項目</span></h2>''')
        for j, t in enumerate(items, 1):
            keep = f'{t["keep"]}年' if t["keep"] else "—"
            body.append(f'''  <article class="item">
    <div class="no">{i:02d}-{j:02d}</div>
    <div class="bd">
      <h3>{E(t["title"])}</h3>
      <p class="meta"><span class="art">{E(t["art"])}</span>
        <span class="tag">{E(t["cat"])}</span>
        <span class="tag">{E(cyc_label(t["cyc"]))}</span>
        <span class="tag">記録保存 {E(keep)}</span></p>
      <p class="cond"><b>該当条件</b>{E(cond_text(t["when"]))}</p>
      <p class="memo"><b>確認点</b>{E(t["memo"])}</p>
    </div>
  </article>''')
        body.append("</section>")

    used = []
    for t in tasks:
        for c in t["when"]:
            for f in ([c] if isinstance(c, str) else c):
                if f not in used: used.append(f)

    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><title>化学物質関係法令 確認点・必要実施事項一覧</title>
<style>
@page {{ size: A4; margin: 15mm 14mm 14mm; }}
*, *::before, *::after {{ box-sizing: border-box; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ margin:0; font-family:"IPAPGothic","IPAGothic",sans-serif; color:#16202e;
       font-size:9.2pt; line-height:1.65; }}
h1,h2,h3 {{ margin:0; }}

/* 表紙 */
.cover {{ break-after: page; padding-top: 26mm; }}
.cover .rule {{ height:5px; background:#1f3f73; margin-bottom:9mm; }}
.cover .eyebrow {{ font-size:8.6pt; letter-spacing:.22em; color:#1f3f73; margin-bottom:4mm; }}
.cover h1 {{ font-size:23pt; line-height:1.35; letter-spacing:.02em; font-weight:700; }}
.cover .sub {{ font-size:10pt; color:#3d4a5e; margin-top:5mm; max-width:132mm; line-height:1.85; }}
.cover .facts {{ display:grid; grid-template-columns:repeat(3,1fr); gap:0; margin-top:12mm;
                 border-top:1px solid #c9d2e0; border-bottom:1px solid #c9d2e0; }}
.cover .facts div {{ padding:5mm 0; border-right:1px solid #e3e8f0; }}
.cover .facts div:last-child {{ border-right:0; }}
.cover .facts .k {{ font-size:8pt; color:#66718a; }}
.cover .facts .v {{ font-size:19pt; font-weight:700; color:#1f3f73; line-height:1.25; }}
.cover .fill {{ margin-top:12mm; border:1px solid #c9d2e0; padding:6mm 7mm; }}
.cover .fill p {{ margin:0 0 4mm; font-size:8.6pt; color:#66718a; }}
.cover .fill .line {{ display:flex; gap:6mm; }}
.cover .fill .line span {{ flex:1; border-bottom:1px solid #98a4b8; padding-bottom:6mm; font-size:8.4pt; color:#66718a; }}
.cover .note {{ margin-top:11mm; font-size:8.2pt; color:#5c6779; line-height:1.85;
                border-left:3px solid #1f3f73; padding:1mm 0 1mm 5mm; }}

/* 凡例 */
.legend {{ break-after: page; }}
.legend h2 {{ font-size:13pt; color:#1f3f73; border-bottom:2px solid #1f3f73; padding-bottom:2mm; margin-bottom:5mm; }}
.legend table {{ width:100%; border-collapse:collapse; font-size:8.6pt; margin-bottom:7mm; }}
.legend th, .legend td {{ border:1px solid #d2d9e6; padding:2.2mm 3mm; text-align:left; vertical-align:top; }}
.legend th {{ background:#eef2f8; color:#3d4a5e; font-weight:700; white-space:nowrap; }}
.legend h3 {{ font-size:10pt; margin:0 0 3mm; color:#16202e; }}
.legend .cols {{ column-count:2; column-gap:8mm; font-size:8.4pt; }}
.legend .cols p {{ margin:0 0 1.6mm; break-inside:avoid; }}
.legend .cols b {{ color:#1f3f73; }}

/* 本文 */
.law {{ break-inside:auto; margin-bottom:7mm; }}
.law h2 {{ font-size:12pt; color:#1f3f73; border-bottom:2px solid #1f3f73;
           padding:0 0 1.8mm; margin:0 0 4mm; break-after:avoid; display:flex;
           align-items:baseline; gap:3mm; }}
.law h2 .ln {{ font-size:8.4pt; color:#8a97ad; letter-spacing:.1em; }}
.law h2 .cnt {{ margin-left:auto; font-size:8.2pt; color:#66718a; font-weight:400; }}
.item {{ display:grid; grid-template-columns:16mm 1fr; gap:3mm; break-inside:avoid;
         padding:2.6mm 0 3mm; border-bottom:1px solid #e6ebf3; }}
.item .no {{ font-size:8pt; color:#8a97ad; padding-top:.6mm; letter-spacing:.04em; }}
.item h3 {{ font-size:10.2pt; font-weight:700; line-height:1.5; }}
.meta {{ margin:1.4mm 0 0; font-size:8pt; color:#66718a; }}
.meta .art {{ color:#1f3f73; font-weight:700; }}
.meta .tag {{ display:inline-block; border:1px solid #c9d2e0; border-radius:2mm;
              padding:.2mm 1.8mm; margin-left:1.6mm; background:#f4f7fb; }}
.cond, .memo {{ margin:1.8mm 0 0; font-size:8.6pt; line-height:1.7; }}
.cond {{ background:#f2f5fa; border-left:2px solid #99a8c4; padding:1.4mm 3mm; color:#3d4a5e; }}
.cond b, .memo b {{ display:inline-block; min-width:17mm; color:#1f3f73; font-size:8pt; }}
.memo {{ color:#25324a; }}

/* 巻末 */
.tail {{ break-before: page; }}
.tail h2 {{ font-size:12pt; color:#1f3f73; border-bottom:2px solid #1f3f73; padding-bottom:2mm; margin-bottom:5mm; }}
.tail .cols {{ column-count:2; column-gap:8mm; font-size:8.4pt; }}
.tail .cols p {{ margin:0 0 1.8mm; break-inside:avoid; }}
.tail .cols b {{ color:#1f3f73; }}
.tail .disc {{ margin-top:7mm; border:1px solid #c9d2e0; padding:5mm 6mm; font-size:8.4pt;
               line-height:1.85; color:#3d4a5e; }}
.tail .disc b {{ color:#16202e; }}
</style></head><body>

<div class="cover">
  <div class="rule"></div>
  <p class="eyebrow">工場内で使用・消費する化学品</p>
  <h1>化学物質関係法令<br>確認点・必要実施事項一覧</h1>
  <p class="sub">工場で化学品を使用・消費する事業場に生じ得る法令上の義務を、法令ごとに整理したものです。
    それぞれについて、どのような場合に該当するのか（該当条件）、何を行う必要があるのか（必要実施事項）、
    実施にあたって何を確認すべきか（確認点）を示しています。</p>
  <div class="facts">
    <div><p class="k">収録法令</p><p class="v">{len(laws)}</p></div>
    <div><p class="k">確認・実施項目</p><p class="v">{len(tasks)}</p></div>
    <div><p class="k">作成日</p><p class="v" style="font-size:12pt">{today}</p></div>
  </div>
  <div class="fill">
    <p>この一覧を適用する事業場</p>
    <div class="line"><span>事業場名</span><span>所在地</span></div>
    <div class="line" style="margin-top:7mm"><span>化学物質管理者</span><span>確認日</span></div>
  </div>
  <p class="note">本書は法令の該当関係を機械的に整理した実務用の資料です。
    最終的な適法性の判断、所轄官庁への確認、専門家（衛生管理者・作業環境測定士・危険物取扱者等）への
    相談に代わるものではありません。法令は改正されます。適用にあたっては必ず最新の条文を確認してください。</p>
</div>

<div class="legend">
  <h2>この一覧の見方</h2>
  <table>
    <tr><th>該当条件</th><td>その義務が生じる条件です。いずれかを満たすと該当します。「かつ」でつながれた条件は、すべてを満たす場合に該当します。</td></tr>
    <tr><th>必要実施事項</th><td>該当した場合に行う必要のあることです。見出しに掲げています。</td></tr>
    <tr><th>確認点</th><td>実施にあたって押さえるべき期限・頻度・対象範囲・記録の要件です。</td></tr>
    <tr><th>分類</th><td>{E(" ／ ".join(cats))}</td></tr>
    <tr><th>周期</th><td>実施の頻度です。「事由発生時」は事象が起きたときに行うもの、「随時（1回）」は一度行えばよいものです。</td></tr>
    <tr><th>記録保存</th><td>法定の最短保存年数です。特別管理物質・がん原性物質に関する記録には30年保存のものがあります。</td></tr>
  </table>
  <h3>収録法令</h3>
  <div class="cols">
    {"".join(f'<p><b>{i:02d}</b>　{E(l)}<span style="color:#8a97ad">（{sum(1 for t in tasks if t["law"]==l)}項目）</span></p>' for i, l in enumerate(laws, 1))}
  </div>
</div>

{"".join(body)}

<div class="tail">
  <h2>該当条件の一覧</h2>
  <div class="cols">
    {"".join(f'<p><b>■</b> {E(FLAG.get(f, f))}</p>' for f in used)}
  </div>
  <div class="disc">
    <p><b>本書の位置づけ。</b>　法令の該当判定を機械的に行い、対応漏れを可視化するための実務資料です。
      個々の事業場の設備・作業内容・取扱量によって、ここに掲げた以外の義務が生じることも、
      逆に適用除外となることもあります。</p>
    <p style="margin-top:3mm"><b>数量に関わる判定について。</b>　消防法の指定数量の倍数、化管法の年間取扱量、
      有機則の消費量による適用除外などは、実際の取扱量・貯蔵量から算定する必要があります。
      本書はその算定結果を前提とした義務の一覧です。</p>
    <p style="margin-top:3mm"><b>改正への対応。</b>　労働安全衛生法のラベル表示・SDS交付・リスクアセスメントの
      対象物質は段階的に拡大しています。取り扱う物質が新たに対象となっていないか、定期的に確認してください。</p>
  </div>
</div>
</body></html>'''



# ============================================================
# 画面で読むためのHTML
# ============================================================
def build_web(tasks):
    laws = []
    for t in tasks:
        if t["law"] not in laws: laws.append(t["law"])
    cats = []
    for t in tasks:
        if t["cat"] not in cats: cats.append(t["cat"])
    today = datetime.date.today().strftime("%Y年%m月%d日")
    data = [dict(law=t["law"], art=t["art"], title=t["title"], cat=t["cat"],
                 cyc=cyc_label(t["cyc"]), keep=(f'{t["keep"]}年' if t["keep"] else ""),
                 cond=cond_text(t["when"]), memo=t["memo"]) for t in tasks]
    payload = json.dumps({"laws": laws, "cats": cats, "items": data}, ensure_ascii=False)

    return '''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>化学物質法令リファレンス</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700&family=BIZ+UDPMincho&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{
  --paper:#f4f6fa; --surface:#fff; --surface-2:#eaeef5; --surface-3:#dfe5ef;
  --ink:#111721; --ink-2:#39445a; --muted:#66718a; --line:#d2d9e6; --line-2:#b3bdd0;
  --accent:#1f3f73; --accent-2:#33609f; --accent-soft:#e4ebf7; --on-accent:#fff;
  --ok:#2a6b48; --ok-soft:#e0efe6; --warn:#95650a; --warn-soft:#f8eed6;
  --crit:#9e1c31; --crit-soft:#f8e3e7;
  --grid:rgba(31,63,115,.07);
  --shadow:0 1px 2px rgba(17,23,33,.06), 0 6px 18px -12px rgba(17,23,33,.28);
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  --sans:"BIZ UDPGothic","Hiragino Sans","Yu Gothic UI","Meiryo",system-ui,sans-serif;
  --serif:"BIZ UDPMincho","Hiragino Mincho ProN","Yu Mincho",serif;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --paper:#0d1117; --surface:#151c26; --surface-2:#1c2531; --surface-3:#26313f;
  --ink:#e7ecf5; --ink-2:#b9c4d6; --muted:#8e9bb2; --line:#2a3542; --line-2:#3b4859;
  --accent:#82abec; --accent-2:#a2c2f4; --accent-soft:#182741; --on-accent:#0d1117;
  --ok:#71c295; --ok-soft:#14271d; --warn:#dfb257; --warn-soft:#2c2413;
  --crit:#f0879b; --crit-soft:#2e141a; --grid:rgba(130,171,236,.09);
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 22px -14px rgba(0,0,0,.8);
}}
:root[data-theme="dark"]{
  --paper:#0d1117; --surface:#151c26; --surface-2:#1c2531; --surface-3:#26313f;
  --ink:#e7ecf5; --ink-2:#b9c4d6; --muted:#8e9bb2; --line:#2a3542; --line-2:#3b4859;
  --accent:#82abec; --accent-2:#a2c2f4; --accent-soft:#182741; --on-accent:#0d1117;
  --ok:#71c295; --ok-soft:#14271d; --warn:#dfb257; --warn-soft:#2c2413;
  --crit:#f0879b; --crit-soft:#2e141a; --grid:rgba(130,171,236,.09);
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 22px -14px rgba(0,0,0,.8);
}
*,*::before,*::after{box-sizing:border-box}
html{color-scheme:light dark; scroll-behavior:smooth}
body{margin:0; background:var(--paper); color:var(--ink); font-family:var(--sans);
     font-size:14px; line-height:1.75; -webkit-font-smoothing:antialiased}
img{max-width:100%} [hidden]{display:none!important}
h1,h2,h3{margin:0; text-wrap:balance} p{margin:0}
button,input,select{font:inherit; color:inherit}
:focus-visible{outline:2px solid var(--accent-2); outline-offset:2px; border-radius:3px}
@media (prefers-reduced-motion:reduce){*{animation:none!important; transition:none!important; scroll-behavior:auto}}
.wrap{max-width:1180px; margin:0 auto; padding:0 20px}

.masthead{background:var(--surface); border-bottom:1px solid var(--line);
  background-image:repeating-linear-gradient(to right,var(--grid) 0 1px,transparent 1px 28px),
                   repeating-linear-gradient(to bottom,var(--grid) 0 1px,transparent 1px 28px)}
.mast-in{display:flex; flex-wrap:wrap; gap:18px; align-items:flex-end; padding:22px 0 18px}
.mast-id{flex:1 1 340px; min-width:0}
.eyebrow{font-family:var(--mono); font-size:11px; letter-spacing:.14em; text-transform:uppercase;
  color:var(--accent); margin-bottom:4px}
.masthead h1{font-family:var(--serif); font-size:28px; font-weight:400; letter-spacing:.02em; line-height:1.3}
.mast-sub{color:var(--muted); font-size:12.5px; margin-top:5px; max-width:64ch}
.mast-meta{display:flex; gap:8px; align-items:center; flex-wrap:wrap}
.chip{display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border:1px solid var(--line-2);
  border-radius:999px; background:var(--surface-2); font-size:12px; color:var(--ink-2); white-space:nowrap}
.chip b{font-family:var(--mono); font-weight:600; color:var(--ink)}
.iconbtn{border:1px solid var(--line-2); background:var(--surface-2); color:var(--ink-2);
  border-radius:6px; padding:5px 10px; font-size:12px; cursor:pointer}
.iconbtn:hover{background:var(--surface-3); color:var(--ink)}

.bar{position:sticky; top:0; z-index:20; background:var(--surface); border-bottom:1px solid var(--line); box-shadow:var(--shadow)}
.bar-in{display:flex; gap:10px; align-items:center; flex-wrap:wrap; padding:11px 0}
.bar input[type=search]{background:var(--surface); border:1px solid var(--line-2); border-radius:6px;
  padding:7px 11px; font-size:13px; flex:1 1 240px; min-width:0}
.cats{display:flex; gap:5px; flex-wrap:wrap}
.cat{border:1px solid var(--line-2); background:transparent; color:var(--muted); border-radius:999px;
  padding:4px 11px; font-size:12px; cursor:pointer; white-space:nowrap}
.cat:hover{color:var(--ink); border-color:var(--accent)}
.cat[aria-pressed="true"]{background:var(--accent); border-color:var(--accent); color:var(--on-accent); font-weight:700}
.hits{font-size:12px; color:var(--muted); font-family:var(--mono); margin-left:auto; white-space:nowrap}

main{padding:22px 0 70px}
.cols{display:grid; grid-template-columns:210px 1fr; gap:26px; align-items:start}
@media (max-width:860px){.cols{grid-template-columns:1fr; gap:14px}}
.toc{position:sticky; top:70px; max-height:calc(100vh - 92px); overflow:auto; padding-right:4px}
.toc .h{font-family:var(--mono); font-size:11px; letter-spacing:.13em; text-transform:uppercase;
  color:var(--muted); margin-bottom:8px}
.toc a{display:flex; gap:8px; align-items:baseline; padding:4px 8px; border-radius:5px;
  color:var(--ink-2); text-decoration:none; font-size:12.5px; line-height:1.5}
.toc a:hover{background:var(--surface-2); color:var(--ink)}
.toc a .n{font-family:var(--mono); font-size:10.5px; color:var(--muted); flex:none}
.toc a .c{margin-left:auto; font-family:var(--mono); font-size:10.5px; color:var(--muted)}
.toc a.off{opacity:.35}
@media (max-width:860px){
  .toc{position:static; max-height:none; display:flex; gap:6px; overflow-x:auto; padding-bottom:6px}
  .toc .h{display:none}
  .toc a{border:1px solid var(--line); border-radius:999px; white-space:nowrap; padding:4px 11px}
  .toc a .c{margin-left:4px}
}

.law{margin-bottom:26px; scroll-margin-top:72px}
.law-hd{display:flex; align-items:baseline; gap:10px; border-bottom:2px solid var(--accent);
  padding-bottom:6px; margin-bottom:12px}
.law-hd h2{font-family:var(--serif); font-size:19px; font-weight:400; letter-spacing:.02em}
.law-hd .n{font-family:var(--mono); font-size:11px; color:var(--muted); letter-spacing:.08em}
.law-hd .c{margin-left:auto; font-size:11.5px; color:var(--muted); font-family:var(--mono)}
.item{background:var(--surface); border:1px solid var(--line); border-radius:8px;
  padding:13px 16px; margin-bottom:9px}
.item h3{font-size:15px; font-weight:700; line-height:1.55}
.item .meta{display:flex; gap:6px; flex-wrap:wrap; align-items:center; margin-top:6px}
.item .art{font-family:var(--mono); font-size:11.5px; color:var(--accent); font-weight:500}
.tag{display:inline-block; border:1px solid var(--line-2); background:var(--surface-2);
  border-radius:999px; padding:1px 8px; font-size:11px; color:var(--ink-2); white-space:nowrap}
.tag.cat-sel{background:var(--accent-soft); border-color:var(--accent); color:var(--accent); font-weight:700}
.field{display:grid; grid-template-columns:78px 1fr; gap:10px; margin-top:9px; font-size:12.8px; line-height:1.8}
.field .k{font-family:var(--mono); font-size:10.5px; letter-spacing:.06em; color:var(--muted); padding-top:3px}
.field.cond .v{background:var(--surface-2); border-left:2px solid var(--line-2);
  padding:5px 10px; border-radius:0 5px 5px 0; color:var(--ink-2)}
.field.memo .v{color:var(--ink-2)}
@media (max-width:560px){.field{grid-template-columns:1fr; gap:2px}.field .k{padding-top:0}}
mark{background:var(--warn-soft); color:var(--ink); padding:0 2px; border-radius:2px}

.empty{padding:40px 16px; text-align:center; color:var(--muted); font-size:13.5px}
.foot{border-top:1px solid var(--line); margin-top:30px; padding:18px 0 44px; color:var(--muted); font-size:11.5px}
.foot .wrap{display:flex; flex-direction:column; gap:7px; max-width:86ch}
.foot b{color:var(--ink-2)}

@media print{
  .bar,.toc,.mast-meta{display:none!important}
  body{background:#fff; font-size:10pt}
  .cols{grid-template-columns:1fr}
  .item{break-inside:avoid; border-color:#bbb}
  .law-hd{break-after:avoid}
  @page{size:A4; margin:14mm}
}
</style>
</head>
<body>

<header class="masthead"><div class="wrap mast-in">
  <div class="mast-id">
    <p class="eyebrow">工場内で使用・消費する化学品</p>
    <h1>化学物質法令リファレンス</h1>
    <p class="mast-sub">工場で化学品を使用・消費する事業場に生じ得る法令上の義務を、法令ごとに整理しています。
      それぞれについて、どのような場合に該当するのか、何を行う必要があるのか、実施にあたって何を確認すべきかを示します。</p>
  </div>
  <div class="mast-meta">
    <span class="chip">収録法令 <b id="cLaw">0</b></span>
    <span class="chip">項目 <b id="cItem">0</b></span>
    <button class="iconbtn" id="btnPrint" type="button">印刷 / PDF</button>
    <button class="iconbtn" id="btnTheme" type="button">◐ テーマ</button>
  </div>
</div></header>

<div class="bar"><div class="wrap bar-in">
  <input type="search" id="q" placeholder="法令名・実施事項・確認点・条文で検索" autocomplete="off" spellcheck="false">
  <div class="cats" id="cats"></div>
  <span class="hits" id="hits"></span>
</div></div>

<main class="wrap"><div class="cols">
  <nav class="toc" id="toc" aria-label="法令の目次"></nav>
  <div id="list"></div>
</div></main>

<footer class="foot"><div class="wrap">
  <p><b>この資料の位置づけ。</b> 法令の該当関係を機械的に整理した実務用の資料です。最終的な適法性の判断、所轄官庁への確認、専門家（衛生管理者・作業環境測定士・危険物取扱者等）への相談に代わるものではありません。</p>
  <p><b>個別性について。</b> 事業場の設備・作業内容・取扱量によって、ここに掲げた以外の義務が生じることも、逆に適用除外となることもあります。消防法の指定数量の倍数、化管法の年間取扱量、有機則の消費量による適用除外などは、実際の取扱量・貯蔵量から算定してください。</p>
  <p><b>改正について。</b> 労働安全衛生法のラベル表示・SDS交付・リスクアセスメントの対象物質は段階的に拡大しています。適用にあたっては必ず最新の条文を確認してください。</p>
  <p id="ver"></p>
</div></footer>

<script>
"use strict";
const DATA = __PAYLOAD__;
const GEN = "__TODAY__";
const $ = s => document.querySelector(s);
const esc = s => String(s==null?"":s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let query = "", cat = "";

function hl(text){
  const t = esc(text);
  if(!query) return t;
  try{
    return t.replace(new RegExp(query.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&"), "gi"), m => `<mark>${m}</mark>`);
  }catch(e){ return t; }
}
const matches = it => {
  if(cat && it.cat !== cat) return false;
  if(!query) return true;
  const q = query.toLowerCase();
  return [it.law, it.art, it.title, it.cond, it.memo, it.cat, it.cyc].some(v => String(v).toLowerCase().includes(q));
};

function render(){
  const hit = DATA.items.filter(matches);
  const byLaw = {};
  hit.forEach(it => (byLaw[it.law] = byLaw[it.law] || []).push(it));
  const shown = DATA.laws.filter(l => byLaw[l]);

  $("#toc").innerHTML = DATA.laws.map((l, i) =>
    `<a href="#law-${i}" class="${byLaw[l] ? "" : "off"}"><span class="n">${String(i+1).padStart(2,"0")}</span><span>${esc(l)}</span><span class="c">${(byLaw[l]||[]).length}</span></a>`
  ).join("");

  $("#list").innerHTML = shown.length ? shown.map(l => {
    const i = DATA.laws.indexOf(l);
    return `<section class="law" id="law-${i}">
      <div class="law-hd"><span class="n">${String(i+1).padStart(2,"0")}</span>
        <h2>${hl(l)}</h2><span class="c">${byLaw[l].length}項目</span></div>
      ${byLaw[l].map(it => `<article class="item">
        <h3>${hl(it.title)}</h3>
        <div class="meta"><span class="art">${hl(it.art)}</span>
          <span class="tag${cat===it.cat?" cat-sel":""}">${esc(it.cat)}</span>
          <span class="tag">${esc(it.cyc)}</span>
          ${it.keep ? `<span class="tag">記録保存 ${esc(it.keep)}</span>` : ""}</div>
        <div class="field cond"><span class="k">該当条件</span><span class="v">${hl(it.cond)}</span></div>
        <div class="field memo"><span class="k">確認点</span><span class="v">${hl(it.memo)}</span></div>
      </article>`).join("")}
    </section>`;
  }).join("") : `<div class="empty">条件に合う項目がありません。検索語を変えるか、分類の絞り込みを外してください。</div>`;

  $("#hits").textContent = (query || cat)
    ? `${hit.length} / ${DATA.items.length} 項目`
    : `${DATA.items.length} 項目`;
}

function init(){
  try{ const th = localStorage.getItem("chem-ref-theme"); if(th) document.documentElement.setAttribute("data-theme", th); }catch(e){}
  $("#cLaw").textContent = DATA.laws.length;
  $("#cItem").textContent = DATA.items.length;
  $("#ver").textContent = `作成 ${GEN}　化学物質法令チェック台帳のチェック項目定義から生成しています。`;
  $("#cats").innerHTML = DATA.cats.map(c =>
    `<button class="cat" type="button" data-cat="${esc(c)}" aria-pressed="false">${esc(c)}</button>`).join("");
  $("#cats").addEventListener("click", e => {
    const b = e.target.closest("[data-cat]"); if(!b) return;
    cat = (cat === b.dataset.cat) ? "" : b.dataset.cat;
    document.querySelectorAll("[data-cat]").forEach(x => x.setAttribute("aria-pressed", String(x.dataset.cat === cat)));
    render();
  });
  $("#q").addEventListener("input", e => { query = e.target.value.trim(); render(); });
  $("#btnPrint").addEventListener("click", () => window.print());
  $("#btnTheme").addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme");
    const next = cur === "dark" ? "light" : (cur === "light" ? null : "dark");
    if(next) document.documentElement.setAttribute("data-theme", next);
    else document.documentElement.removeAttribute("data-theme");
    try{ localStorage.setItem("chem-ref-theme", next || ""); }catch(e){}
  });
  render();
}
init();
</script>
</body></html>'''.replace("__PAYLOAD__", payload).replace("__TODAY__", today)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="法令チェック項目の一覧を組む")
    ap.add_argument("--mode", choices=["print", "web"], default="print")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    tasks = load_tasks()
    out = a.out or ("chem-checklist-print.html" if a.mode == "print" else "chem-checklist.html")
    io.open(out, "w", encoding="utf-8").write(
        build_html(tasks) if a.mode == "print" else build_web(tasks))
    print("%s を出力しました（%d法令 / %d項目 / mode=%s）" %
          (out, len({t["law"] for t in tasks}), len(tasks), a.mode))
