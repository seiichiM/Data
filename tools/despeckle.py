#!/usr/bin/env python3
"""
despeckle.py - スキャン図面(青焼き/マイクロフィルム等)の点々ノイズ除去

処理の流れ:
  1. グレースケール化
  2. 背景ムラ補正 (grey closing による背景推定 → 除算正規化)
  3. Sauvola 適応二値化 (薄い線を残しつつ地汚れを切る)
  4. 連結成分解析でノイズ粒を除去 (面積・寸法・細長さで線と区別)
  5. 任意で細い切れ線の再接続 (closing)

依存: pillow, numpy, scipy

使用例:
  python3 despeckle.py in.png -o out.png
  python3 despeckle.py in.png -o out.png --min-area 20 --window 41
  python3 despeckle.py in.png -o out.png --mode gray      # 濃淡を残す
  python3 despeckle.py in.png --preview preview.png       # 処理前後の比較画像
"""

import argparse
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

Image.MAX_IMAGE_PIXELS = None  # 大判図面スキャンを許可


def to_gray(path):
    im = Image.open(path)
    info = {"mode": im.mode, "size": im.size, "dpi": im.info.get("dpi")}
    if im.mode in ("RGBA", "LA", "PA"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1])
        im = bg
    return np.asarray(im.convert("L"), dtype=np.uint8), info


def flatten_background(gray, radius):
    """暗い線を潰して背景(明るい側)を推定し、除算で紙の濃淡ムラを平坦化する。"""
    if radius <= 0:
        return gray
    bg = ndi.grey_closing(gray, size=(radius, radius))
    bg = ndi.uniform_filter(bg.astype(np.float32), size=radius)
    np.maximum(bg, 1.0, out=bg)
    out = gray.astype(np.float32) / bg * 255.0
    return np.clip(out, 0, 255).astype(np.uint8)


