# -*- coding: utf-8 -*-
"""
安衛法の個別リスト（製造禁止・製造許可・強い変異原性・濃度基準値）を物質マスタへ統合する。

取り込む元データは2種類ある。

 1. NITE-CHRIPから該当カテゴリで絞り込んで出力したxlsx
      列: 一般情報：CAS RN / 一般情報：物質名称
      --ban   製造等が禁止される有害物等（安衛法第55条・令第16条）
      --perm  製造の許可を受けるべき有害物（安衛法第56条・令第17条＝特化則第1類物質）
      --muta  強い変異原性が認められた化学物質（変異原性指針の対象）

 2. 厚生労働省が公表している濃度基準値の一覧xlsx（noudokijyun_*.xlsx）
      シート「濃度基準値等」、3行目が見出し
      列: 物質名 / CAS RN / 八時間濃度基準値 / 短時間濃度基準値 / …
      --noudo FILE[:ラベル]   ラベルは適用期日。省略時はファイル内の列から拾う

  python3 tools/merge_anzen_lists.py --base chem-master.csv --out chem-master.csv \
      --ban 禁止.xlsx --perm 許可.xlsx --muta 変異原性.xlsx \
      --noudo noudokijyun_r050427_1.xlsx:"令和5年4月27日告示" \
      --noudo noudokijyun_r060508.xlsx --noudo noudokijyun_r081001.xlsx
"""
import argparse, csv, datetime, io, json, re, sys, zipfile
from xml.etree.ElementTree import iterparse

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
CAS_RE = re.compile(r"^\d{2,7}-\d{2}-\d$")

def col_index(ref):
    m = re.match(r"[A-Z]+", ref or "")
    if not m: return 0
    n = 0
    for ch in m.group(0): n = n * 26 + (ord(ch) - 64)
    return n - 1

def xlsx_rows(path):
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        with z.open("xl/sharedStrings.xml") as f:
            for _, el in iterparse(f, ("end",)):
                if el.tag == NS + "si":
                    shared.append("".join(t.text or "" for t in el.iter(NS + "t"))); el.clear()
    sheet = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))[0]
    with z.open(sheet) as f:
        for _, el in iterparse(f, ("end",)):
            if el.tag != NS + "row": continue
            cells = {}
            for c in el.findall(NS + "c"):
                t, v, isl = c.get("t"), c.find(NS + "v"), c.find(NS + "is")
                if t == "s" and v is not None:
                    k = int(v.text); val = shared[k] if k < len(shared) else ""
                elif t == "inlineStr" and isl is not None:
                    val = "".join(x.text or "" for x in isl.iter(NS + "t"))
                else:
                    val = v.text if v is not None else ""
                cells[col_index(c.get("r"))] = (val or "").strip()
            el.clear()
            yield [cells.get(i, "") for i in range(max(cells) + 1)] if cells else []

def read_csv(path):
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            with io.open(path, encoding=enc, newline="") as f:
                return [[c.strip() for c in r] for r in csv.reader(f) if any(x.strip() for x in r)]
        except UnicodeDecodeError:
            continue
    raise SystemExit("%s: 文字コードを判別できません" % path)

ZEN = dict((0xFF10 + i, chr(0x30 + i)) for i in range(10))
ZEN.update({0xFF0E: ".", 0xFF05: "%", 0x3000: " ", 0xFF0F: "/",
            0x2010: "-", 0x2011: "-", 0x2012: "-", 0x2013: "-", 0x2014: "-",
            0x2015: "-", 0x2212: "-", 0xFF0D: "-", 0x30FC: "-", 0x2043: "-"})

def norm_cas(s):
    s = (s or "").translate(ZEN).replace(" ", "").strip()
    return s if CAS_RE.match(s) else ""

def norm_val(s):
    """「２ ppm」→「2ppm」、「－」→空。数字だけ半角にして単位はそのまま残す。"""
    s = (s or "").translate(ZEN).strip()
    s = re.sub(r"\s+", "", s)
    s = s.replace("㎎", "mg").replace("㎥", "m3")
    if s in ("", "-", "—"): return ""
    return s

