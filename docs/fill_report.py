# -*- coding: utf-8 -*-
"""
把系统测试数据回填进《数据库应用实践报告》第五部分。
输入：数据库应用实践报告模板-2026-2027-1.docx
输出：数据库应用实践报告-轮渡码头客运管理系统.docx（模板保持不动）
格式：正文宋体 5 号，行距 24 磅
"""
import copy
import docx
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = r"C:/Users/aa/Desktop/数据库应用实践/数据库应用实践报告模板-2026-2027-1.docx"
DST = r"C:/Users/aa/Desktop/数据库应用实践/数据库应用实践报告-轮渡码头客运管理系统.docx"

doc = docx.Document(SRC)

# 定位 "系统测试" 标题
anchor = None
for p in doc.paragraphs:
    if p.style.name.startswith("Heading") and p.text.strip() == "系统测试":
        anchor = p
        break
assert anchor is not None, "未找到『系统测试』标题"
cur = anchor

BODY_FONT = "宋体"
LATIN_FONT = "Times New Roman"


def style_run(run, size=10.5, bold=False, mono=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    name = "Consolas" if mono else LATIN_FONT
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), BODY_FONT if not mono else "宋体")
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)


def P(text, size=10.5, bold=False, style=None, indent=False, mono=False,
      space_before=0, space_after=0, align=None):
    """在 cur 之后插入段落，并把 cur 移到新段落"""
    global cur
    p = doc.add_paragraph(style=style)
    run = p.add_run(text)
    style_run(run, size=size, bold=bold, mono=mono)
    pf = p.paragraph_format
    pf.line_spacing = Pt(24)
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    if indent:
        pf.first_line_indent = Pt(size * 2)
    if align is not None:
        p.alignment = align
    cur._p.addnext(p._p)
    cur = p
    return p


def H(text, level=2):
    """模板只内置 Heading 1，2/3 级标题用直接格式 + 大纲级别实现"""
    global cur
    p = doc.add_paragraph()
    run = p.add_run(text)
    style_run(run, size=14 if level == 2 else 12, bold=True)
    p.paragraph_format.space_before = Pt(10 if level == 2 else 6)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = Pt(24)
    p.paragraph_format.keep_with_next = True      # 标题不得与其后正文分处两页
    pPr = p._p.get_or_add_pPr()
    outline = OxmlElement("w:outlineLvl")
    outline.set(qn("w:val"), str(level - 1))
    pPr.append(outline)
    cur._p.addnext(p._p)
    cur = p
    return p


def set_table_borders(tbl):
    """模板未内置 Table Grid 样式，直接写 w:tblBorders"""
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)
    tblPr.append(borders)


def T(headers, rows, widths=None, font_size=8.5):
    """插入表格；表后补一个空段落作为新 anchor"""
    global cur
    cur.paragraph_format.keep_with_next = True    # 引导语不得与表格分处两页
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    set_table_borders(tbl)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    # 固定布局：autofit=True 会让渲染器按内容均分列宽，使设计好的列宽失效
    tbl.autofit = False

    # 表头跨页重复
    trPr = tbl.rows[0]._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:tblHeader"))

    for j, h in enumerate(headers):
        cell = tbl.rows[0].cells[j]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        style_run(run, size=font_size, bold=True)
        p.paragraph_format.line_spacing = Pt(14)
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)

    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell = tbl.rows[i].cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            style_run(run, size=font_size)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = Pt(14)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)

    # 禁止单行跨页拆断（否则一行文字会被分成两页）
    for row in tbl.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))

    # 短表整表不跨页：行间绑定，避免表头+1 行被留在页尾
    if len(rows) <= 6:
        for row in tbl.rows[:-1]:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = True

    if widths:
        # 按可用宽度缩放，避免表格超出页面右边界（A4 21cm - 左右边距 3.17cm×2 ≈ 14.6cm）
        usable = 14.4
        total = sum(widths)
        scale = usable / total if total > usable else 1.0
        tblPr = tbl._tbl.tblPr
        for old in tblPr.findall(qn("w:tblW")):
            tblPr.remove(old)
        tblW = OxmlElement("w:tblW")
        tblW.set(qn("w:type"), "dxa")
        tblW.set(qn("w:w"), str(int(min(total, usable) * 567)))
        tblPr.insert(0, tblW)
        for j, w in enumerate(widths):
            tbl.columns[j].width = Cm(w * scale)
            for row in tbl.rows:
                row.cells[j].width = Cm(w * scale)

    cur._p.addnext(tbl._tbl)
    # 表后空段落，避免相邻表格粘连
    gap = doc.add_paragraph()
    gap.paragraph_format.line_spacing = Pt(12)
    gap.paragraph_format.space_before = Pt(2)
    gap.paragraph_format.space_after = Pt(2)
    tbl._tbl.addnext(gap._p)
    cur = gap
    return tbl



# ============================================================
# 通用：定位标题 / 插图 / 代码块 / 删除尾部
# ============================================================
FIG_DIR = "C:/Users/aa/Desktop/数据库应用实践/ferry-system/docs/figs/"
SHOT_DIR = "C:/Users/aa/Desktop/数据库应用实践/ferry-system/docs/shots/"


def goto(title):
    """把 cur 定位到指定 Heading 1 段落"""
    global cur
    for p in doc.paragraphs:
        if p.style.name.startswith("Heading") and p.text.strip() == title:
            p.paragraph_format.keep_with_next = True
            cur = p
            return p
    raise SystemExit("未找到标题：" + title)


def IMG(path, width_cm, caption=None):
    """居中插入图片；caption 用 9pt 居中置于图下"""
    global cur
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Cm(width_cm))
    pf = p.paragraph_format
    pf.line_spacing = 1.0          # 固定行高会把图片裁成一条，必须用倍数行距
    pf.first_line_indent = Cm(0)    # 模板正文带首行缩进，会把图整体右移，必须清零
    pf.left_indent = Cm(0)
    pf.space_before = Pt(6)
    pf.space_after = Pt(2)
    pf.keep_with_next = True
    cur._p.addnext(p._p)
    cur = p
    if caption:
        c = P(caption, size=9, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
        c.paragraph_format.keep_with_next = False


def CODE(lines, size=8.5):
    """等宽代码块，浅灰底，无首行缩进"""
    global cur
    for ln in lines:
        p = doc.add_paragraph()
        run = p.add_run(ln if ln.strip() else " ")
        style_run(run, size=size, mono=True)
        pf = p.paragraph_format
        pf.line_spacing = Pt(size * 1.45)
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.left_indent = Pt(14)
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "F4F5F7")
        pPr.append(shd)
        cur._p.addnext(p._p)
        cur = p
    P("", size=4, space_after=2)


def delete_from(text):
    """删除以 text 开头的段落及其后全部内容（用于清除模板撰写要求）"""
    body = doc.element.body
    target = None
    for p in doc.paragraphs:
        if p.text.strip().startswith(text):
            target = p._p
            break
    if target is None:
        return False
    started = False
    for child in list(body):
        if child is target:
            started = True
        if started and child.tag in (qn("w:p"), qn("w:tbl")):
            body.remove(child)
    return True


# ============================================================
# 1 系统需求分析
# ============================================================
def fill_sec1():
    H("1.1 业务背景与建设目标", 2)
    P("轮渡码头客运的业务主线是「航线—船舶—班次—船票」：码头按航线与船舶编排班次，"
      "乘客在班次上选座购票，开船前检票，特殊情况退票或改签，管理层按日、按月汇总售票与收入。", indent=True)
    P("原先的窗口人工售票配合 Excel 台账存在三个具体问题：一是同一座位可能被两个窗口同时卖出，"
      "事后只能退款平息；二是班次取消后要人工逐个电话通知并手工退款，容易漏单；"
      "三是月度报表靠人工汇总，退票算不算收入、改签算不算退票各人算法不同，口径无法复现。", indent=True)
    P("本系统的建设目标因此定为三条：把选座、售票、支付、检票、退改签、统计全流程放进同一数据库应用；"
      "用数据库约束与事务保证「一座一票」；用统一的 SQL 口径保证报表可复现、可核对。", indent=True)

    H("1.2 用户角色与权限需求", 2)
    P("系统按最小权限原则划分三类角色，未登录用户只能访问登录页与注册页。", indent=True)
    T(["角色", "典型操作", "权限边界"],
      [["乘客 PASSENGER", "注册登录、查询班次余票、选座下单、支付、申请退票、改签、查看本人订单与通知",
        "只能操作自己的订单与票，不能进入管理端"],
       ["售票员 SELLER", "窗口代客下单、检票、按订单号查询、办理退票",
        "不能维护航线、船舶、班次与用户"],
       ["管理员 ADMIN", "航线/船舶/班次/座位维护、用户管理、统计报表与 Excel 导出",
        "可访问全部功能，但同样受数据库约束限制"],
       ["未登录", "登录、注册", "仅两个页面，其余请求一律跳转登录"]],
      widths=[3.0, 7.2, 4.2])

    H("1.3 功能性需求", 2)
    P("功能按任务书五个模块划分，逐条对照如下表。", indent=True)
    T(["模块", "功能点", "说明"],
      [["用户与权限", "注册 / 登录 / 个人信息 / 改密 / 用户管理（禁用、解锁）",
        "口令 BCrypt 加密存储；连续 5 次密码错误锁定账户；登录态用 Session 保存"],
       ["基础数据", "航线增删改查、船舶与座位布局、班次发布与取消、班次座位生成",
        "航线按「出发港+到达港」唯一；船舶总座位数与座位明细必须一致；班次状态 PENDING→SELLING→DEPARTED→FINISHED/CANCELLED"],
       ["售票业务", "余票查询、选座锁定、下单、支付、超时取消、退票、改签、检票",
        "锁座保留 5 分钟；一人在同一班次只能有一张有效票；改签需换班次或换座位并结清差价"],
       ["统计报表", "按日/区间售票统计、班次售票与退票、航线与班次上座率、收入汇总、退票原因分布、Excel 导出",
        "全部指标由数据库聚合得出，不在应用层累加；导出用 EasyExcel 流式写"],
       ["通知", "班次取消通知、订单状态通知、未读数",
        "取消班次时在同一事务内向受影响乘客批量写入通知"]],
      widths=[2.4, 7.4, 4.6])

    H("1.4 非功能性需求", 2)
    P("非功能需求只列能被验证的项，每项都对应具体实现手段，见下表。", indent=True)
    T(["类别", "要求", "实现手段"],
      [["数据一致性", "同一班次同一座位不得售出两张有效票；取消班次须同时作废订单、释放座位、生成退款、发送通知",
        "schedule_seat 唯一键 + 条件 UPDATE + 单事务"],
       ["完整性", "外键不得悬空，状态值不得越界，金额不得为负",
        "FOREIGN KEY、CHECK 约束、NOT NULL、唯一索引"],
       ["安全性", "口令不可逆存储；越权请求被拦截；SQL 注入无效",
        "BCrypt 加盐哈希；Session + 两道拦截器 + @RequireRole；MyBatis 全部使用 #{} 预编译"],
       ["性能", "单表万级数据下列表与统计查询秒级返回",
        "按查询条件建索引；列表分页；统计走覆盖索引"],
       ["可用性", "异常不得以堆栈形式暴露给用户",
        "GlobalExceptionHandler 统一转换为 Result 结构，业务异常给出可读提示"],
       ["可维护性", "SQL 与 Java 分离，改 SQL 不需要重新编译",
        "12 个 DAO 接口对应 12 个 XML Mapper"]],
      widths=[2.4, 6.6, 5.4])

    H("1.5 用例图", 2)
    P("系统用例图如图 1 所示。三个参与者按列分区，各自连向本角色可执行的用例；"
      "「登录」为三者共享的公共用例，「查询班次」对乘客与售票员同时开放。", indent=True)
    IMG(FIG_DIR + "fig1_usecase.png", 14.0, "图 1  轮渡码头客运管理系统用例图")
    P("主要用例的前置条件与主流程见下表。", indent=True)
    T(["用例", "前置条件", "主流程"],
      [["在线购票", "已登录且角色为乘客", "选班次 → 选座（锁定 5 分钟）→ 填乘客信息 → 提交订单 → 支付 → 出票"],
       ["窗口售票", "售票员已登录", "选定班次 → 指定乘客与座位 → 代客下单 → 收款确认 → 出票"],
       ["检票", "售票员或管理员已登录，班次未发船", "按票号或订单号检索 → 校验票状态为 PAID → 置为 CHECKED 并记录检票时间"],
       ["退票", "票状态为 PAID 且未检票", "选择退票原因 → 计算手续费 → 票置 REFUNDED、座位释放、写 refund 记录 → 订单重算状态"],
       ["改签", "票状态为 PAID 且未检票", "选新班次与新座位 → 锁新座 → 旧票置 RESCHEDULED、发新票 → 差价写入 refund（RESCHEDULE_DIFF）"],
       ["取消班次", "管理员已登录，班次非已完成", "班次置 CANCELLED → 逐单退票退款 → 释放座位 → 批量写通知"]],
      widths=[2.2, 4.4, 7.8])


