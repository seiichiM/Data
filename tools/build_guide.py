# -*- coding: utf-8 -*-
"""
成分非開示の製品を含むSDSだけで化学物質管理を回すための実務ガイドを組む。

裾切り値・保存年数・照会項目は chemical-compliance.html の定義から取るため、
台帳・リファレンス・ガイドの三者が食い違わない。

  --mode web     画面で読むためのHTML（目次つき）
  --mode print   A4印刷用のHTML。Chromium の --print-to-pdf でPDF化する
"""
import io, json, re, sys, datetime, argparse, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import guide_content as C

SRC = "chemical-compliance.html"
E = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def js_rows(name, src):
    """JSの配列リテラルを1要素ずつ取り出してJSONとして読む。"""
    blk = re.search(r'const %s = \[(.*?)\n\];' % name, src, re.S).group(1)
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
    return [json.loads(r) for r in rows]

def load_defs():
    s = io.open(SRC, encoding="utf-8").read()
    decl = {r[0]: dict(label=r[1], pct=bool(r[2]), hint=r[3]) for r in js_rows("DECL_ITEMS", s)}
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
    tasks = [dict(zip(("id","law","art","title","cat","cyc","when","keep","memo"), json.loads(r)))
             for r in rows]
    return decl, tasks

# ---------- 本文の組み立て ----------
def md(t):
    """**強調** と `等幅` だけを扱う軽い記法。"""
    t = E(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r'<code>\1</code>', t)
    return t

def table(headers, rows, cls=""):
    h = "".join("<th>%s</th>" % md(x) for x in headers)
    b = "".join("<tr>" + "".join("<td>%s</td>" % (x if x.startswith("<") else md(x))
                                 for x in r) + "</tr>" for r in rows)
    return ('<div class="tw"><table class="%s"><thead><tr>%s</tr></thead>'
            '<tbody>%s</tbody></table></div>' % (cls, h, b))

def note(kind, title, body):
    return ('<aside class="note n-%s"><p class="nt">%s</p><p>%s</p></aside>'
            % (kind, md(title), md(body)))

