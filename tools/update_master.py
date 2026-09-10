# -*- coding: utf-8 -*-
"""
公式に公開されている物質一覧（Excel / CSV）を chem-master.csv に反映する。

このスクリプトが自動化するのは「取り込みと突き合わせ」だけで、
ファイルの入手は人が行う。理由は次のとおり。

  * 厚生労働省・NITE・経済産業省のサイトは CORS を許可しておらず、
    ブラウザから直接読むことはできない。
  * 各省庁のダウンロードURLは改正のたびに変わるため、URLを埋め込むと
    かえって壊れやすい。
  * 消防法の品名・指定数量と毒物劇物の指定は CAS番号で公開されていない
    （品名ベース）ため、機械的な突き合わせができない。これらの列は
    既存の chem-master.csv の値をそのまま残す。

使い方
  1. 公式サイトから一覧をダウンロードする（.xlsx または .csv）
  2. どの列に何を書き込むかを --set で指定して流し込む

  # 労働安全衛生法の表示・通知対象物質一覧を反映する
  python3 tools/update_master.py --add 安衛法一覧.xlsx --set 安衛法=対象物

  # 化管法の第一種・第二種指定化学物質を反映する
  python3 tools/update_master.py --add prtr1.xlsx --set 化管法=第一種
  python3 tools/update_master.py --add prtr2.xlsx --set 化管法=第二種

入手先
  労働安全衛生法 表示・通知対象物質   https://www.mhlw.go.jp/stf/newpage_66101.html
  職場の化学物質管理総合サイト        https://cheminfo.johas.go.jp/
  化管法 対象物質（NITE）             https://www.nite.go.jp/chem/prtr/prmate.html
  化管法SDS対象物質（NITE）           https://www.nite.go.jp/chem/prtr/msds/msmate.html
  化管法 対象物質（経済産業省）        https://www.meti.go.jp/policy/chemical_management/law/prtr/2.html
  NITE-CHRIP（法規制の横断検索）      https://www.chem-info.nite.go.jp/chem/chrip/chrip_search/systemTop
"""
import argparse, csv, io, json, os, re, sys, zipfile
import xml.etree.ElementTree as ET

CAS_RE = re.compile(r"\b\d{2,7}-\d{2}-\d\b")
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

def norm_cas(v):
    v = str(v or "")
    v = "".join(chr(ord(c) - 0xFEE0) if "０" <= c <= "９" else c for c in v)
    v = re.sub(r"[‐-―−－ー]", "-", v)
    return re.sub(r"[\s　]", "", v)

# ---------- 読み込み（openpyxl等に依存せず標準ライブラリだけで処理する） ----------
def col_index(ref):
    m = re.match(r"[A-Z]+", ref or "")
    if not m: return 0
    i = 0
    for ch in m.group(0): i = i * 26 + (ord(ch) - 64)
    return i - 1

