-- =============================================================
-- 1.2 现有库升级脚本
-- 仅执行一次；新建库直接使用 01_schema.sql，不需要本文件
-- 执行前请备份数据库
--
-- 解决的问题：
--   改签此前复用 ticket.status='REFUNDED' 表示"旧票作废"，
--   与真实退票共用同一取值，导致按票状态聚合的统计（班次退票量）
--   把改签算成退票；同时改签退还的差价写入 refund 表时也没有类型标记，
--   会被退票量、退票金额、退票原因分布一并统计进去。
-- =============================================================

USE ferry_db;

-- -------------------------------------------------------------
-- 1) 船票状态增加 RESCHEDULED（改签作废），与 REFUNDED（退票）区分
-- -------------------------------------------------------------
ALTER TABLE ticket DROP CHECK chk_ticket_status;

ALTER TABLE ticket
    ADD CONSTRAINT chk_ticket_status
        CHECK (status IN ('UNPAID','PAID','CHECKED','REFUNDED','CANCELLED','RESCHEDULED'));

-- 历史数据回填：出现在 reschedule.old_ticket_id 里的 REFUNDED 票，实际是改签作废
UPDATE ticket t
    JOIN reschedule r ON r.old_ticket_id = t.id
SET t.status = 'RESCHEDULED'
WHERE t.status = 'REFUNDED';

-- -------------------------------------------------------------
-- 2) 退款表增加业务类型，区分"真退票"与"改签退还差价"
-- -------------------------------------------------------------
ALTER TABLE refund
    ADD COLUMN biz_type VARCHAR(20) NOT NULL DEFAULT 'REFUND'
        COMMENT '业务类型 REFUND=退票 / RESCHEDULE_DIFF=改签退还差价' AFTER operator_id,
    ADD KEY idx_type_time (biz_type, refund_time),
    ADD CONSTRAINT chk_refund_biz_type CHECK (biz_type IN ('REFUND','RESCHEDULE_DIFF'));

-- 历史数据回填：改签差价退款当时的原因固定写为"改签退还差价"
UPDATE refund
SET biz_type = 'RESCHEDULE_DIFF'
WHERE reason = '改签退还差价';

-- -------------------------------------------------------------
-- 3) 自检：改签作废票不应再被算作退票
-- -------------------------------------------------------------
SELECT 'ticket 各状态数量' AS check_item;
SELECT status, COUNT(*) AS cnt FROM ticket GROUP BY status;

SELECT '退款按业务类型' AS check_item;
SELECT biz_type, COUNT(*) AS cnt, SUM(refund_amount) AS amount FROM refund GROUP BY biz_type;
