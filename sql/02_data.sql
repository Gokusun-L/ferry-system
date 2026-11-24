-- =============================================================
-- 测试数据初始化脚本
-- 密码统一为 123456 的 BCrypt 加密值（下面账号均可用 123456 登录）
-- =============================================================
-- 强制会话字符集为 utf8mb4（Windows 命令行客户端默认 gbk 会插入乱码/超长）
SET NAMES utf8mb4;
USE ferry_db;

-- 用户（BCrypt("123456")）
INSERT INTO user (username, password, name, phone, id_card, role, status) VALUES
('admin',   '$2a$10$g9zjMnEJYGu1SmeFW38YGeekxNoOVs5uvXFP7lmoEtGKBlhQJy7u6', '系统管理员', '13800000001', NULL, 'ADMIN', 1),
('seller1', '$2a$10$g9zjMnEJYGu1SmeFW38YGeekxNoOVs5uvXFP7lmoEtGKBlhQJy7u6', '售票员小李', '13800000002', NULL, 'SELLER', 1),
('seller2', '$2a$10$g9zjMnEJYGu1SmeFW38YGeekxNoOVs5uvXFP7lmoEtGKBlhQJy7u6', '售票员小王', '13800000003', NULL, 'SELLER', 1),
('zhangsan', '$2a$10$g9zjMnEJYGu1SmeFW38YGeekxNoOVs5uvXFP7lmoEtGKBlhQJy7u6', '张三', '13900000001', '440100199001011234', 'PASSENGER', 1),
('lisi', '$2a$10$g9zjMnEJYGu1SmeFW38YGeekxNoOVs5uvXFP7lmoEtGKBlhQJy7u6', '李四', '13900000002', '440100199202022345', 'PASSENGER', 1),
('wangwu', '$2a$10$g9zjMnEJYGu1SmeFW38YGeekxNoOVs5uvXFP7lmoEtGKBlhQJy7u6', '王五', '13900000003', '440100199303033456', 'PASSENGER', 1);

-- 航线
INSERT INTO route (route_name, depart_port, arrive_port, duration, description) VALUES
('市区-海岛东线', '市区码头', '海岛码头', 60, '市区至海岛快速航线'),
('市区-海岛西线', '市区码头', '西海岸码头', 90, '市区至西海岸航线'),
('海岛-市区东线', '海岛码头', '市区码头', 60, '海岛返回市区航线'),
('北港-南港', '北港码头', '南港码头', 120, '跨海长途航线');

-- 船舶
INSERT INTO ship (ship_name, total_seats, ship_type, description) VALUES
('海鸥号', 20, 'HIGHSPEED', '高速客船，5排×4列'),
('白鹭号', 24, 'NORMAL', '普通客船，6排×4列'),
('金龙号', 30, 'LUXURY', '豪华客船，豪华舱');

-- 船舶座位（海鸥号 5排×A/B/C/D）
INSERT INTO ship_seat (ship_id, seat_no, row_no, col_no) VALUES
(1,'1A',1,'A'),(1,'1B',1,'B'),(1,'1C',1,'C'),(1,'1D',1,'D'),
(1,'2A',2,'A'),(1,'2B',2,'B'),(1,'2C',2,'C'),(1,'2D',2,'D'),
(1,'3A',3,'A'),(1,'3B',3,'B'),(1,'3C',3,'C'),(1,'3D',3,'D'),
(1,'4A',4,'A'),(1,'4B',4,'B'),(1,'4C',4,'C'),(1,'4D',4,'D'),
(1,'5A',5,'A'),(1,'5B',5,'B'),(1,'5C',5,'C'),(1,'5D',5,'D');

-- 白鹭号 6排×A/B/C/D
INSERT INTO ship_seat (ship_id, seat_no, row_no, col_no) VALUES
(2,'1A',1,'A'),(2,'1B',1,'B'),(2,'1C',1,'C'),(2,'1D',1,'D'),
(2,'2A',2,'A'),(2,'2B',2,'B'),(2,'2C',2,'C'),(2,'2D',2,'D'),
(2,'3A',3,'A'),(2,'3B',3,'B'),(2,'3C',3,'C'),(2,'3D',3,'D'),
(2,'4A',4,'A'),(2,'4B',4,'B'),(2,'4C',4,'C'),(2,'4D',4,'D'),
(2,'5A',5,'A'),(2,'5B',5,'B'),(2,'5C',5,'C'),(2,'5D',5,'D'),
(2,'6A',6,'A'),(2,'6B',6,'B'),(2,'6C',6,'C'),(2,'6D',6,'D');

-- 班次（发船时间基于今天动态生成，方便演示）
INSERT INTO schedule (route_id, ship_id, depart_time, arrive_time, price, status) VALUES
(1, 1, DATE_ADD(CURDATE(), INTERVAL 1 DAY) + INTERVAL 8 HOUR,  DATE_ADD(CURDATE(), INTERVAL 1 DAY) + INTERVAL 9 HOUR,  50.00, 'SELLING'),
(1, 1, DATE_ADD(CURDATE(), INTERVAL 1 DAY) + INTERVAL 14 HOUR, DATE_ADD(CURDATE(), INTERVAL 1 DAY) + INTERVAL 15 HOUR, 50.00, 'SELLING'),
(2, 2, DATE_ADD(CURDATE(), INTERVAL 2 DAY) + INTERVAL 9 HOUR,  DATE_ADD(CURDATE(), INTERVAL 2 DAY) + INTERVAL 10 HOUR + INTERVAL 30 MINUTE, 80.00, 'SELLING'),
(4, 3, DATE_ADD(CURDATE(), INTERVAL 3 DAY) + INTERVAL 10 HOUR, DATE_ADD(CURDATE(), INTERVAL 3 DAY) + INTERVAL 12 HOUR, 120.00, 'PENDING');

-- 为每个班次初始化座位状态
INSERT INTO schedule_seat (schedule_id, seat_no, status)
SELECT s.id, ss.seat_no, 'AVAILABLE'
FROM schedule s
JOIN ship_seat ss ON ss.ship_id = s.ship_id;
