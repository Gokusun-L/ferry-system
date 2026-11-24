-- =============================================================
-- 1.1 现有库升级脚本
-- 仅执行一次；新建库直接使用 01_schema.sql，不需要本文件
-- 执行前请备份数据库
-- =============================================================

USE ferry_db;

-- 班次座位表增加选座锁归属用户
ALTER TABLE schedule_seat
    ADD COLUMN lock_user_id BIGINT NULL COMMENT '选座锁定用户ID' AFTER lock_time,
    ADD KEY idx_lock_user (lock_user_id),
    ADD CONSTRAINT fk_schedule_seat_lock_user FOREIGN KEY (lock_user_id) REFERENCES user(id);

-- 系统通知表
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