# ============================================================
# 2 概要设计
# ============================================================
def fill_sec2():
    H("2.1 系统组织结构", 2)
    P("系统采用 Controller—Service—DAO 三层结构，层间只允许自上而下单向调用；"
      "跨层调用（如 Controller 直接访问 DAO）在代码评审阶段一律退回。整体组织结构如图 2 所示。", indent=True)
    IMG(FIG_DIR + "fig2_arch.png", 14.0, "图 2  系统组织结构图")
    P("各层职责与依赖方向如下表。", indent=True)
    T(["层次", "主要组件", "职责", "依赖方向"],
      [["表示层", "Thymeleaf 模板 + 静态资源", "页面渲染、表单提交、AJAX 调用后端接口", "→ 控制层"],
       ["控制层", "7 个 Controller", "接收请求、参数校验、组装返回体、导出文件", "→ 业务层"],
       ["业务层", "6 个 Service 接口 + 6 个实现类", "业务规则、事务边界（@Transactional）、状态流转", "→ 持久层"],
       ["持久层", "12 个 DAO 接口 + 12 个 XML Mapper", "SQL 编写与结果映射，不写业务判断", "→ 数据层"],
       ["数据层", "MySQL 8.0 / InnoDB", "数据存储、约束校验、行级锁与事务", "—"]],
      widths=[2.0, 4.6, 5.8, 2.0])
    P("横切支撑说明：config 负责 WebMvc 配置、拦截器注册与三个定时任务；interceptor 分登录拦截与角色校验两道；"
      "common 提供统一返回体 Result、登录用户 LoginUser、权限注解 @RequireRole 与业务异常 BizException；"
      "exception 用 GlobalExceptionHandler 把异常统一转成 JSON，避免堆栈直接抛给前端。", indent=True)

    H("2.2 模块划分", 2)
    P("按业务内聚拆成六个模块，模块之间通过 Service 接口交互。", indent=True)
    T(["模块", "主要类", "职责"],
      [["用户与权限", "UserController / UserService / UserDao / LoginInterceptor / RoleInterceptor",
        "注册登录、口令加密与校验、账户锁定、角色拦截"],
       ["航线与船舶", "ManageController / RouteService / ShipService / RouteDao / ShipDao / ShipSeatDao",
        "航线唯一性校验、船舶与座位布局维护、逻辑删除"],
       ["班次与座位", "ScheduleService / ScheduleDao / ScheduleSeatDao",
        "班次发布、批量生成、按船舶座位铺开班次座位、状态流转"],
       ["售票与订单", "OrderController / OrderService / OrderDao / TicketDao / ScheduleSeatDao",
        "锁座、下单、支付、取消、退票、改签、检票，是系统的核心模块"],
       ["统计报表", "StatsController / ExportController / StatsService / StatsDao",
        "五类聚合统计与四类 Excel 导出"],
       ["通知", "NotificationController / NotificationDao",
        "班次取消与订单状态通知、未读数"]],
      widths=[2.4, 7.0, 5.0])

    H("2.3 技术选型", 2)
    P("选型的判断标准是：能否用最少的组件把任务书的考核点（完整性约束、CRUD、事务并发、聚合统计、权限）都落到实处。"
      "逐项对照如下表，同时列出被否掉的方案及其代价。", indent=True)
    T(["技术点", "选型", "理由", "被否方案与代价"],
      [["Web 框架", "Spring Boot 3.2.5", "内嵌 Tomcat，一个 main 即可运行；自动装配省去 web.xml 与手工装配 Bean",
        "Servlet + JSP：需自己管理连接池与事务，代码量约三倍"],
       ["持久层", "MyBatis + XML Mapper", "任务书要求 XML 配置；SQL 与 Java 分离，统计类复杂 SQL 可直接书写",
        "JPA/Hibernate：多表聚合要退回原生 SQL，且生成的 SQL 不可控"],
       ["视图", "Thymeleaf", "服务端渲染，无前后端联调成本；模板本身即 HTML，便于与页面截图对照",
        "Vue/React 分离：需额外维护一套工程与跨域配置，对本项目是纯负担"],
       ["权限", "手写 HandlerInterceptor + Session + @RequireRole", "逻辑可见、可断点调试，能说清拦截发生在哪一步",
        "Spring Security：配置量大，对三个角色属过度设计"],
       ["口令", "BCrypt（仅引入 spring-security-crypto）", "自带盐值，同一明文两次加密结果不同；可调强度",
        "引入完整 starter 会连带启用整套过滤器链，反而要写更多放行配置"],
       ["报表导出", "EasyExcel", "流式写，内存占用与行数无关；注解式表头",
        "Apache POI 直接写：需手工管理 Workbook，数据量大时易 OOM"],
       ["数据库", "MySQL 8.0 + InnoDB", "支持事务、行级锁、外键与 CHECK 约束，是并发考核的前提",
        "MyISAM：无事务无行锁，无法实现「一座一票」"]],
      widths=[2.2, 3.6, 4.6, 4.0])

    H("2.4 关键设计决策", 2)
    P("以下四项决策直接决定系统是否正确，逐条给出问题、决策与代价。", indent=True)

    P("（1）订单状态由票推导，不独立维护。", bold=True, space_before=6)
    P("问题：一张订单可含多张票，若订单状态与票状态各存一份，退票、改签、检票任一路径漏改，"
      "就会出现「订单已支付但票已全部退掉」的矛盾数据。"
      "决策：订单状态不手写，统一由 recalcOrderStatus(orderId) 按票的状态重算——全部票为 UNPAID 则订单 UNPAID，"
      "存在已支付或已检票则为 PAID/CHECKED，全部失效则 CANCELLED 或 REFUNDED。"
      "代价：每次票状态变更多一次聚合查询；换来的是订单与票在数据结构上不可能不一致。", indent=True)

    P("（2）锁座用带条件的单条 UPDATE，而不是先查后改。", bold=True, space_before=6)
    P("问题：「先 SELECT 判断可售、再 UPDATE 置为锁定」在并发下存在时间窗，两个线程都能读到 AVAILABLE。"
      "决策：把判断写进 WHERE 子句——"
      "UPDATE schedule_seat SET status='LOCKED', lock_user_id=? "
      "WHERE schedule_id=? AND seat_no=? AND status='AVAILABLE'，以影响行数是否为 1 判定成功。"
      "InnoDB 对该行加排他锁，后到事务的 WHERE 条件不再成立，影响行数为 0。"
      "代价：同班次并发下单被串行化，吞吐低于「先查后改」，这是正确性换来的必要代价。", indent=True)

    P("（3）改签单独设状态，退款区分业务类型。", bold=True, space_before=6)
    P("问题：改签的旧票若直接置为 REFUNDED、差价若直接写入 refund 表，统计时「退票量」会把改签一起算进去。"
      "本项目实测：某班次真实退票 2 张、改签 1 张，修复前报表显示退票 3 张，退票率虚高 50%。"
      "决策：票状态新增 RESCHEDULED（已改签作废），refund 表新增 biz_type，真退票记 REFUND、"
      "改签退差价记 RESCHEDULE_DIFF，全部退票类指标只统计 biz_type='REFUND'。"
      "代价：多一个状态值与一列类型，每个业务分支都要显式赋值；换来的是语义不重载、口径可一句话说清。", indent=True)

    P("（4）单号由「前缀 + 时间戳 + 3 位循环序号」生成，唯一索引兜底。", bold=True, space_before=6)
    P("问题：纯时间戳在并发下必然碰撞；纯 UUID 不可读，窗口核对时无法口述。"
      "决策：genNo(prefix) 用 AtomicInteger 取模 1000 生成 3 位序号，形如 O20261124103015001；"
      "order_no、ticket_no 上建唯一索引，插入冲突按 DuplicateKeyException 重试。"
      "代价：单机有序、集群无序；若改为多实例部署需换成号段或雪花算法，这一点已在第 7 部分列为改进项。", indent=True)


