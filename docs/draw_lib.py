# -*- coding: utf-8 -*-
"""报告插图绘制库：精确控制坐标，保证文字不溢出、连線不重叠、箭头指向明确。"""
import math
from PIL import Image, ImageDraw, ImageFont

FONT = "C:/Windows/Fonts/msyh.ttc"
FONT_B = "C:/Windows/Fonts/msyhbd.ttc"

# 画布按 1cm=160px 设计，插入 Word 时按 14.4cm 宽度缩放
CM = 160

INK = (33, 37, 41)
GREY = (108, 117, 125)
LINE = (52, 58, 64)


def F(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


class Canvas:
    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w, h), bg)
        self.d = ImageDraw.Draw(self.img)

    # ---------- 文本 ----------
    def measure(self, text, font):
        b = self.d.textbbox((0, 0), text, font=font)
        return b[2] - b[0], b[3] - b[1]

    def wrap(self, text, font, max_w):
        """按宽度折行，返回行列表（中文逐字折，英文按空格）"""
        lines, cur = [], ""
        for ch in text:
            if ch == "\n":
                lines.append(cur)
                cur = ""
                continue
            t = cur + ch
            if self.measure(t, font)[0] > max_w and cur:
                lines.append(cur)
                cur = ch
            else:
                cur = t
        if cur:
            lines.append(cur)
        return lines

    def text(self, xy, s, font, fill=INK, anchor="mm"):
        self.d.text(xy, s, font=font, fill=fill, anchor=anchor)

    # ---------- 基本图元 ----------
    def box(self, x, y, w, h, fill="white", outline=LINE, radius=10, width=3):
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                                 fill=fill, outline=outline, width=width)

    def rect(self, x, y, w, h, fill="white", outline=LINE, width=3):
        self.d.rectangle([x, y, x + w, y + h], fill=fill, outline=outline, width=width)

    def ellipse(self, cx, cy, w, h, fill="white", outline=LINE, width=3):
        self.d.ellipse([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2],
                       fill=fill, outline=outline, width=width)

    def diamond(self, cx, cy, w, h, fill="white", outline=LINE, width=3):
        self.d.polygon([(cx, cy - h // 2), (cx + w // 2, cy),
                        (cx, cy + h // 2), (cx - w // 2, cy)],
                       fill=fill, outline=outline, width=width)

    # ---------- 箭头 ----------
    def _head(self, p0, p1, color, size=17):
        """在 p1 处画实心三角箭头，p1 为尖端"""
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        left = (p1[0] - size * math.cos(ang - 0.42), p1[1] - size * math.sin(ang - 0.42))
        right = (p1[0] - size * math.cos(ang + 0.42), p1[1] - size * math.sin(ang + 0.42))
        self.d.polygon([p1, left, right], fill=color)

    def arrow(self, pts, color=LINE, width=3, dashed=False, head=True, head_size=17,
              open_head=False, vee_head=False):
        """折线箭头：pts 为路径点，箭头在最后一段末端"""
        if dashed:
            for i in range(len(pts) - 1):
                self._dash(pts[i], pts[i + 1], color, width)
        else:
            self.d.line(pts, fill=color, width=width, joint="curve")
        if not head:
            return
        p0, p1 = pts[-2], pts[-1]
        if vee_head:
            # 开放 V 形箭头（UML 依赖 / 数据流）
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            s = head_size
            a1 = (p1[0] - s * math.cos(ang - 0.46), p1[1] - s * math.sin(ang - 0.46))
            a2 = (p1[0] - s * math.cos(ang + 0.46), p1[1] - s * math.sin(ang + 0.46))
            self.d.line([a1, p1, a2], fill=color, width=width)
            return
        if open_head:
            # 空心三角（UML 依赖）
            ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
            s = head_size
            a1 = (p1[0] - s * math.cos(ang - 0.42), p1[1] - s * math.sin(ang - 0.42))
            a2 = (p1[0] - s * math.cos(ang + 0.42), p1[1] - s * math.sin(ang + 0.42))
            self.d.polygon([p1, a1, a2], fill="white", outline=color)
            self.d.line([p1, a1, a2, p1], fill=color, width=width)
        else:
            self._head(p0, p1, color, head_size)

    def _dash(self, a, b, color, width, dash=14, gap=10):
        dx, dy = b[0] - a[0], b[1] - a[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        ux, uy = dx / dist, dy / dist
        t = 0.0
        while t < dist:
            e = min(t + dash, dist)
            self.d.line([(a[0] + ux * t, a[1] + uy * t), (a[0] + ux * e, a[1] + uy * e)],
                        fill=color, width=width)
            t = e + gap

    # ---------- 组合图元 ----------
    def entity(self, x, y, w, title, rows, title_h=54, row_h=36, pad=12,
               fill=(232, 240, 254), head_fill=(191, 215, 250), font_size=27):
        """实体框：标题条 + 属性行，行内以 | 分隔（主键加下划线由调用方用 * 标记）"""
        h = title_h + row_h * len(rows) + pad
        self.box(x, y, w, h, fill=fill, radius=8, width=3)
        # 标题区
        self.d.rounded_rectangle([x, y, x + w, y + title_h], radius=8,
                                 fill=head_fill, outline=LINE, width=3)
        self.d.rectangle([x, y + title_h - 12, x + w, y + title_h], fill=head_fill)
        self.d.line([(x, y + title_h), (x + w, y + title_h)], fill=LINE, width=3)
        self.text((x + w // 2, y + title_h // 2), title, F(font_size + 3, True))
        fy = F(font_size)
        cy = y + title_h + pad // 2
        for r in rows:
            pk = r.startswith("*")
            label = r[1:] if pk else r
            self.text((x + 20, cy + row_h // 2), label, fy, fill=INK, anchor="lm")
            if pk:
                tw = self.measure(label, fy)[0]
                self.d.line([(x + 20, cy + row_h // 2 + 16), (x + 20 + tw, cy + row_h // 2 + 16)],
                            fill=INK, width=2)
            cy += row_h
        return h

    def actor(self, cx, cy, label, scale=1.0, color=LINE, label_left=False,
              label_below=False):
        """UML 角色小人，返回连线起点（右侧,中心y）"""
        r = int(15 * scale)
        body = int(34 * scale)
        arm = int(26 * scale)
        leg = int(30 * scale)
        top = cy - int(62 * scale)
        self.d.ellipse([cx - r, top, cx + r, top + 2 * r], outline=color, width=3)
        neck = top + 2 * r
        self.d.line([(cx, neck), (cx, neck + body)], fill=color, width=3)
        hy = neck + int(body * 0.28)
        # 两段独立手臂，避免横线穿过躯干形成交叉
        self.d.line([(cx, hy), (cx - arm // 2, hy)], fill=color, width=3)
        self.d.line([(cx, hy), (cx + arm // 2, hy)], fill=color, width=3)
        self.d.line([(cx, neck + body), (cx - leg // 2, neck + body + leg)], fill=color, width=3)
        self.d.line([(cx, neck + body), (cx + leg // 2, neck + body + leg)], fill=color, width=3)
        fy = F(int(30 * scale), True)
        if label_below:
            # 标签落在脚下：连线自右侧扇出，二者互不侵占
            self.text((cx, neck + body + leg + int(30 * scale)), label, fy)
        elif label_left:
            self.text((cx - int(22 * scale), neck + body + leg + int(26 * scale)), label, fy, anchor="rm")
        else:
            # 标签放在小人正上方：连线自右侧扇出，两者互不侵占
            self.text((cx, top - int(16 * scale)), label, fy)
        return cx + arm // 2 + int(12 * scale), cy


    def title(self, xy, s, size=32):
        self.text(xy, s, F(size, True), fill=(30, 41, 59))

    def save(self, path):
        self.img.save(path, dpi=(300, 300))
        return path
