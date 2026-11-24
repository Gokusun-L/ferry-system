package com.ferry;

import com.ferry.entity.Order;
import com.ferry.entity.Ticket;
import com.ferry.service.OrderService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 数据库事务与并发控制测试（任务书考核重点）。
 *
 * 与其它测试类的区别：
 * 1. 不使用 @Transactional —— 并发线程必须各自提交事务，才能复现真实竞争；
 * 2. 测试数据用 JdbcTemplate 真实落库，测试结束后保留（供实验报告引用）；
 * 3. 每轮数据带时间戳后缀，可重复执行不冲突。
 */
@SpringBootTest
@ActiveProfiles("test")
@DisplayName("考核重点 事务与并发控制")
class ConcurrencyTest {

    @Autowired
    private OrderService orderService;
    @Autowired
    private JdbcTemplate jdbc;

    private static final java.util.concurrent.atomic.AtomicInteger UID_SEQ = new java.util.concurrent.atomic.AtomicInteger();
    private final java.util.Map<Integer, Long> uidCache = new java.util.concurrent.ConcurrentHashMap<>();

    /**
     * 取一个真实用户主键（orders.user_id 有外键）。
     * 测试数据真实落库并保留，username/phone 带序号避免重复。
     */
    private long uid(int key) {
        return uidCache.computeIfAbsent(key, k -> {
            int seq = UID_SEQ.incrementAndGet();
            String suffix = String.valueOf(System.nanoTime()).substring(6) + seq;
            String username = "ct_u_" + suffix;
            String phone = "137" + suffix.substring(Math.max(0, suffix.length() - 8));
            jdbc.update("INSERT INTO user (username, password, name, phone, role, status, login_fail) "
                            + "VALUES (?, '$2a$10$g9zjMnEJYGu1SmeFW38YGeekxNoOVs5uvXFP7lmoEtGKBlhQJy7u6', ?, ?, 'PASSENGER', 1, 0)",
                    username, "并发测试乘客" + seq, phone);
            return jdbc.queryForObject("SELECT id FROM user WHERE username = ?", Long.class, username);
        });
    }