# ============================================================
# 3 数据库设计
# ============================================================
def fill_sec3():
    H("3.1 概念结构设计", 2)
    P("系统共 11 个实体，E-R 图如图 3 所示。图中只保留业务属性，created_at / updated_at 两个审计字段为图面清晰而省略，"
      "其余属性与 sql/01_schema.sql 逐列对应；带下划线的属性为主键，箭头由「1」端指向「N」端。", indent=True)
    IMG(FIG_DIR + "fig3_er.png", 14.0, "图 3  系统 E-R 图")
    P("实体与联系的业务含义见下表。", indent=True)
    T(["实体", "业务含义", "主要联系"],
      [["user 用户", "乘客、售票员、管理员共用一张表，由 role 区分", "1:N orders（作为乘客）、1:N orders（作为售票员）、1:N notification"],
       ["route 航线", "出发港到到达港的固定线路，含预计航行时长", "1:N schedule"],
       ["ship 船舶", "船舶档案与总座位数", "1:N schedule、1:N ship_seat"],
       ["ship_seat 船舶座位", "船舶的物理座位布局（排号、列号）", "N:1 ship"],
       ["schedule 班次", "某航线某船某时刻的一次航行，是售票的载体", "N:1 route、N:1 ship、1:N ticket、1:N schedule_seat"],
       ["schedule_seat 班次座位", "班次上每个座位的实时状态，是防超卖的关键表", "N:1 schedule、N:1 user（锁定人）"],
       ["orders 订单", "一次下单行为，可含多张票", "N:1 user、N:1 schedule、1:N ticket、1:N refund"],
       ["ticket 船票", "一张票对应一个座位，状态决定是否有效", "N:1 orders、N:1 schedule、1:N refund、1:N reschedule"],
       ["refund 退票记录", "真退票与改签退差价共用此表，由 biz_type 区分", "N:1 orders、N:1 ticket、N:1 user（经办人）"],
       ["reschedule 改签记录", "一次改签的原票与新票对应关系", "N:1 ticket（原票）、N:1 ticket（新票）"],
       ["notification 通知", "面向乘客的消息，班次取消时批量产生", "N:1 user"]],
      widths=[3.0, 6.4, 5.0])

    H("3.2 逻辑结构设计", 2)
    P("按「1:N 联系向 N 端归并外键」的规则转换，得到 11 个关系模式。属性集中以 * 标注主键，FK 标注外键。", indent=True)
    T(["关系模式（属性集）", "主键", "外键"],
      [["user(*id, username, password, name, phone, id_card, role, status, login_fail, lock_until)", "id", "—"],
       ["route(*id, route_name, depart_port, arrive_port, duration, description, deleted)", "id", "—"],
       ["ship(*id, ship_name, total_seats, ship_type, description, deleted)", "id", "—"],
       ["ship_seat(*id, ship_id FK, seat_no, row_no, col_no)", "id", "ship_id → ship"],
       ["schedule(*id, route_id FK, ship_id FK, depart_time, arrive_time, price, status, sold_count, deleted)",
        "id", "route_id → route；ship_id → ship"],
       ["schedule_seat(*id, schedule_id FK, seat_no, status, order_id, lock_time, lock_user_id FK)",
        "id", "schedule_id → schedule；lock_user_id → user"],
       ["orders(*id, order_no, user_id FK, seller_id FK, schedule_id FK, total_amount, status, channel, create_time, pay_time)",
        "id", "user_id / seller_id → user；schedule_id → schedule"],
       ["ticket(*id, ticket_no, order_id FK, schedule_id FK, seat_no, passenger_name, id_card, phone, price, status, check_time, checker_id FK)",
        "id", "order_id → orders；schedule_id → schedule；checker_id → user"],
       ["refund(*id, order_id FK, ticket_id FK, refund_amount, fee, reason, refund_time, operator_id FK, biz_type)",
        "id", "order_id → orders；ticket_id → ticket；operator_id → user"],
       ["reschedule(*id, old_ticket_id FK, new_ticket_id FK, old_schedule_id, new_schedule_id, price_diff, reschedule_time)",
        "id", "old_ticket_id / new_ticket_id → ticket"],
       ["notification(*id, user_id FK, type, title, content, is_read, create_time)", "id", "user_id → user"]],
      widths=[8.2, 1.4, 4.4])
    P("转换中处理了三个细节：", indent=True)
    P("（1）orders 与 ticket 是 1:N，ticket 侧保留 order_id；ticket 同时冗余 schedule_id，"
      "是为了按班次直接统计售票量，不必每次都绕回订单表做关联。冗余字段的代价是需要保证它与订单的班次一致，"
      "本项目在下单事务内一次性写入，之后不再修改，因此不存在更新异常。", indent=True)
    P("（2）reschedule 与 ticket 之间有两条联系（原票、新票），因此保留 old_ticket_id 与 new_ticket_id 两个外键，不能合并成一个。", indent=True)
    P("（3）schedule_seat 是「班次 × 座位」的实例表，唯一键 (schedule_id, seat_no) 保证同一班次同一座位只有一行，"
      "这是「一座一票」的最后一道数据库防线——即使应用层判断失效，重复插入也会被唯一索引拒绝。", indent=True)

    H("3.3 数据表与约束", 2)
    P("11 张表的键、外键与关键约束如下表。约束不只是「规范」，每一条都对应一类具体错误数据的拦截。", indent=True)
    T(["表名", "主键", "外键", "关键约束与索引"],
      [["user", "id", "—", "uk_username、uk_phone 唯一；chk_user_role 限定三种角色；chk_user_status 限定 0/1；idx_role"],
       ["route", "id", "—", "chk_route_duration 要求时长 > 0；chk_route_deleted 限定 0/1；app 层按「出发港+到达港」查重"],
       ["ship", "id", "—", "uk_ship_name 唯一；chk_ship_type 限定三种船型；chk_ship_seats 要求座位数 > 0"],
       ["ship_seat", "id", "ship_id → ship", "uk_ship_seat(ship_id, seat_no) 唯一；ON DELETE CASCADE；chk_ship_seat_row > 0"],
       ["schedule", "id", "route_id、ship_id", "chk_schedule_status 限定五种状态；chk_schedule_time 要求到达晚于发船；chk_schedule_price ≥ 0；idx_depart_time、idx_status"],
       ["schedule_seat", "id", "schedule_id、lock_user_id", "uk_schedule_seat(schedule_id, seat_no) 唯一；chk 限定 AVAILABLE/LOCKED/SOLD；idx_lock_user 供超时释放扫描"],
       ["orders", "id", "user_id、seller_id、schedule_id", "uk_order_no 唯一；chk_orders_status 限定六种状态；chk_orders_channel 限定 ONLINE/OFFLINE；chk_orders_amount ≥ 0；idx_pay 相关索引"],
       ["ticket", "id", "order_id、schedule_id、checker_id", "uk_ticket_no 唯一；chk_ticket_status 限定六种状态（含 RESCHEDULED）；idx_schedule_status 供班次统计"],
       ["refund", "id", "order_id、ticket_id、operator_id", "chk_refund_biz_type 限定 REFUND/RESCHEDULE_DIFF；chk 要求退款额 ≥ 0；idx_type_time(biz_type, refund_time) 供退票统计"],
       ["reschedule", "id", "old_ticket_id、new_ticket_id", "chk_reschedule_diff 允许负差价（降价退差）；idx_time 供按时间检索"],
       ["notification", "id", "user_id", "chk_notification_read 限定 0/1；idx_user_read(user_id, is_read) 供未读数查询"]],
      widths=[2.8, 1.2, 4.0, 6.4])

    H("3.4 数据库事务处理", 2)
    P("系统共 5 个跨表写事务，边界一律划在 Service 层方法上，任一环节抛异常整体回滚。", indent=True)
    T(["事务", "涉及表", "一致性要点"],
      [["下单（lockAndCreate）", "schedule_seat、orders、ticket、schedule",
        "先按座位逐个条件更新为 LOCKED，全部成功才建订单与票；任一失败即回滚，不留下「锁了一半」的座位"],
       ["支付（pay）", "orders、ticket、schedule_seat、schedule",
        "条件更新订单 UNPAID→PAID、票 UNPAID→PAID、座位 LOCKED→SOLD，并给 sold_count 加 1；三处任一失败则整体回滚"],
       ["退票（refund）", "ticket、refund、schedule_seat、orders",
        "票置 REFUNDED、写 refund（biz_type=REFUND）、座位释放为 AVAILABLE、订单状态重算；四步同一事务"],
       ["改签（reschedule）", "schedule_seat、ticket、refund、orders",
        "先锁新座，再旧票置 RESCHEDULED、插入新票、差价写 refund（RESCHEDULE_DIFF），最后重算两张订单的状态"],
       ["取消班次（cancelSchedule）", "schedule、orders、ticket、refund、schedule_seat、notification",
        "班次置 CANCELLED；逐单退票退款、释放座位、向乘客批量写通知；全部在一个事务内完成，避免「通知发了钱没退」"]],
      widths=[3.2, 5.0, 6.2])

    P("并发控制手段分三层，逐层收窄，见下表。", indent=True)
    T(["层次", "手段", "拦截的问题"],
      [["数据库约束", "schedule_seat 唯一键、ticket 唯一键、CHECK 约束", "即使应用层全部失效，也不会写入重复座位或非法状态"],
       ["SQL 层", "带条件的 UPDATE、SELECT … FOR UPDATE、更新影响行数判定", "并发抢同一座位时只有一行受影响，后到者得到 0 行"],
       ["应用层", "业务规则校验（一人一班次一票、座位归属、票状态机）+ 定时任务兜底", "语义级冲突；超时未支付与超时锁座由定时任务清理"]],
      widths=[2.4, 6.6, 5.4])
    P("关于隔离级别：系统沿用 MySQL 默认的 REPEATABLE READ。需要读到最新状态的场景不使用快照读，"
      "而是显式加锁读（SELECT … FOR UPDATE）或直接用带条件的 UPDATE；因此不必提升到 SERIALIZABLE，"
      "也就避免了随之而来的大量锁等待与死锁风险。", indent=True)

    H("3.5 统计部分的 SQL 实现", 2)
    P("统计口径先定死，再写 SQL，避免同一个人不同时间算出不同结果。三条口径是："
      "售票按订单支付时间 pay_time 归集、只计 PAID 与 CHECKED 的票；退票按退款时间 refund_time 归集、只计 biz_type='REFUND'；"
      "上座率按有效票数除以船舶总座位重算，不读 sold_count，避免计数漂移影响报表。", indent=True)

    P("（1）按日统计售票与退票", bold=True, space_before=6)
    P("售票与退票分属两张表、两个时间字段，先用 UNION ALL 拉齐成 (日期, 类型, 笔数, 金额) 四列，再一次分组求和，"
      "避免两次查询在应用层拼接导致某些日期缺行。", indent=True)
    CODE([
        "SELECT d.stat_date,",
        "       SUM(CASE WHEN d.kind='SALE'   THEN d.cnt ELSE 0 END) AS sale_count,",
        "       SUM(CASE WHEN d.kind='SALE'   THEN d.amt ELSE 0 END) AS sale_amount,",
        "       SUM(CASE WHEN d.kind='REFUND' THEN d.cnt ELSE 0 END) AS refund_count,",
        "       SUM(CASE WHEN d.kind='REFUND' THEN d.amt ELSE 0 END) AS refund_amount",
        "FROM (",
        "    SELECT DATE(o.pay_time) AS stat_date, 'SALE' AS kind,",
        "           COUNT(*) AS cnt, SUM(t.price) AS amt",
        "    FROM ticket t JOIN orders o ON t.order_id = o.id",
        "    WHERE t.status IN ('PAID','CHECKED')",
        "      AND o.pay_time >= #{start}",
        "      AND o.pay_time <  DATE_ADD(#{end}, INTERVAL 1 DAY)",
        "    GROUP BY DATE(o.pay_time)",
        "    UNION ALL",
        "    SELECT DATE(rf.refund_time), 'REFUND', COUNT(*), SUM(rf.refund_amount)",
        "    FROM refund rf",
        "    WHERE rf.refund_time >= #{start}",
        "      AND rf.refund_time <  DATE_ADD(#{end}, INTERVAL 1 DAY)",
        "      AND rf.biz_type = 'REFUND'          -- 只算真退票，排除改签差价",
        "    GROUP BY DATE(rf.refund_time)",
        ") d",
        "GROUP BY d.stat_date ORDER BY d.stat_date",
    ])

    P("（2）班次售票与退票统计", bold=True, space_before=6)
    P("用条件聚合在一条 SQL 内同时算出售票数、退票数与收入，避免三次扫表；"
      "票表用 LEFT JOIN 且限定状态，保证「零售票」的班次也能出现（若需隐藏则由 HAVING 过滤）。", indent=True)
    CODE([
        "SELECT s.id AS schedule_id, r.route_name, s.depart_time,",
        "       SUM(CASE WHEN t.status IN ('PAID','CHECKED') THEN 1 ELSE 0 END) AS sale_count,",
        "       SUM(CASE WHEN t.status = 'REFUNDED' THEN 1 ELSE 0 END) AS refund_count,",
        "       COALESCE(SUM(CASE WHEN t.status IN ('PAID','CHECKED')",
        "                        THEN t.price ELSE 0 END), 0)                  AS income",
        "FROM schedule s",
        "JOIN route r ON s.route_id = r.id",
        "LEFT JOIN ticket t ON t.schedule_id = s.id",
        "                  AND t.status IN ('PAID','CHECKED','REFUNDED')",
        "WHERE s.deleted = 0 AND s.status <> 'CANCELLED'",
        "  AND s.depart_time >= #{start}",
        "  AND s.depart_time <  DATE_ADD(#{end}, INTERVAL 1 DAY)",
        "GROUP BY s.id, r.route_name, s.depart_time",
        "HAVING sale_count > 0 OR refund_count > 0",
        "ORDER BY s.depart_time",
    ])

    P("（3）上座率", bold=True, space_before=6)
    P("上座率的分子必须与分母同源：分母取 ship.total_seats（船舶物理座位数），分子取该班次有效票数，"
      "两者相除后保留两位小数。若改用 schedule.sold_count 作分子，一旦某次退票漏减，报表会长期偏移且无从发现。", indent=True)
    CODE([
        "SELECT s.id AS schedule_id, r.route_name, s.depart_time,",
        "       sh.ship_name, sh.total_seats,",
        "       COUNT(t.id) AS sold_count,",
        "       ROUND(COUNT(t.id) / sh.total_seats * 100, 2) AS occupancy",
        "FROM schedule s",
        "JOIN route r  ON s.route_id = r.id",
        "JOIN ship  sh ON s.ship_id  = sh.id",
        "LEFT JOIN ticket t ON t.schedule_id = s.id",
        "                  AND t.status IN ('PAID','CHECKED')",
        "WHERE s.deleted = 0 AND s.status <> 'CANCELLED'",
        "GROUP BY s.id, r.route_name, s.depart_time, sh.ship_name, sh.total_seats",
        "ORDER BY occupancy DESC",
    ])

    P("（4）收入汇总与退票率", bold=True, space_before=6)
    P("售票与退票分别聚合成两个派生表后交叉连接，一次算出净收入与退票率。"
      "退票率的分母取「售票笔数 + 退票笔数」——这一口径在报告中固定写明，避免出现「退票数 ÷ 售票数」导致超过 100% 的另一种算法。", indent=True)
    CODE([
        "SELECT s.total_income, s.sale_count,",
        "       r.refund_loss, r.refund_count, r.refund_fee,",
        "       (s.total_income - r.refund_loss) AS net_income,",
        "       CASE WHEN s.sale_count + r.refund_count = 0 THEN 0",
        "            ELSE ROUND(r.refund_count / (s.sale_count + r.refund_count) * 100, 2)",
        "       END AS refund_rate",
        "FROM (",
        "    SELECT COALESCE(SUM(t.price), 0) AS total_income, COUNT(*) AS sale_count",
        "    FROM ticket t JOIN orders o ON t.order_id = o.id",
        "    WHERE t.status IN ('PAID','CHECKED')",
        "      AND o.pay_time >= #{start}",
        "      AND o.pay_time <  DATE_ADD(#{end}, INTERVAL 1 DAY)",
        ") s,",
        "(   SELECT COALESCE(SUM(refund_amount), 0) AS refund_loss,",
        "           COUNT(*) AS refund_count, COALESCE(SUM(fee), 0) AS refund_fee",
        "    FROM refund",
        "    WHERE refund_time >= #{start}",
        "      AND refund_time <  DATE_ADD(#{end}, INTERVAL 1 DAY)",
        "      AND biz_type = 'REFUND'",
        ") r",
    ])


