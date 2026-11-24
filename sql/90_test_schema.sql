-- =============================================================
-- 轮渡码头客运管理系统 数据库设计
-- 数据库：ferry_test  字符集：utf8mb4
-- 说明：本脚本包含建库、建表、约束、索引、测试数据
-- =============================================================

-- 强制会话字符集为 utf8mb4：Windows 命令行客户端默认 gbk，
-- 不加这行会导致插入中文报 "Data too long for column"
SET NAMES utf8mb4;

DROP DATABASE IF EXISTS ferry_test;
CREATE DATABASE ferry_test DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE ferry_test;

-- =============================================================
-- 1. 用户表 user
-- 角色：ADMIN 管理员 / SELLER 售票员 / PASSENGER 乘客
-- =============================================================
CREATE TABLE user (
    id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    username      VARCHAR(50)  NOT NULL COMMENT '用户名',
    password      VARCHAR(100) NOT NULL COMMENT '密码(BCrypt加密)',
    name          VARCHAR(50)  NOT NULL COMMENT '姓名',
    phone         VARCHAR(20)  NOT NULL COMMENT '手机号',
    id_card       VARCHAR(18)  NULL COMMENT '身份证号(乘客)',
    role          VARCHAR(20)  NOT NULL DEFAULT 'PASSENGER' COMMENT '角色',
    status        TINYINT      NOT NULL DEFAULT 1 COMMENT '状态 1启用 0禁用',
    login_fail    INT          NOT NULL DEFAULT 0 COMMENT '连续登录失败次数',
    lock_until    DATETIME     NULL COMMENT '锁定截止时间',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_phone (phone),
    KEY idx_role (role),
    CONSTRAINT chk_user_role CHECK (role IN ('ADMIN','SELLER','PASSENGER')),
    CONSTRAINT chk_user_status CHECK (status IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- =============================================================
-- 2. 航线表 route
-- 逻辑删除：deleted 0正常 1已删除
-- =============================================================
CREATE TABLE route (
    id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '航线ID',
    route_name    VARCHAR(50)  NOT NULL COMMENT '航线名称',
    depart_port   VARCHAR(50)  NOT NULL COMMENT '出发港口',
    arrive_port   VARCHAR(50)  NOT NULL COMMENT '到达港口',
    duration      INT          NOT NULL COMMENT '预计航行时长(分钟)',
    description   VARCHAR(255) NULL COMMENT '航线描述',
    deleted       TINYINT      NOT NULL DEFAULT 0 COMMENT '逻辑删除 0正常 1删除',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT chk_route_duration CHECK (duration > 0),
    CONSTRAINT chk_route_deleted CHECK (deleted IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='航线表';

-- =============================================================
-- 3. 船舶表 ship
-- =============================================================
CREATE TABLE ship (
    id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '船舶ID',
    ship_name     VARCHAR(50)  NOT NULL COMMENT '船名',
    total_seats   INT          NOT NULL COMMENT '总座位数',
    ship_type     VARCHAR(20)  NOT NULL DEFAULT 'NORMAL' COMMENT '类型 NORMAL普通 HIGHSPEED高速 LUXURY豪华',
    description   VARCHAR(255) NULL COMMENT '描述',
    deleted       TINYINT      NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_ship_name (ship_name),
    CONSTRAINT chk_ship_type CHECK (ship_type IN ('NORMAL','HIGHSPEED','LUXURY')),
    CONSTRAINT chk_ship_seats CHECK (total_seats > 0),
    CONSTRAINT chk_ship_deleted CHECK (deleted IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='船舶表';

-- =============================================================
-- 4. 班次表 schedule
-- 状态：PENDING待发布 / SELLING售票中 / DEPARTED已发船 / FINISHED已完成 / CANCELLED已取消
-- =============================================================
CREATE TABLE schedule (
    id            BIGINT         NOT NULL AUTO_INCREMENT COMMENT '班次ID',
    route_id      BIGINT         NOT NULL COMMENT '航线ID',
    ship_id       BIGINT         NOT NULL COMMENT '船舶ID',
    depart_time   DATETIME       NOT NULL COMMENT '发船时间',
    arrive_time   DATETIME       NOT NULL COMMENT '到达时间(自动计算)',
    price         DECIMAL(10,2)  NOT NULL COMMENT '票价',
    status        VARCHAR(20)    NOT NULL DEFAULT 'PENDING' COMMENT '状态',
    sold_count    INT            NOT NULL DEFAULT 0 COMMENT '已售座位数',
    deleted       TINYINT        NOT NULL DEFAULT 0 COMMENT '逻辑删除',
    created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_route (route_id),
    KEY idx_ship (ship_id),
    KEY idx_depart_time (depart_time),
    KEY idx_status (status),
    CONSTRAINT fk_schedule_route FOREIGN KEY (route_id) REFERENCES route(id),
    CONSTRAINT fk_schedule_ship  FOREIGN KEY (ship_id)  REFERENCES ship(id),
    CONSTRAINT chk_schedule_status CHECK (status IN ('PENDING','SELLING','DEPARTED','FINISHED','CANCELLED')),
    CONSTRAINT chk_schedule_price CHECK (price >= 0),
    CONSTRAINT chk_schedule_time CHECK (arrive_time > depart_time),
    CONSTRAINT chk_schedule_deleted CHECK (deleted IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班次表';

-- =============================================================
-- 5. 船舶座位表 ship_seat
-- 描述一艘船具有哪些座位，如 1A、1B、2A、2B
-- =============================================================
CREATE TABLE ship_seat (
    id            BIGINT      NOT NULL AUTO_INCREMENT COMMENT '座位ID',
    ship_id       BIGINT      NOT NULL COMMENT '船舶ID',
    seat_no       VARCHAR(10) NOT NULL COMMENT '座位号 如1A',
    row_no        INT         NOT NULL COMMENT '排号',
    col_no        CHAR(1)     NOT NULL COMMENT '列号 A/B/C/D',
    PRIMARY KEY (id),
    UNIQUE KEY uk_ship_seat (ship_id, seat_no),
    CONSTRAINT fk_ship_seat_ship FOREIGN KEY (ship_id) REFERENCES ship(id) ON DELETE CASCADE,
    CONSTRAINT chk_ship_seat_row CHECK (row_no > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='船舶座位表';

-- =============================================================
-- 6. 班次座位状态表 schedule_seat
-- 状态：AVAILABLE可售 / LOCKED锁定 / SOLD已售
-- 锁定时间 lock_time + 5分钟超时
-- =============================================================
CREATE TABLE schedule_seat (
    id            BIGINT      NOT NULL AUTO_INCREMENT COMMENT '记录ID',
    schedule_id   BIGINT      NOT NULL COMMENT '班次ID',
    seat_no       VARCHAR(10) NOT NULL COMMENT '座位号',
    status        VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE' COMMENT '状态',
    order_id      BIGINT      NULL COMMENT '占用订单ID(锁定/已售时)',
    lock_time     DATETIME    NULL COMMENT '锁定时间',
    lock_user_id  BIGINT      NULL COMMENT '选座锁定用户ID',
    PRIMARY KEY (id),
    UNIQUE KEY uk_schedule_seat (schedule_id, seat_no),
    KEY idx_schedule (schedule_id),
    KEY idx_lock_user (lock_user_id),
    CONSTRAINT fk_schedule_seat_schedule FOREIGN KEY (schedule_id) REFERENCES schedule(id) ON DELETE CASCADE,
    CONSTRAINT fk_schedule_seat_lock_user FOREIGN KEY (lock_user_id) REFERENCES user(id),
    CONSTRAINT chk_schedule_seat_status CHECK (status IN ('AVAILABLE','LOCKED','SOLD'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班次座位状态表';

-- =============================================================
-- 7. 订单表 orders
-- 状态：UNPAID待支付 / PAID已支付 / CHECKED已检票 / FINISHED已完成 / CANCELLED已取消 / REFUNDED已退票
-- 渠道：ONLINE线上 / OFFLINE线下
-- =============================================================
CREATE TABLE orders (
    id            BIGINT         NOT NULL AUTO_INCREMENT COMMENT '订单ID',
    order_no      VARCHAR(40)    NOT NULL COMMENT '订单编号',
    user_id       BIGINT         NULL COMMENT '下单乘客ID(线下代购可为空)',
    seller_id     BIGINT         NULL COMMENT '售票员ID(线下售票时)',
    schedule_id   BIGINT         NOT NULL COMMENT '班次ID',
    total_amount  DECIMAL(10,2)  NOT NULL COMMENT '总金额',
    status        VARCHAR(20)    NOT NULL DEFAULT 'UNPAID' COMMENT '订单状态',
    channel       VARCHAR(20)    NOT NULL DEFAULT 'ONLINE' COMMENT '渠道',
    create_time   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下单时间',
    pay_time      DATETIME       NULL COMMENT '支付时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_order_no (order_no),
    KEY idx_user (user_id),
    KEY idx_schedule (schedule_id),
    KEY idx_status (status),
    KEY idx_seller (seller_id),
    KEY idx_create_time (create_time),
    CONSTRAINT fk_orders_user     FOREIGN KEY (user_id)     REFERENCES user(id),
    CONSTRAINT fk_orders_seller   FOREIGN KEY (seller_id)   REFERENCES user(id),
    CONSTRAINT fk_orders_schedule FOREIGN KEY (schedule_id) REFERENCES schedule(id),
    CONSTRAINT chk_orders_status CHECK (status IN ('UNPAID','PAID','CHECKED','FINISHED','CANCELLED','REFUNDED')),
    CONSTRAINT chk_orders_channel CHECK (channel IN ('ONLINE','OFFLINE')),
    CONSTRAINT chk_orders_amount CHECK (total_amount >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单表';

-- =============================================================
-- 8. 船票表 ticket
-- 每张船票对应一个座位
-- 状态：UNPAID / PAID / CHECKED / REFUNDED / CANCELLED
-- =============================================================
CREATE TABLE ticket (
    id            BIGINT         NOT NULL AUTO_INCREMENT COMMENT '船票ID',
    ticket_no     VARCHAR(40)    NOT NULL COMMENT '船票编号',
    order_id      BIGINT         NOT NULL COMMENT '订单ID',
    schedule_id   BIGINT         NOT NULL COMMENT '班次ID',
    seat_no       VARCHAR(10)    NOT NULL COMMENT '座位号',
    passenger_name VARCHAR(50)   NOT NULL COMMENT '乘客姓名',
    id_card       VARCHAR(18)    NOT NULL COMMENT '身份证号',
    phone         VARCHAR(20)    NULL COMMENT '手机号',
    price         DECIMAL(10,2)  NOT NULL COMMENT '票价',
    status        VARCHAR(20)    NOT NULL DEFAULT 'UNPAID' COMMENT '票状态',
    check_time    DATETIME       NULL COMMENT '检票时间',
    checker_id    BIGINT         NULL COMMENT '检票员ID',
    PRIMARY KEY (id),
    UNIQUE KEY uk_ticket_no (ticket_no),
    KEY idx_order (order_id),
    KEY idx_schedule_seat (schedule_id, seat_no),
    KEY idx_id_card (id_card),
    CONSTRAINT fk_ticket_order    FOREIGN KEY (order_id)    REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_schedule FOREIGN KEY (schedule_id) REFERENCES schedule(id),
    CONSTRAINT fk_ticket_checker  FOREIGN KEY (checker_id)  REFERENCES user(id),
    -- RESCHEDULED 表示该票因改签已作废，与 REFUNDED(退票) 语义不同，不可混用
    CONSTRAINT chk_ticket_status CHECK (status IN ('UNPAID','PAID','CHECKED','REFUNDED','CANCELLED','RESCHEDULED')),
    CONSTRAINT chk_ticket_price CHECK (price >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='船票表';

-- =============================================================
-- 9. 退票记录表 refund
-- =============================================================
CREATE TABLE refund (
    id            BIGINT         NOT NULL AUTO_INCREMENT COMMENT '退票ID',
    order_id      BIGINT         NOT NULL COMMENT '订单ID',
    ticket_id     BIGINT         NULL COMMENT '船票ID',
    refund_amount DECIMAL(10,2)  NOT NULL COMMENT '退款金额',
    fee           DECIMAL(10,2)  NOT NULL DEFAULT 0 COMMENT '手续费',
    reason        VARCHAR(255)   NULL COMMENT '退票原因',
    refund_time   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '退票时间',
    operator_id   BIGINT         NULL COMMENT '操作人(乘客本人或售票员)',
    -- 区分两类资金流出：REFUND=真退票；RESCHEDULE_DIFF=改签退还的差价。
    -- 退票量/退票率只统计 REFUND，否则改签会被算成退票。
    biz_type      VARCHAR(20)    NOT NULL DEFAULT 'REFUND' COMMENT '业务类型 REFUND/RESCHEDULE_DIFF',
    PRIMARY KEY (id),
    KEY idx_order (order_id),
    KEY idx_type_time (biz_type, refund_time),
    CONSTRAINT fk_refund_order FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT fk_refund_ticket FOREIGN KEY (ticket_id) REFERENCES ticket(id),
    CONSTRAINT chk_refund_amount CHECK (refund_amount >= 0),
    CONSTRAINT chk_refund_biz_type CHECK (biz_type IN ('REFUND','RESCHEDULE_DIFF'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='退票记录表';

-- =============================================================
-- 10. 改签记录表 reschedule
-- =============================================================
CREATE TABLE reschedule (
    id              BIGINT        NOT NULL AUTO_INCREMENT COMMENT '改签ID',
    old_ticket_id   BIGINT        NOT NULL COMMENT '原票ID',
    new_ticket_id   BIGINT        NOT NULL COMMENT '新票ID',
    old_schedule_id BIGINT        NOT NULL COMMENT '原班次ID',
    new_schedule_id BIGINT        NOT NULL COMMENT '新班次ID',
    price_diff      DECIMAL(10,2) NOT NULL COMMENT '差价(正补负退)',
    reschedule_time DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '改签时间',
    PRIMARY KEY (id),
    KEY idx_old_ticket (old_ticket_id),
    CONSTRAINT fk_reschedule_old_ticket FOREIGN KEY (old_ticket_id) REFERENCES ticket(id),
    CONSTRAINT fk_reschedule_new_ticket FOREIGN KEY (new_ticket_id) REFERENCES ticket(id),
    CONSTRAINT fk_reschedule_old_schedule FOREIGN KEY (old_schedule_id) REFERENCES schedule(id),
    CONSTRAINT fk_reschedule_new_schedule FOREIGN KEY (new_schedule_id) REFERENCES schedule(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='改签记录表';

-- =============================================================
-- 11. 系统通知表 notification
-- 类型：SCHEDULE_CANCEL班次取消 / REFUND_SUCCESS退票成功 / RESCHEDULE改签成功
-- =============================================================
CREATE TABLE notification (
    id            BIGINT       NOT NULL AUTO_INCREMENT COMMENT '通知ID',
    user_id       BIGINT       NOT NULL COMMENT '接收用户ID',
    type          VARCHAR(30)  NOT NULL COMMENT '通知类型',
    title         VARCHAR(100) NOT NULL COMMENT '标题',
    content       VARCHAR(500) NOT NULL COMMENT '通知内容',
    is_read       TINYINT      NOT NULL DEFAULT 0 COMMENT '是否已读 0未读 1已读',
    create_time   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_user_read (user_id, is_read, create_time),
    CONSTRAINT fk_notification_user FOREIGN KEY (user_id) REFERENCES user(id),
    CONSTRAINT chk_notification_type CHECK (type IN ('SCHEDULE_CANCEL','REFUND_SUCCESS','RESCHEDULE')),
    CONSTRAINT chk_notification_read CHECK (is_read IN (0,1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统通知表';