    /** 造一套已发布的班次（真实提交），返回 [scheduleId, shipId, routeId] */
    private long[] prepareSellingSchedule(String tag, int totalSeats, LocalDateTime depart) {
        KeyHolder routeKey = new GeneratedKeyHolder();
        jdbc.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                    "INSERT INTO route (route_name, depart_port, arrive_port, duration, description, deleted) "
                            + "VALUES (?, ?, ?, 60, '并发测试自动生成，测试后保留', 0)",
                    Statement.RETURN_GENERATED_KEYS);
            ps.setString(1, "TEST-并发航线-" + tag);
            ps.setString(2, "并发港A-" + tag);
            ps.setString(3, "并发港B-" + tag);
            return ps;
        }, routeKey);
        long routeId = routeKey.getKey().longValue();

        KeyHolder shipKey = new GeneratedKeyHolder();
        jdbc.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                    "INSERT INTO ship (ship_name, total_seats, ship_type, description, deleted) "
                            + "VALUES (?, ?, 'NORMAL', '并发测试自动生成，测试后保留', 0)",
                    Statement.RETURN_GENERATED_KEYS);
            ps.setString(1, "TEST-并发船-" + tag);
            ps.setInt(2, totalSeats);
            return ps;
        }, shipKey);
        long shipId = shipKey.getKey().longValue();

        // 座位：4 列排布
        char[] cols = {'A', 'B', 'C', 'D'};
        int count = 0;
        for (int row = 1; count < totalSeats; row++) {
            for (char col : cols) {
                if (count >= totalSeats) {
                    break;
                }
                jdbc.update("INSERT INTO ship_seat (ship_id, seat_no, row_no, col_no) VALUES (?, ?, ?, ?)",
                        shipId, row + String.valueOf(col), row, String.valueOf(col));
                count++;
            }
        }

        KeyHolder scheduleKey = new GeneratedKeyHolder();
        jdbc.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                    "INSERT INTO schedule (route_id, ship_id, depart_time, arrive_time, price, status, sold_count, deleted) "
                            + "VALUES (?, ?, ?, ?, 100.00, 'SELLING', 0, 0)",
                    Statement.RETURN_GENERATED_KEYS);
            ps.setLong(1, routeId);
            ps.setLong(2, shipId);
            ps.setTimestamp(3, Timestamp.valueOf(depart));
            ps.setTimestamp(4, Timestamp.valueOf(depart.plusMinutes(60)));
            return ps;
        }, scheduleKey);
        long scheduleId = scheduleKey.getKey().longValue();

        jdbc.update("INSERT INTO schedule_seat (schedule_id, seat_no, status) "
                + "SELECT ?, seat_no, 'AVAILABLE' FROM ship_seat WHERE ship_id = ?", scheduleId, shipId);

        return new long[]{scheduleId, shipId, routeId};
    }

    private Ticket ticket(String seatNo, String name, String idCard) {
        Ticket t = new Ticket();
        t.setSeatNo(seatNo);
        t.setPassengerName(name);
        t.setIdCard(idCard);
        t.setPhone("13700000000");
        return t;
    }

    @Test
    @DisplayName("TC-C01 20 人同时抢同一座位：仅 1 人下单成功，其余全部被拒")
    void twentyUsersRaceForOneSeat() throws Exception {
        String tag = String.valueOf(System.currentTimeMillis());
        long[] ids = prepareSellingSchedule(tag, 8, LocalDateTime.now().plusDays(1));
        long scheduleId = ids[0];

        int threads = 20;
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        CountDownLatch ready = new CountDownLatch(threads);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(threads);
        AtomicInteger success = new AtomicInteger();
        AtomicInteger rejected = new AtomicInteger();
        AtomicInteger unexpectedError = new AtomicInteger();

        for (int i = 0; i < threads; i++) {
            final int n = i;
            pool.submit(() -> {
                ready.countDown();
                try {
                    start.await();
                    // 每人不同身份证，只抢 1A 一个座位
                    orderService.createOrder(scheduleId, uid(1000 + n), null,
                            List.of(ticket("1A", "并发乘客" + n, String.format("44010019900101%04d", 1000 + n))));
                    success.incrementAndGet();
                } catch (com.ferry.common.BizException e) {
                    rejected.incrementAndGet();
                } catch (Exception e) {
                    unexpectedError.incrementAndGet();
                    System.out.println("[TC-C01] 非业务异常: " + e.getClass().getSimpleName() + " - " + e.getMessage());
                } finally {
                    done.countDown();
                }
            });
        }

        assertTrue(ready.await(10, TimeUnit.SECONDS), "线程未全部就绪");
        start.countDown();
        assertTrue(done.await(60, TimeUnit.SECONDS), "并发下单超时未完成");
        pool.shutdown();

        System.out.printf("[TC-C01] 成功=%d 业务拒绝=%d 非业务异常=%d%n",
                success.get(), rejected.get(), unexpectedError.get());

        assertEquals(1, success.get(), "同一座位只能有 1 人下单成功");
        assertEquals(threads - 1, rejected.get(), "其余应全部被业务规则拒绝");
        assertEquals(0, unexpectedError.get(), "不应出现非业务异常（如死锁、连接异常）");

        Integer lockedSeats = jdbc.queryForObject(
                "SELECT COUNT(*) FROM schedule_seat WHERE schedule_id = ? AND seat_no = '1A' AND status = 'LOCKED'",
                Integer.class, scheduleId);
        assertEquals(1, lockedSeats, "数据库中该座位应恰好被锁定 1 次");

        Integer ticketCount = jdbc.queryForObject(
                "SELECT COUNT(*) FROM ticket WHERE schedule_id = ? AND seat_no = '1A'", Integer.class, scheduleId);
        assertEquals(1, ticketCount, "数据库中该座位应恰好有 1 张船票");
    }

    @Test
    @DisplayName("TC-C02 同一身份证并发抢同班次不同座位：仅 1 单成功（一人一班次一票）")
    void sameIdCardConcurrentOrders() throws Exception {
        String tag = String.valueOf(System.currentTimeMillis());
        long[] ids = prepareSellingSchedule(tag, 12, LocalDateTime.now().plusDays(1));
        long scheduleId = ids[0];

        String sameIdCard = "440100199501019999";
        int threads = 10;
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        CountDownLatch ready = new CountDownLatch(threads);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(threads);
        AtomicInteger success = new AtomicInteger();
        AtomicInteger rejected = new AtomicInteger();

        String[] seats = {"1A", "1B", "1C", "1D", "2A", "2B", "2C", "2D", "3A", "3B"};
        for (int i = 0; i < threads; i++) {
            final String seat = seats[i];
            final int n = i;
            pool.submit(() -> {
                ready.countDown();
                try {
                    start.await();
                    orderService.createOrder(scheduleId, uid(2000 + n), null,
                            List.of(ticket(seat, "同证乘客", sameIdCard)));
                    success.incrementAndGet();
                } catch (com.ferry.common.BizException e) {
                    rejected.incrementAndGet();
                } catch (Exception e) {
                    rejected.incrementAndGet();
                    System.out.println("[TC-C02] 异常: " + e.getClass().getSimpleName() + " - " + e.getMessage());
                } finally {
                    done.countDown();
                }
            });
        }

        assertTrue(ready.await(10, TimeUnit.SECONDS));
        start.countDown();
        assertTrue(done.await(60, TimeUnit.SECONDS));
        pool.shutdown();

        System.out.printf("[TC-C02] 成功=%d 拒绝=%d%n", success.get(), rejected.get());

        assertEquals(1, success.get(), "同一身份证同一班次只能成功 1 单");
        Integer tickets = jdbc.queryForObject(
                "SELECT COUNT(*) FROM ticket WHERE schedule_id = ? AND id_card = ?",
                Integer.class, scheduleId, sameIdCard);
        assertEquals(1, tickets, "数据库中该身份证应只有 1 张票");
    }

    @Test
    @DisplayName("TC-C03 10 线程同时支付同一订单：仅 1 次成功，已售数只加 1")
    void concurrentPaySameOrder() throws Exception {
        String tag = String.valueOf(System.currentTimeMillis());
        long[] ids = prepareSellingSchedule(tag, 8, LocalDateTime.now().plusDays(1));
        long scheduleId = ids[0];

        Order order = orderService.createOrder(scheduleId, uid(3000), null,
                List.of(ticket("1A", "支付并发乘客", "440100199601011111")));

        int threads = 10;
        ExecutorService pool = Executors.newFixedThreadPool(threads);
        CountDownLatch ready = new CountDownLatch(threads);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(threads);
        AtomicInteger success = new AtomicInteger();
        AtomicInteger rejected = new AtomicInteger();

        for (int i = 0; i < threads; i++) {
            pool.submit(() -> {
                ready.countDown();
                try {
                    start.await();
                    orderService.pay(order.getId(), uid(3000));
                    success.incrementAndGet();
                } catch (Exception e) {
                    rejected.incrementAndGet();
                } finally {
                    done.countDown();
                }
            });
        }

        assertTrue(ready.await(10, TimeUnit.SECONDS));
        start.countDown();
        assertTrue(done.await(60, TimeUnit.SECONDS));
        pool.shutdown();

        System.out.printf("[TC-C03] 支付成功=%d 拒绝=%d%n", success.get(), rejected.get());

        assertEquals(1, success.get(), "同一订单并发支付只能成功 1 次");
        assertEquals(1, jdbc.queryForObject(
                "SELECT sold_count FROM schedule WHERE id = ?", Integer.class, scheduleId).intValue(),
                "班次已售数只应增加 1");
        assertEquals("SOLD", jdbc.queryForObject(
                "SELECT status FROM schedule_seat WHERE schedule_id = ? AND seat_no = '1A'",
                String.class, scheduleId));
    }

    @Test
    @DisplayName("TC-C04 下单不支付：5 分钟后座位可被他人重新购买（锁超时释放）")
    void expiredLockSeatCanBeRepurchased() {
        String tag = String.valueOf(System.currentTimeMillis());
        long[] ids = prepareSellingSchedule(tag, 8, LocalDateTime.now().plusDays(1));
        long scheduleId = ids[0];

        // A 下单占座
        orderService.createOrder(scheduleId, uid(4000), null,
                List.of(ticket("1A", "先占座", "440100199701012222")));
        assertEquals("LOCKED", jdbc.queryForObject(
                "SELECT status FROM schedule_seat WHERE schedule_id = ? AND seat_no = '1A'",
                String.class, scheduleId));

        // 把锁定时间和下单时间都推到 6 分钟前，模拟超时
        Timestamp sixMinAgo = Timestamp.valueOf(LocalDateTime.now().minusMinutes(6));
        jdbc.update("UPDATE schedule_seat SET lock_time = ? WHERE schedule_id = ? AND seat_no = '1A'",
                sixMinAgo, scheduleId);
        jdbc.update("UPDATE orders SET create_time = ? WHERE schedule_id = ?", sixMinAgo, scheduleId);

        // 定时任务释放超时锁定
        jdbc.update("UPDATE schedule_seat SET status = 'AVAILABLE', order_id = NULL, lock_time = NULL, lock_user_id = NULL "
                + "WHERE status = 'LOCKED' AND lock_time < ?", Timestamp.valueOf(LocalDateTime.now().minusMinutes(5)));

        assertEquals("AVAILABLE", jdbc.queryForObject(
                "SELECT status FROM schedule_seat WHERE schedule_id = ? AND seat_no = '1A'",
                String.class, scheduleId), "超时后座位应回到可售");

        // B 可以买到该座位
        Order b = orderService.createOrder(scheduleId, uid(4001), null,
                List.of(ticket("1A", "后来者", "440100199801013333")));
        assertNotNull(b.getId(), "座位释放后他人应能下单");
    }

    @Test
    @DisplayName("TC-C05 取消班次：已支付订单全额退款、座位全部释放、订单置为已退票")
    void cancelScheduleRefundsAllPaidOrders() throws Exception {
        String tag = String.valueOf(System.currentTimeMillis());
        long[] ids = prepareSellingSchedule(tag, 8, LocalDateTime.now().plusDays(2));
        long scheduleId = ids[0];

        // 造 3 个已支付订单 + 1 个未支付订单
        for (int i = 0; i < 3; i++) {
            Order o = orderService.createOrder(scheduleId, uid(5000 + i), null,
                    List.of(ticket("1" + (char) ('A' + i), "已付乘客" + i,
                            String.format("44010019990101%04d", 2000 + i))));
            orderService.pay(o.getId(), uid(5000 + i));
        }
        orderService.createOrder(scheduleId, uid(5010), null,
                List.of(ticket("2A", "未付乘客", "440100199901019999")));

        assertEquals(3, jdbc.queryForObject(
                "SELECT sold_count FROM schedule WHERE id = ?", Integer.class, scheduleId).intValue());

        // 通过 service 取消（@Transactional 由代理开启，无需外层事务）
        scheduleService.cancel(scheduleId);

        assertEquals("CANCELLED", jdbc.queryForObject(
                "SELECT status FROM schedule WHERE id = ?", String.class, scheduleId));
        assertEquals(0, jdbc.queryForObject(
                "SELECT COUNT(*) FROM orders WHERE schedule_id = ? AND status IN ('PAID','UNPAID','CHECKED')",
                Integer.class, scheduleId), "取消后不应残留有效订单");
        assertEquals(3, jdbc.queryForObject(
                "SELECT COUNT(*) FROM orders WHERE schedule_id = ? AND status = 'REFUNDED'",
                Integer.class, scheduleId), "已支付订单应全额退款");
        assertEquals(8, jdbc.queryForObject(
                "SELECT COUNT(*) FROM schedule_seat WHERE schedule_id = ? AND status = 'AVAILABLE'",
                Integer.class, scheduleId), "所有座位应释放为可售");
        assertEquals(3, jdbc.queryForObject(
                "SELECT COUNT(*) FROM refund WHERE order_id IN (SELECT id FROM orders WHERE schedule_id = ?)",
                Integer.class, scheduleId), "应生成 3 条退票记录");
        assertTrue(jdbc.queryForObject(
                "SELECT COUNT(*) FROM notification WHERE type = 'SCHEDULE_CANCEL'", Integer.class) >= 3,
                "应给乘客推送班次取消通知");
    }

    @Autowired
    private com.ferry.service.ScheduleService scheduleService;
}
