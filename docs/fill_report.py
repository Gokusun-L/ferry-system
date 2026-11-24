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
            p.paragraph_format.line_spacing = Pt(14)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)

    # 禁止单行跨页拆断（否则一行文字会被分成两页）
    for row in tbl.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))

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
   ["模块二 航线/船舶/班次/座位", "12", "12", "0"],
   ["模块三 售票与订单", "17", "17", "0"],
   ["模块五 统计报表", "8", "8", "0"],
   ["权限隔离", "7", "7", "0"],
   ["事务与并发", "5", "5", "0"],
   ["合计", "58", "58", "0"]],
  widths=[7.0, 2.4, 2.4, 2.4])

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

H("5.3.2 模块二：航线、船舶、班次、座位", 3)
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

H("5.3.3 模块三：售票、订单、退票、改签、检票", 3)
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

H("5.3.4 模块五：统计报表", 3)
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
P("refund: refund_amount=100.00, fee=0.00, biz_type='REFUND', reason='班次取消自动退票'",
  mono=True, indent=True)
P("notification: type=SCHEDULE_CANCEL, title='班次取消通知',", mono=True, indent=True)
P("              content='您订单 O2026… 所在班次已取消，票款 ¥100.00 已全额退还'", mono=True, indent=True)

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

doc.save(DST)
print("saved:", DST)
