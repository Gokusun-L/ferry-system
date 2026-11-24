package com.ferry;

import com.ferry.common.BizException;
import com.ferry.config.ScheduledTask;
import com.ferry.dao.ScheduleDao;
import com.ferry.dao.ScheduleSeatDao;
import com.ferry.dao.ShipSeatDao;
import com.ferry.entity.Route;
import com.ferry.entity.Schedule;
import com.ferry.entity.Ship;
import com.ferry.entity.ShipSeat;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 模块二测试：航线、船舶、班次、座位的业务规则与状态流转。
 */
@DisplayName("模块二 航线船舶班次座位")
class RouteShipScheduleTest extends BaseIntegrationTest {

    @Autowired
    private ShipSeatDao shipSeatDao;
    @Autowired
    private ScheduleSeatDao scheduleSeatDao;
    @Autowired
    private ScheduleDao scheduleDao;
    @Autowired
    private ScheduledTask scheduledTask;

    // ===== 航线 =====

    @Test
    @DisplayName("TC-R01 航线新增成功，航行时长必须大于 0")
    void createRoute_ok() {
        Route r = newRoute();
        assertNotNull(r.getId());
        assertEquals(60, routeService.getById(r.getId()).getDuration().intValue());

        Route bad = new Route();
        bad.setRouteName("测试航线-时长0");
        bad.setDepartPort("甲港");
        bad.setArrivePort("乙港");
        bad.setDuration(0);
        BizException ex = assertThrows(BizException.class, () -> routeService.create(bad));
        assertTrue(ex.getMessage().contains("时长"), "实际：" + ex.getMessage());
    }

    @Test
    @DisplayName("TC-R02 航线唯一性：同出发港+到达港+名称 拒绝重复；同港口不同名称允许")
    void route_uniqueness_isTriple() {
        Route a = newRoute();
        // 三元组完全相同 → 拒绝
        Route dup = new Route();
        dup.setRouteName(a.getRouteName());
        dup.setDepartPort(a.getDepartPort());
        dup.setArrivePort(a.getArrivePort());
        dup.setDuration(90);
        BizException ex = assertThrows(BizException.class, () -> routeService.create(dup));
        assertTrue(ex.getMessage().contains("已存在相同"), "实际：" + ex.getMessage());

        // 同港口、不同航线名 → 允许（快线/慢线并存）
        Route slow = new Route();
        slow.setRouteName(a.getRouteName() + "-慢线");
        slow.setDepartPort(a.getDepartPort());
        slow.setArrivePort(a.getArrivePort());
        slow.setDuration(120);
        assertDoesNotThrow(() -> routeService.create(slow), "同港口不同航线名应允许创建");
    }

    @Test
    @DisplayName("TC-R03 航线删除：有未完成班次时拒绝，无班次时可逻辑删除")
    void deleteRoute_blockedByUnfinishedSchedule() {
        Route r = newRoute();
        Ship ship = newShip(8);
        newSellingSchedule(r, ship, LocalDateTime.now().plusDays(3), "50.00");

        BizException ex = assertThrows(BizException.class, () -> routeService.delete(r.getId()));
        assertTrue(ex.getMessage().contains("未完成班次"), "实际：" + ex.getMessage());

        // 无班次的航线可删除，且删除后查询不到
        Route empty = newRoute();
        routeService.delete(empty.getId());
        assertThrows(BizException.class, () -> routeService.getById(empty.getId()));
    }

    // ===== 船舶与座位 =====

    @Test
    @DisplayName("TC-S01 新增船舶自动生成座位，数量等于总座位数，编号为 排号+列号")
    void createShip_generatesSeats() {
        Ship ship = newShip(10);
        List<ShipSeat> seats = shipSeatDao.listByShip(ship.getId());
        assertEquals(10, seats.size(), "座位数应等于 total_seats");
        assertEquals("1A", seats.get(0).getSeatNo());
        assertTrue(seats.stream().anyMatch(s -> "3B".equals(s.getSeatNo())), "应存在 3B 座位");
        // 4 列排布：10 个座位 = 3 排（4+4+2）
        assertEquals(2, seats.stream().filter(s -> s.getRowNo() == 3).count(), "第3排应有2个座位");
    }