# ============================================================
# 4 详细设计
# ============================================================
def fill_sec4():
    H("4.1 类设计", 2)
    P("以售票核心链路为例，类图如图 4 所示。Controller 只做参数装配与返回，"
      "业务规则集中在 OrderServiceImpl，DAO 全部为接口、由 XML Mapper 提供实现。", indent=True)
    IMG(FIG_DIR + "fig4_class.png", 14.0, "图 4  售票核心链路类图")
    T(["类", "职责", "关键方法"],
      [["OrderController", "接收下单、支付、退票、改签、检票请求；从 Session 取当前用户", "createOrder、pay、refund、reschedule、checkin"],
       ["OrderService（接口）", "定义售票业务的对外契约，隔离实现", "lockSeats、createOrder、pay、cancelOrder、refund、reschedule、checkIn"],
       ["OrderServiceImpl", "全部业务规则与事务边界；状态机流转、座位归属校验、订单状态重算", "recalcOrderStatus、seatLockFailureReason、genNo"],
       ["ScheduleSeatDao", "班次座位状态的条件更新与加锁读", "lock、markSold、releaseForOrder、findByIdForUpdate"],
       ["ScheduleDao", "班次已售数增减与加锁读", "incrementSold、decrementSold、findByIdForUpdate"],
       ["TicketDao", "票的写入与状态条件更新", "insert、updateStatusIf、listByOrder"],
       ["RefundDao", "退票与改签差价记录", "insert、listByOrder"],
       ["OrderDao", "订单写入、状态条件更新、超时未付查询", "insert、updateStatus、cancelIfUnpaid、listExpiredUnpaid"]],
      widths=[3.2, 7.2, 4.0])

    H("4.2 包设计", 2)
    P("系统包结构如图 5 所示。左侧四层为纵向调用链，右侧为横切关注点；"
      "箭头一律由使用者指向被依赖者，exception 包由 Spring 回调、没有入边。", indent=True)
    IMG(FIG_DIR + "fig5_pkg.png", 14.0, "图 5  系统包图")
    P("包之间的约束：controller 不得直接引用 dao；entity 不得引用 service；"
      "common 为最底层，只能被引用、不得反向引用任何业务包。这三点保证了依赖方向单一，"
      "修改 SQL 不会波及控制层，替换视图也不会波及业务层。", indent=True)

    H("4.3 核心业务流程", 2)
    P("在线购票主流程如图 6 所示，分四段：查询、锁定、下单、支付。", indent=True)
    IMG(FIG_DIR + "fig6_flow.png", 14.0, "图 6  在线购票主流程图")
    P("（1）查询段：按出发港、到达港与日期查班次，返回余票（总座位数减有效票数），不读 sold_count。", indent=True)
    P("（2）锁定段：逐座执行条件更新；任一失败则回查该座位当前状态，区分「座位不存在」「已售」「已被他人锁定」三种原因给出不同提示，"
      "并回滚已锁定的座位。锁定保留 5 分钟，超时由定时任务释放。", indent=True)
    P("（3）下单段：校验一人一班次只能有一张有效票、座位归属与锁定人一致，通过后写入订单与票，票初始状态 UNPAID。", indent=True)
    P("（4）支付段：条件更新订单与票为 PAID、座位为 SOLD，班次已售数加 1；超过 30 分钟未支付由定时任务转 CANCELLED 并释放座位。", indent=True)

    H("4.4 并发控制设计", 2)
    P("抢座是整个系统唯一真正存在竞争的操作，其控制流程如图 7 所示。", indent=True)
    IMG(FIG_DIR + "fig7_lock.png", 14.0, "图 7  并发抢座控制流程")
    P("核心是一句带条件的 UPDATE。它同时完成三件事：判断座位是否可售、加行锁、改状态；"
      "三者在一个原子操作内完成，因此不存在「判断通过但改之前被别人抢先」的时间窗。", indent=True)
    P("实测结果（20 线程同时抢同一座位，ConcurrencyTest 真实落库、不加事务回滚）：成功 1 单、业务拒绝 19 单、非业务异常 0、死锁 0。"
      "同身份证并发下单 10 线程成功 1 单，并发支付 10 线程仅 1 次生效且 sold_count 只加 1。", indent=True)
    T(["场景", "并发度", "预期", "实测"],
      [["抢同一座位", "20 线程", "仅 1 单成功，其余给出明确失败原因", "成功 1 / 拒绝 19 / 异常 0"],
       ["同一身份证下单", "10 线程", "仅 1 单成功", "成功 1 / 拒绝 9"],
       ["并发支付同一订单", "10 线程", "仅 1 次生效，已售数只加 1", "支付成功 1 / 拒绝 9"],
       ["取消班次 vs 支付", "条件更新互斥", "不会出现「已支付却被取消」", "cancelIfUnpaid 影响行数为 0 即跳过"]],
      widths=[3.6, 2.6, 4.4, 3.8])

    H("4.5 接口清单", 2)
    P("后端接口统一以 /api 开头，返回 Result{code, msg, data}；权限由 @RequireRole 声明，未标注的接口仅要求登录。", indent=True)
    T(["方法", "路径", "权限", "说明"],
      [["POST", "/api/seats/lock", "登录", "锁定座位，返回逐座结果"],
       ["POST", "/api/seats/unlock", "登录", "主动释放本人锁定的座位"],
       ["POST", "/api/orders", "登录", "创建订单（在线/窗口共用，按 channel 区分）"],
       ["POST", "/api/orders/{id}/pay", "登录", "支付订单"],
       ["POST", "/api/orders/{id}/cancel", "登录", "取消未支付订单"],
       ["POST", "/api/orders/{id}/refund", "登录", "退票"],
       ["POST", "/api/tickets/{id}/reschedule", "登录", "改签"],
       ["POST", "/api/checkin", "ADMIN, SELLER", "检票"],
       ["GET", "/api/orders/my", "PASSENGER", "我的订单"],
       ["GET", "/api/orders", "ADMIN, SELLER", "按条件查询订单"],
       ["GET", "/api/schedules/{id}/seat-map", "登录", "座位图（含锁定人与本人标记）"],
       ["POST", "/api/routes", "ADMIN", "新增航线（含唯一性校验）"],
       ["POST", "/api/schedules/{id}/cancel", "ADMIN", "取消班次并批量退票"],
       ["GET", "/api/stats/*", "ADMIN", "五类统计查询"],
       ["GET", "/api/export/{sales|route|seller|occupancy}", "ADMIN", "四类 Excel 导出"],
       ["GET", "/api/notifications", "登录", "通知列表与未读数"]],
      widths=[1.4, 6.2, 2.6, 4.6])


