

# ============================================================
# 3 数据库设计
# ============================================================
def fill_sec3():
    H("3.1 概念结构设计", 2)
    P("系统共 11 个实体，E-R 图如图 3 所示。图中只保留业务属性，created_at / updated_at 两个审计字段为图面清晰而省略，"
      "其余属性与 sql/01_schema.sql 逐列对应；带下划线的属性为主键，箭头由「1」端指向「N」端。", indent=True)
    IMG(FIG_DIR + "fig3_er.png", 14.6, "图 3  系统 E-R 图")
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
        "       SUM(CASE WHEN t.status = 'REFUNDED' THEN 1 ELSE 0 END)         AS refund_count,",
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
    IMG(FIG_DIR + "fig4_class.png", 14.6, "图 4  售票核心链路类图")
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
    IMG(FIG_DIR + "fig5_pkg.png", 14.6, "图 5  系统包图")
    P("包之间的约束：controller 不得直接引用 dao；entity 不得引用 service；"
      "common 为最底层，只能被引用、不得反向引用任何业务包。这三点保证了依赖方向单一，"
      "修改 SQL 不会波及控制层，替换视图也不会波及业务层。", indent=True)

    H("4.3 核心业务流程", 2)
    P("在线购票主流程如图 6 所示，分四段：查询、锁定、下单、支付。", indent=True)
    IMG(FIG_DIR + "fig6_flow.png", 14.6, "图 6  在线购票主流程图")
    P("（1）查询段：按出发港、到达港与日期查班次，返回余票（总座位数减有效票数），不读 sold_count。", indent=True)
    P("（2）锁定段：逐座执行条件更新；任一失败则回查该座位当前状态，区分「座位不存在」「已售」「已被他人锁定」三种原因给出不同提示，"
      "并回滚已锁定的座位。锁定保留 5 分钟，超时由定时任务释放。", indent=True)
    P("（3）下单段：校验一人一班次只能有一张有效票、座位归属与锁定人一致，通过后写入订单与票，票初始状态 UNPAID。", indent=True)
    P("（4）支付段：条件更新订单与票为 PAID、座位为 SOLD，班次已售数加 1；超过 30 分钟未支付由定时任务转 CANCELLED 并释放座位。", indent=True)

    H("4.4 并发控制设计", 2)
    P("抢座是整个系统唯一真正存在竞争的操作，其控制流程如图 7 所示。", indent=True)
    IMG(FIG_DIR + "fig7_lock.png", 14.6, "图 7  并发抢座控制流程")
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