    @Test
    @DisplayName("TC-S02 船舶删除：有未完成班次时拒绝")
    void deleteShip_blockedByUnfinishedSchedule() {
        Route r = newRoute();
        Ship ship = newShip(8);
        newSellingSchedule(r, ship, LocalDateTime.now().plusDays(4), "60.00");
        BizException ex = assertThrows(BizException.class, () -> shipService.delete(ship.getId()));
        assertTrue(ex.getMessage().contains("未完成班次"), "实际：" + ex.getMessage());
    }

    // ===== 班次 =====

    @Test
    @DisplayName("TC-SC01 新增班次：到达时间自动 = 发船时间 + 航线时长")
    void createSchedule_computesArriveTime() {
        Route r = newRoute(); // duration=60
        Ship ship = newShip(8);
        LocalDateTime depart = LocalDateTime.of(2027, 3, 1, 9, 0);

        Schedule s = new Schedule();
        s.setRouteId(r.getId());
        s.setShipId(ship.getId());
        s.setDepartTime(depart);
        s.setPrice(new BigDecimal("88.00"));
        scheduleService.create(s);

        Schedule saved = scheduleService.getById(s.getId());
        assertEquals(depart.plusMinutes(60), saved.getArriveTime(), "到达时间应为发船时间+60分钟");
        assertEquals("PENDING", saved.getStatus(), "新建班次应为待发布");
        assertEquals(0, saved.getSoldCount().intValue());
    }

    @Test
    @DisplayName("TC-SC02 新增班次：同船舶时间重叠拒绝，紧邻不重叠允许")
    void createSchedule_rejectsShipTimeConflict() {
        Route r = newRoute();
        Ship ship = newShip(8);
        LocalDateTime depart = LocalDateTime.of(2027, 3, 2, 9, 0);

        Schedule first = new Schedule();
        first.setRouteId(r.getId());
        first.setShipId(ship.getId());
        first.setDepartTime(depart);
        first.setPrice(new BigDecimal("50.00"));
        scheduleService.create(first); // 9:00-10:00

        // 9:30 发船，重叠 → 拒绝
        Schedule overlap = new Schedule();
        overlap.setRouteId(r.getId());
        overlap.setShipId(ship.getId());
        overlap.setDepartTime(depart.plusMinutes(30));
        overlap.setPrice(new BigDecimal("50.00"));
        BizException ex = assertThrows(BizException.class, () -> scheduleService.create(overlap));
        assertTrue(ex.getMessage().contains("时间冲突"), "实际：" + ex.getMessage());

        // 10:00 发船，紧邻不重叠 → 允许
        Schedule adjacent = new Schedule();
        adjacent.setRouteId(r.getId());
        adjacent.setShipId(ship.getId());
        adjacent.setDepartTime(depart.plusHours(1));
        adjacent.setPrice(new BigDecimal("50.00"));
        assertDoesNotThrow(() -> scheduleService.create(adjacent), "紧邻时段不应判为冲突");
    }

    @Test
    @DisplayName("TC-SC03 新增班次后自动初始化该班次的座位，状态全部 AVAILABLE")
    void createSchedule_initializesSeats() {
        Route r = newRoute();
        Ship ship = newShip(12);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(5), "70.00");

