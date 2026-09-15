# -*- coding: utf-8 -*-
"""
法令リファレンスとSDS運用ガイドを chemical-compliance.html のタブとして埋め込む。

別々に生成したHTMLをそのまま入れると、CSSの:rootやbody、id名が
台帳側とぶつかる。そこで取り込むときに

  ・CSSのセレクタをパネル配下へ限定する（:root とbody はパネル自身に読み替える）
  ・id属性と、CSS・JSからのid参照をまとめて改名する
  ・@page は台帳側の印刷指定を壊すので捨てる
  ・スクリプトは即時関数で包み、変数が台帳の外に漏れないようにする

を機械的に行う。埋め込み先は chemical-compliance.html の
<!-- EMBED:xxx --> 〜 <!-- /EMBED:xxx --> の間。

  python3 tools/embed_docs.py
"""
import io, re, sys

APP = "chemical-compliance.html"
DOCS = [
    # (差し込み先のキー, 元ファイル, id接頭辞)
    ("ref",   "chem-checklist.html", "rf"),
    ("guide", "chem-guide.html",     "gd"),
]

WS = re.compile(r'\s+|/\*.*?\*/', re.S)

def scope_selector(prelude, sel):
    out = []
    for s in prelude.split(","):
        s = s.strip()
        if not s: continue
        if s in (":root", "html", "body"):
            out.append(sel)
        elif s.startswith(":root"):
            rest = s[5:]
            m = re.match(r'^((?:\[[^\]]*\]|:not\([^)]*\)|\.[\w-]+|#[\w-]+)*)(.*)$', rest)
            out.append((":root" + m.group(1) + " " + sel + m.group(2)).strip())
        elif s.startswith("body"):
            out.append(sel + s[4:])
        elif s.startswith("*"):
            out.append(sel + " " + s)
        else:
            out.append(sel + " " + s)
    return ",".join(out)

def scope_css(css, sel):
    res, i, n = [], 0, len(css)
    while i < n:
        m = WS.match(css, i)
        if m:
            res.append(m.group(0)); i = m.end(); continue
        j = i
        while j < n and css[j] not in "{;": j += 1
        if j >= n:
            res.append(css[i:]); break
        if css[j] == ";":
            res.append(css[i:j+1]); i = j + 1; continue
        prelude = css[i:j].strip()
        depth, k = 0, j
        while k < n:
            if css[k] == "{": depth += 1
            elif css[k] == "}":
                depth -= 1
                if depth == 0: break
            k += 1
        body, i = css[j+1:k], k + 1
        if prelude.startswith("@"):
            name = prelude.split()[0].lower()
            if name in ("@media", "@supports", "@layer", "@container"):
                res.append(prelude + "{" + scope_css(body, sel) + "}")
            elif name == "@page":
                pass                      # 台帳側の用紙指定を上書きさせない
            else:
                res.append(prelude + "{" + body + "}")   # @font-face・@keyframes
        else:
            res.append(scope_selector(prelude, sel) + "{" + body + "}")
    return "".join(res)

def split_doc(path):
    s = io.open(path, encoding="utf-8").read()
    styles = "".join(m.group(1) for m in re.finditer(r"<style>(.*?)</style>", s, re.S))
    scripts = "".join(m.group(1) for m in re.finditer(r"<script>(.*?)</script>", s, re.S))
    body = re.search(r"<body[^>]*>(.*)</body>", s, re.S).group(1)
    body = re.sub(r"<script>.*?</script>", "", body, flags=re.S)
    title = re.search(r"<title>(.*?)</title>", s, re.S).group(1)
    return title, styles, scripts, body

def rename_ids(prefix, html, css, js):
    ids = sorted(set(re.findall(r'\bid="([^"]+)"', html)), key=len, reverse=True)
    if not ids: return html, css, js, {}
    ren = {i: prefix + "-" + i for i in ids}
    alt = "|".join(re.escape(i) for i in ids)
    # HTML: id と、id を指す属性
    html = re.sub(r'\bid="(%s)"' % alt, lambda m: 'id="%s"' % ren[m.group(1)], html)
    html = re.sub(r'\b(href)="#(%s)"' % alt,
                  lambda m: '%s="#%s"' % (m.group(1), ren[m.group(2)]), html)
    html = re.sub(r'\b(for|aria-labelledby|aria-controls|aria-describedby|list)="(%s)"' % alt,
                  lambda m: '%s="%s"' % (m.group(1), ren[m.group(2)]), html)
    # CSS: #id セレクタ
    css = re.sub(r'#(%s)\b' % alt, lambda m: "#" + ren[m.group(1)], css)
    # JS: "#id" / '#id' と getElementById("id")
    js = re.sub(r'(["\'])#(%s)\1' % alt,
                lambda m: '%s#%s%s' % (m.group(1), ren[m.group(2)], m.group(1)), js)
    js = re.sub(r'(getElementById\(\s*["\'])(%s)(["\'])' % alt,
                lambda m: m.group(1) + ren[m.group(2)] + m.group(3), js)
    return html, css, js, ren

def build_one(key, src, prefix):
    title, css, js, body = split_doc(src)
    sel = "#panel-" + key
    body, css, js, _ = rename_ids(prefix, body, css, js)
    css = scope_css(css, sel)
    # 台帳側にテーマ切替と保存・印刷があるため、埋め込んだ側の操作ボタンは隠す
    css += "\n%s .iconbtn,%s .tools{display:none!important}" % (sel, sel)
    out = ['<style data-embed="%s">%s</style>' % (key, css),
           body.strip(),
           '<script data-embed="%s">(function(){%s})();</script>' % (key, js)]
    return title, "\n".join(out)

def inject(app, key, html):
    a, b = "<!-- EMBED:%s -->" % key, "<!-- /EMBED:%s -->" % key
    i, j = app.index(a), app.index(b)
    return app[:i + len(a)] + "\n" + html + "\n" + app[j:]

def main():
    app = io.open(APP, encoding="utf-8").read()
    for key, src, prefix in DOCS:
        title, html = build_one(key, src, prefix)
        app = inject(app, key, html)
        print("  %-6s %-22s → %7d文字  「%s」" % (key, src, len(html), title))
    io.open(APP, "w", encoding="utf-8").write(app)
    print("%s に埋め込みました（%d bytes）" % (APP, len(app)))

if __name__ == "__main__":
    main()
