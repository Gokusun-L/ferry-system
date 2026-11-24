# ER 模型与关系模式设计

## 一、需求分析

轮渡码头客运管理系统需要管理三类角色（管理员、售票员、乘客）围绕航线、船舶、班次、船票展开的购票、退票、检票、统计业务。

核心业务实体：
- **用户(User)**：系统使用者，分管理员/售票员/乘客三类
- **航线(Route)**：码头之间的客运线路
- **船舶(Ship)**：执行航线的运力
- **班次(Schedule)**：航线+船舶+时间的组合，售票的基本单位
- **座位(ShipSeat/ScheduleSeat)**：船舶的物理座位，及具体班次的座位状态
- **订单(Order)**：购票产生的交易记录
- **船票(Ticket)**：订单内的每一张票，对应一个座位
- **退票(Refund)**：退票产生的记录
- **改签(Reschedule)**：改签产生的记录

## 二、ER 模型

### 实体关系说明

1. **航线 1 : N 班次**：一条航线可产生多个班次，一个班次属于一条航线
2. **船舶 1 : N 班次**：一艘船执行多个班次，一个班次由一艘船执行
3. **船舶 1 : N 座位**：一艘船有多个座位
4. **班次 1 : N 班次座位**：一个班次有多个座位状态
5. **用户 1 : N 订单**：一个乘客可下多个订单
6. **订单 1 : N 船票**：一个订单含多张船票
7. **班次 1 : N 订单**：一个班次有多个订单
8. **订单 1 : N 退票**：一个订单可有退票记录
9. **船票 1 : 1 改签**：一张票可改签一次

### ER 图（文字描述）

```
[用户] 1 ──── N [订单] N ──── 1 [班次] N ──── 1 [航线]
                 │                    │
                 │ 1                  │ N
                 │                    │
                 N                    N
              [船票] 1 ── 1 [班次座位] N ── 1 [船舶] 1 ── N [船舶座位]
                 │
                 ├── 1:1 ── [改签]
                 └── 1:N ── [退票]
```

## 三、关系模式设计

### 1. user（用户表）
| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | BIGINT | PK, AUTO_INCREMENT | 用户ID |
| username | VARCHAR(50) | NOT NULL, UNIQUE | 用户名 |
| password | VARCHAR(100) | NOT NULL | 密码(BCrypt) |
| name | VARCHAR(50) | NOT NULL | 姓名 |
| phone | VARCHAR(20) | NOT NULL, UNIQUE | 手机号 |
| id_card | VARCHAR(18) | NULL | 身份证号 |
| role | VARCHAR(20) | NOT NULL, CHECK | 角色 |
| status | TINYINT | NOT NULL, DEFAULT 1, CHECK | 状态 |
| login_fail | INT | NOT NULL, DEFAULT 0 | 失败次数 |
| lock_until | DATETIME | NULL | 锁定时间 |

### 2. route（航线表）
| 字段 | 类型 | 约束 |
|---|---|---|
| id | BIGINT | PK |
| route_name | VARCHAR(50) | NOT NULL |
| depart_port | VARCHAR(50) | NOT NULL |
| arrive_port | VARCHAR(50) | NOT NULL |
| duration | INT | NOT NULL, CHECK(>0) |
| description | VARCHAR(255) | NULL |
| deleted | TINYINT | NOT NULL, DEFAULT 0（逻辑删除）|

### 3. ship（船舶表）
| 字段 | 类型 | 约束 |
|---|---|---|
| id | BIGINT | PK |
| ship_name | VARCHAR(50) | NOT NULL, UNIQUE |
| total_seats | INT | NOT NULL, CHECK(>0) |
| ship_type | VARCHAR(20) | NOT NULL, CHECK |
| description | VARCHAR(255) | NULL |
| deleted | TINYINT | NOT NULL, DEFAULT 0 |

### 4. schedule（班次表）
| 字段 | 类型 | 约束 |
|---|---|---|
| id | BIGINT | PK |
| route_id | BIGINT | FK → route.id |
| ship_id | BIGINT | FK → ship.id |
| depart_time | DATETIME | NOT NULL |
| arrive_time | DATETIME | NOT NULL, CHECK(>depart) |
| price | DECIMAL(10,2) | NOT NULL, CHECK(>=0) |
| status | VARCHAR(20) | NOT NULL, CHECK |
| sold_count | INT | NOT NULL, DEFAULT 0 |
| deleted | TINYINT | NOT NULL, DEFAULT 0 |

### 5. ship_seat（船舶座位表）
| 字段 | 类型 | 约束 |
|---|---|---|
| id | BIGINT | PK |
| ship_id | BIGINT | FK → ship.id, ON DELETE CASCADE |
| seat_no | VARCHAR(10) | NOT NULL, UNIQUE(ship_id, seat_no) |
| row_no | INT | NOT NULL, CHECK(>0) |
| col_no | CHAR(1) | NOT NULL |

### 6. schedule_seat（班次座位状态表）
| 字段 | 类型 | 约束 |
|---|---|---|
| id | BIGINT | PK |
| schedule_id | BIGINT | FK → schedule.id, ON DELETE CASCADE |
| seat_no | VARCHAR(10) | NOT NULL, UNIQUE(schedule_id, seat_no) |
| status | VARCHAR(20) | NOT NULL, CHECK(AVAILABLE/LOCKED/SOLD) |
| order_id | BIGINT | NULL |
| lock_time | DATETIME | NULL |