        var seats = scheduleSeatDao.listBySchedule(s.getId());
        assertEquals(12, seats.size(), "班次座位数应等于船舶座位数");
        assertTrue(seats.stream().allMatch(x -> "AVAILABLE".equals(x.getStatus())), "初始座位应全部可售");
    }

    @Test
    @DisplayName("TC-SC04 批量生成班次：日期范围内每天一条，冲突日期自动跳过")
    void batchCreate_generatesDailyAndSkipsConflict() {
        Route r = newRoute();
        Ship ship = newShip(8);
        LocalDate start = LocalDate.of(2027, 4, 1);
        LocalDate end = LocalDate.of(2027, 4, 5);

        // 先在 4/3 10:00 建一个班次，制造冲突
        Schedule pre = new Schedule();
        pre.setRouteId(r.getId());
        pre.setShipId(ship.getId());
        pre.setDepartTime(LocalDate.of(2027, 4, 3).atTime(10, 0));
        pre.setPrice(new BigDecimal("40.00"));
        scheduleService.create(pre);

        List<Schedule> created = scheduleService.batchCreate(
                r.getId(), ship.getId(), start, end, 10, 0, new BigDecimal("40.00"));

        assertEquals(4, created.size(), "5天中1天冲突，应生成4个班次");
        assertTrue(created.stream().noneMatch(x -> x.getDepartTime().toLocalDate().equals(LocalDate.of(2027, 4, 3))),
                "冲突日期不应生成");
    }

    @Test
    @DisplayName("TC-SC05 班次状态流转：PENDING→SELLING→DEPARTED→FINISHED")
    void scheduleStatusFlow() {
        Route r = newRoute();
        Ship ship = newShip(8);
        LocalDateTime depart = LocalDateTime.now().plusMinutes(30);

        Schedule s = new Schedule();
        s.setRouteId(r.getId());
        s.setShipId(ship.getId());
        s.setDepartTime(depart);
        s.setPrice(new BigDecimal("50.00"));
        scheduleService.create(s);
        assertEquals("PENDING", scheduleService.getById(s.getId()).getStatus());

        scheduleService.publish(s.getId());
        assertEquals("SELLING", scheduleService.getById(s.getId()).getStatus());

        // 把发船时间改成过去，模拟到达发船时刻
        Schedule past = new Schedule();
        past.setId(s.getId());
        past.setRouteId(r.getId());
        past.setShipId(ship.getId());
        past.setDepartTime(LocalDateTime.now().minusMinutes(1));
        past.setArriveTime(LocalDateTime.now().plusMinutes(59));
        past.setPrice(new BigDecimal("50.00"));
        scheduleDao.update(past);

        scheduledTask.departSellingSchedules();
        assertEquals("DEPARTED", scheduleService.getById(s.getId()).getStatus(), "到点应自动置为已发船");

        // 到达时间也过去 → 完成
        Schedule done = new Schedule();
        done.setId(s.getId());
        done.setRouteId(r.getId());
        done.setShipId(ship.getId());
        done.setDepartTime(LocalDateTime.now().minusHours(3));
        done.setArriveTime(LocalDateTime.now().minusHours(2));
        done.setPrice(new BigDecimal("50.00"));
        scheduleDao.update(done);

        scheduledTask.finishDepartedSchedules();
        assertEquals("FINISHED", scheduleService.getById(s.getId()).getStatus(), "到达后应自动完成");
    }

    @Test
    @DisplayName("TC-SC06 已发船班次不允许修改；已取消班次不允许修改")
    void updateSchedule_blockedAfterDeparture() {
        Route r = newRoute();
        Ship ship = newShip(8);
        LocalDateTime depart = LocalDateTime.now().plusHours(2);

        Schedule s = new Schedule();
        s.setRouteId(r.getId());
        s.setShipId(ship.getId());
        s.setDepartTime(depart);
        s.setPrice(new BigDecimal("50.00"));
        scheduleService.create(s);

        // 正常修改（未发船、无订单）应成功
        Schedule edit = new Schedule();
        edit.setId(s.getId());
        edit.setRouteId(r.getId());
        edit.setShipId(ship.getId());
        edit.setDepartTime(depart.plusHours(1));
        edit.setPrice(new BigDecimal("66.00"));
        assertDoesNotThrow(() -> scheduleService.update(edit));

        // 直接改库状态为已发船，再修改 → 拒绝
        scheduleDao.updateStatus(s.getId(), "DEPARTED");
        BizException ex = assertThrows(BizException.class, () -> scheduleService.update(edit));
        assertTrue(ex.getMessage().contains("已发船"), "实际：" + ex.getMessage());
    }

    @Test
    @DisplayName("TC-SC07 班次删除：有未完成订单时拒绝")
    void deleteSchedule_blockedByActiveOrder() {
        Route r = newRoute();
        Ship ship = newShip(8);
        Schedule s = newSellingSchedule(r, ship, LocalDateTime.now().plusDays(2), "50.00");

        var ticket = new com.ferry.entity.Ticket();
        ticket.setSeatNo("1A");
        ticket.setPassengerName("删除校验乘客");
        ticket.setIdCard("440100199001018888");
        ticket.setPhone("13711118888");
        orderService_create(s.getId(), ticket);

        BizException ex = assertThrows(BizException.class, () -> scheduleService.delete(s.getId()));
        assertTrue(ex.getMessage().contains("未完成订单"), "实际：" + ex.getMessage());
    }

    @Autowired
    private com.ferry.service.OrderService orderService;

    private void orderService_create(Long scheduleId, com.ferry.entity.Ticket ticket) {
        orderService.createOrder(scheduleId, null, null, List.of(ticket));
    }
}
