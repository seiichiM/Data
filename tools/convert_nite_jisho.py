# -*- coding: utf-8 -*-
"""
NITE「一般化学物質等製造（輸入）実績等届出書作成支援ソフト」のマスター辞書を、
物質マスタの形式（chem-master.csv と同じ列）に変換する。

  入手先 https://www.nite.go.jp/chem/kasinn/ippan_todokede/jisyo04.html

取り込むのは CAS番号と官報公示名称の対応だけにしている。
辞書に含まれる「物質区分」の数値コードは、対応する化審法の区分が公式資料で
確認できなかったため取り込まない。誤った区分で法令判定を動かすより、
既存マスタの値をそのまま残すほうが安全なため。
（列を持たないCSVは既存の値を書き換えない仕組みになっている）

  python3 tools/convert_nite_jisho.py MasterJisho.xlsx --out nite-jisho.csv
"""
import argparse, io, re, sys, zipfile
from xml.etree.ElementTree import iterparse

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
CAS_RE = re.compile(r"\d{2,7}-\d{2}-\d")

def col_index(ref):
    m = re.match(r"[A-Z]+", ref or "")
    if not m: return 0
    n = 0
    for ch in m.group(0): n = n * 26 + (ord(ch) - 64)
    return n - 1

def read_shared(z):
    out = []
    with z.open("xl/sharedStrings.xml") as f:
        for _, el in iterparse(f, ("end",)):
            if el.tag == NS + "si":
                out.append("".join(t.text or "" for t in el.iter(NS + "t")))
                el.clear()
    return out

def rows(z, shared):
    with z.open("xl/worksheets/sheet1.xml") as f:
        for _, el in iterparse(f, ("end",)):
            if el.tag != NS + "row": continue
            cells = {}
            for c in el.findall(NS + "c"):
                t, v = c.get("t"), c.find(NS + "v")
                if t == "s" and v is not None:
                    k = int(v.text); val = shared[k] if k < len(shared) else ""
                elif t == "inlineStr":
                    isel = c.find(NS + "is")
                    val = "".join(x.text or "" for x in isel.iter(NS + "t")) if isel is not None else ""
                else:
                    val = v.text if v is not None else ""
                cells[col_index(c.get("r"))] = (val or "").strip()
            el.clear()
            if cells: yield [cells.get(i, "") for i in range(max(cells) + 1)]

HEADER = ["CAS番号","物質名","安衛法","皮膚等障害","がん原性","特化則","特別管理物質","有機則",
          "鉛則","粉じん則","化管法","毒劇法","消防法品名","化審法","大防法","水濁法有害物質",
          "土対法","女性則","備考","出所"]

def main():
    ap = argparse.ArgumentParser(description="NITEマスター辞書を物質マスタ形式へ変換する")
    ap.add_argument("xlsx")
    ap.add_argument("--out", default="nite-jisho.csv")
    ap.add_argument("--js", default="", help="同じ内容をJS形式でも書き出す（file://用）")
    ap.add_argument("--source", default="NITE化審法辞書")
    ap.add_argument("--columns", choices=["min", "std", "full"], default="min",
                    help="min=CAS番号と物質名だけ（既定）/ std=+官報公示整理番号を備考へ / full=マスタの全列。"
                         "stdは既存マスタの備考を上書きするため、注記を残したい場合はminを使う")
    a = ap.parse_args()

    z = zipfile.ZipFile(a.xlsx)
    shared = read_shared(z)
    print("共有文字列 %d件を読み込みました" % len(shared))

    seen, out, total, nocas, dup, conflict = {}, [], 0, 0, 0, 0
    icas = iname = imiti = None
    for r in rows(z, shared):
        total += 1
        if icas is None:
            # 見出し行から列位置を決める。1行目は注記でCASの語を含むため、
            # CAS列と官報公示名称列の両方が揃った行だけを見出しとして採用する
            c = n = m = None
            for i, h in enumerate(r):
                if "CAS" in h and c is None: c = i
                if "官報公示名称" in h: n = i
                if "官報公示番号" in h: m = i
            if c is not None and n is not None:
                icas, iname, imiti = c, n, m
                print("見出し行を検出: CAS=%d列 名称=%d列 公示番号=%s列" % (c, n, m))
            continue
        cas = (r[icas] if icas is not None and icas < len(r) else "").strip()
        if not CAS_RE.fullmatch(cas): nocas += 1; continue
        name = (r[iname] if iname is not None and iname < len(r) else "").strip()
        miti = (r[imiti] if imiti is not None and imiti < len(r) else "").strip()
        if not name: continue
        if cas in seen:
            dup += 1
            if seen[cas][0] != name: conflict += 1
            continue
        seen[cas] = (name, miti)
        out.append((cas, name, miti))

    print("総行数 %d ／ CAS番号なし %d ／ 重複 %d（うち名称違い %d）" % (total, nocas, dup, conflict))
    print("出力 %d物質" % len(out))

    # 値を持たない列は書き出さない。取り込み側は「CSVに無い列の既存値は残す」
    # 仕様なので、列を削っても他法令の判定は壊れない。
    cols = {"min": ["CAS番号", "物質名"],
            "std": ["CAS番号", "物質名", "備考"],
            "full": HEADER}[a.columns]
    def cell(v): return '"' + str(v).replace('"', '""') + '"'
    lines = [",".join(cell(h) for h in cols)]
    for cas, name, miti in out:
        row = {"CAS番号": cas, "物質名": name,
               "備考": ("官報公示整理番号 " + miti) if miti else "",
               "出所": a.source}
        lines.append(",".join(cell(row.get(h, "")) for h in cols))
    text = "\r\n".join(lines) + "\r\n"
    io.open(a.out, "w", encoding="utf-8-sig").write(text)
    print("%s を出力しました（%.1f MB）" % (a.out, len(text.encode()) / 1048576))

    if a.js:
        import json
        io.open(a.js, "w", encoding="utf-8").write(
            "/* NITE化審法マスター辞書から生成した物質名辞書。\n"
            "   chemical-compliance.html と同じフォルダに置いてください。\n"
            "   出典 https://www.nite.go.jp/chem/kasinn/ippan_todokede/jisyo04.html */\n"
            "window.CHEM_MASTER_CSV = " + json.dumps(text, ensure_ascii=False) + ";\n")
        print("%s を出力しました" % a.js)

if __name__ == "__main__":
    main()