# ============================================================
# 6 实现效果
# ============================================================
def fill_sec6():
    P("以下截图取自实际运行的系统（ferry_db 演示库），按「登录 → 查询 → 选座 → 下单 → 售票 → 检票 → 管理 → 统计」的业务顺序排列，"
      "每张图下说明该页面验证了哪条需求。", indent=True)

    H("6.1 登录页", 2)
    P("未登录访问任何受保护页面都会被 LoginInterceptor 拦截并跳转到此页；登录成功后按角色进入对应首页（乘客进班次查询、"
      "售票员进线下售票、管理员进用户管理）。密码在库中以 BCrypt 哈希存储，登录时比对哈希而非明文。", indent=True)
    IMG(SHOT_DIR + "01_login.png", 14.0, "图 6-1  登录页")

    H("6.2 班次查询与余票", 2)
    P("按出发港、到达港与日期检索班次，列表给出航线、船舶、发船与到达时间、票价与余票。"
      "余票由「船舶总座位数 − 该班次有效票数」实时计算，不读冗余的 sold_count，因此退票后余票会立即回升。", indent=True)
    IMG(SHOT_DIR + "02_search.png", 14.0, "图 6-2  班次查询（乘客端）")

    H("6.3 选座与座位锁定", 2)
    P("点击「选座购票」弹出座位图，四种状态用颜色区分并在图例中标明：白色可选、蓝色为本人已选、黄色为他人锁定、灰色为已售。"
      "本人锁定的座位可以点击取消，他人锁定的座位不可点击——这一点直接对应 4.4 节的条件更新：只有锁定人是自己时才允许再次操作。", indent=True)
    IMG(SHOT_DIR + "04_seat.png", 14.0, "图 6-3  选座弹窗（4A 本人已选、5A 他人锁定、2A/3A 已售）")
    P("图中 4A 已被当前乘客锁定并计入总价 ¥50，5A 被另一位乘客锁定而呈黄色不可选，2A、3A 已有订单故为灰色。", indent=True)

    H("6.4 我的订单", 2)
    P("乘客只能看到自己的订单，状态由票推导得出（已支付、已退票等）。列表按订单号、航线、发船时间、金额、状态与下单时间展示，"
      "并提供退票、改签、详情三个操作——按钮的可用性由票状态决定，例如已退票的订单不再显示退票与改签。", indent=True)
    IMG(SHOT_DIR + "03_orders.png", 14.0, "图 6-4  我的订单")

    H("6.5 窗口售票", 2)
    P("售票员登录后进入线下售票页，代客购票需填写乘客姓名、身份证号与手机号，并在同一座位图上选座。"
      "与在线购票的差别只在下单渠道（channel=OFFLINE）与操作人（seller_id），座位锁定、订单与票的写入走的是同一套 Service 方法。", indent=True)
    IMG(SHOT_DIR + "05_sell.png", 14.0, "图 6-5  窗口售票（代客购票）")

    H("6.6 检票", 2)
    P("检票可按票号或订单号检索，也可先选班次再统计。图中的票表同时出现「已退票」「已检票」「已改签」「待检票」四种状态，"
      "其中「已改签」正是 2.4 节新增的 RESCHEDULED——旧票保留痕迹但不再有效，用它检票会被明确拒绝。", indent=True)
    IMG(SHOT_DIR + "06_checkin.png", 14.0, "图 6-6  检票与班次检票统计")

    H("6.7 班次管理", 2)
    P("管理员可按航线、船舶、日期与状态筛选班次，并对单个班次执行详情、编辑、取消、删除，或批量生成连续班次。"
      "「取消」会触发 3.4 节描述的六表事务：班次置 CANCELLED、逐单退票退款、释放座位、批量写通知。", indent=True)
    IMG(SHOT_DIR + "08_schedules.png", 14.0, "图 6-7  班次管理")

    H("6.8 用户管理", 2)
    P("用户管理支持按用户名、角色、姓名检索，以及编辑资料、重置密码、禁用账户。三类角色同表存储、由 role 字段区分，"
      "禁用后该用户立即无法登录（登录时校验 status），但历史订单与票仍然保留，避免破坏外键完整性。", indent=True)
    IMG(SHOT_DIR + "09_users.png", 14.0, "图 6-8  用户管理")

    H("6.9 统计报表与导出", 2)
    P("统计页按日期区间展示七项指标：售票量 7 张、总收入 ¥410.00、退票量 3 张、退票金额 ¥180.00、手续费 ¥0.00、净收入 ¥230.00、退票率 30%，"
      "下方依次是周期收入统计、售票员业绩排名、航线售票统计、班次售票统计与班次上座率。"
      "四类报表均可导出为 .xlsx，中文表头由 EasyExcel 注解声明。", indent=True)
    IMG(SHOT_DIR + "07_stats.png", 14.0, "图 6-9  统计报表（含四类 Excel 导出入口）")
    P("图中退票量为 3 张而非 4 张，正是 5.6 节缺陷 4 修复后的结果：改签产生的差价退款记作 RESCHEDULE_DIFF，不计入退票量与退票率。", indent=True)


