package com.ferry;

import com.ferry.common.BizException;
import com.ferry.dao.OrderDao;
import com.ferry.dao.RefundDao;
import com.ferry.dao.RescheduleDao;
import com.ferry.dao.ScheduleDao;
import com.ferry.dao.ScheduleSeatDao;
import com.ferry.dao.TicketDao;
import com.ferry.entity.Order;
import com.ferry.entity.Route;
import com.ferry.entity.Schedule;
import com.ferry.entity.ScheduleSeat;
import com.ferry.entity.Ship;
import com.ferry.entity.Ticket;
import com.ferry.service.OrderService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;

import java.math.BigDecimal;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 模块三测试：售票、订单、支付、退票、改签、检票。
 * 重点覆盖任务书"数据库事务与并发控制"的状态校验分支。
 */
@DisplayName("模块三 售票与订单")
class OrderServiceTest extends BaseIntegrationTest {

    @Autowired
    private OrderService orderService;
    @Autowired
    private OrderDao orderDao;
    @Autowired
    private TicketDao ticketDao;
    @Autowired
    private ScheduleDao scheduleDao;
    @Autowired
    private ScheduleSeatDao scheduleSeatDao;
    @Autowired
    private RefundDao refundDao;
    @Autowired
    private RescheduleDao rescheduleDao;
    @Autowired
    private JdbcTemplate jdbcTemplate;

    /** 真实用户主键（订单 user_id/seller_id 有外键，不能用假ID） */
    private Long u1;
    private Long u2;
    private Long u3;
    private Long checkerId;

    @BeforeEach
    void createUsers() {
        u1 = newPassenger();
        u2 = newPassenger();
        u3 = newPassenger();
        checkerId = u2; // 检票员复用其中一个真实用户
    }

    /** 直接改下单时间，用于构造"支付超时"场景（不属于生产接口，仅测试造数） */
    private void backdateOrder(Long orderId, int minutes) {
        jdbcTemplate.update("UPDATE orders SET create_time = ? WHERE id = ?",
                Timestamp.valueOf(LocalDateTime.now().minusMinutes(minutes)), orderId);
    }

    private Ticket ticket(String seatNo, String name, String idCard, String phone) {
        Ticket t = new Ticket();
        t.setSeatNo(seatNo);
        t.setPassengerName(name);
        t.setIdCard(idCard);
        t.setPhone(phone);
        return t;
    }

    private String seatStatus(Long scheduleId, String seatNo) {
        ScheduleSeat seat = scheduleSeatDao.findByScheduleAndSeat(scheduleId, seatNo);
        return seat == null ? null : seat.getStatus();
    }

    // ===== 下单 =====