def chapters(decl, tasks):
    ch = []

    # ---- 第1章 ----
    body = [
      "<p>" + md(
        "SDSは日本産業規格 JIS Z 7253 に沿って16の項目で構成されます。"
        "化学物質管理の判定に直接効くのは、そのうち次の6項目です。"
        "成分が非開示でも、**第15項は通常そのまま記載されます**。"
        "供給者にとっては、対象法令を伝えないほうが譲渡・提供者としての義務に反するためです。") + "</p>",
      table(["項目", "読み取ること", "非開示だと失われるもの"], [
        ["第2項 危険有害性の要約",
         "GHS区分、絵表示、注意書き。リスクアセスメントの出発点になります",
         "失われません（製品としての区分が書かれます）"],
        ["第3項 組成・成分情報",
         "成分名・CAS番号・含有率",
         "**ここが空白になります。** 物質単位の判定がすべて止まります"],
        ["第8項 ばく露防止・保護措置",
         "管理濃度、許容濃度、濃度基準値、保護具の種類",
         "物質ごとの値は落ちますが、製品としての保護具指定は残ります"],
        ["第9項 物理的・化学的性質",
         "引火点、沸点、蒸気圧。消防法の品名と換気の要否に効きます",
         "失われません"],
        ["第14項 輸送上の注意",
         "国連番号、クラス。危険物としての性状が裏取りできます",
         "失われません"],
        ["第15項 適用法令",
         "**該当する法令の名称。非開示製品ではここが唯一の手がかりです**",
         "失われません"],
      ]),
      note("warn", "第15項が「該当なし」でも安心はできません",
        "裾切り値未満のため記載していないだけのことがあります。"
        "また「本製品は○○法の対象外です」という記載は製品単位の話で、"
        "成分単位では該当することがあります。いずれも含有率を聞いて確かめてください。"),
      note("crit", "SDSの日付を必ず見てください",
        "令和6年4月1日に安衛法の表示・通知対象物が大きく増えました。"
        "それ以前に発行されたSDSは、現在は対象になっている物質を"
        "第15項に書いていない可能性があります。"
        "発行日または改訂日が令和6年3月以前のものは、改訂版を請求してください。"),
    ]
    ch.append(("SDSのどこを見るか", "sds", body))

    # ---- 第2章 ----
    rows = [[f"レベル{a}", f"<b>{E(b)}</b>", md(c), md(d), md(e)] for a,b,c,d,e in C.LEVELS]
    body = [
      "<p>" + md(
        "同じ「SDSがある」状態でも、開示の程度で到達できるところが変わります。"
        "手持ちのSDSを3つに仕分けるところから始めてください。"
        "**レベルCだけを供給者への照会に回せば、作業量は実際の非開示品の数まで下がります。**") + "</p>",
      table(["", "開示の程度", "SDSの見え方", "確定できること", "残る制限"], rows),
      note("ok", "レベルBは実務上いちばん多い形です",
        "多くの供給者は「法令の対象になる成分だけ」を開示します。"
        "これで法令判定は全部できます。含有率が「1〜5%」のような範囲表記のときは、"
        "**上限値で計算してください。** 届出漏れが起きません。"),
    ]
    ch.append(("開示のレベルを3つに分ける", "levels", body))

    # ---- 第3章 ----
    rows = []
    for key, phrases in C.SEC15:
        d = decl.get(key)
        if not d: continue
        rows.append(["<br>".join("・" + E(p) for p in phrases),
                     "<b>%s</b>" % E(d["label"]),
                     "要" if d["pct"] else "不要",
                     md(d["hint"] or "—")])
    body = [
      "<p>" + md(
        "第15項の書き方は供給者ごとに揺れます。条番号を書くもの、規則名だけのもの、"
        "略称のものがあります。**条番号か規則名のどちらかが一致すれば同じもの**として扱ってください。"
        "左の表記を見つけたら、台帳の対応する照会項目を「含有あり」にします。") + "</p>",
      table(["第15項によくある表記", "台帳の照会項目", "含有率", "判定に効くこと"], rows, "sec15"),
      "<h3>第15項に書かれていても、照会項目にしないもの</h3>",
      table(["記載", "扱い"], [[f"<b>{E(a)}</b>", md(b)] for a, b in C.SEC15_NOT]),
      note("warn", "化審法の区分を取り違えないでください",
        "「一般化学物質」「優先評価化学物質」「監視化学物質」は、"
        "製造・輸入事業者の届出区分です。取扱事業場に措置を課すものではありません。"
        "**第一種特定化学物質**と**第二種特定化学物質**だけが使用の規制に関わります。"),
    ]
    ch.append(("第15項の表記から照会項目へ", "sec15", body))

    # ---- 第4章 ----
    rows = []
    for law, mark, fixed, pending in C.BY_LAW:
        rows.append(["<b>%s</b>" % E(law), E(mark),
                     "<ul>" + "".join("<li>%s</li>" % md(x) for x in fixed) + "</ul>",
                     md(pending)])
    body = [
      "<p>" + md(
        "ここが本題です。**含有率が分からなくても、法令名が分かれば確定する義務はかなりあります。**"
        "先にこれを実施しておけば、照会の回答を待つあいだも管理が止まりません。") + "</p>",
      table(["法令", "第15項の記載例", "含有率なしで確定すること", "含有率・数量がないとできないこと"],
            rows, "bylaw"),
      note("crit", "化管法のPRTR届出だけは例外です",
        "「含有あり」だけでは足りません。物質名・政令番号・含有率・年間取扱量のすべてが要ります。"
        "化管法上、指定化学物質の名称と含有率はSDSの記載事項なので、"
        "**これは法的に請求できます。** 照会の優先度を上げてください。"),
    ]
    ch.append(("法令名だけで確定する義務", "fixed", body))

    # ---- 第5章 ----
    rows = [[f"段階{a}", f"<b>{E(b)}</b>", "<span class='q'>「%s」</span>" % E(c), E(d), md(e)]
            for a,b,c,d,e in C.ASK_LEVELS]
    body = [
      "<p>" + md(
        "全成分の開示を求めると営業秘密を理由に断られます。"
        "**聞き方を下げるほど答えてもらいやすくなり、それでも法令判定には足ります。**"
        "段階3から入って、足りないところだけ段階2・1へ上げるのが実務的です。") + "</p>",
      table(["", "聞く内容", "文面", "回答率", "備考"], rows, "ask"),
      "<h3>法的に請求できる範囲</h3>",
      "<p>" + md(
        "**労働安全衛生法第57条の2の通知対象物については、「成分及びその含有量」の通知が法定事項です。**"
        "令和6年4月1日から、含有量は重量パーセントでの通知が原則になりました"
        "（それ以前は10%刻みの範囲表記が認められていました）。"
        "化管法の指定化学物質についても、名称と含有率はSDSの記載事項です。") + "</p>",
      "<p>" + md(
        "つまり「営業秘密なので含有率は出せません」は、"
        "**これらの対象物質に関しては通りません。** 照会状にこの根拠を書き添えてください。") + "</p>",
      note("warn", "例外規定の細部は原典で確認してください",
        "営業上の秘密に当たる場合の取扱いには別途の定めがあります。"
        "強く求める前に、告示本文または所轄労働基準監督署でご確認ください。"),
      "<h3>回収の管理</h3>",
      "<ul class='steps'>"
      "<li>回答期限を切る（2〜3週間が目安）</li>"
      "<li>回答者名・回答書番号・回答日を必ず控える。台帳の「回答者・回答書番号」「回答日」欄に入れます</li>"
      "<li>期限を過ぎたものは督促し、督促した事実も記録する</li>"
      "<li>回答が得られないまま使い続ける場合は、その判断と理由を残す</li>"
      "</ul>",
    ]
    ch.append(("供給者への聞き方", "ask", body))

    # ---- 第6章 ----
    body = [
      "<p>" + md(
        "回答が来ない、あるいは一部しか来ないことは必ず起きます。"
        "そのときに**「分からないから対象外」としないこと**が、この管理のいちばん重要な原則です。") + "</p>",
      note("crit", "不明は非該当ではありません",
        "台帳は未回答の項目を対象外と判断しません。"
        "「回答が一部のみ 12/20項目」として要確認に残り、回答が揃うまで判定を確定させません。"
        "ここを曖昧にすると、あとで該当が判明したときに遡って是正できなくなります。"),
      "<h3>着地のさせ方</h3>",
      table(["選択肢", "内容", "向いている場面"], [
        ["最悪ケース運用",
         "該当する前提で措置する。特化則相当の局所排気・作業環境測定・特殊健診まで実施する",
         "代替品がなく、使用を止められない場合。コストは上がりますが違法にはなりません"],
        ["供給者の切替",
         "開示する供給者の同等品に変える",
         "同等品がある場合。**もっとも確実です**"],
        ["購買条件への織り込み",
         "取引基本契約や購買仕様書に、SDSの改訂提供と裾切り値超過の有無の回答を条項として入れる",
         "新規採用品から効きます。長期的にはこれがいちばん効きます"],
        ["使用の中止",
         "該当のおそれが高く、措置も代替も難しい場合",
         "製造等禁止物質・化審法第一種特定化学物質のおそれがある場合は、これ以外の選択肢はありません"],
      ]),
      "<h3>記録に残すこと</h3>",
      "<p>" + md(
        "立入検査で問われるのは「なぜ判定できていないか」ではなく"
        "「判定できないことを認識し、何をしたか」です。次の3つを残してください。") + "</p>",
      "<ul class='steps'>"
      "<li>SDS第15項に何が書かれていたか（SDSそのものを保管）</li>"
      "<li>供給者に何をいつ聞き、どう回答されたか（照会状の控えと回答書）</li>"
      "<li>回答が得られない状態で、どう扱うと判断したか（安全衛生委員会の議事録が使えます）</li>"
      "</ul>",
    ]
    ch.append(("情報が埋まらないときの扱い", "gaps", body))

    # ---- 第7章 ----
    body = [
      "<p>" + md("SDS起点の管理は、次の4つの機会に動かします。") + "</p>",
      table(["機会", "やること", "期限・周期"], [
        ["新規採用時",
         "SDSを入手し、開示レベルを判定。レベルCなら購買が発注する前に照会をかける",
         "発注前"],
        ["定期の棚卸し",
         "全製品のSDSの発行日を確認し、古いものは改訂版を請求。照会の未回答を督促",
         "年1回"],
        ["SDSの定期確認",
         "「人体に及ぼす作用」に変更がないかを確認し、変更があればSDSを更新して再度周知",
         "**5年以内ごと**（安衛則第34条の2の5）"],
        ["変更時",
         "供給者の変更、製品の仕様変更、作業内容の変更があればリスクアセスメントをやり直す",
         "都度"],
      ]),
      note("ok", "購買を巻き込むのがいちばん効きます",
        "照会は安全衛生部門が単独でやると回収率が上がりません。"
        "**発注前の条件**にしてしまえば、供給者は答えざるを得なくなります。"
        "新規採用品からで構いません。既存品は年1回の棚卸しで少しずつ潰していきます。"),
    ]
    ch.append(("年間の回し方", "cycle", body))
    return ch