def otsu(gray):
    """大津の判別分析法による大域しきい値。"""
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    total = hist.sum()
    if total == 0:
        return 128
    idx = np.arange(256, dtype=np.float64)
    w0 = np.cumsum(hist)
    w1 = total - w0
    m0 = np.cumsum(hist * idx)
    mt = m0[-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        mu0 = m0 / w0
        mu1 = (mt - m0) / w1
        between = w0 * w1 * (mu0 - mu1) ** 2
    between[~np.isfinite(between)] = -1
    return int(np.argmax(between))


def otsu3(gray):
    """3クラス大津法。地 / 地汚れ(粒) / インク を分け、下側の境界を返す。

    地汚れの多いスキャンでは2クラス大津法は「地」対「粒+インク」を
    分けてしまい、しきい値が明るすぎて粒を拾う。3クラスに分けて
    下側の境界(=インクと粒の境)を採ると、粒を落としつつ線を残せる。
    """
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    total = hist.sum()
    if total == 0:
        return 128
    idx = np.arange(256, dtype=np.float64)
    w = np.cumsum(hist)
    m = np.cumsum(hist * idx)

    def seg(a, b):  # [a, b) の重みと重み付き平均和
        wa = w[b - 1] - (w[a - 1] if a > 0 else 0.0)
        ma = m[b - 1] - (m[a - 1] if a > 0 else 0.0)
        return wa, ma

    best, best_t = -1.0, (85, 170)
    for t1 in range(1, 254):
        w0, m0 = seg(0, t1)
        if w0 <= 0:
            continue
        v0 = m0 * m0 / w0
        for t2 in range(t1 + 1, 255):
            w1, m1 = seg(t1, t2)
            w2, m2 = seg(t2, 256)
            if w1 <= 0 or w2 <= 0:
                continue
            v = v0 + m1 * m1 / w1 + m2 * m2 / w2
            if v > best:
                best, best_t = v, (t1, t2)
    return best_t[0]


def sauvola(gray, window, k, R=128.0):
    """Sauvola 適応二値化。戻り値は ink=True の bool 配列。"""
    f = gray.astype(np.float32)
    mean = ndi.uniform_filter(f, size=window)
    mean_sq = ndi.uniform_filter(f * f, size=window)
    var = np.maximum(mean_sq - mean * mean, 0.0)
    std = np.sqrt(var, out=var)
    thresh = mean * (1.0 + k * (std / R - 1.0))
    return thresh, std


def analyze_components(ink):
    """連結成分の面積・外接矩形を返す。"""
    lab, n = ndi.label(ink, structure=np.ones((3, 3), dtype=np.uint8))
    if n == 0:
        return lab, 0, np.zeros(1, dtype=np.int64), []
    areas = np.bincount(lab.ravel(), minlength=n + 1)
    return lab, n, areas, ndi.find_objects(lab)


def auto_params(areas, n, budget):
    """成分面積の分布からノイズ粒の上限サイズを推定する。

    地汚れは「小さく・数が非常に多い」集団として現れるので、
    小さい側から画素数を積み上げ、全インク画素の budget 割合に達する
    直前の面積を閾値に採る。
    """
    if n == 0:
        return 8, 4
    a = np.sort(areas[1:])
    total = a.sum()
    cum = np.cumsum(a)
    idx = int(np.searchsorted(cum, total * budget))
    idx = min(idx, len(a) - 1)
    min_area = int(np.clip(a[idx], 6, 400))
    min_extent = int(np.clip(round(np.sqrt(min_area) * 1.8), 3, 40))
    return min_area, min_extent


def binarize(flat, window, k, gate, gate_offset, contrast_min):
    """Sauvola + 大域しきい値ゲート + 局所コントラストゲート。

    Sauvola は平坦な地でも「周囲よりわずかに暗い」画素を拾うため、
    地汚れを増やしてしまう。大域しきい値より明るい画素は
    インクとみなさない、という上限を掛けて抑える。
    """
    f = flat.astype(np.float32)
    thresh, std = sauvola(flat, window, k)
    if gate == "none":
        t_global = 256
    else:
        base = otsu3(flat) if gate == "otsu3" else otsu(flat)
        t_global = base + gate_offset
    ink = (f < thresh) & (f < t_global)
    if contrast_min > 0:
        ink &= std > contrast_min
    return ink, t_global


def line_se(length, angle):
    """指定方向の線状構造要素を作る。"""
    se = np.zeros((length, length), dtype=bool)
    c = length // 2
    if angle == 0:
        se[c, :] = True
    elif angle == 90:
        se[:, c] = True
    elif angle == 45:
        np.fill_diagonal(np.fliplr(se), True)
    else:
        np.fill_diagonal(se, True)
    return se


def directional_keep(ink, length, reconstruct=True):
    """ある方向に length px 以上続く構造だけを線として残す。

    図面の線・文字の画は方向をもって伸びるが、スキャンの胡麻粒は
    どの方向にも伸びない。粒どうしが繋がって塊になっていても効く。
    再構成を有効にすると、細った線を元の太さまで復元する。
    """
    if length <= 1:
        return ink
    markers = np.zeros_like(ink)
    for angle in (0, 90, 45, 135):
        markers |= ndi.binary_opening(ink, structure=line_se(length, angle))
    if not markers.any():
        return ink
    if reconstruct:
        return ndi.binary_propagation(markers, mask=ink)
    return markers


def drop_specks(ink, lab, n, areas, slices, min_area, min_extent,
                keep_aspect, max_fill):
    """小さく・短く・細長くもなく・べったり詰まった成分をノイズ粒として除去。

    塗りつぶし率 (面積 / 外接矩形面積) が判別の要。
    ゴミ粒は塊なので 1.0 に近く、手書き文字や線の断片は細いので低い。
    """
    if n == 0:
        return ink, 0
    remove = np.zeros(n + 1, dtype=bool)
    for i, sl in enumerate(slices, start=1):
        if sl is None or areas[i] > min_area:
            continue
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        long_side, short_side = max(h, w), max(min(h, w), 1)
        if long_side > min_extent:
            continue
        if long_side / short_side >= keep_aspect and long_side >= 3:
            continue  # 細長い断片 = 切れた線
        if areas[i] / float(h * w) < max_fill:
            continue  # スカスカ = 文字や線の一部
        remove[i] = True

    removed = int(remove[1:].sum())
    if removed:
        ink = ink & ~remove[lab]
    return ink, removed


def fill_pinholes(ink, max_area):
    """線の中にできた白い抜け穴を埋める。"""
    if max_area <= 0:
        return ink
    lab, n = ndi.label(~ink, structure=np.ones((3, 3), dtype=np.uint8))
    if n == 0:
        return ink
    areas = np.bincount(lab.ravel())
    small = np.zeros(n + 1, dtype=bool)
    small[1:] = areas[1:] <= max_area
    # 画像外周に接する成分(=紙の地)は埋めない
    border = np.unique(
        np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    )
    small[border] = False
    return ink | small[lab]


def main(argv=None):
    p = argparse.ArgumentParser(
        description="スキャン図面の点々ノイズを除去する",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("input", help="入力 PNG/JPEG/TIFF")
    p.add_argument("-o", "--output", help="出力 PNG")
    p.add_argument("--level", choices=["mild", "normal", "strong", "max"],
                   help="強度プリセット。個別オプションを明示すればそちらが優先")
    p.add_argument("--mode", choices=["bw", "gray"], default="bw",
                   help="bw=1bit二値(軽い) / gray=元の濃淡を残しノイズだけ白く飛ばす")
    p.add_argument("--bg-radius", type=int, default=25,
                   help="背景ムラ推定の半径px。線幅より十分大きく。0で無効")
    p.add_argument("--window", type=int, default=31, help="Sauvola の窓サイズpx(奇数)")
    p.add_argument("-k", type=float, default=0.20,
                   help="Sauvola の k。大きいほど拾う線が減る(地汚れに強い)")
    p.add_argument("--gate", choices=["otsu3", "otsu2", "none"], default="otsu3",
                   help="大域しきい値の決め方。otsu3=地/粒/線の3クラス分離(地汚れに強い)")
    p.add_argument("--gate-offset", type=int, default=0,
                   help="大域しきい値(大津)への補正。+で薄い線も拾う/-で地汚れに強い")
    p.add_argument("--contrast-min", type=float, default=0.0,
                   help="局所標準偏差がこれ未満の領域はインクとみなさない")
    p.add_argument("--min-area", type=int, default=30,
                   help="これ以下の画素数の孤立塊をノイズとする")
    p.add_argument("--min-extent", type=int, default=8,
                   help="外接矩形の長辺がこれ以下のものだけ除去対象にする")
    p.add_argument("--keep-aspect", type=float, default=3.0,
                   help="縦横比がこれ以上の細長い塊は線断片として残す")
    p.add_argument("--max-fill", type=float, default=0.55,
                   help="外接矩形に対する充填率がこれ未満の塊は残す(文字・線の保護)")
    p.add_argument("--auto", action="store_true",
                   help="min-area / min-extent を画像から自動推定する")
    p.add_argument("--auto-budget", type=float, default=0.45,
                   help="--auto 時、ノイズとみなす画素量の上限比率")
    p.add_argument("--directional", type=int, default=0,
                   help="この長さpx以上、いずれかの方向に伸びる構造だけを残す。"
                        "粒が繋がって塊になっている図面に有効。0で無効")
    p.add_argument("--no-reconstruct", action="store_true",
                   help="--directional 時に線の太さを復元しない(より強く消えるが線が細る)")
    p.add_argument("--fill-pinholes", type=int, default=0,
                   help="線内部の白抜け穴をこの画素数まで埋める。0で無効")
    p.add_argument("--close", type=int, default=0,
                   help="切れた線を繋ぐ closing の半径px。0で無効。1以上は線が太る")
    p.add_argument("--invert", action="store_true",
                   help="白線/黒地の図面の場合に指定")
    p.add_argument("--preview", help="処理前後を上下に並べた確認用PNGを書き出す")
    p.add_argument("--quiet", action="store_true")
    a = p.parse_args(argv)

    if a.level:
        presets = {
            "mild":   dict(min_area=20,  min_extent=6,  max_fill=0.50),
            "normal": dict(min_area=30,  min_extent=8,  max_fill=0.55),
            "strong": dict(min_area=80,  min_extent=12, max_fill=0.45),
            "max":    dict(min_area=150, min_extent=18, max_fill=0.35),
        }[a.level]
        given = {x.lstrip("-").replace("-", "_") for x in (argv or sys.argv[1:])
                 if x.startswith("--")}
        for key, val in presets.items():
            if key not in given:
                setattr(a, key, val)

    if not a.output and not a.preview:
        p.error("--output か --preview のどちらかを指定してください")

    gray, info = to_gray(a.input)
    orig = gray.copy()
    if a.invert:
        gray = 255 - gray
    log = (lambda *m: None) if a.quiet else (lambda *m: print(*m, file=sys.stderr))
    log(f"[1/5] 読み込み {info['size'][0]}x{info['size'][1]} mode={info['mode']} dpi={info['dpi']}")

    flat = flatten_background(gray, a.bg_radius)
    log(f"[2/5] 背景平坦化 radius={a.bg_radius}")

    win = a.window if a.window % 2 else a.window + 1
    ink, t_global = binarize(flat, win, a.k, a.gate, a.gate_offset, a.contrast_min)
    log(f"[3/5] 二値化 window={win} k={a.k} 大域しきい値={t_global} ink={ink.mean() * 100:.2f}%")

    lab, n, areas, slices = analyze_components(ink)
    min_area, min_extent = a.min_area, a.min_extent
    if a.auto:
        min_area, min_extent = auto_params(areas, n, a.auto_budget)
        log(f"      自動推定: --min-area {min_area} --min-extent {min_extent}")
    ink, removed = drop_specks(ink, lab, n, areas, slices,
                               min_area, min_extent, a.keep_aspect, a.max_fill)
    log(f"[4/5] 成分 {n} 個中 {removed} 個をノイズ除去 (残 ink={ink.mean() * 100:.2f}%)")

    if a.directional:
        ink = directional_keep(ink, a.directional, not a.no_reconstruct)
        log(f"      方向性フィルタ L={a.directional} 適用 (残 ink={ink.mean() * 100:.2f}%)")

    if a.fill_pinholes:
        ink = fill_pinholes(ink, a.fill_pinholes)
    if a.close:
        st = np.ones((a.close * 2 + 1,) * 2, dtype=bool)
        ink = ndi.binary_closing(ink, structure=st)

    if a.mode == "bw":
        out = np.where(ink, 0, 255).astype(np.uint8)
        img = Image.fromarray(out).convert("1")
    else:
        src = orig if not a.invert else 255 - orig
        out = np.where(ink, src, 255).astype(np.uint8)
        img = Image.fromarray(out)

    if a.invert:
        img = Image.fromarray(255 - np.asarray(img.convert("L")))

    if a.output:
        kw = {"optimize": True}
        if info["dpi"]:
            kw["dpi"] = info["dpi"]
        img.save(a.output, **kw)
        log(f"[5/5] 書き出し {a.output}")

    if a.preview:
        before = Image.fromarray(orig).convert("L")
        after = img.convert("L")
        w, h = before.size
        canvas = Image.new("L", (w, h * 2 + 8), 128)
        canvas.paste(before, (0, 0))
        canvas.paste(after, (0, h + 8))
        canvas.save(a.preview, optimize=True)
        log(f"[5/5] 比較画像 {a.preview}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