    @Test
    @DisplayName("TC-O01 正常下单：订单待支付、座位锁定、船票待支付、金额=票价×张数")
    void createOrder_locksSeatsAndComputesAmount() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "50.00");

        Order order = orderService.createOrder(s.getId(), u1, null, List.of(
                ticket("1A", "张三", "440100199001010001", "13711110001"),
                ticket("1B", "李四", "440100199001010002", "13711110002")));

        assertNotNull(order.getId());
        assertTrue(order.getOrderNo().startsWith("O"));
        assertEquals("UNPAID", order.getStatus());
        assertEquals("ONLINE", order.getChannel());
        assertEquals(0, new BigDecimal("100.00").compareTo(order.getTotalAmount()), "2张×50 应为100");

        assertEquals("LOCKED", seatStatus(s.getId(), "1A"));
        assertEquals("LOCKED", seatStatus(s.getId(), "1B"));
        assertTrue(ticketDao.listByOrder(order.getId()).stream().allMatch(t -> "UNPAID".equals(t.getStatus())));
    }

    @Test
    @DisplayName("TC-O02 下单失败：一人一班次一票（同一身份证重复购买）")
    void createOrder_rejectsDuplicateIdCardInSameSchedule() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "50.00");

        orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));

        BizException ex = assertThrows(BizException.class, () -> orderService.createOrder(
                s.getId(), u1, null,
                List.of(ticket("1B", "张三", "440100199001010001", "13711110001"))));
        assertTrue(ex.getMessage().contains("已购票"), "实际：" + ex.getMessage());
    }

    @Test
    @DisplayName("TC-O03 下单失败：超过 5 张、座位重复、身份证格式错误、座位已被占用")
    void createOrder_validationBranches() {
        Route r = newRoute();
        Ship ship = newShip(12);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "30.00");

        // 超过5张
        List<Ticket> six = List.of(
                ticket("1A", "甲", "440100199001010011", "13711110011"),
                ticket("1B", "乙", "440100199001010012", "13711110012"),
                ticket("1C", "丙", "440100199001010013", "13711110013"),
                ticket("1D", "丁", "440100199001010014", "13711110014"),
                ticket("2A", "戊", "440100199001010015", "13711110015"),
                ticket("2B", "己", "440100199001010016", "13711110016"));
        BizException tooMany = assertThrows(BizException.class,
                () -> orderService.createOrder(s.getId(), u1, null, six));
        assertTrue(tooMany.getMessage().contains("最多购买5张"), "实际：" + tooMany.getMessage());

        // 座位重复
        BizException dupSeat = assertThrows(BizException.class, () -> orderService.createOrder(
                s.getId(), u1, null, List.of(
                        ticket("3A", "甲", "440100199001010021", "13711110021"),
                        ticket("3A", "乙", "440100199001010022", "13711110022"))));
        assertTrue(dupSeat.getMessage().contains("座位号重复"), "实际：" + dupSeat.getMessage());

        // 身份证格式错误
        BizException badId = assertThrows(BizException.class, () -> orderService.createOrder(
                s.getId(), u1, null, List.of(ticket("3B", "甲", "123", "13711110023"))));
        assertTrue(badId.getMessage().contains("身份证号格式"), "实际：" + badId.getMessage());

        // 手机号格式错误
        BizException badPhone = assertThrows(BizException.class, () -> orderService.createOrder(
                s.getId(), u1, null, List.of(ticket("3C", "甲", "440100199001010031", "999"))));
        assertTrue(badPhone.getMessage().contains("手机号格式"), "实际：" + badPhone.getMessage());

        // 座位已被他人锁定
        orderService.createOrder(s.getId(), u2, null,
                List.of(ticket("3A", "占位", "440100199001010041", "13711110041")));
        BizException occupied = assertThrows(BizException.class, () -> orderService.createOrder(
                s.getId(), u3, null, List.of(ticket("3A", "抢座", "440100199001010042", "13711110042"))));
        assertTrue(occupied.getMessage().contains("被他人锁定"), "实际：" + occupied.getMessage());
    }

    // ===== 支付 =====

    @Test
    @DisplayName("TC-O04 支付成功：订单已支付、座位已售、班次已售数+1、票状态已支付")
    void pay_marksSeatSoldAndIncrementsCount() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "50.00");

        Order order = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));
        orderService.pay(order.getId(), u1);

        Order paid = orderDao.findById(order.getId());
        assertEquals("PAID", paid.getStatus());
        assertNotNull(paid.getPayTime(), "支付时间应写入");
        assertEquals("SOLD", seatStatus(s.getId(), "1A"));
        assertEquals(1, scheduleDao.findById(s.getId()).getSoldCount().intValue(), "班次已售数应为1");
        assertEquals("PAID", ticketDao.listByOrder(order.getId()).get(0).getStatus());
    }

    @Test
    @DisplayName("TC-O05 支付失败：非本人订单不可支付")
    void pay_rejectsNonOwner() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "50.00");

        Order order = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));

        BizException notOwner = assertThrows(BizException.class, () -> orderService.pay(order.getId(), 999L));
        assertTrue(notOwner.getMessage().contains("无权"), "实际：" + notOwner.getMessage());
    }

    @Test
    @DisplayName("TC-O06 支付失败：超过5分钟支付时限")
    void pay_rejectsTimeout() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "50.00");

        Order order = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));

        // 把下单时间改到 10 分钟前，再首次读取订单（避免 MyBatis 一级缓存返回旧值）
        backdateOrder(order.getId(), 10);
        BizException timeout = assertThrows(BizException.class, () -> orderService.pay(order.getId(), u1));
        assertTrue(timeout.getMessage().contains("超时"), "实际：" + timeout.getMessage());
    }

    @Test
    @DisplayName("TC-O07 支付失败：已支付订单不可重复支付")
    void pay_rejectsDuplicate() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "50.00");

        Order order = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));
        orderService.pay(order.getId(), u1);

        BizException again = assertThrows(BizException.class, () -> orderService.pay(order.getId(), u1));
        assertTrue(again.getMessage().contains("状态异常"), "实际：" + again.getMessage());
    }

    @Test
    @DisplayName("TC-O08 取消订单：座位从锁定释放为可售，票与订单置为已取消")
    void cancelOrder_releasesSeats() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "50.00");

        Order order = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));
        assertEquals("LOCKED", seatStatus(s.getId(), "1A"));

        orderService.cancelOrder(order.getId(), u1);

        assertEquals("AVAILABLE", seatStatus(s.getId(), "1A"), "取消后座位应可再售");
        assertEquals("CANCELLED", orderDao.findById(order.getId()).getStatus());
        assertEquals("CANCELLED", ticketDao.listByOrder(order.getId()).get(0).getStatus());
    }

    // ===== 退票 =====

    @Test
    @DisplayName("TC-O09 退票：发船前2小时以上全额退款")
    void refund_fullWhenMoreThan2Hours() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusHours(5), "100.00");

        Order order = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));
        orderService.pay(order.getId(), u1);

        orderService.refund(order.getId(), u1, "PASSENGER", "行程变更");

        var refunds = refundDao.listByOrder(order.getId());
        assertEquals(1, refunds.size());
        assertEquals(0, new BigDecimal("0.00").compareTo(refunds.get(0).getFee()), "2小时以上手续费应为0");
        assertEquals(0, new BigDecimal("100.00").compareTo(refunds.get(0).getRefundAmount()), "应全额退款");
        assertEquals("REFUNDED", orderDao.findById(order.getId()).getStatus());
        assertEquals("AVAILABLE", seatStatus(s.getId(), "1A"), "退票后座位应释放");
        assertEquals(0, scheduleDao.findById(s.getId()).getSoldCount().intValue(), "已售数应回退");
    }

    @Test
    @DisplayName("TC-O10 退票：发船前2小时内收取20%手续费")
    void refund_charges20PercentWithin2Hours() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusHours(1), "100.00");

        Order order = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));
        orderService.pay(order.getId(), u1);

        orderService.refund(order.getId(), u1, "PASSENGER", "临时有事");

        var refund = refundDao.listByOrder(order.getId()).get(0);
        assertEquals(0, new BigDecimal("20.00").compareTo(refund.getFee()), "手续费应为票价20%");
        assertEquals(0, new BigDecimal("80.00").compareTo(refund.getRefundAmount()), "退款应为80%");
    }

    @Test
    @DisplayName("TC-O11 退票失败：发船后不可退、已检票不可退、待支付不可退、非本人不可退")
    void refund_rejectedCases() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusHours(5), "80.00");

        // 待支付不可退
        Order unpaid = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "甲", "440100199001010001", "13711110001")));
        BizException exUnpaid = assertThrows(BizException.class,
                () -> orderService.refund(unpaid.getId(), u1, "PASSENGER", "不想买了"));
        assertTrue(exUnpaid.getMessage().contains("未支付"), "实际：" + exUnpaid.getMessage());

        // 已检票不可退
        Order paid = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1B", "乙", "440100199001010002", "13711110002")));
        orderService.pay(paid.getId(), u1);
        orderService.checkIn(ticketDao.listByOrder(paid.getId()).get(0).getTicketNo(), checkerId, null);
        BizException exChecked = assertThrows(BizException.class,
                () -> orderService.refund(paid.getId(), u1, "PASSENGER", "不想去了"));
        assertTrue(exChecked.getMessage().contains("已检票"), "实际：" + exChecked.getMessage());

        // 非本人不可退
        Order other = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1C", "丙", "440100199001010003", "13711110003")));
        orderService.pay(other.getId(), u1);
        BizException exOther = assertThrows(BizException.class,
                () -> orderService.refund(other.getId(), 999L, "PASSENGER", "恶意退票"));
        assertTrue(exOther.getMessage().contains("无权"), "实际：" + exOther.getMessage());

        // 发船后不可退：把班次发船时间改到过去
        Schedule past = new Schedule();
        past.setId(s.getId());
        past.setRouteId(r.getId());
        past.setShipId(ship.getId());
        past.setDepartTime(LocalDateTime.now().minusMinutes(10));
        past.setArriveTime(LocalDateTime.now().plusMinutes(50));
        past.setPrice(new BigDecimal("80.00"));
        scheduleDao.update(past);
        BizException exDeparted = assertThrows(BizException.class,
                () -> orderService.refund(other.getId(), u1, "PASSENGER", "晚了"));
        assertTrue(exDeparted.getMessage().contains("已发船"), "实际：" + exDeparted.getMessage());
    }

    // ===== 改签 =====

    @Test
    @DisplayName("TC-O12 改签成功：原票作废释放、新票已支付、记录差价与日志")
    void reschedule_movesTicketAndLogs() {
        Route r = newRoute();
        Ship ship = newShip(8);
        LocalDateTime base = LocalDateTime.now().plusHours(6);
        Schedule oldS = newSellingSchedule(r, ship, base, "100.00");
        // 新班次用另一艘船，避免时间冲突
        Ship ship2 = newShip(8);
        Schedule newS = newSellingSchedule(r, ship2, base.plusHours(2), "130.00");

        Order order = orderService.createOrder(oldS.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));
        orderService.pay(order.getId(), u1);
        Ticket oldTicket = ticketDao.listByOrder(order.getId()).get(0);

        orderService.reschedule(oldTicket.getId(), newS.getId(), "2B", u1);

        List<Ticket> tickets = ticketDao.listByOrder(order.getId());
        Ticket refunded = tickets.stream().filter(t -> t.getId().equals(oldTicket.getId())).findFirst().orElseThrow();
        // 改签作废必须是 RESCHEDULED，不能复用 REFUNDED，否则会被退票统计误算
        assertEquals("RESCHEDULED", refunded.getStatus(), "原票应作废，且状态与退票区分");
        assertEquals("AVAILABLE", seatStatus(oldS.getId(), "1A"), "原座位应释放");

        Ticket fresh = tickets.stream().filter(t -> !t.getId().equals(oldTicket.getId())).findFirst().orElseThrow();
        assertEquals("PAID", fresh.getStatus());
        assertEquals("2B", fresh.getSeatNo());
        assertEquals(newS.getId(), fresh.getScheduleId());
        assertEquals("SOLD", seatStatus(newS.getId(), "2B"));

        var logs = rescheduleDao.listByOldTicket(oldTicket.getId());
        assertEquals(1, logs.size(), "应记录一条改签日志");
        assertEquals(0, new BigDecimal("30.00").compareTo(logs.get(0).getPriceDiff()), "差价应为 +30");
    }

    @Test
    @DisplayName("TC-O13 改签失败：发船前1小时内、目标班次相同、座位被占、未支付")
    void reschedule_rejectedCases() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule soon = newSellingSchedule(r, ship, LocalDateTime.now().plusMinutes(30), "100.00");
        Ship ship2 = newShip(8);
        Schedule later = newSellingSchedule(r, ship2, LocalDateTime.now().plusHours(8), "100.00");

        Order order = orderService.createOrder(soon.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));
        orderService.pay(order.getId(), u1);
        Ticket t = ticketDao.listByOrder(order.getId()).get(0);

        // 1小时内不可改签
        BizException withinHour = assertThrows(BizException.class,
                () -> orderService.reschedule(t.getId(), later.getId(), "1A", u1));
        assertTrue(withinHour.getMessage().contains("1小时"), "实际：" + withinHour.getMessage());

        // 用时间充裕的班次继续测其余分支
        Ship ship3 = newShip(8);
        Schedule far = newSellingSchedule(r, ship3, LocalDateTime.now().plusHours(10), "100.00");
        Order o2 = orderService.createOrder(far.getId(), u1, null,
                List.of(ticket("1A", "李四", "440100199001010002", "13711110002")));
        orderService.pay(o2.getId(), u1);
        Ticket t2 = ticketDao.listByOrder(o2.getId()).get(0);

        // 目标班次与原班次相同
        BizException sameSchedule = assertThrows(BizException.class,
                () -> orderService.reschedule(t2.getId(), far.getId(), "2A", u1));
        assertTrue(sameSchedule.getMessage().contains("不能与原班次相同"), "实际：" + sameSchedule.getMessage());

        // 目标座位被他人占用
        orderService.createOrder(later.getId(), u2, null,
                List.of(ticket("2C", "占位", "440100199001010003", "13711110003")));
        BizException occupied = assertThrows(BizException.class,
                () -> orderService.reschedule(t2.getId(), later.getId(), "2C", u1));
        assertTrue(occupied.getMessage().contains("被他人锁定"), "实际：" + occupied.getMessage());

        // 未支付票不可改签
        Ship ship4 = newShip(8);
        Schedule far2 = newSellingSchedule(r, ship4, LocalDateTime.now().plusHours(12), "100.00");
        Order unpaid = orderService.createOrder(far2.getId(), u1, null,
                List.of(ticket("1A", "王五", "440100199001010004", "13711110004")));
        Ticket unpaidTicket = ticketDao.listByOrder(unpaid.getId()).get(0);
        BizException notPaid = assertThrows(BizException.class,
                () -> orderService.reschedule(unpaidTicket.getId(), later.getId(), "4D", u1));
        assertTrue(notPaid.getMessage().contains("仅已支付"), "实际：" + notPaid.getMessage());
    }

    // ===== 检票 =====

    @Test
    @DisplayName("TC-O14 检票成功：票置为已检票，记录检票时间与检票员，订单联动为已检票")
    void checkIn_success() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusMinutes(20), "50.00");

        Order order = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "张三", "440100199001010001", "13711110001")));
        orderService.pay(order.getId(), u1);
        Ticket t = ticketDao.listByOrder(order.getId()).get(0);

        orderService.checkIn(t.getTicketNo(), checkerId, null);

        Ticket checked = ticketDao.findById(t.getId());
        assertEquals("CHECKED", checked.getStatus());
        assertNotNull(checked.getCheckTime());
        assertEquals(checkerId.longValue(), checked.getCheckerId().longValue());
        assertEquals("CHECKED", orderDao.findById(order.getId()).getStatus(), "订单应联动为已检票");
    }

    @Test
    @DisplayName("TC-O15 检票失败：重复检票、已退票、未支付、已过期、非本班次")
    void checkIn_rejectedCases() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Ship ship2 = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusMinutes(30), "50.00");
        Schedule other = newSellingSchedule(r, ship2, LocalDateTime.now().plusHours(3), "50.00");

        // 未支付不可检
        Order unpaid = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1A", "甲", "440100199001010001", "13711110001")));
        Ticket tUnpaid = ticketDao.listByOrder(unpaid.getId()).get(0);
        BizException exUnpaid = assertThrows(BizException.class,
                () -> orderService.checkIn(tUnpaid.getTicketNo(), checkerId, null));
        assertTrue(exUnpaid.getMessage().contains("未支付"), "实际：" + exUnpaid.getMessage());

        // 正常支付后可检
        Order paid = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1B", "乙", "440100199001010002", "13711110002")));
        orderService.pay(paid.getId(), u1);
        Ticket tPaid = ticketDao.listByOrder(paid.getId()).get(0);

        // 非本班次
        BizException wrongSchedule = assertThrows(BizException.class,
                () -> orderService.checkIn(tPaid.getTicketNo(), checkerId, other.getId()));
        assertTrue(wrongSchedule.getMessage().contains("不属于所选班次"), "实际：" + wrongSchedule.getMessage());

        orderService.checkIn(tPaid.getTicketNo(), checkerId, s.getId());

        // 重复检票
        BizException again = assertThrows(BizException.class,
                () -> orderService.checkIn(tPaid.getTicketNo(), checkerId, s.getId()));
        assertTrue(again.getMessage().contains("已检票"), "实际：" + again.getMessage());

        // 已退票
        Order refunded = orderService.createOrder(s.getId(), u1, null,
                List.of(ticket("1C", "丙", "440100199001010003", "13711110003")));
        orderService.pay(refunded.getId(), u1);
        orderService.refund(refunded.getId(), u1, "PASSENGER", "退掉");
        Ticket tRefunded = ticketDao.listByOrder(refunded.getId()).get(0);
        BizException exRefunded = assertThrows(BizException.class,
                () -> orderService.checkIn(tRefunded.getTicketNo(), checkerId, null));
        assertTrue(exRefunded.getMessage().contains("已退票"), "实际：" + exRefunded.getMessage());

        // 已过期：班次发船时间改到 3 小时前（超过2小时宽限）
        Order expired = orderService.createOrder(other.getId(), u1, null,
                List.of(ticket("1A", "丁", "440100199001010004", "13711110004")));
        orderService.pay(expired.getId(), u1);
        Ticket tExpired = ticketDao.listByOrder(expired.getId()).get(0);
        Schedule past = new Schedule();
        past.setId(other.getId());
        past.setRouteId(r.getId());
        past.setShipId(ship2.getId());
        past.setDepartTime(LocalDateTime.now().minusHours(3));
        past.setArriveTime(LocalDateTime.now().minusHours(2));
        past.setPrice(new BigDecimal("50.00"));
        scheduleDao.update(past);
        BizException exExpired = assertThrows(BizException.class,
                () -> orderService.checkIn(tExpired.getTicketNo(), checkerId, null));
        assertTrue(exExpired.getMessage().contains("已过期"), "实际：" + exExpired.getMessage());
    }

    @Test
    @DisplayName("TC-O16 检票记录统计：按班次统计已检票/总售票/未检票数量与明细字段")
    void checkInStatistics_bySchedule() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusMinutes(30), "50.00");

        // 3 张已支付，其中 2 张已检票
        for (int i = 0; i < 3; i++) {
            Long buyer = newPassenger();
            Order o = orderService.createOrder(s.getId(), buyer, null,
                    List.of(ticket("1" + (char) ('A' + i), "统计乘客" + i,
                            String.format("44010019900101%04d", 6000 + i), "13711116" + String.format("%03d", i))));
            orderService.pay(o.getId(), buyer);
            if (i < 2) {
                orderService.checkIn(ticketDao.listByOrder(o.getId()).get(0).getTicketNo(), checkerId, s.getId());
            }
        }

        List<Ticket> tickets = orderService.listTicketsBySchedule(s.getId());
        long checked = tickets.stream().filter(t -> "CHECKED".equals(t.getStatus())).count();
        long unpaidOrUnchecked = tickets.size() - checked;

        assertEquals(3, tickets.size(), "该班次总售票数应为3");
        assertEquals(2, checked, "已检票数应为2");
        assertEquals(1, unpaidOrUnchecked, "未检票数应为1");

        Ticket firstChecked = tickets.stream().filter(t -> "CHECKED".equals(t.getStatus())).findFirst().orElseThrow();
        assertNotNull(firstChecked.getCheckTime(), "检票记录应含检票时间");
        assertEquals(checkerId, firstChecked.getCheckerId(), "检票记录应含检票员");
        assertNotNull(firstChecked.getSeatNo(), "检票记录应含座位号");
        assertNotNull(firstChecked.getPassengerName(), "检票记录应含乘客姓名");
    }

    @Test
    @DisplayName("TC-O17 单号唯一性：连续 40 次下单，订单号与船票号均不重复")
    void generatedNumbersAreUnique() {
        Route r = newRoute();
        Ship ship = newShip(40);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "10.00");

        java.util.Set<String> orderNos = new java.util.HashSet<>();
        java.util.Set<String> ticketNos = new java.util.HashSet<>();

        for (int i = 0; i < 40; i++) {
            Order o = orderService.createOrder(s.getId(), u1, null,
                    List.of(ticket(seatOf(i), "幂等乘客", String.format("44010019900101%04d", 7000 + i),
                            "13711117" + String.format("%03d", i))));
            assertTrue(orderNos.add(o.getOrderNo()), "订单号重复：" + o.getOrderNo());
            String ticketNo = ticketDao.listByOrder(o.getId()).get(0).getTicketNo();
            assertTrue(ticketNos.add(ticketNo), "船票号重复：" + ticketNo);
        }
        assertEquals(40, orderNos.size());
        assertEquals(40, ticketNos.size());
    }

    /** 40 座 = 10 排 × 4 列，按序号生成座位号 */
    private String seatOf(int index) {
        return (index / 4 + 1) + String.valueOf((char) ('A' + index % 4));
    }
}