### 7. orders（订单表）
| 字段 | 类型 | 约束 |
|---|---|---|
| id | BIGINT | PK |
| order_no | VARCHAR(40) | NOT NULL, UNIQUE |
| user_id | BIGINT | FK → user.id |
| seller_id | BIGINT | FK → user.id |
| schedule_id | BIGINT | FK → schedule.id |
| total_amount | DECIMAL(10,2) | NOT NULL, CHECK(>=0) |
| status | VARCHAR(20) | NOT NULL, CHECK |
| channel | VARCHAR(20) | NOT NULL, CHECK(ONLINE/OFFLINE) |
| create_time | DATETIME | NOT NULL |
| pay_time | DATETIME | NULL |

### 8. ticket（船票表）
| 字段 | 类型 | 约束 |
|---|---|---|
| id | BIGINT | PK |
| ticket_no | VARCHAR(40) | NOT NULL, UNIQUE |
| order_id | BIGINT | FK → orders.id, ON DELETE CASCADE |
| schedule_id | BIGINT | FK → schedule.id |
| seat_no | VARCHAR(10) | NOT NULL |
| passenger_name | VARCHAR(50) | NOT NULL |
| id_card | VARCHAR(18) | NOT NULL |
| phone | VARCHAR(20) | NULL |
| price | DECIMAL(10,2) | NOT NULL, CHECK(>=0) |
| status | VARCHAR(20) | NOT NULL, CHECK (UNPAID / PAID / CHECKED / REFUNDED / CANCELLED / RESCHEDULED) |
| check_time | DATETIME | NULL |
| checker_id | BIGINT | FK → user.id |

### 9. refund（退票记录表）
| 字段 | 类型 | 约束 |
|---|---|---|
| id | BIGINT | PK |
| order_id | BIGINT | FK → orders.id |
| ticket_id | BIGINT | FK → ticket.id |
| refund_amount | DECIMAL(10,2) | NOT NULL, CHECK(>=0) |
| fee | DECIMAL(10,2) | NOT NULL, DEFAULT 0 |
| reason | VARCHAR(255) | NULL |
| refund_time | DATETIME | NOT NULL |
| operator_id | BIGINT | NULL |
| biz_type | VARCHAR(20) | NOT NULL, DEFAULT 'REFUND', CHECK (REFUND / RESCHEDULE_DIFF) |

> `biz_type` 用于区分两类资金流出：`REFUND` 是真正的退票，`RESCHEDULE_DIFF` 是改签时退还的差价。
> 退票量、退票率、退票原因分布等指标只统计 `REFUND`，否则改签会被误算为退票。

### 10. reschedule（改签记录表）
| 字段 | 类型 | 约束 |
|---|---|---|
| id | BIGINT | PK |
| old_ticket_id | BIGINT | FK → ticket.id |
| new_ticket_id | BIGINT | FK → ticket.id |
| old_schedule_id | BIGINT | FK → schedule.id |
| new_schedule_id | BIGINT | FK → schedule.id |
| price_diff | DECIMAL(10,2) | NOT NULL |
| reschedule_time | DATETIME | NOT NULL |

## 四、设计理由

### 1. 为什么座位拆成两张表（ship_seat + schedule_seat）？

任务书明确要求"两层座位信息"：
- **船舶座位(ship_seat)**：描述一艘船有哪些座位（静态，船不变座位就不变）
- **班次座位(schedule_seat)**：描述某班次各座位状态（动态，每个班次独立）

如果合并成一张表，则每个班次都要重复存储船舶的座位定义，且船座位调整时需同步所有班次。拆成两层符合"定义"与"状态"分离的第三范式，也避免了数据冗余。

### 2. 为什么用逻辑删除（deleted 字段）而非物理删除？

任务书要求"对已产生有效业务数据的航线、船舶、班次应合理删除限制或逻辑删除"。物理删除会破坏：
- 历史订单/船票的外键引用完整性
- 统计报表的历史数据

逻辑删除保留数据，仅标记不可见，兼顾业务完整性与历史可追溯。

### 3. 为什么订单和船票分两张表？

一个订单可含多张船票（最多5张），是典型的 1:N 关系。拆开后：
- 每张票可独立检票、退票、改签（状态独立流转）
- 支持"一人一班次一票"按身份证号在 ticket 表查询

### 4. 为什么班次表冗余 sold_count 字段？

`sold_count`（已售座位数）是高频查询字段（班次列表显示余票）。若不冗余，每次列表都要 `COUNT(schedule_seat WHERE status='SOLD')`，班次多时性能差。冗余后用 UPDATE 维护，查询 O(1)。这是典型的"以空间换时间"的读多写少优化。

### 5. 并发控制如何保证？

关键在 `schedule_seat.lock` 的 SQL：
```sql
UPDATE schedule_seat SET status='LOCKED' ...
WHERE schedule_id=? AND seat_no=? AND status='AVAILABLE'
```
这条 UPDATE 的 `WHERE status='AVAILABLE'` 条件配合 InnoDB 行级锁，保证并发时只有一个事务能成功将座位从 AVAILABLE 改为 LOCKED，其他事务受影响行数为 0，从而阻止重复售票。
