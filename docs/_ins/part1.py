
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
    pf.line_spacing = Pt(24)
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
    IMG(FIG_DIR + "fig1_usecase.png", 14.6, "图 1  轮渡码头客运管理系统用例图")
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
    IMG(FIG_DIR + "fig2_arch.png", 14.6, "图 2  系统组织结构图")
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
