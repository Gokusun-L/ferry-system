# -*- coding: utf-8 -*-
"""重建目录：按正文标题逐条生成条目，页码取自实际排版后的 PDF。

模板自带的目录是一个 TOC 域，缓存结果停留在「全部第 3 页」。这里把它改成
静态条目（toc 1/2/3 样式 + 右对齐点线制表位），页码按两遍法确定：
先写占位页码 -> 导出 PDF -> 逐标题定位所在页 -> 回填真实页码。
条目数量在两遍之间不变，因此分页不会漂移。
"""
import os
import re
import sys

import pymupdf
from docx import Document
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml.ns import qn
from docx.shared import Pt, Twips

DOCX = r"C:\Users\aa\Desktop\数据库应用实践\数据库应用实践报告-轮渡码头客运管理系统.docx"
PDF = r"C:\tmp\chk\数据库应用实践报告-轮渡码头客运管理系统.pdf"
TAB_POS = 8306          # 与原模板右对齐制表位一致（twips）


def heading_level(p):
    name = p.style.name or ""
    if name.startswith("Heading"):
        try:
            return int(name.split()[-1])
        except ValueError:
            return 1
    pPr = p._p.pPr
    if pPr is not None:
        o = pPr.find(qn("w:outlineLvl"))
        if o is not None:
            return int(o.get(qn("w:val"))) + 1
    return None


def collect(doc):
    """按出现顺序收集 (level, 显示文本)，一级标题的序号由模板自动编号生成，这里补上"""
    out = []
    n1 = n2 = 0
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        lvl = heading_level(p)
        if not lvl or lvl > 2:      # 目录只列一、二级标题，三级放在正文
            continue
        if lvl == 1:
            n1 += 1
            n2 = 0
            out.append((1, "%d. %s" % (n1, t), t))
        elif lvl == 2:
            n2 += 1
            out.append((2, t, t))
        else:
            out.append((3, t, t))
    return out


def page_map(pdf_path, items):
    """顺序扫描 PDF，返回每条标题所在的页码（1 起）"""
    doc = pymupdf.open(pdf_path)
    pages = []
    body = 0
    for i in range(doc.page_count):
        raw = doc[i].get_text("text")
        # 目录页含大量点线引导符，正文里不会出现 5 处以上，据此剔除
        if raw.count("....") >= 5:
            pages.append("")
            continue
        if body == 0:
            body = i
        pages.append(re.sub(r"\s+", "", raw))
    res, cur = [], 0
    for _, disp, raw in items:
        key = re.sub(r"\s+", "", raw)
        hit = None
        for i in range(cur, len(pages)):
            if key and key in pages[i]:
                hit = i
                break
        if hit is None:                      # 兜底：全文再找一次
            for i in range(len(pages)):
                if key and key in pages[i]:
                    hit = i
                    break
        if hit is None:
            hit = cur
        cur = hit
        res.append(hit + 1)
    return res


def rebuild(items, pages):
    doc = Document(DOCX)
    ps = doc.paragraphs
    title_i = None
    for i, p in enumerate(ps):
        if p.text.strip().replace(" ", "") == "目录":
            title_i = i
            break
    if title_i is None:
        raise SystemExit("未找到「目 录」标题")

    old = [p for p in ps if (p.style.name or "").startswith("toc")]
    for p in old:
        p._p.getparent().remove(p._p)

    anchor = ps[title_i]._p
    from docx.shared import Cm
    IND = {1: Cm(0), 2: Cm(0.75), 3: Cm(1.5)}
    for (lvl, disp, _), pg in zip(items, pages):
        p = doc.add_paragraph(style="toc %d" % min(lvl, 2))
        run = p.add_run(disp)
        run.font.size = None
        p.add_run("\t")
        p.add_run(str(pg))
        pf = p.paragraph_format
        pf.tab_stops.add_tab_stop(Twips(TAB_POS - {1: 0, 2: 425, 3: 850}[lvl]),
                                   WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        pf.space_before = Twips(0)
        pf.space_after = Twips(0)
        pf.line_spacing = Pt(14)
        pf.left_indent = IND[lvl]
        anchor.addnext(p._p)
        anchor = p._p
    doc.save(DOCX)


def main():
    doc = Document(DOCX)
    items = collect(doc)
    if "--dry" in sys.argv:
        for lvl, disp, _ in items:
            print(lvl, disp)
        print("共", len(items), "条")
        return
    pages = page_map(PDF, items) if os.path.exists(PDF) else [0] * len(items)
    rebuild(items, pages)
    for (lvl, disp, _), pg in zip(items, pages):
        print("%s%s%s" % ("  " * (lvl - 1), disp, "." * max(3, 46 - len(disp) * 2)), pg)


if __name__ == "__main__":
    main()
