# -*- coding: utf-8 -*-
"""
NITE-CHRIP（化学物質総合情報提供システム）の法規制一覧を物質マスタへ統合する。

CHRIPの一覧は「該当（●）／非該当（-）」の二値で、特化則の第1類〜第3類、
有機則の第1種〜第3種、化管法の第一種・第二種といった区分までは持たない。
そのまま取り込むと、内蔵マスタが持っている細かい区分が失われる。
そこで既存の値を優先し、空いているところだけをCHRIPで埋める。
区分が分からないまま該当だけが判明したものは「?」を入れ、アプリ側で
「区分未確定」として要確認に出す。

  python3 tools/merge_chrip.py CHRIP.xlsx --base chem-master.csv --out chem-master.csv
"""
import argparse, csv, io, json, re, sys, zipfile
from xml.etree.ElementTree import iterparse

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
CAS_RE = re.compile(r"\d{2,7}-\d{2}-\d")

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
            if cells: yield [cells.get(i, "") for i in range(max(cells) + 1)]

def read_csv(path):
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            with io.open(path, encoding=enc, newline="") as f:
                return [[c.strip() for c in r] for r in csv.reader(f) if any(x.strip() for x in r)]
        except UnicodeDecodeError:
            continue
    raise SystemExit("%s: 文字コードを判別できません" % path)

# CHRIPの列見出し → マスタの列と、●のときに入れる値
MAP = [
 ("化審法：第一種特定化学物質", "化審法",       "第一種特定"),
 ("化審法：第二種特定化学物質", "化審法",       "第二種特定"),
 ("がん原性物質",               "がん原性",     "該当"),
 ("濃度の基準",                 "濃度基準値",   "該当"),
 ("皮膚等障害化学物質等",       "皮膚等障害",   "該当"),
 ("特定化学物質等",             "特化則",       "?"),
 ("有機溶剤等",                 "有機則",       "?"),
 ("安衛法：危険物",             "安衛法危険物", "該当"),
]
KAKAN_HINTS = ["令和５年度分以降", "令和5年度分以降"]

def main():
    ap = argparse.ArgumentParser(description="NITE-CHRIPの法規制一覧を物質マスタへ統合する")
    ap.add_argument("xlsx")
    ap.add_argument("--base", default="chem-master.csv")
    ap.add_argument("--out",  default="chem-master.csv")
    ap.add_argument("--js",   default="chem-master.js")
    ap.add_argument("--anzen", choices=["auto", "all", "none"], default="auto",
                    help="新規物質の安衛法列の扱い。"
                         "all=すべて表示・通知対象物とする（CHRIPで安衛法の対象物質に絞って出力した一覧の場合）。"
                         "auto=安衛法の各列に●があるものだけ対象物とし、他は要確認（既定）。"
                         "none=安衛法列を空のままにする")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    base = read_csv(a.base)
    header = base[0]
    rows = [dict(zip(header, r + [""] * (len(header) - len(r)))) for r in base[1:]]
    by_cas = {r.get("CAS番号", ""): r for r in rows if r.get("CAS番号") not in ("", "-")}
    print("統合前: %d物質" % len(rows))

    src = xlsx_rows(a.xlsx)
    head = next(src)
    while not any("CAS" in h for h in head):
        head = next(src)
    idx = {}
    for i, h in enumerate(head):
        hh = h.replace(" ", "")
        if "CASRN" in hh or ("CAS" in hh and "RN" in hh): idx["cas"] = i
        elif "物質名称" in hh: idx["name"] = i
        elif any(k in hh for k in KAKAN_HINTS) and "化管法" in hh: idx["kakan"] = i
        else:
            for key, col, val in MAP:
                if key in hh and col not in idx: idx[col] = i
    need = ["cas", "name"]
    for k in need:
        if k not in idx: raise SystemExit("%s の列を見つけられません。見出し: %s" % (k, head))
    print("列の対応: " + " / ".join("%s=%d列" % (k, v) for k, v in sorted(idx.items(), key=lambda x: x[1])))

    added = updated = nocas = 0
    filled = {}
    ANZEN_COLS = ["がん原性", "濃度基準値", "皮膚等障害", "特化則", "有機則", "安衛法危険物"]
    for r in src:
        g = lambda i: (r[i] if i is not None and i < len(r) else "").strip()
        cas = g(idx["cas"])
        if not CAS_RE.fullmatch(cas): nocas += 1; continue
        name = g(idx["name"])
        rec = by_cas.get(cas)
        new = rec is None
        if new:
            rec = {h: "" for h in header}
            rec["CAS番号"] = cas
            rec["物質名"] = name or cas
            rec["出所"] = "NITE-CHRIP"
            rows.append(rec); by_cas[cas] = rec; added += 1
        else:
            updated += 1

        # 既に値があるところは触らない。空いているところだけCHRIPで埋める
        def fill(col, val):
            if col not in header or not val: return
            if rec.get(col): return
            rec[col] = val; filled[col] = filled.get(col, 0) + 1

        for key, col, val in MAP:
            if col in idx and g(idx[col]) == "●": fill(col, val)
        if "kakan" in idx and g(idx["kakan"]) == "●": fill("化管法", "要確認")

        # CHRIPの出力には表示・通知対象かどうかの列が無い。CHRIPで安衛法の
        # 対象物質に絞って出力した一覧なら、全行が表示・通知対象物になる
        # （絞り込み条件そのものなので列に現れない）。その場合は --anzen all。
        # 絞らずに出力した一覧なら、特化則・有機則・がん原性・濃度基準値・
        # 皮膚等障害のいずれかに該当するものは表示・通知対象物に含まれるため
        # 対象物とし、判断材料が無いものは要確認として実際に使う物質だけを
        # 拾い上げる。
        if new:
            if a.anzen == "all":
                rec["安衛法"] = "対象物"
            elif a.anzen == "auto":
                rec["安衛法"] = "対象物" if any(rec.get(c) for c in ANZEN_COLS) else "要確認"

    print("CHRIP: 新規 %d物質 / 既存に照合 %d物質 / CAS番号なし %d行（--anzen %s）"
          % (added, updated, nocas, a.anzen))
    print("空欄を埋めた件数:")
    for c in ["安衛法危険物", "濃度基準値", "がん原性", "皮膚等障害", "特化則", "有機則", "化審法", "化管法"]:
        if filled.get(c): print("  %-12s %5d" % (c, filled[c]))
    print("統合後: %d物質" % len(rows))

    if a.dry_run:
        print("\n--dry-run のため書き込みませんでした"); return

    def cell(v): return '"' + str(v).replace('"', '""') + '"'
    lines = [",".join(cell(h) for h in header)]
    lines += [",".join(cell(r.get(h, "")) for h in header) for r in rows]
    text = "\r\n".join(lines) + "\r\n"
    io.open(a.out, "w", encoding="utf-8-sig").write(text)
    io.open(a.js, "w", encoding="utf-8").write(
        "/* 化学物質法令チェック台帳 物質マスタ\n"
        "   chemical-compliance.html と同じフォルダに置いてください。\n"
        "   内蔵マスタに NITE-CHRIP の法規制一覧を統合したものです。 */\n"
        "window.CHEM_MASTER_CSV = " + json.dumps(text, ensure_ascii=False) + ";\n")
    print("\n%s（%.1f MB）と %s を出力しました" % (a.out, len(text.encode()) / 1048576, a.js))

if __name__ == "__main__":
    main()
