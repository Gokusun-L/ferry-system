# -*- coding: utf-8 -*-
"""插图几何校验：连线交叉、标注压线、图形触边裁切。

判定口径（只对「细线」生效，避免把文字笔画、色块边框误判成线）：
1) 长游程 —— 线像素要求所在水平/竖直连续暗像素长度 >= MINRUN，
   文字笔画通常 < 25px，色块填充更是大块，都不会进入线掩膜。
2) 交叉点 —— 线掩膜上上下左右 ±R 同时有线像素（4 臂）。
   折线拐角 2 臂、T 形接头 3 臂，不误判。
3) 标注压线 —— 红色「1 / N」连通域外接框内出现线掩膜像素。
4) 触边裁切 —— 非白像素进入画布边缘 2px。

用法：python check_figs.py [fig3_er.png ...]
"""
import os
import sys

import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")
R = 7
MINRUN = 40


def run_lengths(mask, axis):
    """返回每个像素所在连续 True 段的长度（axis=1 横向）"""
    m = mask if axis == 1 else mask.T
    out = np.zeros(m.shape, np.int32)
    for i in range(m.shape[0]):
        row = m[i]
        if not row.any():
            continue
        idx = np.flatnonzero(np.diff(np.concatenate(([0], row.view(np.int8), [0]))))
        for a, b in zip(idx[0::2], idx[1::2]):
            out[i, a:b] = b - a
    return out if axis == 1 else out.T


def classify(path):
    a = np.array(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    reddish = (r - g > 45) & (r - b > 25) & (r > 110) & (g < 120)
    dark = a.max(axis=2) < 110
    return a, dark, reddish


def thin_lines(dark):
    """线掩膜：所在水平/竖直连续段够长，且局部密度低（排除实心箭头与文字笔画）"""
    rh = run_lengths(dark, 1)
    rv = run_lengths(dark, 0)
    long = (rh >= MINRUN) | (rv >= MINRUN)
    k = 15
    pad = np.pad(dark.astype(np.int32), ((1, 0), (1, 0)))
    ii = pad.cumsum(0).cumsum(1)
    h, w = dark.shape
    y0 = np.clip(np.arange(h) - k // 2, 0, h)
    y1 = np.clip(np.arange(h) + k // 2 + 1, 0, h)
    x0 = np.clip(np.arange(w) - k // 2, 0, w)
    x1 = np.clip(np.arange(w) + k // 2 + 1, 0, w)
    dense = (ii[np.ix_(y1, x1)] - ii[np.ix_(y0, x1)]
             - ii[np.ix_(y1, x0)] + ii[np.ix_(y0, x0)])
    return dark & long & (dense <= 110)


def crossings(line):
    h, w = line.shape
    ys, xs = np.where(line)
    hits = []
    for y, x in zip(ys, xs):
        if x < R or y < R or x >= w - R or y >= h - R:
            continue
        if (line[y, x - R] and line[y, x + R]
                and line[y - R, x] and line[y + R, x]):
            hits.append((int(x), int(y)))
    groups = []
    for x, y in hits:
        for gp in groups:
            if abs(gp[0] - x) <= 8 and abs(gp[1] - y) <= 8:
                break
        else:
            groups.append((x, y))
    return groups


def label_touch(line, reddish):
    h, w = line.shape
    seen = np.zeros((h, w), bool)
    bad = []
    ys, xs = np.where(reddish)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        stack = [(y0, x0)]
        seen[y0, x0] = True
        pts = []
        while stack:
            y, x = stack.pop()
            pts.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and reddish[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        if len(pts) < 30:
            continue
        ys_ = [p[0] for p in pts]
        xs_ = [p[1] for p in pts]
        y1, y2, x1, x2 = min(ys_), max(ys_), min(xs_), max(xs_)
        if (y2 - y1) > 60 or (x2 - x1) > 60:      # 非「1 / N」字形
            continue
        sub = line[max(0, y1 - 1):y2 + 2, max(0, x1 - 1):x2 + 2]
        if sub.sum() > 0:
            bad.append((int(x1), int(y1), int(x2 - x1 + 1), int(y2 - y1 + 1), int(sub.sum())))
    return bad


def edge_cut(a):
    ink = a.max(axis=2) < 245
    out = []
    if ink[:2, :].any():
        out.append("顶部")
    if ink[-2:, :].any():
        out.append("底部")
    if ink[:, :2].any():
        out.append("左侧")
    if ink[:, -2:].any():
        out.append("右侧")
    return out


def main(names):
    names = names or sorted(f for f in os.listdir(OUT) if f.startswith("fig"))
    bad_total = 0
    for n in names:
        a, dark, reddish = classify(os.path.join(OUT, n))
        line = thin_lines(dark)
        cg, lb, ec = crossings(line), label_touch(line, reddish), edge_cut(a)
        flag = bool(cg or lb or ec)
        bad_total += flag
        print("%-18s %dx%d  交叉 %d %s | 压线 %d %s | 触边 %s"
              % (n, line.shape[1], line.shape[0], len(cg), cg[:6] if cg else "-",
                 len(lb), lb[:6] if lb else "-", ec or "无"))
    print("\n结论：%s" % ("全部通过" if bad_total == 0 else "%d 张图存在问题" % bad_total))


if __name__ == "__main__":
    main(sys.argv[1:])