# ============================================================
# 7 总结
# ============================================================
def fill_sec7():
    H("7.1 完成情况", 2)
    P("任务书要求的五个功能模块全部实现并通过测试：用户与权限、航线船舶班次座位、售票与订单（下单、支付、退票、改签、检票）、"
      "统计报表、通知。数据库侧的考核点也逐项落地：11 张表的完整性约束（外键、CHECK、唯一索引）、完整的 CRUD、"
      "五个跨表事务、五类聚合统计、以及基于拦截器的权限隔离。加分项「报表导出 Excel」实现四类报表，使用 EasyExcel 流式写出。", indent=True)
    P("测试方面共 58 个用例全部通过，其中 5 个为并发用例，真实落库、不加事务回滚，用于证明「一座一票」在竞争下成立。"
      "测试过程中发现并修复 4 个真实缺陷，其中「单号碰撞」影响生产可用性、「改签污染退票统计」影响管理决策，均属于不看数据发现不了的问题。", indent=True)

    H("7.2 主要收获", 2)
    P("（1）约束比校验可靠。最初把「一座一票」完全交给 Service 层的 if 判断，并发测试立刻暴露了时间窗问题。"
      "改为「唯一索引 + 条件更新」之后，正确性不再依赖调用方是否记得判断——即使将来新增一个下单入口忘了校验，数据库仍然拦得住。", indent=True)
    P("（2）事务边界要划在业务动作上，而不是数据库操作上。下单、支付、退票、改签、取消班次这五个动作各自是一个事务，"
      "而不是「一个 DAO 方法一个事务」。这条界线画错，就会出现「座位锁了但订单没建」「票退了但座位没释放」这类中间状态。", indent=True)
    P("（3）统计口径必须先写清楚再写 SQL。改签算不算退票，在代码里表现为一个 biz_type 字段，在管理上却决定退票率是高是低。"
      "把口径写进注释，比事后解释便宜得多。", indent=True)
    P("（4）测试要按业务状态切分，而不是把断言堆在一个方法里。MyBatis 一级缓存导致的「改了时间却不报超时」就是典型的坑："
      "同一事务内二次查询返回缓存对象，断言自然失败。拆成独立用例后问题消失，也顺带说明了为什么集成测试要理解框架的缓存边界。", indent=True)

    H("7.3 不足与改进方向", 2)
    P("（1）单号生成只保证单机有序。genNo 用进程内 AtomicInteger 取模，多实例部署会重复，唯一索引能兜底重试但会产生额外失败。"
      "改进方向是换数据库号段或雪花算法。", indent=True)
    P("（2）未做吞吐压测。同班次下单被 FOR UPDATE 与条件更新串行化，是为正确性做的取舍；"
      "真实高峰期的并发量尚未测量，无法给出容量结论。", indent=True)
    P("（3）统计查询未加缓存。区间较大时每次都要扫票表与退款表，宜按日预聚合到统计表或物化视图。", indent=True)
    P("（4）前端未做组件化。座位图、订单表格逻辑在多页面重复，宜抽成公共组件复用。", indent=True)


# ============================================================
# 按章节顺序填充正文（第 1-4 部分）
# ============================================================
goto("系统需求分析"); fill_sec1()
goto("概要设计");     fill_sec2()
goto("数据库设计");   fill_sec3()
goto("详细设计");     fill_sec4()
cur = anchor          # 回到「系统测试」标题，衔接下面原有的第 5 部分代码

# ============================================================
# 5.1 测试环境与测试方法
# ============================================================
H("5.1 测试环境与测试方法", 2)

P("测试环境如下表。测试库 ferry_test 与演示库 ferry_db 隔离，表结构与约束完全一致。",
  indent=True)

T(["项目", "配置"],
  [["操作系统", "Windows 10/11 (win32)"],
   ["JDK", "OpenJDK 17（Spring Boot 3.2.5 要求）"],
   ["数据库", "MySQL 8.0.44，InnoDB，隔离级别 REPEATABLE READ"],
   ["测试框架", "JUnit 5 + Spring Boot Test + MockMvc"],
   ["数据库工具", "DataGrip"],
   ["测试库", "ferry_test（结构与 ferry_db 一致）"]],
  widths=[4.0, 11.0])

P("测试方法说明：", bold=True, space_before=4)
P("（1）采用集成测试而非单元测试。全部用例连接真实 MySQL，不使用 H2 等内存数据库。"
  "原因是本项目考核重点是外键约束、CHECK 约束、行级锁、SELECT … FOR UPDATE 与事务回滚，"
  "这些在内存库中语义不同，测不出真实问题。", indent=True)
P("（2）事务隔离。单线程业务用例继承 BaseIntegrationTest 并加 @Transactional，"
  "执行后自动回滚，用例之间互不污染。", indent=True)
P("（3）并发用例独立处理。并发测试不能包在单个事务内（否则线程看不到彼此的提交），"
  "因此单独实现为 ConcurrencyTest，用 JdbcTemplate 真实落库，测试后保留数据作为报告证据。", indent=True)
P("（4）测试数据合法性。所有订单均使用库中真实存在的用户，"
  "因为 orders.user_id 有外键约束，避免出现“测试通过但数据非法”的假阳性。", indent=True)

T(["测试类", "用例数", "覆盖范围"],
  [["UserServiceTest", "9", "注册、登录、密码加密、锁定、禁用、改密"],
   ["RouteShipScheduleTest", "12", "航线、船舶、座位、班次、状态流转"],
   ["OrderServiceTest", "17", "下单、支付、取消、退票、改签、检票、单号唯一性"],
   ["StatsServiceTest", "8", "聚合统计五类指标 + 改签对退票口径的隔离"],
   ["PermissionTest", "7", "登录拦截、角色越权拦截"],
   ["ConcurrencyTest", "5", "并发抢座、并发一人一票、并发支付、锁超时、取消班次退票"],
   ["合计", "58", "覆盖任务书全部功能模块与数据库考核要点"]],
  widths=[4.6, 1.8, 8.6])

# ============================================================
# 5.2 测试结果汇总
# ============================================================
H("5.2 测试结果汇总", 2)
P("执行全量测试，控制台输出：", indent=True)
P("Tests run: 58, Failures: 0, Errors: 0, Skipped: 0", mono=True, indent=True)
P("BUILD SUCCESS", mono=True, indent=True)

T(["模块", "用例数", "通过", "失败"],
  [["模块一 用户与权限", "9", "9", "0"],
   ["模块二 基础数据", "12", "12", "0"],
   ["模块三 售票业务", "17", "17", "0"],
   ["模块四 统计报表", "8", "8", "0"],
   ["权限隔离", "7", "7", "0"],
   ["事务与并发", "5", "5", "0"],
   ["合计", "58", "58", "0"]],
  widths=[7.0, 2.4, 2.4, 2.4])
P("说明：通知模块无独立用例，其批量写入逻辑在「取消班次」「支付超时取消」两条用例中一并断言", indent=True)

# ============================================================
# 5.3 测试用例明细
# ============================================================
H("5.3 测试用例明细", 2)
P("下表列出各模块的测试用例、输入数据与实测结果。“结论”列均为修复后最终执行结果。", indent=True)

H("5.3.1 模块一：用户与权限", 3)
T(["编号", "被测功能", "测试数据", "预期结果", "实际结果", "结论"],
  [["TC-U01", "乘客注册", "用户名 test_reg_ok，密码 123456，角色传 ADMIN",
    "密码 BCrypt 密文入库，角色强制 PASSENGER", "密码 $2a$10$…，角色 PASSENGER", "通过"],
   ["TC-U02", "用户名唯一", "重复注册同名用户", "抛「用户名已存在」", "抛出该异常", "通过"],
   ["TC-U03", "手机号格式", "手机号 12345", "抛「手机号格式不正确」", "抛出该异常", "通过"],
   ["TC-U04", "身份证格式", "身份证 123456", "抛「身份证号格式不正确」", "抛出该异常", "通过"],
   ["TC-U05", "登录成功", "test_login_ok / 123456", "返回角色，失败次数清零", "角色 PASSENGER，login_fail=0", "通过"],
   ["TC-U06", "登录锁定", "连续 5 次错误密码", "第 5 次锁定 10 分钟，锁定期内正确密码也拒绝",
    "lock_until 已写入且晚于当前时间，正确密码返回「账号已锁定」", "通过"],
   ["TC-U07", "禁用账号", "禁用后登录", "抛「账号已被禁用」", "抛出该异常", "通过"],
   ["TC-U08", "修改密码", "先错误原密码，再正确原密码", "错误拒绝；正确后可登录",
    "分别返回「原密码错误」与登录成功", "通过"],
   ["TC-U09", "管理员建号", "角色传 PASSENGER", "拒绝创建", "抛「仅可创建售票员或管理员账号」", "通过"]],
  widths=[1.95, 2.1, 3.4, 3.3, 3.3, 1.2])

H("5.3.2 模块二：基础数据", 3)
T(["编号", "被测功能", "测试数据", "预期结果", "实际结果", "结论"],
  [["TC-R01", "新增航线", "时长 60 分钟；另建时长 0 的航线", "正常入库；时长 0 被拒",
    "入库成功；抛「航行时长必须大于0」", "通过"],
   ["TC-R02", "航线唯一性", "同「出发港+到达港+航线名」；同港口不同名", "三元组重复拒绝；同港口不同名允许",
    "前者抛「已存在相同出发港、到达港和航线名称的航线」，后者成功", "通过"],
   ["TC-R03", "航线删除", "有 SELLING 班次；另一条无班次", "前者拒绝；后者逻辑删除且查询不到",
    "前者抛「有未完成班次」，后者 deleted=1", "通过"],
   ["TC-S01", "船舶座位生成", "新建 10 座船", "生成 10 座位，1A…3B，第 3 排 2 个",
    "10 条记录，编号与排数符合", "通过"],
   ["TC-S02", "船舶删除", "船有 SELLING 班次", "拒绝删除", "抛「有未完成班次」", "通过"],
   ["TC-SC01", "班次到达时间", "发船 09:00，航线 60 分钟", "到达 10:00，状态 PENDING",
    "到达 10:00，PENDING，已售 0", "通过"],
   ["TC-SC02", "船舶时间冲突", "已有 9:00-10:00，再建 9:30 与 10:00", "9:30 拒绝；10:00 允许",
    "9:30 抛「时间冲突」，10:00 成功", "通过"],
   ["TC-SC03", "班次座位初始化", "12 座船建班次", "生成 12 条，全部 AVAILABLE", "12 条，全部 AVAILABLE", "通过"],
   ["TC-SC04", "批量生成班次", "04-01 至 04-05 每天 10:00，先在 04-03 造冲突", "生成 4 条，跳过 04-03",
    "生成 4 条，无 04-03", "通过"],
   ["TC-SC05", "班次状态流转", "发布→改发船时间为过去→改到达时间为过去",
    "PENDING→SELLING→DEPARTED→FINISHED", "四次断言均符合", "通过"],
   ["TC-SC06", "已发船不可改", "正常改；改库为 DEPARTED 后再改", "前者成功；后者拒绝",
    "前者成功；后者抛「已发船，不允许修改」", "通过"],
   ["TC-SC07", "班次删除校验", "班次有 UNPAID 订单", "拒绝删除", "抛「有未完成订单」", "通过"]],
  widths=[1.95, 2.1, 3.4, 3.3, 3.3, 1.2])