def excel_date(s):
    """Excelのシリアル値を「令和8年10月1日」の形にする。"""
    try:
        n = int(float(s))
    except ValueError:
        return ""
    if not (20000 < n < 80000): return ""
    d = datetime.date(1899, 12, 30) + datetime.timedelta(days=n)
    if d.year >= 2019:
        return "令和%d年%d月%d日" % (d.year - 2018, d.month, d.day)
    return "%d年%d月%d日" % (d.year, d.month, d.day)

def norm_era(s):
    s = (s or "").translate(ZEN).strip()
    m = re.search(r"令和(\d+)年(\d+)月(\d+)日", s)
    return "令和%s年%s月%s日" % m.groups() if m else ""

# ---- CHRIP出力（該当物質だけを並べた一覧）を読む ----
def read_chrip_list(path):
    rows = list(xlsx_rows(path))
    hi = next((i for i, r in enumerate(rows[:10])
               if any("CAS" in c for c in r) and any("物質名" in c for c in r)), None)
    if hi is None: raise SystemExit("%s: 見出し行が見つかりません" % path)
    head = rows[hi]
    ic = next(i for i, c in enumerate(head) if "CAS" in c)
    inm = next(i for i, c in enumerate(head) if "物質名" in c)
    out = []
    for r in rows[hi + 1:]:
        cas = norm_cas(r[ic]) if len(r) > ic else ""
        name = (r[inm] if len(r) > inm else "").strip()
        if not cas and not name: continue
        out.append((cas, name))
    return out

# ---- 厚生労働省の濃度基準値一覧を読む ----
def read_noudo_list(path, label):
    rows = list(xlsx_rows(path))
    hi = next((i for i, r in enumerate(rows[:10])
               if any(c.startswith("物質名") for c in r) and any("CAS" in c for c in r)), None)
    if hi is None: raise SystemExit("%s: 見出し行が見つかりません" % path)
    head = rows[hi]
    def col(kw):
        return next((i for i, c in enumerate(head) if c.startswith(kw)), -1)
    inm, ic = col("物質名"), col("CAS")
    i8, isht, iap = col("八時間"), col("短時間"), col("濃度基準値等の適用期日")
    out = []
    prev_name = prev_ap = ""
    for r in rows[hi + 1:]:
        g = lambda i: (r[i] if 0 <= i < len(r) else "")
        raw = g(ic).translate(ZEN).strip()
        cass = [c for c in (norm_cas(x) for x in re.split(r"[,、/]", raw)) if c]
        name = g(inm).strip()
        ap = label or norm_era(g(iap)) or excel_date(g(iap))
        # 同じ物質名の下にCAS番号だけが並ぶ行（セル結合）は、直前の行の値を引き継ぐ
        if cass:
            if not name: name = prev_name
            if not ap:   ap = prev_ap
            prev_name, prev_ap = name, ap
        if not cass and not name: continue
        if not cass and not re.search(r"[ぁ-んァ-ヶ一-龠Ａ-Ｚ]", name[:2]): continue  # 備考行
        rec = (norm_val(g(i8)), norm_val(g(isht)), ap)
        if cass:
            for c in cass: out.append((c, name, rec))
        else:
            out.append(("", name, rec))
    return out

COLS = ["製造禁止", "製造許可", "強い変異原性",
        "八時間濃度基準値", "短時間濃度基準値", "濃度基準値適用日"]

