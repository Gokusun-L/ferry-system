package com.ferry;

import com.ferry.entity.Order;
import com.ferry.entity.Route;
import com.ferry.entity.Schedule;
import com.ferry.entity.Ship;
import com.ferry.entity.Ticket;
import com.ferry.service.OrderService;
import com.ferry.service.StatsService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 模块五测试：聚合统计（GROUP BY / SUM / CASE WHEN / AVG / 排序）。
 */
@DisplayName("模块五 统计报表")
class StatsServiceTest extends BaseIntegrationTest {

    @Autowired
    private StatsService statsService;
    @Autowired
    private OrderService orderService;

    /** 真实用户池：订单 user_id 有外键约束 */
    private java.util.List<Long> users;

    @BeforeEach
    void createUsers() {
        users = new java.util.ArrayList<>();
        for (int i = 0; i < 8; i++) {
            users.add(newPassenger());
        }
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
    @DisplayName("TC-ST01 按航线统计：售票量只计已支付/已检票，退票不计入销售额")
    void statsByRoute_countsOnlyValidOrders() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "100.00");

        // 2 单已支付
        for (int i = 0; i < 2; i++) {
            Order o = orderService.createOrder(s.getId(), users.get(i), null,
                    List.of(ticket("1" + (char) ('A' + i), "统计乘客" + i,
                            String.format("44010019900101%04d", 3000 + i))));
            orderService.pay(o.getId(), users.get(i));
        }
        // 1 单支付后退票
        Order refunded = orderService.createOrder(s.getId(), users.get(4), null,
                List.of(ticket("2A", "退票乘客", "440100199001019001")));
        orderService.pay(refunded.getId(), users.get(4));
        orderService.refund(refunded.getId(), users.get(4), "ADMIN", "统计测试退票");

        LocalDate today = LocalDate.now();
        List<Map<String, Object>> rows = statsService.statsByRoute(today.minusDays(1), today.plusDays(1));
        Map<String, Object> row = rows.stream()
                .filter(m -> r.getRouteName().equals(String.valueOf(m.get("route_name"))))
                .findFirst().orElseThrow(() -> new AssertionError("统计结果应包含航线：" + r.getRouteName()));