H("5.3.3 模块三：售票业务", 3)
T(["编号", "被测功能", "测试数据", "预期结果", "实际结果", "结论"],
  [["TC-O01", "正常下单", "票价 50，买 1A、1B", "订单 UNPAID，总价 100，座位 LOCKED",
    "全部符合", "通过"],
   ["TC-O02", "一人一班次一票", "同身份证二次下单", "拒绝", "抛「在该班次已购票」", "通过"],
   ["TC-O03", "下单参数校验", "6 张票／座位重复／身份证 123／手机 999／座位被占",
    "五种情况分别拒绝", "分别提示「最多购买5张」「座位号重复」「身份证号格式不正确」「手机号格式不正确」「已被他人锁定」", "通过"],
   ["TC-O04", "支付成功", "支付 50 元订单", "订单 PAID、座位 SOLD、sold_count=1", "全部符合", "通过"],
   ["TC-O05", "非本人支付", "他人订单", "拒绝", "抛「无权操作该订单」", "通过"],
   ["TC-O06", "支付超时", "下单时间改为 10 分钟前", "拒绝", "抛「支付超时」", "通过"],
   ["TC-O07", "重复支付", "已支付订单再支付", "拒绝", "抛「订单状态异常」", "通过"],
   ["TC-O08", "取消订单", "待支付订单取消", "座位回 AVAILABLE，订单/票 CANCELLED", "全部符合", "通过"],
   ["TC-O09", "退票全额", "票价 100，5 小时后发船", "手续费 0，退款 100，座位释放，已售回退", "全部符合", "通过"],
   ["TC-O10", "退票扣费", "票价 100，1 小时后发船", "手续费 20，退款 80", "手续费 20.00，退款 80.00", "通过"],
   ["TC-O11", "退票拒绝", "待支付／已检票／非本人／已发船", "四种均拒绝",
    "分别提示「未支付」「含已检票船票」「无权」「已发船」", "通过"],
   ["TC-O12", "改签成功", "原票 100 元改至 130 元班次，座位 2B",
    "原票 REFUNDED、原座位释放、新票 PAID、差价 +30、生成日志", "全部符合，差价 30.00", "通过"],
   ["TC-O13", "改签拒绝", "30 分钟内发船／同班次／座位被占／未支付", "四种均拒绝",
    "分别提示「1小时内不可改签」「不能与原班次相同」「已被他人锁定」「仅已支付」", "通过"],
   ["TC-O14", "检票成功", "已支付票号", "票 CHECKED，记录检票时间与检票员，订单联动", "全部符合", "通过"],
   ["TC-O15", "检票拒绝", "未支付／非本班次／重复检票／已退票／超发船 2 小时", "五种均拒绝",
    "分别提示「未支付」「不属于所选班次」「已检票」「已退票」「已过期」", "通过"],
   ["TC-O16", "检票记录统计", "某班次 3 张已支付，2 张已检", "总售票 3、已检票 2、未检票 1，明细含时间/检票员",
    "全部符合", "通过"],
   ["TC-O17", "单号唯一性", "连续下单 40 次", "40 个订单号、40 个船票号互不重复", "集合大小均为 40", "通过"]],
  widths=[1.95, 2.1, 3.4, 3.3, 3.3, 1.2])

H("5.3.4 模块四：统计报表", 3)
T(["编号", "被测功能", "测试数据", "预期结果", "实际结果", "结论"],
  [["TC-ST01", "按航线统计", "2 单已支付 + 1 单支付后退票", "售票量 2、金额 200（退票不计入）", "2 / 200.00", "通过"],
   ["TC-ST02", "收入三口径", "1 单保留 + 1 单退票，各 100 元", "净收入 = 总收入 - 退票损失", "三口径关系成立", "通过"],
   ["TC-ST03", "上座率与预警", "8 座卖 4 张", "上座率 50.00%；等于 50 不进预警", "50.00%，预警不含该班次", "通过"],
   ["TC-ST04", "时间段分组", "全库班次按发船小时分组", "返回早/午/晚班及平均上座率",
    "返回「早班(06-12)」「午班(12-18)」「晚班(18-24)」", "通过"],
   ["TC-ST05", "售票员排名", "全部 SELLER 业绩", "按金额降序", "降序成立", "通过"],
   ["TC-ST06", "退票原因统计", "退票 1 笔 60 元，原因「统计专用原因」", "该原因笔数 1、金额 60", "1 / 60.00", "通过"],
   ["TC-ST07", "改签不入退票量", "100 元班次 1 张票改签至 130 元班次",
    "原班次无售票无退票，整行不出现", "原班次未出现；目标班次 1 / 0", "通过"],
   ["TC-ST08", "改签差价不入退票", "130 元改签至 100 元，产生 30 元差价退款",
    "退票笔数不变、原因分布无此项", "笔数不变，无该项", "通过"]],
  widths=[1.95, 2.1, 3.4, 3.3, 3.3, 1.2])

H("5.3.5 权限隔离", 3)
T(["编号", "被测场景", "请求", "预期结果", "实际结果", "结论"],
  [["TC-P01", "未登录访问页面", "GET /admin/users", "302 跳 /login", "302 → /login", "通过"],
   ["TC-P02", "未登录访问接口", "GET /api/users", "302 跳 /login", "302 → /login", "通过"],
   ["TC-P03", "乘客越权", "乘客会话 GET /api/users", "403，body code=403", "403，code=403", "通过"],
   ["TC-P04", "售票员权限", "售票员查航线 / 查用户", "航线 200，用户 403", "200 / 403", "通过"],
   ["TC-P05", "管理员放行", "管理员 GET /api/users", "200，code=0", "200，code=0", "通过"],
   ["TC-P06", "乘客越权页面", "乘客 GET /admin/users", "302 跳 /", "302 → /", "通过"],
   ["TC-P07", "订单数据隔离", "乘客 GET /api/orders 与 /api/orders/my", "前者 403，后者 200", "403 / 200", "通过"]],
  widths=[1.95, 2.4, 4.0, 3.2, 2.8, 1.2])

# ============================================================
# 5.4 事务与并发专项测试
# ============================================================
H("5.4 事务与并发专项测试（考核重点）", 2)
P("并发测试统一使用 CountDownLatch 让所有线程阻塞在同一时刻后同时发起请求，"
  "以确保竞争真实发生，而不是被线程调度错开。", indent=True)

T(["编号", "场景", "并发设计", "预期"],
  [["TC-C01", "20 人抢同一座位", "20 线程同时下单，座位均为 1A，身份证各不相同", "仅 1 单成功，19 单被拒，无死锁"],
   ["TC-C02", "同一身份证并发购票", "10 线程用同一身份证抢 10 个不同座位", "仅 1 单成功"],
   ["TC-C03", "同一订单并发支付", "10 线程同时调用支付", "仅 1 次成功，sold_count 只加 1"],
   ["TC-C04", "锁超时释放", "A 占座→锁定时间推至 6 分钟前→释放→B 购买同座", "B 下单成功"],
   ["TC-C05", "取消班次自动退票", "3 单已支付 + 1 单未支付，取消班次", "全退、座位全释放、生成退票记录与通知"]],
  widths=[1.6, 3.4, 6.4, 3.8])

P("实测输出（控制台）：", bold=True, space_before=4)
P("[TC-C01] 成功=1 业务拒绝=19 非业务异常=0", mono=True, indent=True)
P("[TC-C02] 成功=1 拒绝=9", mono=True, indent=True)
P("[TC-C03] 支付成功=1 拒绝=9", mono=True, indent=True)

T(["编号", "成功", "被拒", "非业务异常", "数据库最终状态", "结论"],
  [["TC-C01", "1", "19", "0", "座位 1A 为 LOCKED ×1，船票记录 ×1", "通过"],
   ["TC-C02", "1", "9", "0", "该身份证在该班次船票记录 ×1", "通过"],
   ["TC-C03", "1", "9", "0", "座位 SOLD，sold_count=1", "通过"],
   ["TC-C04", "—", "—", "—", "超时后座位 AVAILABLE，他人可购", "通过"],
   ["TC-C05", "—", "—", "—", "班次 CANCELLED，3 单 REFUNDED，8 座位全 AVAILABLE，3 条退款，3 条通知", "通过"]],
  widths=[1.6, 1.2, 1.2, 2.0, 7.4, 1.2])

P("一致性实现手段与设计理由：", bold=True, space_before=4)
T(["并发场景", "实现手段", "为什么这样做"],
  [["抢同一座位",
    "UPDATE schedule_seat SET status='LOCKED' WHERE schedule_id=? AND seat_no=? AND status='AVAILABLE'，判断受影响行数",
    "用 SQL 原子条件更新代替“先查后改”。先查后改两步之间存在时间窗，必然超卖；条件更新由 InnoDB 行锁保证互斥"],
   ["一人一班次一票",
    "下单前 SELECT … FROM schedule WHERE id=? FOR UPDATE 锁班次行，再校验身份证",
    "同一身份证并发下单时，“校验-插入”必须原子。锁班次行把同班次下单串行化，校验才可信。代价是同班次吞吐下降，换取正确性"],
   ["并发支付",
    "UPDATE orders SET status='PAID' WHERE id=? AND status='UNPAID'",
    "条件更新天然幂等，第二次支付影响 0 行直接拒绝，避免重复累加 sold_count"],
   ["座位锁超时",
    "lock_time 字段 + 定时任务 UPDATE … WHERE status='LOCKED' AND lock_time < NOW()-5min",
    "用状态校验而非内存定时器，应用重启不丢锁；批量 UPDATE 一次释放，不必逐条处理"],
   ["取消班次退票",
    "cancel() 整段包在 @Transactional，内部逐单退票",
    "班次状态、订单、座位、退款、通知五张表必须同生共死，任一失败全部回滚"]],
  widths=[2.6, 6.4, 6.2])

# ============================================================
# 5.5 测试数据留存
# ============================================================
H("5.5 测试数据留存", 2)
P("测试执行后 ferry_test 库保留全部测试数据：并发用例真实提交，单线程用例已回滚。"
  "以下为执行完毕后的数据库快照。", indent=True)