def main():
    ap = argparse.ArgumentParser(description="安衛法の個別リストを物質マスタへ統合する")
    ap.add_argument("--base", default="chem-master.csv")
    ap.add_argument("--out",  default="chem-master.csv")
    ap.add_argument("--js",   default="chem-master.js")
    ap.add_argument("--ban")
    ap.add_argument("--perm")
    ap.add_argument("--muta")
    ap.add_argument("--noudo", action="append", default=[],
                    help="濃度基準値一覧のxlsx。FILE:ラベル でも指定できる")
    ap.add_argument("--anzen", choices=["all", "ask", "none"], default="ask",
                    help="新規に増える物質の安衛法列。all=表示・通知対象物、"
                         "ask=要確認（既定）、none=空のまま")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    base = read_csv(a.base)
    header = base[0][:]
    for c in COLS:
        if c not in header:
            header.insert(header.index("備考") if "備考" in header else len(header), c)
    rows = [dict(zip(base[0], r + [""] * (len(base[0]) - len(r)))) for r in base[1:]]
    for r in rows:
        for c in COLS: r.setdefault(c, "")

    def key_of(cas, name):
        return cas if cas else "name:" + name
    index = {}
    for r in rows:
        index[key_of(norm_cas(r.get("CAS番号", "")), r.get("物質名", ""))] = r

    stat = {}
    def touch(cas, name, apply_fn, tag):
        k = key_of(cas, name)
        rec = index.get(k)
        new = rec is None
        if new:
            rec = dict((h, "") for h in header)
            rec["CAS番号"] = cas or "-"
            rec["物質名"] = name or cas
            rec["出所"] = "外部辞書"
            if a.anzen == "all":  rec["安衛法"] = "対象物"
            elif a.anzen == "ask": rec["安衛法"] = "要確認"
            rows.append(rec); index[k] = rec
        apply_fn(rec)
        s = stat.setdefault(tag, {"hit": 0, "new": 0})
        s["hit"] += 1
        if new: s["new"] += 1

    if a.ban:
        for cas, name in read_chrip_list(a.ban):
            touch(cas, name, lambda r: r.__setitem__("製造禁止", "該当"), "製造禁止")
    if a.perm:
        def ap_perm(r):
            r["製造許可"] = "該当"
            # 製造許可物質＝令別表第3第1号＝特化則の第1類物質。
            # CHRIPから入った「?」（区分未確定）はここで第1類に確定できる。
            if r.get("特化則", "") in ("", "?", "要確認"): r["特化則"] = "第1類"
        for cas, name in read_chrip_list(a.perm):
            touch(cas, name, ap_perm, "製造許可")
    if a.muta:
        for cas, name in read_chrip_list(a.muta):
            touch(cas, name, lambda r: r.__setitem__("強い変異原性", "該当"), "強い変異原性")

    for spec in a.noudo:
        path, _, label = spec.partition(":")
        for cas, name, (v8, vs, apd) in read_noudo_list(path, label):
            def ap_noudo(r, v8=v8, vs=vs, apd=apd):
                r["濃度基準値"] = "該当"
                if v8: r["八時間濃度基準値"] = v8
                if vs: r["短時間濃度基準値"] = vs
                if apd: r["濃度基準値適用日"] = apd
            touch(cas, name, ap_noudo, "濃度基準値")

    print("取り込み結果")
    for k, v in stat.items():
        print("  %-12s 該当 %5d件（うち新規 %d件）" % (k, v["hit"], v["new"]))
    print("  物質マスタ %d件 → %d件" % (len(base) - 1, len(rows)))
    for c in COLS:
        print("  列 %-16s 値あり %d件" % (c, sum(1 for r in rows if r.get(c))))
    if a.dry_run:
        return

    def cell(v): return '"' + str(v).replace('"', '""') + '"'
    lines = [",".join(cell(h) for h in header)]
    lines += [",".join(cell(r.get(h, "")) for h in header) for r in rows]
    text = "\r\n".join(lines) + "\r\n"
    io.open(a.out, "w", encoding="utf-8-sig").write(text)
    print("\n%s を出力しました（%d行）" % (a.out, len(rows)))
    if a.js:
        io.open(a.js, "w", encoding="utf-8").write(
            "/* 物質マスタ。chemical-compliance.html と同じフォルダに置くと自動で読み込まれる。 */\n"
            "window.CHEM_MASTER_CSV = " + json.dumps(text, ensure_ascii=False) + ";\n")
        print("%s を出力しました" % a.js)

if __name__ == "__main__":
    main()
