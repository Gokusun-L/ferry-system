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
│   ├── 01_schema.sql     # 建库建表（含全部约束）
│   └── 02_data.sql       # 测试数据初始化
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

### 2. 修改数据库连接

编辑 `src/main/resources/application.yml`：

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/ferry_db?...
    username: root      # 改成你的账号
    password: root      # 改成你的密码
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

10 张表：user、route、ship、schedule、ship_seat、schedule_seat、orders、ticket、refund、reschedule。

ER 关系详见 `docs/ER模型与关系模式设计.md`。