T(["表名", "记录数", "说明"],
  [["user", "37", "测试乘客、并发测试用户"],
   ["route", "5", "并发测试航线"],
   ["ship", "5", "并发测试船舶"],
   ["ship_seat", "44", "船舶座位定义"],
   ["schedule", "5", "并发测试班次"],
   ["schedule_seat", "44", "班次座位状态"],
   ["orders", "9", "见 5.5.3"],
   ["ticket", "9", "与订单一一对应"],
   ["refund", "3", "班次取消自动退票"],
   ["reschedule", "0", "改签用例在事务内回滚"],
   ["notification", "3", "班次取消通知"]],
  widths=[3.4, 1.8, 9.8])

T(["座位状态", "数量", "含义"],
  [["AVAILABLE", "40", "可售"],
   ["LOCKED", "3", "已被下单锁定（未支付）"],
   ["SOLD", "1", "已支付售出"]],
  widths=[3.4, 1.8, 9.8])

T(["订单状态", "渠道", "数量", "金额合计"],
  [["PAID", "ONLINE", "1", "100.00"],
   ["UNPAID", "ONLINE", "3", "300.00"],
   ["CANCELLED", "ONLINE", "2", "200.00"],
   ["REFUNDED", "ONLINE", "3", "300.00"]],
  widths=[3.4, 3.0, 2.4, 3.2])

P("并发测试班次的已售数与实际售出座位核对如下，两者完全一致，"
  "说明“座位状态与船票订单数据保持一致”的业务规则得到满足。", indent=True, space_before=4)
T(["班次ID", "总座位", "状态", "sold_count", "实际 SOLD 座位", "对应用例", "核对"],
  [["1", "8", "CANCELLED", "0", "0", "TC-C05 全退", "一致"],
   ["2", "12", "SELLING", "0", "0", "TC-C02 未支付", "一致"],
   ["3", "8", "SELLING", "0", "0", "TC-C01 未支付", "一致"],
   ["4", "8", "SELLING", "1", "1", "TC-C03 已支付", "一致"],
   ["5", "8", "SELLING", "0", "0", "TC-C04 超时释放", "一致"]],
  widths=[1.6, 1.8, 2.6, 2.4, 3.0, 3.4, 1.4])

P("退票与通知记录示例：", bold=True, space_before=4)
P("refund:        refund_amount=100.00, fee=0.00, biz_type='REFUND'",
  mono=True, indent=True, align=WD_ALIGN_PARAGRAPH.LEFT)
P("               reason='班次取消自动退票'",
  mono=True, indent=True, align=WD_ALIGN_PARAGRAPH.LEFT)
P("notification:  type=SCHEDULE_CANCEL, title='班次取消通知'",
  mono=True, indent=True, align=WD_ALIGN_PARAGRAPH.LEFT)
P("               content='您订单 O2026… 已取消，票款 ¥100.00 全额退还'",
  mono=True, indent=True, align=WD_ALIGN_PARAGRAPH.LEFT)

# ============================================================
# 5.6 测试中发现并修复的缺陷
# ============================================================
H("5.6 测试中发现并修复的缺陷", 2)
P("测试与代码复核过程中发现 4 个真实缺陷，均已定位根因并修复，修复后补充了对应回归用例。",
  indent=True)

P("缺陷 1：订单号/船票号生成存在碰撞", bold=True, space_before=4)
T(["项目", "内容"],
  [["现象", "第 4 轮测试报 DuplicateKeyException: Duplicate entry 'O202611241544085046' for key 'orders.uk_order_no'，下单失败"],
   ["根因", "单号格式为「O + 秒级时间戳 + 4 位随机数」。同一秒内随机值仅 9000 种，按生日悖论数十次下单即碰撞；撞上唯一约束即抛异常。这不是偶发，而是熵不足的必然"],
   ["影响", "售票高峰同一秒数十单时，用户会随机遇到“下单失败”，且报错为数据库异常而非业务提示"],
   ["修复", "改为「前缀 + 毫秒时间戳 + 3 位进程内自增序列」。同一毫秒 1000 单以内严格不重复"],
   ["遗留限制", "集群部署时进程内序列不共享，需改用雪花算法或数据库序列（已在代码注释标注）"],
   ["回归用例", "TC-O17：连续 40 次下单，断言 40 个订单号与 40 个船票号互不重复"]],
  widths=[2.6, 12.6])

P("缺陷 2：座位锁定失败的提示不区分原因", bold=True, space_before=4)
T(["项目", "内容"],
  [["现象", "传入不存在的座位号（如 8 座船的 4A）时，提示“座位 4A 已被占用”，与实际原因不符"],
   ["根因", "lock() 返回受影响行数 0 有两种可能：座位在该班次不存在、座位被他人锁定或已售。原实现把两种情况合并成同一句提示"],
   ["影响", "用户会反复重试不存在的座位；运维排查时无法从提示区分是数据问题还是并发问题"],
   ["修复", "新增 seatLockFailureReason()：锁定失败后回查座位，区分「不存在」「已售出」「已被他人锁定」"],
   ["回归用例", "TC-O03、TC-O13 断言同步改为校验具体提示语"]],
  widths=[2.6, 12.6])

P("缺陷 3：航线唯一性校验粒度小于任务书要求", bold=True, space_before=4)
T(["项目", "内容"],
  [["现象", "代码复核发现 countSameRoute() 只比较「出发港 + 到达港」，任务书要求「出发港口、到达港口和航线名称的组合」"],
   ["根因", "实现时按两元组判断唯一性，比要求更严格"],
   ["影响", "同一对港口只能建一条航线，无法并存“市区-海岛快线”与“市区-海岛慢线”，误伤正常业务"],
   ["修复", "DAO 与 Mapper 增加 routeName 参数，改为三元组判断"],
   ["回归用例", "TC-R02：三元组重复被拒，同港口不同航线名允许创建"]],
  widths=[2.6, 12.6])

P("缺陷 4：改签被算成退票，退票量与退票率虚高", bold=True, space_before=4)
T(["项目", "内容"],
  [["现象", "把 1 张票从班次1改签到班次2后，班次1 的「退票量」由 2 变成 3，但实际无人退票；"
           "收入汇总的退票笔数同样多出 1 笔。改签到票价更低的班次时，「改签退还差价」还会出现在退票原因分布里"],
   ["根因", "ticket.status 与 refund 表都被复用承载了两类业务事实。改签的实现是「旧票作废 + 新开一张票」，"
           "旧票被置成 REFUNDED，与真实退票共用同一取值；改签退还的差价也写进 refund 表且无类型字段。"
           "而班次统计按 t.status='REFUNDED' 聚合、收入汇总与退票原因按 refund 全表聚合，"
           "于是改签被无差别计入退票。这是「一个字段承担两个语义」造成的统计污染，不是某条 SQL 写错"],
   ["影响", "退票量、退票率、退票损失、退票原因分布四项指标全部虚高。退票率是管理决策指标，"
           "虚高会误导对航线服务质量的判断"],
   ["修复", "① ticket.status 增加独立取值 RESCHEDULED，改签时旧票置为该状态，不再复用 REFUNDED；"
           "② refund 表增加 biz_type（REFUND / RESCHEDULE_DIFF），差价退款打独立标记；"
           "③ 四处退款聚合统一追加 biz_type='REFUND' 过滤；"
           "④ 提供 04_migration_1_2.sql 增量升级，并从 reschedule.old_ticket_id 回填历史改签票"],
   ["备选方案与否决理由", "只在统计 SQL 里排除 reschedule.old_ticket_id 改动更小，但状态语义仍然重载，"
           "任何新增的按 REFUNDED 聚合都会再踩同一个坑，属于打补丁而非治因，故否决"],
   ["回归用例", "TC-ST07、TC-ST08；同时修正 TC-O12 对原票状态的断言"]],
  widths=[2.9, 12.3])

P("实测对照（ferry_db 班次1：2 张真退票 + 1 张改签作废）：", space_before=4)
T(["指标", "修复前", "修复后", "真实值"],
  [["班次1 退票量", "3", "2", "2"],
   ["收入汇总 退票笔数", "4", "3", "3"],
   ["收入汇总 退票损失", "210.00", "180.00", "180.00"]],
  widths=[5.4, 3.2, 3.2, 3.2])

P("测试设计要点：MyBatis 一级缓存对测试的影响", bold=True, space_before=6)
P("编写支付超时用例时出现过“改了下单时间但支付没报超时”的现象。根因不在业务代码："
  "同一测试事务内，MyBatis 一级缓存（SqlSession 级）会缓存首次 findById 的结果，"
  "改库后再次查询仍返回旧对象；生产环境每次请求是独立 SqlSession，不受影响。", indent=True)
P("处理方式：把一个测试方法里“预期失败的写操作”拆成独立用例（TC-O05/O06/O07），"
  "保证每个用例内订单只被首次读取，避免缓存干扰断言。这也说明测试用例应按“业务状态”切分，"
  "而不是把多条断言堆在一个方法里。", indent=True)

# ============================================================
# 5.7 测试结论
# ============================================================
H("5.7 测试结论", 2)
P("（1）58 个用例全部通过，覆盖任务书五个功能模块与数据库考核要点"
  "（完整性约束、CRUD、事务并发、聚合统计、权限隔离）。", indent=True)
P("（2）并发控制达到预期：20 线程抢同一座位仅 1 单成功、0 次死锁；"
  "同一身份证并发下单仅 1 单成功；并发支付仅 1 次生效且已售数只加 1。", indent=True)
P("（3）事务原子性得到验证：取消班次时订单、座位、退款、通知四类数据一致变更，无残留有效订单。", indent=True)
P("（4）数据一致性得到验证：各测试班次 sold_count 与实际 SOLD 座位数完全一致。", indent=True)
P("（5）测试暴露并修复 4 个真实缺陷：单号碰撞影响生产可用性，改签污染退票统计影响管理决策，"
  "二者都不属于表面问题；另两个为提示不准确与唯一性校验粒度不足。", indent=True)
P("（6）剩余风险：未做并发吞吐压测（FOR UPDATE 串行化同班次下单是有意的正确性取舍）；"
  "集群部署时单号生成需替换方案。", indent=True)


# ============================================================
# 第 6、7 部分，并删除模板末尾的撰写要求
# ============================================================
goto("实现效果"); fill_sec6()
goto("总结");     fill_sec7()
removed = delete_from("（以下内容为撰写要求")
print("撰写要求已删除:", removed)

doc.save(DST)
print("saved:", DST)
