package com.ferry.service.impl;

import com.ferry.common.BizException;
import com.ferry.dao.*;
import com.ferry.entity.*;
import com.ferry.service.OrderService;
import com.ferry.service.ScheduleService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ScheduleServiceImpl implements ScheduleService {

    private final ScheduleDao scheduleDao;
    private final ShipDao shipDao;
    private final RouteDao routeDao;
    private final ShipSeatDao shipSeatDao;
    private final ScheduleSeatDao scheduleSeatDao;
    private final OrderDao orderDao;
    private final TicketDao ticketDao;
    private final OrderService orderService;

    @Override
    public List<Schedule> search(Long routeId, Long shipId, String date, String status, int page, int size) {
        int offset = (page - 1) * size;
        return scheduleDao.search(routeId, shipId, date, status, offset, size);
    }

    @Override
    public long count(Long routeId, Long shipId, String date, String status) {
        return scheduleDao.count(routeId, shipId, date, status);
    }

    @Override
    public Schedule getById(Long id) {
        Schedule s = scheduleDao.findById(id);
        if (s == null || s.getDeleted() == 1) {
            throw new BizException("班次不存在");
        }
        return s;
    }

    @Override
    @Transactional
    public void create(Schedule schedule) {
        Route route = routeDao.findById(schedule.getRouteId());
        if (route == null || route.getDeleted() == 1) {
            throw new BizException("航线不存在");
        }
        Ship ship = shipDao.findById(schedule.getShipId());
        if (ship == null || ship.getDeleted() == 1) {
            throw new BizException("船舶不存在");
        }
        if (schedule.getDepartTime() == null) {
            throw new BizException("发船时间不能为空");
        }
        if (schedule.getPrice() == null || schedule.getPrice().compareTo(BigDecimal.ZERO) < 0) {
            throw new BizException("票价不能为负");
        }
        // 自动计算到达时间
        LocalDateTime arrive = schedule.getDepartTime().plusMinutes(route.getDuration());
        schedule.setArriveTime(arrive);
        // 船舶时间冲突校验
        int conflict = scheduleDao.countConflict(schedule.getShipId(), schedule.getDepartTime(), arrive, null);
        if (conflict > 0) {
            throw new BizException("该船舶在该时间段已有班次，存在时间冲突");
        }
        schedule.setStatus("PENDING");
        schedule.setSoldCount(0);
        scheduleDao.insert(schedule);
        // 初始化班次座位
        initScheduleSeats(schedule.getId(), ship.getId());
    }

    @Override
    @Transactional
    public List<Schedule> batchCreate(Long routeId, Long shipId, LocalDate startDate, LocalDate endDate,
                                      int hour, int minute, BigDecimal price) {
        Route route = routeDao.findById(routeId);
        if (route == null || route.getDeleted() == 1) {
            throw new BizException("航线不存在");
        }
        Ship ship = shipDao.findById(shipId);
        if (ship == null || ship.getDeleted() == 1) {
            throw new BizException("船舶不存在");
        }
        if (startDate.isAfter(endDate)) {
            throw new BizException("开始日期不能晚于结束日期");
        }
        if (startDate.plusDays(90).isBefore(endDate)) {
            throw new BizException("单次最多生成90天班次");
        }
        if (hour < 0 || hour > 23 || minute < 0 || minute > 59) {
            throw new BizException("发船时间不合法");
        }
        if (price == null || price.compareTo(BigDecimal.ZERO) < 0) {
            throw new BizException("票价不能为负");
        }
        List<Schedule> created = new ArrayList<>();
        LocalDate d = startDate;
        while (!d.isAfter(endDate)) {
            LocalDateTime depart = d.atTime(hour, minute);
            LocalDateTime arrive = depart.plusMinutes(route.getDuration());
            int conflict = scheduleDao.countConflict(shipId, depart, arrive, null);
            if (conflict == 0) {
                Schedule s = new Schedule();
                s.setRouteId(routeId);
                s.setShipId(shipId);
                s.setDepartTime(depart);
                s.setArriveTime(arrive);
                s.setPrice(price);
                s.setStatus("PENDING");
                s.setSoldCount(0);
                scheduleDao.insert(s);
                initScheduleSeats(s.getId(), shipId);
                created.add(s);
            }
            d = d.plusDays(1);
        }
        return created;
    }

    @Override
    @Transactional
    public void update(Schedule schedule) {
        Schedule exist = getById(schedule.getId());
        if ("DEPARTED".equals(exist.getStatus()) || "FINISHED".equals(exist.getStatus())) {
            throw new BizException("班次已发船，不允许修改");
        }
        if ("CANCELLED".equals(exist.getStatus())) {
            throw new BizException("班次已取消，不允许修改");
        }
        // 已产生订单的班次不允许修改
        int orderCount = scheduleDao.countUnfinishedOrder(schedule.getId());
        if (orderCount > 0) {
            throw new BizException("该班次已产生订单，不允许修改");
        }
        Route route = routeDao.findById(schedule.getRouteId());
        if (route == null || route.getDeleted() == 1) {
            throw new BizException("航线不存在");
        }
        if (schedule.getPrice() == null || schedule.getPrice().compareTo(BigDecimal.ZERO) < 0) {
            throw new BizException("票价不能为负");
        }
        if (schedule.getDepartTime() == null) {
            throw new BizException("发船时间不能为空");
        }
        LocalDateTime arrive = schedule.getDepartTime().plusMinutes(route.getDuration());
        schedule.setArriveTime(arrive);
        int conflict = scheduleDao.countConflict(schedule.getShipId(), schedule.getDepartTime(), arrive, schedule.getId());
        if (conflict > 0) {
            throw new BizException("该船舶在该时间段已有班次，存在时间冲突");
        }
        // 换船：重建座位（此时无订单，座位均为可用）
        if (!schedule.getShipId().equals(exist.getShipId())) {
            Ship ship = shipDao.findById(schedule.getShipId());
            if (ship == null || ship.getDeleted() == 1) {
                throw new BizException("船舶不存在");
            }
            scheduleSeatDao.deleteBySchedule(schedule.getId());
            initScheduleSeats(schedule.getId(), ship.getId());
        }
        scheduleDao.update(schedule);
    }

    @Override
    @Transactional
    public void publish(Long id) {
        Schedule schedule = getById(id);
        if (!"PENDING".equals(schedule.getStatus())) {
            throw new BizException("仅待发布班次可发布");
        }
        if (schedule.getDepartTime() == null || !schedule.getDepartTime().isAfter(LocalDateTime.now())) {
            throw new BizException("发船时间已过，不能发布");
        }
        scheduleDao.updateStatus(id, "SELLING");
    }

    @Override
    @Transactional
    public void cancel(Long id) {
        Schedule schedule = getById(id);
        if ("CANCELLED".equals(schedule.getStatus())) {
            throw new BizException("班次已取消");
        }
        if ("DEPARTED".equals(schedule.getStatus()) || "FINISHED".equals(schedule.getStatus())) {
            throw new BizException("班次已发船，不能取消");
        }
        // 已支付/已检票的订单全额退款（含通知）
        Set<Long> paidOrderIds = ticketDao.listBySchedule(id).stream()
                .filter(t -> "PAID".equals(t.getStatus()) || "CHECKED".equals(t.getStatus()))
                .map(Ticket::getOrderId)
                .collect(Collectors.toSet());
        for (Long orderId : paidOrderIds) {
            orderService.refundForCancellation(orderId, null);
        }
        // 未支付船票取消并释放座位
        Set<Long> cancelledOrderIds = new HashSet<>();
        for (Ticket t : ticketDao.listBySchedule(id)) {
            if ("UNPAID".equals(t.getStatus())
                    && ticketDao.updateStatusIf(t.getId(), "UNPAID", "CANCELLED") > 0) {
                scheduleSeatDao.releaseForOrder(t.getScheduleId(), t.getSeatNo(), t.getOrderId());
                cancelledOrderIds.add(t.getOrderId());
            }
        }
        // 清理仍被锁定的座位
        scheduleSeatDao.releaseAllBySchedule(id);
        scheduleDao.updateStatus(id, "CANCELLED");
        for (Long orderId : cancelledOrderIds) {
            orderService.recalcOrderStatus(orderId);
        }
    }

    @Override
    public void delete(Long id) {
        Schedule schedule = getById(id);
        int unfinished = scheduleDao.countUnfinishedOrder(id);
        if (unfinished > 0) {
            throw new BizException("该班次有未完成订单，请先取消班次");
        }
        scheduleDao.logicDelete(id);
    }

    @Override
    public List<Schedule> listForPortSearch(String departPort, String arrivePort, String date) {
        return scheduleDao.listForPortSearch(departPort, arrivePort, date);
    }

    private void initScheduleSeats(Long scheduleId, Long shipId) {
        List<ShipSeat> shipSeats = shipSeatDao.listByShip(shipId);
        List<ScheduleSeat> list = new ArrayList<>();
        for (ShipSeat ss : shipSeats) {
            ScheduleSeat seat = new ScheduleSeat();
            seat.setScheduleId(scheduleId);
            seat.setSeatNo(ss.getSeatNo());
            seat.setStatus("AVAILABLE");
            list.add(seat);
        }
        if (!list.isEmpty()) {
            scheduleSeatDao.insertBatch(list);
        }
    }
}