def appendices(decl, tasks):
    ap = []
    # 付録A 裾切り値
    rows = []
    for key, d in decl.items():
        if not d["pct"]: continue
        rows.append(["<b>%s</b>" % E(d["label"]), md(d["hint"] or "—")])
    ap.append(("裾切り値が要る照会項目", "cutoff", [
      "<p>" + md("次の項目は、「含有あり」の回答だけでは判定が終わりません。"
                 "含有率か、裾切り値を超えるかのYes／Noが要ります。") + "</p>",
      table(["照会項目", "裾切り値"], rows)]))

    # 付録B 保存年数（TASKSから機械的に）
    keeps = {}
    for t in tasks:
        if t["keep"]:
            keeps.setdefault(t["keep"], []).append("%s（%s）" % (t["title"], t["art"]))
    rows = [["<b>%d年</b>" % k, "<br>".join("・" + E(x) for x in sorted(v))]
            for k, v in sorted(keeps.items(), reverse=True)]
    ap.append(("記録の保存年数", "keep", [
      "<p>" + md("台帳の法令タスク定義から機械的に抜き出したものです。"
                 "**特別管理物質とがん原性物質の30年保存**は、"
                 "非開示のまま取り扱っていると最も見落としやすい義務です。") + "</p>",
      table(["保存年数", "対象となる記録"], rows)]))

    # 付録C 照会状
    ap.append(("照会状のひな形", "letter", [
      "<p>" + md("そのまま使えます。別紙には台帳の"
                 "「含有調査依頼書をCSVで保存」で出したものを付けてください。") + "</p>",
      "<pre class='letter'>%s</pre>" % E(C.LETTER)]))
    return ap

