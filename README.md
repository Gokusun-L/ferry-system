# 轮渡码头客运管理系统

基于 Spring Boot + MyBatis + MySQL 的完整数据库应用实践项目。

## 技术栈

| 层 | 组件 |
|---|---|
| 语言/运行时 | Java 17 (JDK 17+) |
| 框架 | Spring Boot 3.2.5 |
| 视图 | Thymeleaf 服务端渲染 |
| 数据访问 | MyBatis（Controller-Service-DAO 三层，DAO 用 XML Mapper） |
| 数据库 | MySQL 8.0 |
| 密码加密 | BCrypt（spring-security-crypto） |
| 报表导出 | EasyExcel |
| 权限控制 | 手写拦截器 + Session（非 Spring Security） |

## 项目结构

```
ferry-system/
├── sql/
│   ├── 01_schema.sql           # 建库建表（含全部约束）
│   ├── 02_data.sql             # 测试数据初始化
│   └── 03_migration_1_1.sql    # 旧库升级脚本（新增通知表与座位锁字段）
├── docs/                       # 设计文档、测试报告、分工表、报表插图
├── src/main/java/com/ferry/
│   ├── controller/       # 控制层
│   ├── service/          # 业务层（接口 + impl 实现）
│   ├── dao/              # 数据访问接口
│   ├── entity/           # 实体类
│   ├── config/           # 配置（拦截器、定时任务）
│   ├── interceptor/      # 登录拦截器
│   ├── common/           # 通用类（Result、BizException、LoginUser）
│   └── exception/        # 全局异常处理
├── src/main/resources/
│   ├── mapper/           # MyBatis XML Mapper
│   ├── templates/        # Thymeleaf 页面
│   ├── static/           # CSS/JS
│   └── application.yml   # 配置
└── pom.xml
```

## 运行步骤

### 1. 初始化数据库

用 DataGrip 连接 MySQL，依次执行：

```bash
source sql/01_schema.sql
source sql/02_data.sql
```

或者直接在 DataGrip 中打开这两个脚本逐个运行。

> 新环境只需执行 01、02；如果本机已有旧版 `ferry_db`，再执行 `sql/03_migration_1_1.sql` 升级。

### 2. 修改数据库连接

编辑 `src/main/resources/application.yml`：

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/ferry_db?...
    username: root      # 改成你的账号
    password: ""        # 改成你的密码
```

### 3. 启动

```bash
# 方式一：Maven 启动
mvn spring-boot:run

# 方式二：打包后运行
mvn package -DskipTests
java -jar target/ferry-system-1.0.0.jar
```

访问：http://localhost:8080

## 测试账号（密码均为 123456）

| 角色 | 用户名 | 说明 |
|---|---|---|
| 管理员 | admin | 全部功能 |
| 售票员 | seller1 / seller2 | 线下售票、检票、退票、个人业绩 |
| 乘客 | zhangsan / lisi / wangwu | 查询、购票、订单、退票、改签 |

## 功能模块

1. **用户与权限**：注册、登录、用户管理、个人中心、BCrypt 加密、失败5次锁定10分钟
2. **航线/船舶/班次**：CRUD、逻辑删除、班次状态流转、船舶时间冲突校验、批量生成班次、座位初始化
3. **售票与订单**：选座锁定5分钟、下单、模拟支付、超时释放、退票（分档手续费）、改签、售票员线下售票
4. **检票**：检票校验、检票记录、检票统计
5. **统计报表**：售票统计、上座率、收入、退票统计、EasyExcel 导出
6. **消息通知**：班次取消、退票成功、改签结果通知，顶部铃铛未读数轮询

## 界面设计（v3）

设计语言参考 Linear / Vercel 后台与 SaaS 分栏登录形态，纯 CSS + Thymeleaf 实现（无前端框架、无构建工具）：

- **布局**：深色近黑侧边栏（图标导航 + 激活态渐变高亮）+ 浅色毛玻璃顶栏（头像/角色/铃铛）
- **品牌色**：海洋蓝 → 青渐变（`#2563eb → #0ea5c4`），用于按钮、激活态、统计卡顶条
- **组件体系**：卡片头（渐变图标块 + 标题 + 描述）、状态胶囊（pill）、欢迎横幅（hero-banner）、快捷入口（quick-grid）、座位图例、弹窗动效
- **角色首页**：欢迎横幅 + 四个快捷入口卡片
- **登录/注册**：分栏布局——左侧表单、右侧品牌视觉区
- **插画资源**：`src/main/resources/static/images/` 下三张手绘 SVG 插画（`login-hero.svg` 登录页、`hero-banner.svg` 首页横幅、`empty-state.svg` 空状态），可离线使用

所有样式集中在 `src/main/resources/static/css/style.css`，页面结构以模板 `templates/layout.html` 为公共骨架。

## 考核要点实现对照

| 考核点 | 实现位置 |
|---|---|
| 主键/外键/唯一/非空/枚举/默认/检查约束 | `sql/01_schema.sql` |
| 逻辑删除 | route/ship/schedule 表 deleted 字段 |
| 事务与并发控制 | `OrderServiceImpl`（FOR UPDATE 原子锁定）|
| 座位锁定5分钟超时释放 | `ScheduledTask` + `ScheduleSeatDao.lock` |
| 并发购票控制 | `ScheduleSeatDao.lock` 的 `WHERE status='AVAILABLE'` 原子更新 |
| 取消班次自动退票 | `ScheduleServiceImpl.cancel` |
| 改签事务 | `OrderServiceImpl.reschedule`（退旧票+出新票+日志同一事务）|
| 聚合查询/分组统计 | `StatsMapper.xml`（GROUP BY/SUM/CASE WHEN/AVG）|
| 密码加密 | `UserServiceImpl`（BCryptPasswordEncoder）|
| 数据隔离 | 手写拦截器 + 角色判断 |

## 数据库表设计

11 张表：user、route、ship、schedule、ship_seat、schedule_seat、orders、ticket、refund、reschedule、notification。

ER 关系详见 `docs/ER模型与关系模式设计.md`。

## 两人分工与学习入口

完整分工见 [`docs/两人分工表.md`](docs/两人分工表.md)，按业务域纵向切分，每人负责两个模块，从建表到页面全包：

| 成员 | 负责模块 | 建议学习顺序 |
|---|---|---|
| 成员甲 | 用户权限与通知；航线、船舶、班次与座位 | 先看 `sql/01_schema.sql` 中 user/route/ship/schedule 相关表 → `UserServiceImpl` 登录与权限 → `ManageController`/`ScheduleServiceImpl` → `templates/admin/` 对应页面 |
| 成员乙 | 售票订单退改签；检票统计与导出 | 先看 orders/ticket/refund/reschedule 表 → `OrderServiceImpl` 下单/支付/退票/改签 → `StatsMapper.xml` 与 `StatsServiceImpl` → `templates/passenger/`、`seller/`、`admin/stats.html` |

协作者上手顺序：克隆仓库 → 导入 01、02 两个 SQL → 修改 `application.yml` 数据库账号密码 → `mvn spring-boot:run` → 用测试账号走一遍自己负责模块的主流程。
