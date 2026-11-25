# -*- coding: utf-8 -*-
"""生成报告插图。用法：python make_figs.py [fig1 fig2 ...]"""
import os
import sys

from draw_lib import Canvas, F, LINE, INK, GREY

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")
os.makedirs(OUT, exist_ok=True)

BLUE_FILL = (232, 240, 254)
BLUE_HEAD = (191, 215, 250)
GREEN_FILL = (220, 252, 231)
GREEN_HEAD = (167, 243, 208)
AMBER_FILL = (254, 249, 195)
AMBER_HEAD = (253, 224, 71)
PURPLE_FILL = (237, 233, 254)
PURPLE_HEAD = (196, 181, 253)
GREY_FILL = (243, 244, 246)
GREY_HEAD = (209, 213, 219)


# ============================================================
# 图 1  用例图
# ============================================================
def fig_usecase():
    cv = Canvas(1770, 1150)
    # 系统边界
    cv.box(30, 80, 1710, 1000, fill=(250, 251, 253), outline=(120, 130, 145), radius=16, width=4)
    cv.text((80, 126), "轮渡码头客运管理系统", F(34, True), fill=(30, 41, 59), anchor="lm")

    groups = [
        dict(actor="乘客", acx=140, ecx=470,
             cases=["注册与登录", "查询班次与余票", "选座并锁座", "在线支付出票",
                    "查看我的订单", "退票与改签"]),
        dict(actor="售票员", acx=700, ecx=1030,
             cases=["窗口代客售票", "办理退票", "办理改签", "检票验票", "查看个人业绩"]),
        dict(actor="管理员", acx=1260, ecx=1590,
             cases=["用户管理", "航线管理", "船舶与座位管理", "班次管理",
                    "统计报表", "报表导出"]),
    ]
    EW, EH = 300, 96
    STEP = 152
    CY = 580

    for g in groups:
        n = len(g["cases"])
        start = CY - (n - 1) * STEP // 2
        port = cv.actor(g["acx"], CY, g["actor"], scale=1.35, label_below=True)
        for i, name in enumerate(g["cases"]):
            cy = start + i * STEP
            cv.ellipse(g["ecx"], cy, EW, EH, fill="white", outline=(59, 130, 246), width=3)
            lines = cv.wrap(name, F(30), EW - 56)
            ly = cy - (len(lines) - 1) * 19
            for ln in lines:
                cv.text((g["ecx"], ly), ln, F(30))
                ly += 38
            cv.arrow([port, (g["ecx"] - EW // 2, cy)], width=3, head_size=15)

    return cv.save(os.path.join(OUT, "fig1_usecase.png"))


# ============================================================
# 图 2  系统架构图
# ============================================================
def fig_arch():
    layers = [
        ("表示层", "Thymeleaf 模板 21 个页面 · 原生 JS + CSS", BLUE_FILL, BLUE_HEAD),
        ("控制层", "Controller 7 个 · 参数校验 · 会话取用户 · 统一 Result", GREEN_FILL, GREEN_HEAD),
        ("业务层", "Service 接口 6 个 + 6 个 Impl · 事务边界 · 业务规则校验", AMBER_FILL, AMBER_HEAD),
        ("持久层", "DAO 接口 12 个 + 12 个 XML Mapper · 动态 SQL · 结果映射", PURPLE_FILL, PURPLE_HEAD),
        ("数据层", "MySQL 8.0 InnoDB · 11 张表 · 外键 / CHECK / 唯一索引", GREY_FILL, GREY_HEAD),
    ]
    x, w = 130, 1130
    H = 170
    GAP = 104
    top0 = 100
    total_h = top0 + len(layers) * H + (len(layers) - 1) * GAP + 90
    cv = Canvas(1820, total_h)

    tops = []
    y = top0
    for name, desc, fill, head in layers:
        cv.box(x, y, w, H, fill=fill, radius=12, width=3)
        cv.box(x, y, 230, H, fill=head, radius=12, width=3)
        cv.d.rectangle([x + 220, y, x + 230, y + H], fill=head)
        cv.d.line([(x + 230, y), (x + 230, y + H)], fill=LINE, width=3)
        cv.text((x + 115, y + H // 2), name, F(38, True))
        lines = cv.wrap(desc, F(30), w - 270)
        ty = y + H // 2 - (len(lines) - 1) * 19
        for ln in lines:
            cv.text((x + 262, ty), ln, F(30), anchor="lm")
            ty += 40
        tops.append((y, y + H))
        y += H + GAP

    # 层间向下箭头（调用方向）
    for i in range(len(layers) - 1):
        y0 = tops[i][1]
        y1 = tops[i + 1][0]
        cv.arrow([(x + w // 2, y0 + 6), (x + w // 2, y1 - 8)], width=4, head_size=20)
    labels = ["请求", "调用", "读写", "SQL"]
    for i, lb in enumerate(labels):
        cv.text((x + w // 2 + 26, tops[i][1] + GAP // 2), lb, F(26), fill=GREY, anchor="lm")

    # 右侧横切支撑（高度按内容计算，避免大片空白）
    items = [("登录拦截 · @RequireRole", 0),
             ("全局异常 · 统一 Result", 0),
             ("BCrypt · 登录失败锁定", 0),
             ("单号生成（毫秒+序列）", 0),
             ("定时任务：", 0),
             ("锁超时释放", 1),
             ("支付超时自动取消", 1),
             ("班次状态自动流转", 1)]
    sx, sw = 1340, 440
    head_h = 96
    item_h = 52
    # 框高覆盖两条入边的落点（业务层、持久层），避免箭头指向框外
    sy = tops[1][0] - 10
    sh = (tops[3][0] + 60) + 38 - sy
    cv.box(sx, sy, sw, sh, fill=(255, 251, 235), outline=(217, 119, 6), radius=12, width=3)
    cv.text((sx + sw // 2, sy + 46), "横切支撑", F(34, True), fill=(146, 64, 14))
    cv.d.line([(sx + 40, sy + 74), (sx + sw - 40, sy + 74)], fill=(217, 119, 6), width=2)
    _bh = item_h * (len(items) - 1) + 30
    ty = sy + head_h + max(22, (sh - head_h - _bh) // 2) + 15
    for text, lvl in items:
        bx = sx + 30 + lvl * 34
        if lvl == 0:
            cv.text((bx, ty), "·", F(30), fill=(69, 26, 3), anchor="lm")
        else:
            cv.text((bx, ty), "–", F(30), fill=(146, 64, 14), anchor="lm")
        cv.text((bx + 22, ty), text, F(30), fill=(69, 26, 3), anchor="lm")
        ty += item_h

    # 各层依赖横切能力（箭头由层指向横切框，方向不可反）
    for yy in (tops[2][0] + 60, tops[3][0] + 60):
        cv.arrow([(x + w + 2, yy), (sx - 1, yy)], color=(217, 119, 6), width=3,
                 dashed=True, head_size=16)
    return cv.save(os.path.join(OUT, "fig2_arch.png"))


def _label_near(cv, p, seg, text, sign, color=(190, 30, 60)):
    """在连线端点旁标注基数，沿线段方向偏移 sign*30，垂直方向偏 24"""
    if not text:
        return
    dx, dy = seg
    L = (dx * dx + dy * dy) ** 0.5 or 1
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    cv.text((p[0] + sign * ux * 34 + px * 24, p[1] + sign * uy * 34 + py * 24),
            text, F(28, True), fill=color)


def _link(cv, pts, c1="", c2="", color=LINE):
    cv.arrow(pts, color=color, width=3, head_size=16)
    _label_near(cv, pts[0], (pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]), c1, 1)
    _label_near(cv, pts[-1], (pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]), c2, -1)


# ============================================================
# 图 3  E-R 图
# ============================================================
def fig_er():
    """E-R 图：属性与 sql/01_schema.sql 逐列对应，仅省略 created_at / updated_at 审计字段

    版面：三列竖向排布。画布收窄到 1540px，插入 14.6cm 时每 cm ≈ 105px，
    正文字号 26px 即约 7pt，保证打印与屏幕阅读都能看清。
    连线只走两条列间走廊（x 415~535、895~1015）与右侧留白，互不交叉。
    """
    cv = Canvas(1430, 1880)
    W = 360
    L0, L1, L2 = 55, 535, 1015
    FS = 26

    # ---- 第一列 ----
    cv.entity(L0, 80, W, "user 用户",
              ["*id", "username 用户名", "password 密码", "name 姓名", "phone 手机号",
               "id_card 身份证号", "role 角色", "status 状态",
               "login_fail 失败次数", "lock_until 锁定至"], font_size=FS)          # 80-506
    cv.entity(L0, 576, W, "route 航线",
              ["*id", "route_name 航线名", "depart_port 出发港", "arrive_port 到达港",
               "duration 时长(分)", "description 描述", "deleted 逻辑删除"],
              font_size=FS)                                                       # 576-894
    cv.entity(L0, 964, W, "ship 船舶",
              ["*id", "ship_name 船名", "total_seats 总座位", "ship_type 类型",
               "description 描述", "deleted 逻辑删除"], font_size=FS)              # 964-1246
    cv.entity(L0, 1316, W, "ship_seat 船舶座位",
              ["*id", "ship_id 船舶 FK", "seat_no 座位号", "row_no 排号", "col_no 列号"],
              font_size=FS)                                                       # 1316-1562

    # ---- 第二列 ----
    cv.entity(L1, 80, W, "notification 通知",
              ["*id", "user_id 接收人 FK", "type 类型", "title 标题",
               "content 内容", "is_read 是否已读", "create_time 创建时间"],
              font_size=FS)                                                       # 80-398
    cv.entity(L1, 468, W, "orders 订单",
              ["*id", "order_no 订单号", "user_id 乘客 FK", "seller_id 售票员 FK",
               "schedule_id 班次 FK", "total_amount 金额", "status 状态",
               "channel 渠道", "create_time 下单时间", "pay_time 支付时间"],
              font_size=FS)                                                       # 468-894
    cv.entity(L1, 964, W, "schedule 班次",
              ["*id", "route_id 航线 FK", "ship_id 船舶 FK", "depart_time 发船时间",
               "arrive_time 到达时间", "price 票价", "status 状态",
               "sold_count 已售数", "deleted 逻辑删除"], font_size=FS)             # 964-1354
    cv.entity(L1, 1424, W, "schedule_seat 班次座位",
              ["*id", "schedule_id 班次 FK", "seat_no 座位号", "status 状态",
               "order_id 占用订单", "lock_time 锁定时间", "lock_user_id 锁定用户 FK"],
              font_size=FS)                                                       # 1424-1742

    # ---- 第三列（refund 在上、ticket 居中、reschedule 在下：orders 指向的两张表上下相邻） ----
    cv.entity(L2, 80, W, "refund 退票记录",
              ["*id", "order_id 订单 FK", "ticket_id 船票 FK",
               "refund_amount 退款额", "fee 手续费", "reason 原因",
               "refund_time 退款时间", "operator_id 经办人 FK", "biz_type 业务类型"],
              font_size=FS)                                                       # 80-470
    cv.entity(L2, 540, W, "ticket 船票",
              ["*id", "ticket_no 票号", "order_id 订单 FK", "schedule_id 班次 FK",
               "seat_no 座位号", "passenger_name 姓名", "id_card 身份证号",
               "phone 联系电话", "price 票价", "status 状态",
               "check_time 检票时间", "checker_id 检票员 FK"], font_size=FS)       # 540-1038
    cv.entity(L2, 1108, W, "reschedule 改签记录",
              ["*id", "old_ticket_id 原票 FK", "new_ticket_id 新票 FK",
               "old_schedule_id 原班次", "new_schedule_id 新班次",
               "price_diff 差价", "reschedule_time 改签时间"], font_size=FS)       # 1108-1426

    LB = dict(fill=(190, 30, 60))
    FS_LB = 27

    def _rel(pts, p1, p2):
        """画联系线并在 p1/p2 两处显式落基数标注（坐标手工给定，避免压线或互相重叠）"""
        cv.arrow(pts, width=3, head_size=16)
        cv.text(p1, "1", F(FS_LB, True), fill=LB["fill"])
        cv.text(p2, "N", F(FS_LB, True), fill=LB["fill"])

    # ---- 走廊一（x 415~535）：user / route / ship 指向 notification / orders / schedule ----
    _rel([(415, 190), (535, 190)], (445, 166), (507, 166))                          # user-notification
    _rel([(415, 300), (470, 300), (470, 620), (535, 620)],
         (438, 276), (508, 596))                                                    # user-orders
    _rel([(415, 720), (500, 720), (500, 1150), (535, 1150)],
         (438, 696), (515, 1126))                                                   # route-schedule
    _rel([(415, 1120), (455, 1120), (455, 1290), (535, 1290)],
         (432, 1096), (508, 1266))                                                  # ship-schedule
    _rel([(235, 1246), (235, 1316)], (262, 1262), (262, 1300))                      # ship-ship_seat

    # ---- 走廊二（x 895~1015）：orders / schedule 指向 refund / ticket ----
    # 三条连线的纵向区间互不交错：orders(560)→refund(250)、orders(780)→ticket(650)、schedule(1040)→ticket(800)
    _rel([(895, 560), (940, 560), (940, 250), (1015, 250)],
         (915, 536), (990, 226))                                                    # orders-refund
    _rel([(895, 780), (975, 780), (975, 650), (1015, 650)],
         (915, 756), (992, 776))                                                    # orders-ticket
    _rel([(895, 1040), (950, 1040), (950, 800), (1015, 800)],
         (915, 1016), (985, 826))                                                   # schedule-ticket
    _rel([(775, 1354), (775, 1424)], (802, 1370), (802, 1408))                      # schedule-schedule_seat

    # ---- 第三列内部 ----
    _rel([(1255, 540), (1255, 470)], (1282, 526), (1282, 484))                      # ticket-refund
    _rel([(1255, 1038), (1255, 1108)], (1282, 1052), (1282, 1094))                  # ticket-reschedule

    # 图例
    lx, ly = 55, 1790
    cv.box(lx, ly, 1010, 76, fill=(248, 250, 252), outline=(160, 170, 180), radius=8, width=2)
    cv.text((lx + 22, ly + 38), "图例：", F(25, True), anchor="lm")
    cv.d.line([(lx + 108, ly + 38), (lx + 244, ly + 38)], fill=LINE, width=3)
    cv.arrow([(lx + 196, ly + 38), (lx + 244, ly + 38)], width=3, head_size=15)
    cv.text((lx + 120, ly + 18), "1", F(24, True), fill=(190, 30, 60))
    cv.text((lx + 222, ly + 18), "N", F(24, True), fill=(190, 30, 60))
    cv.text((lx + 292, ly + 38), "一对多联系；下划线属性为主键；省略 created_at / updated_at",
            F(24), anchor="lm")
    return cv.save(os.path.join(OUT, "fig3_er.png"))


# ============================================================
# 图 4  类图（售票核心链路）
# ============================================================
def _class_box(cv, x, y, w, name, stereo, methods, fill=(236, 254, 255), head=(165, 243, 252)):
    hh = 70 if stereo else 62
    mh = 38
    h = hh + mh * len(methods) + 14
    cv.box(x, y, w, h, fill=fill, radius=6, width=3)
    cv.d.rectangle([x, y, x + w, y + hh], fill=head, outline=LINE, width=3)
    if stereo:
        cv.text((x + w // 2, y + 21), stereo, F(23), fill=(70, 80, 95))
        cv.text((x + w // 2, y + 49), name, F(29, True))
    else:
        cv.text((x + w // 2, y + hh // 2), name, F(29, True))
    cv.d.line([(x, y + hh), (x + w, y + hh)], fill=LINE, width=3)
    my = y + hh + 8
    for m in methods:
        cv.text((x + 22, my + 14), m, F(24), anchor="lm")
        my += mh
    return h


def fig_class():
    """类图：左列控制层→业务层接口→实现类，右列五个 DAO 接口。

    画布收窄到 1390px，插入 14.6cm 时正文约 6.9pt；实现类右边界对准
    DAO 列左边界作扇形依赖，五条线共起点，互不交叉。
    """
    cv = Canvas(1390, 1580)
    W1, X1 = 560, 55
    W2, X2 = 500, 835

    _class_box(cv, X1, 80, W1, "OrderController", "",
               ["+ createOrder(body, session)", "+ lockSeats(body, session)",
                "+ pay(id, session)", "+ refund(id, body, session)",
                "+ reschedule(id, body, session)", "+ checkin(body, session)"],
               fill=(219, 234, 254), head=(147, 197, 253))                  # 80-390
    _class_box(cv, X1, 462, W1, "OrderService", "«interface»",
               ["+ createOrder(sid, uid, sellerId, tickets)",
                "+ lockSeats(sid, seatNos, uid)", "+ pay(orderId, uid)",
                "+ cancelOrder(orderId, uid)", "+ refund(orderId, uid, role, reason)",
                "+ reschedule(tid, newSid, newSeat, uid)",
                "+ checkIn(code, checkerId, sid)"],
               fill=(220, 252, 231), head=(134, 239, 172))                  # 462-812
    _class_box(cv, X1, 882, W1, "OrderServiceImpl", "",
               ["- genNo(prefix) : String",
                "- seatLockFailureReason(sid, seatNo) : String",
                "- recalcOrderStatus(orderId) : void",
                "- getSchedule(sid) : Schedule",
                "- lockSchedule(sid) : Schedule"],
               fill=(254, 249, 195), head=(253, 224, 71))                   # 882-1156

    dao = [("OrderDao", ["+ insert / findById / findByOrderNo", "+ updateStatus(orderId, status)"]),
           ("TicketDao", ["+ insert / listByOrder / findByTicketNo", "+ updateStatusIf(id, from, to)"]),
           ("ScheduleSeatDao", ["+ lock / markSold / releaseForOrder", "+ findByIdForUpdate(sid)"]),
           ("ScheduleDao", ["+ incrementSold / decrementSold", "+ findByIdForUpdate(id)"]),
           ("RefundDao", ["+ insert(refund)", "+ listByOrder(orderId)"])]
    STEP = 190
    top = 1019 - (STEP * (len(dao) - 1) + 152) // 2       # 以实现类中线为基准居中
    for i, (name, ms) in enumerate(dao):
        _class_box(cv, X2, top + i * STEP, W2, name, "«interface»", ms,
                   fill=(237, 233, 254), head=(196, 181, 253))

    # 依赖：Controller -> Service（开放 V 箭头，尖抵接口框上边界 462）
    cv.arrow([(335, 390), (335, 462)], width=3, dashed=True, head_size=18, vee_head=True)
    # 实现：Impl -> Service（空心三角，尖抵接口框下边界 812）
    cv.arrow([(335, 882), (335, 812)], width=3, dashed=True, head_size=20, open_head=True)
    # 依赖：Impl -> 各 DAO（共起点扇形，互不交叉；开放 V 箭头）
    for i in range(len(dao)):
        cv.arrow([(615, 1019), (X2, top + i * STEP + 76)],
                 width=3, dashed=True, head_size=15, vee_head=True)

    cv.text((55, 1508), "说明：Controller 只做参数装配与会话取用户，业务规则与事务边界落在 OrderServiceImpl；",
            F(24), fill=GREY, anchor="lm")
    cv.text((55, 1546), "DAO 均为接口，SQL 由 XML Mapper 提供；返回实体来自 entity 包，与 3.2 节关系模型一一对应。",
            F(24), fill=GREY, anchor="lm")
    return cv.save(os.path.join(OUT, "fig4_class.png"))


# ============================================================
# 图 5  包图
# ============================================================
def _pkg(cv, x, y, w, h, name, notes, fill=BLUE_FILL, head=BLUE_HEAD):
    tab_w, tab_h = 170, 34
    cv.d.rectangle([x, y, x + tab_w, y + tab_h], fill=head, outline=LINE, width=3)
    cv.d.rectangle([x, y + tab_h, x + w, y + h], fill=fill, outline=LINE, width=3)
    cv.d.line([(x, y + tab_h), (x + tab_w, y + tab_h)], fill=LINE, width=3)
    cv.text((x + tab_w // 2, y + tab_h // 2), "package", F(20), fill=(60, 70, 85))
    cv.text((x + w // 2, y + tab_h + 38), name, F(28, True))
    if isinstance(notes, str):
        notes = [notes]
    for i, ln in enumerate(notes):
        cv.text((x + w // 2, y + tab_h + 78 + i * 34), ln, F(25), fill=GREY)


def fig_pkg():
    """包图：左列四层纵向调用链，右列四个横切包；箭头一律「使用者 -> 被依赖者」。

    画布 1400px，插入 14.6cm 时包名约 8.3pt、说明文字约 7.4pt。
    两条跨列走线分居 x=730 / x=680 两条走廊，纵向区间不交错，故不交叉。
    """
    cv = Canvas(1400, 1150)
    colL, colR, W, H_ = 55, 785, 560, 180
    Y = [90, 340, 590, 840]

    _pkg(cv, colL, Y[0], W, H_, "com.ferry.controller", "7 个 Controller · 接收请求")
    _pkg(cv, colL, Y[1], W, H_, "com.ferry.service", "6 个接口 + impl 实现 · 事务边界",
         GREEN_FILL, GREEN_HEAD)
    _pkg(cv, colL, Y[2], W, H_, "com.ferry.dao", "12 个 DAO 接口 · 对应 XML Mapper",
         PURPLE_FILL, PURPLE_HEAD)
    _pkg(cv, colL, Y[3], W, H_, "com.ferry.entity", "11 个实体类 · 与库表一一对应",
         GREY_FILL, GREY_HEAD)

    _pkg(cv, colR, Y[0], W, H_, "com.ferry.config", "WebMvc 配置 · 拦截器注册 · 定时任务")
    _pkg(cv, colR, Y[1], W, H_, "com.ferry.interceptor", "LoginInterceptor / RoleInterceptor")
    _pkg(cv, colR, Y[2], W, H_, "com.ferry.common",
         ["Result / LoginUser / @RequireRole", "BizException 统一业务异常"])
    _pkg(cv, colR, Y[3], W, H_, "com.ferry.exception", "GlobalExceptionHandler 统一异常处理")

    midL, midR = colL + W // 2, colR + W // 2
    # 左列分层依赖（向下）
    for i in range(3):
        cv.arrow([(midL, Y[i] + H_), (midL, Y[i + 1])], width=3, dashed=True,
                 head_size=16, vee_head=True)
    # 右列：config 注册 interceptor；二者都使用 common；exception 处理 common 抛出的异常
    cv.arrow([(midR, Y[0] + H_), (midR, Y[1])], width=3, dashed=True, head_size=16, vee_head=True)
    cv.arrow([(midR, Y[1] + H_), (midR, Y[2])], width=3, dashed=True, head_size=16, vee_head=True)
    cv.arrow([(midR, Y[3]), (midR, Y[2] + H_)], width=3, dashed=True, head_size=16, vee_head=True)

    # controller / service 使用 common：外层走 x=730，内层走 x=680，纵向区间不交错
    cv.arrow([(colL + W, 180), (730, 180), (730, 640), (colR, 640)],
             width=3, dashed=True, head_size=16, vee_head=True)
    cv.arrow([(colL + W, 430), (680, 430), (680, 720), (colR, 720)],
             width=3, dashed=True, head_size=16, vee_head=True)

    cv.text((55, 1078), "说明：箭头由使用者指向被依赖者；exception 由 Spring 回调，无入边；"
                        "各包的自动装配入口为 FerryApplication。",
            F(25), fill=GREY, anchor="lm")
    return cv.save(os.path.join(OUT, "fig5_pkg.png"))


# ============================================================
# 图 6  在线购票主流程
# ============================================================
def fig_flow():
    """在线购票主流程：节点纵坐标显式给出，箭头一律「上框底边 -> 下框顶边」"""
    cv = Canvas(1500, 1960)
    cx, w = 430, 520
    bx, bw = 740, 600          # 右侧分支列左边界与宽度
    NODES = [
        ("start", "term", 60, 76), ("query", "proc", 200, 96), ("pick", "proc", 360, 96),
        ("d1", "dec", 520, 170), ("lock", "proc", 754, 96), ("submit", "proc", 914, 96),
        ("d2", "dec", 1074, 160), ("order", "proc", 1298, 96), ("d3", "dec", 1458, 160),
        ("pay", "proc", 1682, 96), ("end", "term", 1842, 76),
    ]
    TEXT = {"start": "开始", "query": "查询在售班次与余票", "pick": "选择座位（最多 5 个）",
            "d1": "座位可锁定？", "lock": "锁定座位（保留 5 分钟）",
            "submit": "填写乘客信息并提交订单", "d2": "校验通过？",
            "order": "生成订单与船票（UNPAID）", "d3": "30 分钟内支付？",
            "pay": "出票：票 PAID / 座位 SOLD", "end": "结束"}
    GREEN = {"order", "pay"}

    for key, kind, y, h in NODES:
        t = TEXT[key]
        if kind == "term":
            cv.box(cx - 160, y, 320, 76, fill=(226, 232, 240), radius=38, width=3)
            cv.text((cx, y + 38), t, F(28, True))
        elif kind == "proc":
            cv.box(cx - w // 2, y, w, h, fill=(GREEN_FILL if key in GREEN else BLUE_FILL),
                   radius=10, width=3)
            cv.text((cx, y + h // 2), t, F(27))
        else:
            cv.diamond(cx, y + h // 2, 480, h, fill=AMBER_FILL, outline=LINE, width=3)
            cv.text((cx, y + h // 2), t, F(26))

    box = {k: (y, h) for k, _, y, h in NODES}

    # 主干：上框底边 -> 下框顶边（箭头尖正好落在下框顶边）
    for i in range(len(NODES) - 1):
        a, b = NODES[i][0], NODES[i + 1][0]
        ya, ha = box[a]
        yb, _ = box[b]
        cv.arrow([(cx, ya + ha), (cx, yb)], width=3, head_size=17)

    # 三个判定框的「是」：落在本框下顶点与下框顶边之间的空档
    for k in ("d1", "d2", "d3"):
        y, h = box[k]
        cv.text((cx + 24, y + h + 22), "是", F(24, True), fill=(22, 101, 52), anchor="lm")

    # 分支列：提示框与判定框中线对齐
    BR = {"d1": (110, 2), "d2": (104, 2), "d3": (104, 2)}
    BR_TEXT = {"d1": ("提示：座位不存在 / 已售 /", "已被他人锁定"),
               "d2": ("拒绝下单：一人一班次一票、", "座位归属不符"),
               "d3": ("订单转 CANCELLED，票作废，", "座位释放为 AVAILABLE")}
    for k, (bh, nl) in BR.items():
        y, h = box[k]
        mid = y + h // 2
        by = mid - bh // 2
        # 否：判定框右顶点 -> 提示框左边
        cv.d.line([(cx + 240, mid), (bx, mid)], fill=LINE, width=3)
        cv.text((cx + 270, mid - 26), "否", F(26, True), fill=(190, 30, 60))
        cv.box(bx, by, bw, bh, fill=(254, 226, 226), radius=10, width=3)
        for j, ln in enumerate(BR_TEXT[k]):
            cv.text((bx + bw // 2, by + bh // 2 - 22 + j * 44), ln, F(24))

    # 锁定失败 -> 重新选座
    d1y, d1h = box["d1"]
    py, ph = box["pick"]
    back_x = bx + bw // 2
    cv.arrow([(back_x, d1y + d1h // 2 - 55), (back_x, py + ph // 2), (cx + w // 2, py + ph // 2)],
             width=3, head_size=16, dashed=True)
    cv.text((back_x + 16, py + ph // 2 - 24), "重新选座", F(23), fill=GREY, anchor="lm")
    return cv.save(os.path.join(OUT, "fig6_flow.png"))


# ============================================================
# 图 7  并发抢座控制
# ============================================================
def fig_lock():
    cv = Canvas(1500, 1090)
    cx, w = 400, 620
    bx, bw = 1130, 330

    def proc(y, text, h=96, fill=BLUE_FILL):
        cv.box(cx - w // 2, y, w, h, fill=fill, radius=10, width=3)
        lines = cv.wrap(text, F(26), w - 40)
        ty = y + h // 2 - (len(lines) - 1) * 17
        for ln in lines:
            cv.text((cx, ty), ln, F(26))
            ty += 34
        return y + h

    cv.box(cx - 150, 50, 300, 74, fill=(226, 232, 240), radius=37, width=3)
    cv.text((cx, 87), "用户提交选座", F(28, True))

    y = 190
    cv.box(cx - 390, y, 780, 164, fill=(254, 249, 195), radius=10, width=3)
    cv.text((cx, y + 50), "执行条件更新（单条 SQL，原子操作）", F(27, True))
    cv.text((cx, y + 100), "UPDATE schedule_seat SET status='LOCKED', lock_time=NOW()",
            F(23), fill=(60, 70, 85))
    cv.text((cx, y + 138), "WHERE schedule_id=? AND seat_no=? AND status='AVAILABLE'",
            F(23), fill=(60, 70, 85))
    y1 = y + 164

    dy = y1 + 60
    cv.diamond(cx, dy + 90, 520, 180, fill=AMBER_FILL, width=3)
    cv.text((cx, dy + 70), "受影响行数 = 1 ？", F(26))
    cv.text((cx, dy + 106), "（InnoDB 返回的影响行数）", F(21), fill=GREY)

    # 是：向下
    y2 = dy + 180 + 46
    cv.arrow([(cx, dy + 182), (cx, y2 - 1)], width=3, head_size=17)
    cv.text((cx + 24, dy + 200), "是", F(25, True), fill=(22, 101, 52), anchor="lm")
    y3 = proc(y2, "锁定成功，占用座位并继续下单", 96, fill=GREEN_FILL)
    cv.box(cx - 110, y3 + 40, 220, 66, fill=(220, 252, 231), radius=33, width=3)
    cv.text((cx, y3 + 73), "进入支付", F(26, True))
    cv.arrow([(cx, y3 + 2), (cx, y3 + 39)], width=3, head_size=16)

    # 否：向右
    cv.arrow([(cx + 260, dy + 90), (bx - 40, dy + 90)], width=3, head_size=17)
    cv.text((cx + 286, dy + 62), "否", F(25, True), fill=(190, 30, 60))
    cv.box(bx - 40, dy + 18, bw, 150, fill=(254, 226, 226), radius=10, width=3)
    cv.text((bx - 40 + bw // 2, dy + 46), "回查该座位当前状态", F(24))
    cv.text((bx - 40 + bw // 2, dy + 84), "区分三种原因提示", F(24))
    cv.text((bx - 40 + bw // 2, dy + 122), "（不存在 / 已售 / 他人锁定）", F(21), fill=GREY)

    # 说明
    cv.box(80, 930, 1340, 110, fill=(248, 250, 252), outline=(160, 170, 180), radius=10, width=2)
    cv.text((110, 962), "并发要点：同一行的并发 UPDATE 由 InnoDB 行锁串行化。先到的事务持锁并提交后，",
            F(24), anchor="lm")
    cv.text((110, 1002), "后到事务的 WHERE 条件不再成立，影响行数恒为 0，因此不会出现两个用户买到同一座位。",
            F(24), anchor="lm")
    return cv.save(os.path.join(OUT, "fig7_lock.png"))


if __name__ == "__main__":
    want = sys.argv[1:] or ["fig1", "fig2", "fig3", "fig4", "fig5", "fig6", "fig7"]
    fn = {"fig1": fig_usecase, "fig2": fig_arch, "fig3": fig_er, "fig4": fig_class,
          "fig5": fig_pkg, "fig6": fig_flow, "fig7": fig_lock}
    for k in want:
        print(fn[k]())