# ---------- 見た目 ----------
CSS = """
:root{
  --paper:#f4f6fa; --surface:#fff; --surface-2:#eaeef5; --surface-3:#dfe5ef;
  --ink:#111721; --ink-2:#39445a; --muted:#66718a; --line:#d2d9e6; --line-2:#b3bdd0;
  --accent:#1f3f73; --accent-2:#33609f; --accent-soft:#e4ebf7; --on-accent:#fff;
  --ok:#2a6b48; --ok-soft:#e0efe6; --warn:#95650a; --warn-soft:#f8eed6;
  --crit:#9e1c31; --crit-soft:#f8e3e7;
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
  --crit:#f0879b; --crit-soft:#2e141a;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 22px -14px rgba(0,0,0,.8);
}}
:root[data-theme="dark"]{
  --paper:#0d1117; --surface:#151c26; --surface-2:#1c2531; --surface-3:#26313f;
  --ink:#e7ecf5; --ink-2:#b9c4d6; --muted:#8e9bb2; --line:#2a3542; --line-2:#3b4859;
  --accent:#82abec; --accent-2:#a2c2f4; --accent-soft:#182741; --on-accent:#0d1117;
  --ok:#71c295; --ok-soft:#14271d; --warn:#dfb257; --warn-soft:#2c2413;
  --crit:#f0879b; --crit-soft:#2e141a;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 22px -14px rgba(0,0,0,.8);
}
*{box-sizing:border-box}
body{margin:0; background:var(--paper); color:var(--ink);
     font-family:var(--sans); font-size:15px; line-height:1.85;
     -webkit-text-size-adjust:100%}
code{font-family:var(--mono); font-size:.92em; background:var(--surface-2);
     padding:1px 5px; border-radius:3px}
b{font-weight:700}
.wrap{max-width:1180px; margin:0 auto; padding-inline:20px; padding-block:0}

/* 表紙 */
.cover{padding-block:56px 40px; border-bottom:3px double var(--line-2)}
.eyebrow{font-family:var(--mono); font-size:11.5px; letter-spacing:.16em;
         text-transform:uppercase; color:var(--accent-2); margin:0 0 14px}
.cover h1{font-family:var(--serif); font-weight:700; font-size:clamp(28px,5.2vw,46px);
          line-height:1.3; margin:0 0 18px; text-wrap:balance; letter-spacing:.01em}
.cover .lead{max-width:44em; font-size:16.5px; color:var(--ink-2); margin:0}
.facts{display:flex; flex-wrap:wrap; gap:10px 36px; margin:30px 0 0; padding:0}
.facts div{margin:0}
.facts dt{font-size:11.5px; color:var(--muted); margin:0 0 2px; letter-spacing:.02em}
.facts dd{margin:0; font-family:var(--mono); font-size:26px; font-weight:600;
          color:var(--accent); line-height:1.1; font-variant-numeric:tabular-nums}
.facts dd .u{font-family:var(--sans); font-size:12px; font-weight:400;
             color:var(--ink-2); margin-left:4px}
.meta{display:flex; flex-wrap:wrap; gap:8px 22px; margin-top:28px;
      padding-top:20px; border-top:1px solid var(--line);
      font-family:var(--mono); font-size:11.5px; color:var(--muted)}

/* 本体 2カラム */
.main{display:grid; grid-template-columns:232px minmax(0,1fr); gap:44px;
      align-items:start; padding-block:40px 72px}
@media (max-width:900px){ .main{grid-template-columns:minmax(0,1fr); gap:24px} }

nav.toc{position:sticky; top:16px; font-size:13px; line-height:1.6}
@media (max-width:900px){ nav.toc{position:static; background:var(--surface);
  border:1px solid var(--line); border-radius:8px; padding:16px 18px} }
nav.toc p.tt{font-family:var(--mono); font-size:10.5px; letter-spacing:.14em;
             text-transform:uppercase; color:var(--muted); margin:0 0 10px}
nav.toc ol{list-style:none; margin:0; padding:0; display:flex;
           flex-direction:column; gap:2px}
nav.toc a{display:flex; gap:9px; text-decoration:none; color:var(--ink-2);
          padding:5px 8px; border-radius:5px; border-left:2px solid transparent}
nav.toc a:hover{background:var(--surface-2); color:var(--accent)}
nav.toc a .n{font-family:var(--mono); font-size:11px; color:var(--muted);
             flex:none; padding-top:2px}
nav.toc a:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
nav.toc .ap{margin-top:14px; padding-top:12px; border-top:1px solid var(--line)}

article{min-width:0; display:flex; flex-direction:column; gap:52px}
section{scroll-margin-top:20px}
section>h2{font-family:var(--serif); font-size:24px; line-height:1.4; margin:0 0 4px;
           display:flex; gap:14px; align-items:baseline; text-wrap:balance}
section>h2 .n{font-family:var(--mono); font-size:13px; color:var(--accent-2);
              flex:none; letter-spacing:.06em}
section>h2+.rule{height:2px; background:var(--accent); opacity:.24; margin:0 0 22px}
section h3{font-size:15.5px; margin:34px 0 10px; color:var(--accent);
           letter-spacing:.02em}
section p{margin:0 0 16px; max-width:46em}
section>ul.steps{margin:0 0 16px; padding-left:1.25em; max-width:46em}
section>ul.steps li{margin-bottom:6px}

/* 表 */
.tw{overflow-x:auto; margin:0 0 20px; border:1px solid var(--line);
    border-radius:8px; background:var(--surface); box-shadow:var(--shadow)}
table{border-collapse:collapse; width:100%; min-width:660px; font-size:13.5px}
thead th{background:var(--surface-2); text-align:left; font-weight:700;
         padding:11px 14px; border-bottom:1px solid var(--line-2);
         color:var(--ink-2); font-size:12.5px; white-space:nowrap}
tbody td{padding:11px 14px; border-bottom:1px solid var(--line);
         vertical-align:top; line-height:1.7}
tbody tr:last-child td{border-bottom:none}
tbody tr:nth-child(even){background:color-mix(in srgb, var(--surface-2) 45%, transparent)}
td ul{margin:0; padding-left:1.15em}
td ul li{margin-bottom:3px}
td .q{font-family:var(--serif); color:var(--accent)}
table.sec15 td:nth-child(1){min-width:270px}
table.sec15 td:nth-child(3){text-align:center; font-family:var(--mono); white-space:nowrap}
table.bylaw td:nth-child(1){min-width:150px}
table.ask td:nth-child(1){font-family:var(--mono); white-space:nowrap; color:var(--accent-2)}
table.ask td:nth-child(4){text-align:center; white-space:nowrap}

/* 注記 */
.note{margin:0 0 20px; padding:14px 18px; border-radius:8px;
      border-left:4px solid var(--line-2); background:var(--surface-2)}
.note p{margin:0; max-width:44em; font-size:14px}
.note .nt{font-weight:700; margin-bottom:5px}
.n-ok{background:var(--ok-soft); border-left-color:var(--ok)}
.n-ok .nt{color:var(--ok)}
.n-warn{background:var(--warn-soft); border-left-color:var(--warn)}
.n-warn .nt{color:var(--warn)}
.n-crit{background:var(--crit-soft); border-left-color:var(--crit)}
.n-crit .nt{color:var(--crit)}

pre.letter{font-family:var(--sans); font-size:13.5px; line-height:1.95;
  background:var(--surface); border:1px solid var(--line); border-left:4px solid var(--accent);
  border-radius:8px; padding:22px 26px; overflow-x:auto; white-space:pre-wrap;
  box-shadow:var(--shadow); margin:0}

footer{border-top:1px solid var(--line); padding-block:26px 48px;
       font-size:12.5px; color:var(--muted)}
footer p{margin:0 0 8px; max-width:56em}
.tools{display:flex; gap:8px; flex-wrap:wrap; margin-top:24px}
.iconbtn{font:inherit; font-size:12.5px; cursor:pointer; padding:7px 14px;
  border-radius:6px; border:1px solid var(--line-2); background:var(--surface);
  color:var(--ink-2)}
.iconbtn:hover{border-color:var(--accent); color:var(--accent)}
.iconbtn:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
@media (prefers-reduced-motion:reduce){ *{animation:none!important; transition:none!important} }
"""