        // 已支付2单，退票1单不计入售票量
        assertEquals(2, ((Number) row.get("sale_count")).intValue(),
                "售票量应为2（退票不计入），实际=" + row.get("sale_count"));
        assertEquals(0, new BigDecimal("200.00").compareTo(new BigDecimal(String.valueOf(row.get("sale_amount")))),
                "售票金额应为200，实际=" + row.get("sale_amount"));
    }

    @Test
    @DisplayName("TC-ST02 收入汇总：总收入、退票损失、净收入三口径正确")
    void incomeSummary_threeMetrics() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "100.00");

        Order keep = orderService.createOrder(s.getId(), users.get(0), null,
                List.of(ticket("1A", "保留", "440100199001018001")));
        orderService.pay(keep.getId(), users.get(0));

        Order back = orderService.createOrder(s.getId(), users.get(1), null,
                List.of(ticket("1B", "退掉", "440100199001018002")));
        orderService.pay(back.getId(), users.get(1));
        orderService.refund(back.getId(), users.get(1), "ADMIN", "收入统计测试");

        LocalDate today = LocalDate.now();
        Map<String, Object> income = statsService.incomeSummary(today.minusDays(1), today.plusDays(1));

        BigDecimal total = new BigDecimal(String.valueOf(income.get("total_income")));
        BigDecimal loss = new BigDecimal(String.valueOf(income.get("refund_loss")));
        BigDecimal net = new BigDecimal(String.valueOf(income.get("net_income")));

        assertTrue(total.compareTo(new BigDecimal("100.00")) >= 0, "总收入应至少含保留单100，实际=" + total);
        assertTrue(loss.compareTo(new BigDecimal("100.00")) >= 0, "退票损失应至少100，实际=" + loss);
        assertEquals(0, total.subtract(loss).compareTo(net), "净收入应等于总收入-退票损失");
    }

    @Test
    @DisplayName("TC-ST03 上座率：已售/总座位×100，低上座率预警只返回低于阈值班次")
    void occupancy_andLowWarning() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "100.00");

        // 卖 4 张，8 座 → 上座率 50%
        for (int i = 0; i < 4; i++) {
            Order o = orderService.createOrder(s.getId(), users.get(i), null,
                    List.of(ticket("1" + (char) ('A' + i), "上座率乘客" + i,
                            String.format("44010019900101%04d", 4000 + i))));
            orderService.pay(o.getId(), users.get(i));
        }

        List<Map<String, Object>> occ = statsService.scheduleOccupancy();
        Map<String, Object> mine = occ.stream()
                .filter(m -> String.valueOf(s.getId()).equals(String.valueOf(m.get("schedule_id"))))
                .findFirst().orElseThrow();
        assertEquals(0, new BigDecimal("50.00").compareTo(new BigDecimal(String.valueOf(mine.get("occupancy")))),
                "上座率应为50%，实际=" + mine.get("occupancy"));

        // 阈值 50：等于 50 不算"低于"，不应出现在预警里
        List<Map<String, Object>> low = statsService.lowOccupancy();
        assertTrue(low.stream().noneMatch(m -> String.valueOf(s.getId()).equals(String.valueOf(m.get("schedule_id")))),
                "上座率等于50%不应被预警（预警条件为 <50%）");
    }

    @Test
    @DisplayName("TC-ST04 时间段上座率：早班/午班/晚班分组可正常聚合")
    void occupancyByPeriod_groupsByHour() {
        List<Map<String, Object>> rows = statsService.occupancyByPeriod();
        assertNotNull(rows);
        // 每组应含 period 与 avg_occupancy 字段
        for (Map<String, Object> row : rows) {
            assertTrue(row.containsKey("period"), "结果应包含 period 列");
            assertTrue(row.containsKey("avg_occupancy"), "结果应包含 avg_occupancy 列");
            String period = String.valueOf(row.get("period"));
            assertTrue(period.contains("早班") || period.contains("午班") || period.contains("晚班"),
                    "period 应为早/午/晚班之一，实际=" + period);
        }
    }

    @Test
    @DisplayName("TC-ST05 售票员业绩排名：按金额降序，只统计 SELLER 角色")
    void sellerRanking_descByAmount() {
        LocalDate today = LocalDate.now();
        List<Map<String, Object>> rows = statsService.statsBySeller(today.minusDays(30), today.plusDays(1));
        assertNotNull(rows);
        BigDecimal prev = null;
        for (Map<String, Object> row : rows) {
            BigDecimal amount = new BigDecimal(String.valueOf(row.get("sale_amount")));
            if (prev != null) {
                assertTrue(prev.compareTo(amount) >= 0, "应按售票金额降序排列");
            }
            prev = amount;
        }
    }

    @Test
    @DisplayName("TC-ST06 退票统计：按原因分组返回退票笔数与金额")
    void refundStats_groupsByReason() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(1), "60.00");

        Order o = orderService.createOrder(s.getId(), users.get(0), null,
                List.of(ticket("1A", "退票统计", "440100199001019100")));
        orderService.pay(o.getId(), users.get(0));
        orderService.refund(o.getId(), users.get(0), "ADMIN", "统计专用原因");

        LocalDate today = LocalDate.now();
        List<Map<String, Object>> rows = statsService.refundStats(today.minusDays(1), today.plusDays(1));
        Map<String, Object> mine = rows.stream()
                .filter(m -> "统计专用原因".equals(String.valueOf(m.get("reason"))))
                .findFirst().orElseThrow(() -> new AssertionError("应统计到该退票原因"));
        assertEquals(1, ((Number) mine.get("refund_count")).intValue());
        assertEquals(0, new BigDecimal("60.00").compareTo(new BigDecimal(String.valueOf(mine.get("refund_amount")))),
                "全额退票金额应为60");
    }

    @Test
    @DisplayName("TC-ST07 改签不计入退票量：班次统计的退票数不应被改签作废票污染")
    void rescheduleNotCountedAsRefund() {
        Route r = newRoute();
        Ship ship = newShip(8);
        LocalDateTime base = LocalDateTime.now().plusHours(6);
        Schedule from = newSellingSchedule(r, ship, base, "100.00");
        Ship ship2 = newShip(8);
        Schedule to = newSellingSchedule(r, ship2, base.plusHours(2), "130.00");

        Order o = orderService.createOrder(from.getId(), users.get(0), null,
                List.of(ticket("1A", "改签乘客", "440100199001019200")));
        orderService.pay(o.getId(), users.get(0));
        Ticket old = orderService.listTicketsByOrder(o.getId()).stream()
                .filter(t -> "PAID".equals(t.getStatus())).findFirst().orElseThrow();

        orderService.reschedule(old.getId(), to.getId(), "2B", users.get(0));

        LocalDate today = LocalDate.now();
        List<Map<String, Object>> rows = statsService.statsBySchedule(today.minusDays(1), today.plusDays(3));

        // 统计 SQL 只返回"有售票或有退票"的班次。改签后原班次既无有效票、也无退票，
        // 因此必须整行消失；修复前因旧票被标记 REFUNDED，refund_count 虚增为 1 会让它错误出现。
        assertTrue(rows.stream().noneMatch(m -> from.getId().equals(
                        ((Number) m.get("schedule_id")).longValue())),
                "改签不是退票：原班次不应出现退票记录，因无售票无退票应整行不出现");

        Map<String, Object> toRow = rows.stream()
                .filter(m -> to.getId().equals(((Number) m.get("schedule_id")).longValue()))
                .findFirst().orElseThrow(() -> new AssertionError("目标班次应出现在统计中"));
        assertEquals(1, ((Number) toRow.get("sale_count")).intValue(), "目标班次应计1张");
        assertEquals(0, ((Number) toRow.get("refund_count")).intValue());
    }

    @Test
    @DisplayName("TC-ST08 改签退还差价不计入退票：退票量/退票原因/退票损失均不受影响")
    void reschedulePriceDiffNotCountedAsRefund() {
        // 由贵改便宜：130 → 100，产生30元差价退款
        Route r = newRoute();
        Ship ship = newShip(8);
        LocalDateTime base = LocalDateTime.now().plusHours(6);
        Schedule expensive = newSellingSchedule(r, ship, base, "130.00");
        Ship ship2 = newShip(8);
        Schedule cheap = newSellingSchedule(r, ship2, base.plusHours(2), "100.00");

        Order o = orderService.createOrder(expensive.getId(), users.get(1), null,
                List.of(ticket("1A", "差价乘客", "440100199001019300")));
        orderService.pay(o.getId(), users.get(1));
        Ticket old = orderService.listTicketsByOrder(o.getId()).stream()
                .filter(t -> "PAID".equals(t.getStatus())).findFirst().orElseThrow();

        LocalDate today = LocalDate.now();
        Map<String, Object> before = statsService.incomeSummary(today, today);
        int refundCountBefore = ((Number) before.get("refund_count")).intValue();

        orderService.reschedule(old.getId(), cheap.getId(), "2B", users.get(1));

        Map<String, Object> after = statsService.incomeSummary(today, today);
        assertEquals(refundCountBefore, ((Number) after.get("refund_count")).intValue(),
                "改签差价退款不得计入退票笔数");

        List<Map<String, Object>> reasons = statsService.refundStats(today.minusDays(1), today.plusDays(1));
        assertTrue(reasons.stream().noneMatch(m -> "改签退还差价".equals(String.valueOf(m.get("reason")))),
                "改签差价不应出现在退票原因分布中");
    }
}