def read_xlsx(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(NS + "si"):
            shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
    sheets = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
    if not sheets: raise SystemExit("%s: ワークシートが見つかりません" % path)
    rows = []
    for row in ET.fromstring(z.read(sheets[0])).iter(NS + "row"):
        cells = {}
        for c in row.findall(NS + "c"):
            t, v, ins = c.get("t"), c.find(NS + "v"), c.find(NS + "is")
            if t == "s" and v is not None and v.text and int(v.text) < len(shared):
                val = shared[int(v.text)]
            elif t == "inlineStr" and ins is not None:
                val = "".join(x.text or "" for x in ins.iter(NS + "t"))
            else:
                val = v.text if v is not None else ""
            cells[col_index(c.get("r"))] = (val or "").strip()
        if any(cells.values()):
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
    return rows

def read_csv(path):
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            with io.open(path, encoding=enc, newline="") as f:
                return [[c.strip() for c in r] for r in csv.reader(f) if any(x.strip() for x in r)]
        except UnicodeDecodeError:
            continue
    raise SystemExit("%s: 文字コードを判別できません" % path)

def read_any(path):
    return read_xlsx(path) if path.lower().endswith((".xlsx", ".xlsm")) else read_csv(path)

# ---------- 抽出（列の並びに依存しないよう、内容から推定する） ----------
def extract(rows):
    """CAS番号らしい値が最も多い列をCAS列、その隣接で文字列が最も多い列を名称列とみなす。
       省庁ごとに様式が違い、改正で列が動くため、ヘッダー名には依存させない。"""
    cas_hits, text_hits = {}, {}
    for r in rows:
        for i, c in enumerate(r):
            if CAS_RE.fullmatch(norm_cas(c)): cas_hits[i] = cas_hits.get(i, 0) + 1
            elif c and not re.fullmatch(r"[\d.,\-\s]+", c): text_hits[i] = text_hits.get(i, 0) + 1
    if not cas_hits:
        return [], None, None
    ci = max(cas_hits, key=cas_hits.get)
    ni = None
    if text_hits:
        # CAS列に近く、文字列の多い列を名称とみなす
        ni = max(text_hits, key=lambda i: (text_hits[i] - abs(i - ci) * 3))
    out, seen = [], set()
    for r in rows:
        if ci >= len(r): continue
        cas = norm_cas(r[ci])
        if not CAS_RE.fullmatch(cas) or cas in seen: continue
        seen.add(cas)
        name = r[ni].strip() if (ni is not None and ni < len(r)) else ""
        out.append((cas, name))
    return out, ci, ni

# ---------- 出力 ----------
def write_outputs(header, rows, csv_path, js_path):
    def cell(v): return '"' + str(v).replace('"', '""') + '"'
    lines = [",".join(cell(h) for h in header)]
    lines += [",".join(cell(r.get(h, "")) for h in header) for r in rows]
    text = "\r\n".join(lines) + "\r\n"
    io.open(csv_path, "w", encoding="utf-8-sig").write(text)
    io.open(js_path, "w", encoding="utf-8").write(
        "/* 化学物質法令チェック台帳 物質マスタ\n"
        "   chemical-compliance.html と同じフォルダに置いてください。\n"
        "   ファイルを直接開く場合は、ブラウザの制約によりCSVではなくこのファイルが読み込まれます。\n"
        "   内容は chem-master.csv と同一です。tools/update_master.py が生成します。 */\n"
        "window.CHEM_MASTER_CSV = " + json.dumps(text, ensure_ascii=False) + ";\n")

def main():
    ap = argparse.ArgumentParser(description="公式の物質一覧を chem-master.csv に反映する")
    ap.add_argument("--base", default="chem-master.csv", help="更新前のマスタCSV")
    ap.add_argument("--add", action="append", default=[], metavar="FILE",
                    help="取り込む一覧（.xlsx / .csv）。複数指定できます")
    ap.add_argument("--set", action="append", default=[], metavar="列名=値",
                    help="取り込んだ行に書き込む値。例 安衛法=対象物 / 化管法=第一種")
    ap.add_argument("--source", default="", help="出所欄に記録する文字列")
    ap.add_argument("--out", default="chem-master.csv", help="出力先CSV")
    ap.add_argument("--js", default="chem-master.js", help="出力先JS（file://用）")
    ap.add_argument("--dry-run", action="store_true", help="書き込まずに結果だけ表示する")
    a = ap.parse_args()

    if not os.path.exists(a.base):
        raise SystemExit("%s がありません。先に tools/build_master.py を実行してください。" % a.base)
    base = read_csv(a.base)
    header, rows = base[0], [dict(zip(base[0], r + [""] * (len(base[0]) - len(r)))) for r in base[1:]]
    by_cas = {norm_cas(r.get("CAS番号", "")): r for r in rows if norm_cas(r.get("CAS番号", "")) not in ("", "-")}
    print("更新前: %d物質" % len(rows))

    sets = {}
    for kv in a.set:
        if "=" not in kv: raise SystemExit("--set は 列名=値 の形式で指定してください: " + kv)
        k, v = kv.split("=", 1)
        if k not in header: raise SystemExit("列名 %r はマスタにありません。使える列: %s" % (k, " / ".join(header)))
        sets[k] = v
    if a.add and not sets:
        print("注意: --set の指定がないため、名称の補完のみ行います")

    added = updated = 0
    for path in a.add:
        pairs, ci, ni = extract(read_any(path))
        if not pairs:
            print("  %s: CAS番号を含む列を見つけられませんでした" % path); continue
        print("  %s: %d物質を検出（CAS列=%s 名称列=%s）" % (path, len(pairs), ci, ni))
        for cas, name in pairs:
            r = by_cas.get(cas)
            if r is None:
                r = {h: "" for h in header}
                r["CAS番号"], r["物質名"] = cas, name or cas
                r["出所"] = a.source or os.path.basename(path)
                rows.append(r); by_cas[cas] = r; added += 1
            else:
                if not r.get("物質名") and name: r["物質名"] = name
                updated += 1
            r.update(sets)

    print("追加 %d物質 / 更新 %d物質 → 更新後 %d物質" % (added, updated, len(rows)))
    for label, f in [("安衛法 対象物", lambda r: r.get("安衛法") == "対象物"),
                     ("特化則", lambda r: r.get("特化則")),
                     ("有機則", lambda r: r.get("有機則")),
                     ("化管法", lambda r: r.get("化管法")),
                     ("毒物・劇物", lambda r: r.get("毒劇法")),
                     ("消防法 危険物", lambda r: r.get("消防法品名"))]:
        print("  %-14s %5d" % (label, sum(1 for r in rows if f(r))))

    if a.dry_run:
        print("\n--dry-run のため書き込みませんでした")
        return
    write_outputs(header, rows, a.out, a.js)
    print("\n%s と %s を更新しました" % (a.out, a.js))
    print("この2ファイルを chemical-compliance.html と同じフォルダに置いてください。")

if __name__ == "__main__":
    main()