PRINT_CSS = """
@page{size:A4; margin:16mm 14mm 14mm}
body{background:#fff; color:#111721; font-size:10pt; line-height:1.7;
     font-family:"BIZ UDPGothic","IPAPGothic","Hiragino Sans","Yu Gothic UI",sans-serif}
.wrap{max-width:none; padding:0}
.cover{padding:0 0 10mm; margin-bottom:8mm; border-bottom:2.4pt double #b3bdd0;
       break-after:avoid}
.cover h1{font-family:inherit; font-weight:700; font-size:22pt; margin:0 0 5mm}
.cover .lead{font-size:10.5pt; max-width:none}
.eyebrow{font-size:8pt; color:#33609f}
.facts{gap:4mm 12mm; margin-top:7mm}
.facts dt{font-size:7.5pt}
.facts dd{font-size:15pt; color:#1f3f73}
.facts dd .u{font-size:8pt}
.meta{font-size:8pt; margin-top:6mm; padding-top:4mm; border-top:.4pt solid #d2d9e6}
nav.toc{break-after:page; position:static; font-size:10pt}
nav.toc ol{gap:1mm}
nav.toc a{color:#111721; padding:1mm 0; border:none}
article{display:block}
section{break-before:page; margin:0}
section:first-of-type{break-before:avoid}
section>h2{font-family:inherit; font-size:15pt; margin:0 0 2mm; break-after:avoid}
section>h2 .n{font-size:9.5pt}
section>h2+.rule{height:1.2pt; background:#1f3f73; opacity:1; margin-bottom:5mm}
section h3{font-size:11pt; margin:6mm 0 2mm; break-after:avoid}
section p{max-width:none; margin:0 0 3mm}
.tw{overflow:visible; box-shadow:none; border:1px solid #b3bdd0; margin-bottom:5mm;
    break-inside:auto}
table{min-width:0; font-size:8.6pt; width:100%; table-layout:fixed}
thead{display:table-header-group}
thead th{background:#eaeef5; padding:2mm 2.5mm; font-size:8.4pt;
         white-space:normal; border-bottom:.8pt solid #b3bdd0}
tbody td{padding:2mm 2.5mm; border-bottom:.4pt solid #d2d9e6; line-height:1.55;
         word-break:break-word}
tbody tr{break-inside:avoid}
tbody tr:nth-child(even){background:#f7f9fc}
table.sec15 td:nth-child(1),table.bylaw td:nth-child(1){min-width:0}
.note{break-inside:avoid; margin-bottom:5mm; padding:3mm 4mm; border-radius:2mm}
.note p{font-size:9pt; max-width:none}
pre.letter{font-size:9pt; padding:5mm 6mm; box-shadow:none; break-inside:avoid;
           line-height:1.8}
footer{break-before:page; border-top:.8pt solid #d2d9e6; padding:5mm 0 0; font-size:8.5pt}
.tools{display:none}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
 '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
 'family=BIZ+UDPGothic:wght@400;700&family=BIZ+UDPMincho&'
 'family=IBM+Plex+Mono:wght@400;500;600&display=swap">')

SAVE_JS = """
(function(){
  var btn = document.getElementById("btnSave"), pr = document.getElementById("btnPrint");
  if(pr) pr.addEventListener("click", function(){ window.print(); });
  var dl = null;
  if(window.claude && typeof window.claude.use === "function"){
    window.claude.use("downloads").then(function(d){ if(d) dl = d; }).catch(function(){});
  }
  if(!btn) return;
  btn.addEventListener("click", async function(){
    var name = "SDSだけで進める化学物質管理.html";
    var html = ["<!doctype html>", '<html lang="ja">',
                document.documentElement.innerHTML, "</html>", ""].join(String.fromCharCode(10));
    if(dl){
      try{ await dl.save({filename:name, data:html}); return; }
      catch(e){ if(e && e.code === "declined") return; }
    }
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([html], {type:"text/html;charset=utf-8"}));
    a.download = name; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function(){ URL.revokeObjectURL(a.href); }, 3000);
  });
})();
"""

def render(mode, decl, tasks):
    chs = chapters(decl, tasks)
    aps = appendices(decl, tasks)
    today = datetime.date.today().strftime("%Y年%m月%d日")

    toc = []
    for i, (title, hid, _) in enumerate(chs, 1):
        toc.append('<li><a href="#%s"><span class="n">%d</span><span>%s</span></a></li>'
                   % (hid, i, E(title)))
    ap_toc = []
    for i, (title, hid, _) in enumerate(aps):
        ap_toc.append('<li><a href="#ap-%s"><span class="n">%s</span><span>%s</span></a></li>'
                      % (hid, "ABCDEF"[i], E(title)))

    secs = []
    for i, (title, hid, body) in enumerate(chs, 1):
        secs.append('<section id="%s"><h2><span class="n">第%d章</span>'
                    '<span>%s</span></h2><div class="rule"></div>%s</section>'
                    % (hid, i, E(title), "".join(body)))
    for i, (title, hid, body) in enumerate(aps):
        secs.append('<section id="ap-%s"><h2><span class="n">付録%s</span>'
                    '<span>%s</span></h2><div class="rule"></div>%s</section>'
                    % (hid, "ABCDEF"[i], E(title), "".join(body)))

    laws = []
    for t in tasks:
        if t["law"] not in laws: laws.append(t["law"])
    facts = "".join('<div><dt>%s</dt><dd>%s<span class="u">%s</span></dd></div>' % f for f in [
      ("SDS第15項からの照会項目", len(decl), "項目"),
      ("うち含有率が要るもの", sum(1 for d in decl.values() if d["pct"]), "項目"),
      ("判定の対象になる法令", len(laws), "法令"),
      ("法令上の確認点", len(tasks), "項目"),
    ])
    tools = ("" if mode == "print" else
      '<div class="tools"><button class="iconbtn" id="btnSave" type="button">HTMLで保存</button>'
      '<button class="iconbtn" id="btnPrint" type="button">印刷 / PDF</button></div>')
    script = "" if mode == "print" else "<script>%s</script>" % SAVE_JS

    return """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
