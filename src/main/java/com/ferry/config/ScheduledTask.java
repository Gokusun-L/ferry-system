package com.ferry.config;

import com.ferry.dao.OrderDao;
import com.ferry.dao.ScheduleDao;
import com.ferry.dao.ScheduleSeatDao;
import com.ferry.dao.TicketDao;
import com.ferry.entity.Order;
import com.ferry.entity.Schedule;
import com.ferry.entity.Ticket;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 定时任务：
 * 1. 支付超时订单自动取消、释放座位（每30秒）
 * 2. 超时锁定座位自动释放（每30秒）
 * 3. 已发船且已到到达时间的班次自动置为完成（每1分钟）
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ScheduledTask {

    private final OrderDao orderDao;
    private final TicketDao ticketDao;
    private final ScheduleSeatDao scheduleSeatDao;
    private final ScheduleDao scheduleDao;

    @Scheduled(fixedDelay = 30000)
    @Transactional
    public void releaseExpiredOrders() {
        List<Order> expired = orderDao.listExpiredUnpaid(LocalDateTime.now().minusMinutes(5));
        for (Order order : expired) {
            // 条件更新，避免与支付并发时误取消已支付订单
            if (orderDao.cancelIfUnpaid(order.getId()) == 0) {
                continue;
            }
            for (Ticket t : ticketDao.listByOrder(order.getId())) {
                if ("UNPAID".equals(t.getStatus())
                        && ticketDao.updateStatusIf(t.getId(), "UNPAID", "CANCELLED") > 0) {
                    scheduleSeatDao.releaseForOrder(t.getScheduleId(), t.getSeatNo(), order.getId());
                }
            }
            log.info("订单 {} 支付超时，已自动取消", order.getOrderNo());
        }
    }

    @Scheduled(fixedDelay = 30000)
    @Transactional
    public void releaseExpiredSeats() {
        int count = scheduleSeatDao.releaseExpiredLocks(LocalDateTime.now().minusMinutes(5));
        if (count > 0) {
            log.info("释放超时锁定座位 {} 个", count);
        }
    }

    @Scheduled(fixedDelay = 60000)
    @Transactional
    public void departSellingSchedules() {
        List<Schedule> schedules = scheduleDao.listSellingToDepart(LocalDateTime.now());
        for (Schedule s : schedules) {
            scheduleDao.updateStatus(s.getId(), "DEPARTED");
            log.info("班次 {} 已到发船时间，状态置为已发船", s.getId());
        }
    }

    @Scheduled(fixedDelay = 60000)
    @Transactional
    public void finishDepartedSchedules() {
        List<Schedule> schedules = scheduleDao.listDepartedUnfinished();
        for (Schedule s : schedules) {
            scheduleDao.updateStatus(s.getId(), "FINISHED");
            orderDao.finishCheckedBySchedule(s.getId());
            log.info("班次 {} 已完成", s.getId());
        }
    }
}