%(fonts)s
<style>%(css)s%(pcss)s</style>
</head>
<body>
<div class="wrap">
  <header class="cover">
    <p class="eyebrow">実務ガイド / 成分非開示の化学品</p>
    <h1>%(title)s</h1>
    <p class="lead">%(lead)s</p>
    <dl class="facts">%(facts)s</dl>
    <div class="meta"><span>%(today)s 版</span><span>全%(nch)d章・付録%(nap)d</span>
      <span>対象：安全衛生担当・購買担当</span></div>
  </header>
  <div class="main">
    <nav class="toc" aria-label="目次">
      <p class="tt">目次</p>
      <ol>%(toc)s</ol>
      <ol class="ap">%(aptoc)s</ol>
    </nav>
    <article>%(secs)s</article>
  </div>
  <footer>
    <p><b>このガイドの位置づけ。</b> 成分が開示されない化学品を含む状態で、
      法令上の義務を取りこぼさずに管理を回すための手順をまとめたものです。
      最終的な適法性の判断、所轄官庁への確認、専門家への相談に代わるものではありません。</p>
    <p>裾切り値・記録の保存年数・照会項目は、化学物質法令チェック台帳
      （chemical-compliance.html）の定義から機械的に取り出しています。
      台帳を更新すれば、このガイドも再生成するだけで追従します。</p>
    <p>%(today)s 作成。tools/build_guide.py が生成しています。</p>
    %(tools)s
  </footer>
</div>
%(script)s
</body>
</html>
""" % dict(title=E(C.TITLE), lead=E(C.LEAD), fonts=FONTS, css=CSS,
           pcss=("@media print{%s}" % PRINT_CSS) if mode == "web" else PRINT_CSS,
           today=today, nch=len(chs), nap=len(aps), facts=facts,
           toc="".join(toc), aptoc="".join(ap_toc), secs="".join(secs),
           tools=tools, script=script)

def main():
    ap = argparse.ArgumentParser(description="SDS運用ガイドを組む")
    ap.add_argument("--mode", choices=["web", "print"], default="web")
    ap.add_argument("--out")
    a = ap.parse_args()
    decl, tasks = load_defs()
    out = a.out or ("chem-guide.html" if a.mode == "web" else "chem-guide-print.html")
    html = render(a.mode, decl, tasks)
    io.open(out, "w", encoding="utf-8").write(html)
    print("%s を出力しました（照会項目%d / 法令タスク%d / mode=%s）"
          % (out, len(decl), len(tasks), a.mode))

if __name__ == "__main__":
    main()
