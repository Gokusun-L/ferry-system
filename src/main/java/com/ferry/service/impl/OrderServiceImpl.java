package com.ferry.service.impl;

import com.ferry.common.BizException;
import com.ferry.dao.*;
import com.ferry.entity.*;
import com.ferry.service.OrderService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.ThreadLocalRandom;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class OrderServiceImpl implements OrderService {

    private final OrderDao orderDao;
    private final TicketDao ticketDao;
    private final ScheduleDao scheduleDao;
    private final ScheduleSeatDao scheduleSeatDao;
    private final RefundDao refundDao;
    private final RescheduleDao rescheduleDao;
    private final NotificationDao notificationDao;

    private static final int LOCK_MINUTES = 5;
    private static final long FULL_REFUND_MINUTES = 120;
    private static final BigDecimal REFUND_FEE_RATE = new BigDecimal("0.2");
    /**
     * 单号格式：前缀 + 毫秒时间戳(17) + 三位进程内序列(3)。
     * 原实现用「秒级时间戳 + 4 位随机数」，同一秒内下单量大时随机值会重复，
     * 触发 uk_order_no/uk_ticket_no 唯一约束导致下单直接失败（测试已复现）。
     * 改为毫秒时间戳 + 严格自增序列：同一毫秒内最多 1000 单不重复。
     * 集群部署时进程内序列不共享，需改用雪花算法或数据库序列。
     */
    private static final DateTimeFormatter NO_FMT = DateTimeFormatter.ofPattern("yyyyMMddHHmmssSSS");
    private static final java.util.concurrent.atomic.AtomicInteger NO_SEQ = new java.util.concurrent.atomic.AtomicInteger(0);
    private static final Pattern ID_CARD = Pattern.compile("^\\d{17}[\\dXx]$");
    private static final Pattern PHONE = Pattern.compile("^1[3-9]\\d{9}$");

    @Override
    @Transactional
    public void lockSeats(Long scheduleId, List<String> seatNos, Long userId) {
        Schedule schedule = getSchedule(scheduleId);
        if (!"SELLING".equals(schedule.getStatus())) {
            throw new BizException("班次不在售票中");
        }
        if (seatNos == null || seatNos.isEmpty()) {
            throw new BizException("请选择座位");
        }
        if (seatNos.size() > 5) {
            throw new BizException("最多选择5个座位");
        }
        if (new HashSet<>(seatNos).size() != seatNos.size()) {
            throw new BizException("座位号重复");
        }
        // 选座即锁：AVAILABLE 或本人已锁定的座位可锁定，锁定时长5分钟
        LocalDateTime now = LocalDateTime.now();
        for (String seatNo : seatNos) {
            int affected = scheduleSeatDao.lock(scheduleId, seatNo, null, userId, now);
            if (affected == 0) {
                throw new BizException(seatLockFailureReason(scheduleId, seatNo));
            }
        }
    }

    @Override
    public List<ScheduleSeat> listSeatMap(Long scheduleId) {
        getSchedule(scheduleId);
        return scheduleSeatDao.listBySchedule(scheduleId);
    }

    @Override
    @Transactional
    public void unlockSeats(Long scheduleId, List<String> seatNos, Long userId) {
        if (seatNos == null) {
            return;
        }
        for (String seatNo : seatNos) {
            scheduleSeatDao.unlock(scheduleId, seatNo, userId);
        }
    }

    @Override
    @Transactional
    public Order createOrder(Long scheduleId, Long userId, Long sellerId, List<Ticket> tickets) {
        // 锁定班次行：串行化同一班次的“一人一票”校验与座位锁定，避免并发下重复购票
        Schedule schedule = lockSchedule(scheduleId);
        if (!"SELLING".equals(schedule.getStatus())) {
            throw new BizException("班次不在售票中");
        }
        if (tickets == null || tickets.isEmpty()) {
            throw new BizException("至少选择一张船票");
        }
        if (tickets.size() > 5) {
            throw new BizException("最多购买5张船票");
        }
        Set<String> seatNos = tickets.stream().map(Ticket::getSeatNo).collect(Collectors.toSet());
        if (seatNos.size() != tickets.size()) {
            throw new BizException("座位号重复");
        }
        Set<String> idCards = tickets.stream().map(Ticket::getIdCard).collect(Collectors.toSet());
        if (idCards.size() != tickets.size()) {
            throw new BizException("同一订单中身份证号不能重复");
        }
        for (Ticket t : tickets) {
            String name = t.getPassengerName() == null ? "" : t.getPassengerName().trim();
            String idCard = t.getIdCard() == null ? "" : t.getIdCard().trim().toUpperCase();
            String phone = t.getPhone() == null ? "" : t.getPhone().trim();
            if (name.isEmpty()) {
                throw new BizException("乘客姓名不能为空");
            }
            if (!ID_CARD.matcher(idCard).matches()) {
                throw new BizException("身份证号格式不正确");
            }
            if (!PHONE.matcher(phone).matches()) {
                throw new BizException("手机号格式不正确");
            }
            t.setPassengerName(name);
            t.setIdCard(idCard);
            t.setPhone(phone);
            int dup = ticketDao.countByScheduleAndIdCard(scheduleId, idCard);
            if (dup > 0) {
                throw new BizException("身份证号 " + idCard + " 在该班次已购票，一人一班次仅限一票");
            }
        }

        BigDecimal total = schedule.getPrice().multiply(BigDecimal.valueOf(tickets.size()));
        Order order = new Order();
        order.setOrderNo(genNo("O"));
        order.setUserId(userId);
        order.setSellerId(sellerId);
        order.setScheduleId(scheduleId);
        order.setTotalAmount(total);
        order.setStatus("UNPAID");
        order.setChannel(sellerId != null ? "OFFLINE" : "ONLINE");
        orderDao.insert(order);

        // 生成船票 + 锁定座位（并发安全）
        LocalDateTime now = LocalDateTime.now();
        for (Ticket t : tickets) {
            int affected = scheduleSeatDao.lock(scheduleId, t.getSeatNo(), order.getId(), userId, now);
            if (affected == 0) {
                throw new BizException(seatLockFailureReason(scheduleId, t.getSeatNo()));
            }
            t.setOrderId(order.getId());
            t.setScheduleId(scheduleId);
            t.setPrice(schedule.getPrice());
            t.setStatus("UNPAID");
            t.setTicketNo(genTicketNo());
        }
        ticketDao.insertBatch(tickets);
        return order;
    }

    @Override
    @Transactional
    public void pay(Long orderId, Long userId) {
        Order order = orderDao.findById(orderId);
        if (order == null) {
            throw new BizException("订单不存在");
        }
        if (!"UNPAID".equals(order.getStatus())) {
            throw new BizException("订单状态异常，无法支付");
        }
        boolean owner = userId != null
                && (userId.equals(order.getUserId()) || userId.equals(order.getSellerId()));
        if (!owner) {
            throw new BizException("无权操作该订单");
        }
        Schedule schedule = getSchedule(order.getScheduleId());
        if (!"SELLING".equals(schedule.getStatus())) {
            throw new BizException("班次不在售票中，无法支付");
        }
        // 支付超时：交由定时任务取消，避免在事务内先释放再抛异常导致回滚
        if (LocalDateTime.now().isAfter(order.getCreateTime().plusMinutes(LOCK_MINUTES))) {
            throw new BizException("支付超时，订单将被自动取消");
        }
        if (orderDao.markPaid(orderId, LocalDateTime.now()) == 0) {
            throw new BizException("订单状态已变更，请刷新后重试");
        }
        List<Ticket> tickets = ticketDao.listByOrder(orderId);
        if (tickets.isEmpty()) {
            throw new BizException("订单没有船票");
        }
        for (Ticket t : tickets) {
            if (scheduleSeatDao.markSold(t.getScheduleId(), t.getSeatNo(), orderId) == 0) {
                throw new BizException("座位 " + t.getSeatNo() + " 锁定已失效，请重新下单");
            }
            if (ticketDao.updateStatusIf(t.getId(), "UNPAID", "PAID") == 0) {
                throw new BizException("船票状态已变更，请刷新后重试");
            }
            scheduleDao.incrementSold(t.getScheduleId(), 1);
        }
    }

    @Override
    @Transactional
    public void cancelOrder(Long orderId, Long userId) {
        Order order = orderDao.findById(orderId);
        if (order == null) {
            throw new BizException("订单不存在");
        }
        if (!"UNPAID".equals(order.getStatus())) {
            throw new BizException("仅待支付订单可取消");
        }
        if (userId != null && !userId.equals(order.getUserId())) {
            throw new BizException("无权操作该订单");
        }
        cancelAndRelease(order);
    }

    @Override
    @Transactional
    public void refund(Long orderId, Long operatorId, String operatorRole, String reason) {
        Order order = orderDao.findById(orderId);
        if (order == null) {
            throw new BizException("订单不存在");
        }
        checkRefundPermission(order, operatorId, operatorRole);
        Schedule schedule = getSchedule(order.getScheduleId());
        LocalDateTime now = LocalDateTime.now();
        if (!now.isBefore(schedule.getDepartTime())) {
            throw new BizException("班次已发船，不可退票");
        }

        List<Ticket> tickets = ticketDao.listByOrder(orderId);
        if (tickets.stream().anyMatch(t -> "CHECKED".equals(t.getStatus()))) {
            throw new BizException("订单中含已检票船票，不可退票");
        }
        if (tickets.stream().anyMatch(t -> "UNPAID".equals(t.getStatus()))) {
            throw new BizException("订单未支付，不可退票");
        }
        List<Ticket> refundable = tickets.stream()
                .filter(t -> "PAID".equals(t.getStatus()))
                .toList();
        if (refundable.isEmpty()) {
            throw new BizException("没有可退的船票");
        }

        long minutesBefore = Duration.between(now, schedule.getDepartTime()).toMinutes();
        BigDecimal totalRefund = BigDecimal.ZERO;
        for (Ticket t : refundable) {
            BigDecimal fee = minutesBefore >= FULL_REFUND_MINUTES
                    ? BigDecimal.ZERO
                    : t.getPrice().multiply(REFUND_FEE_RATE).setScale(2, RoundingMode.HALF_UP);
            BigDecimal refundAmount = t.getPrice().subtract(fee);
            totalRefund = totalRefund.add(refundAmount);

            if (ticketDao.updateStatusIf(t.getId(), "PAID", "REFUNDED") == 0) {
                throw new BizException("船票状态已变更，请刷新后重试");
            }
            scheduleSeatDao.releaseForOrder(t.getScheduleId(), t.getSeatNo(), orderId);
            scheduleDao.decrementSold(t.getScheduleId(), 1);

            Refund refund = new Refund();
            refund.setOrderId(orderId);
            refund.setTicketId(t.getId());
            refund.setRefundAmount(refundAmount);
            refund.setFee(fee);
            refund.setReason(reason);
            refund.setOperatorId(operatorId);
            refund.setBizType(Refund.BIZ_REFUND);
            refundDao.insert(refund);
        }
        recalcOrderStatus(orderId);
        notifyUser(order.getUserId(), "REFUND_SUCCESS", "退票成功",
                "订单 " + order.getOrderNo() + " 退票成功，退款金额 ¥" + totalRefund
                        + (reason == null || reason.isEmpty() ? "" : "，原因：" + reason));
    }

    @Override
    @Transactional
    public void refundForCancellation(Long orderId, Long operatorId) {
        Order order = orderDao.findById(orderId);
        if (order == null) {
            return;
        }
        BigDecimal totalRefund = BigDecimal.ZERO;
        for (Ticket t : ticketDao.listByOrder(orderId)) {
            if (!"PAID".equals(t.getStatus()) && !"CHECKED".equals(t.getStatus())) {
                continue;
            }
            if (ticketDao.updateStatusIf(t.getId(), t.getStatus(), "REFUNDED") == 0) {
                continue;
            }
            scheduleSeatDao.releaseForOrder(t.getScheduleId(), t.getSeatNo(), orderId);
            scheduleDao.decrementSold(t.getScheduleId(), 1);
            totalRefund = totalRefund.add(t.getPrice());

            Refund refund = new Refund();
            refund.setOrderId(orderId);
            refund.setTicketId(t.getId());
            refund.setRefundAmount(t.getPrice());
            refund.setFee(BigDecimal.ZERO);
            refund.setReason("班次取消自动退票");
            refund.setOperatorId(operatorId);
            refund.setBizType(Refund.BIZ_REFUND);
            refundDao.insert(refund);
        }
        recalcOrderStatus(orderId);
        if (totalRefund.compareTo(BigDecimal.ZERO) > 0) {
            notifyUser(order.getUserId(), "SCHEDULE_CANCEL", "班次取消通知",
                    "您订单 " + order.getOrderNo() + " 所在班次已取消，票款 ¥" + totalRefund + " 已全额退还");
        }
    }

    @Override
    @Transactional
    public void reschedule(Long ticketId, Long newScheduleId, String newSeatNo, Long userId) {
        Ticket oldTicket = ticketDao.findById(ticketId);
        if (oldTicket == null) {
            throw new BizException("船票不存在");
        }
        if (!"PAID".equals(oldTicket.getStatus())) {
            throw new BizException("仅已支付且未检票的船票可改签");
        }
        Order order = orderDao.findById(oldTicket.getOrderId());
        if (order == null) {
            throw new BizException("订单不存在");
        }
        if (userId != null && !userId.equals(order.getUserId())) {
            throw new BizException("无权操作该订单");
        }
        if (newSeatNo == null || newSeatNo.isEmpty()) {
            throw new BizException("请选择新座位");
        }
        Schedule oldSchedule = getSchedule(oldTicket.getScheduleId());
        // 锁定目标班次行，串行化“目标班次同一身份证”校验与座位锁定
        Schedule newSchedule = lockSchedule(newScheduleId);
        if (newSchedule.getId().equals(oldSchedule.getId())) {
            throw new BizException("改签班次不能与原班次相同");
        }
        if (!"SELLING".equals(newSchedule.getStatus())) {
            throw new BizException("目标班次不在售票中");
        }
        LocalDateTime now = LocalDateTime.now();
        if (!now.isBefore(newSchedule.getDepartTime())) {
            throw new BizException("目标班次已发船");
        }
        // 发船前1小时以上可改签
        if (now.plusHours(1).isAfter(oldSchedule.getDepartTime())) {
            throw new BizException("发船前1小时内不可改签");
        }
        int dup = ticketDao.countByScheduleAndIdCard(newScheduleId, oldTicket.getIdCard());
        if (dup > 0) {
            throw new BizException("该身份证在目标班次已购票");
        }
        // 锁定目标座位（原子操作）
        if (scheduleSeatDao.lock(newScheduleId, newSeatNo, order.getId(), userId, now) == 0) {
            throw new BizException(seatLockFailureReason(newScheduleId, newSeatNo));
        }
        BigDecimal priceDiff = newSchedule.getPrice().subtract(oldTicket.getPrice());

        // 原票作废并释放座位（按票所属班次释放）
        // 注意：改签作废用 RESCHEDULED 而非 REFUNDED。二者是不同业务事实，
        // 复用 REFUNDED 会让"退票量/退票原因"等按票状态聚合的统计把改签算成退票。
        if (ticketDao.updateStatusIf(oldTicket.getId(), "PAID", "RESCHEDULED") == 0) {
            throw new BizException("船票状态已变更，请刷新后重试");
        }
        scheduleSeatDao.releaseForOrder(oldTicket.getScheduleId(), oldTicket.getSeatNo(), order.getId());
        scheduleDao.decrementSold(oldTicket.getScheduleId(), 1);

        // 新票
        Ticket newTicket = new Ticket();
        newTicket.setTicketNo(genTicketNo());
        newTicket.setOrderId(order.getId());
        newTicket.setScheduleId(newScheduleId);
        newTicket.setSeatNo(newSeatNo);
        newTicket.setPassengerName(oldTicket.getPassengerName());
        newTicket.setIdCard(oldTicket.getIdCard());
        newTicket.setPhone(oldTicket.getPhone());
        newTicket.setPrice(newSchedule.getPrice());
        newTicket.setStatus("PAID");
        ticketDao.insert(newTicket);
        if (scheduleSeatDao.markSold(newScheduleId, newSeatNo, order.getId()) == 0) {
            throw new BizException("目标座位锁定已失效");
        }
        scheduleDao.incrementSold(newScheduleId, 1);

        // 改签日志
        Reschedule rs = new Reschedule();
        rs.setOldTicketId(oldTicket.getId());
        rs.setNewTicketId(newTicket.getId());
        rs.setOldScheduleId(oldTicket.getScheduleId());
        rs.setNewScheduleId(newScheduleId);
        rs.setPriceDiff(priceDiff);
        rescheduleDao.insert(rs);

        // 差价双向结算：新票更贵需补款，更便宜则记录退款
        // 这笔钱是"改签退还差价"，不是退票，故打 RESCHEDULE_DIFF 标记，避免污染退票统计
        if (priceDiff.compareTo(BigDecimal.ZERO) < 0) {
            Refund refund = new Refund();
            refund.setOrderId(order.getId());
            refund.setTicketId(newTicket.getId());
            refund.setRefundAmount(priceDiff.abs());
            refund.setFee(BigDecimal.ZERO);
            refund.setReason("改签退还差价");
            refund.setOperatorId(userId);
            refund.setBizType(Refund.BIZ_RESCHEDULE_DIFF);
            refundDao.insert(refund);
        }
        recalcOrderStatus(order.getId());
        notifyUser(order.getUserId(), "RESCHEDULE", "改签成功",
                "船票 " + oldTicket.getTicketNo() + " 已改签至 " + newSchedule.getDepartTime()
                        + "，座位 " + newSeatNo + "，差价 ¥" + priceDiff);
    }

    @Override
    @Transactional
    public void checkIn(String code, Long checkerId, Long scheduleId) {
        if (code == null || code.isBlank()) {
            throw new BizException("请输入船票编号或订单号");
        }
        String key = code.trim();
        Ticket ticket = ticketDao.findByTicketNo(key);
        if (ticket != null) {
            doCheckIn(ticket, checkerId, scheduleId);
            recalcOrderStatus(ticket.getOrderId());
            return;
        }
        Order order = orderDao.findByOrderNo(key);
        if (order == null) {
            throw new BizException("船票或订单不存在");
        }
        List<Ticket> tickets = ticketDao.listByOrder(order.getId()).stream()
                .filter(t -> !"CANCELLED".equals(t.getStatus())
                        && !"REFUNDED".equals(t.getStatus())
                        && !"RESCHEDULED".equals(t.getStatus()))
                .toList();
        if (tickets.isEmpty()) {
            throw new BizException("订单没有可检票的船票");
        }
        for (Ticket t : tickets) {
            if (!"PAID".equals(t.getStatus())) {
                throw new BizException("订单中包含已检票或未支付的船票，无法整单检票");
            }
            doCheckIn(t, checkerId, scheduleId);
        }
        recalcOrderStatus(order.getId());
    }

    private void doCheckIn(Ticket ticket, Long checkerId, Long scheduleId) {
        if (!"PAID".equals(ticket.getStatus())) {
            if ("CHECKED".equals(ticket.getStatus())) {
                throw new BizException("该票已检票");
            } else if ("REFUNDED".equals(ticket.getStatus())) {
                throw new BizException("该票已退票");
            } else if ("RESCHEDULED".equals(ticket.getStatus())) {
                throw new BizException("该票已改签，请使用改签后的新票检票");
            } else if ("CANCELLED".equals(ticket.getStatus())) {
                throw new BizException("该票已取消");
            } else {
                throw new BizException("该票未支付，不可检票");
            }
        }
        if (scheduleId != null && !scheduleId.equals(ticket.getScheduleId())) {
            throw new BizException("该票不属于所选班次");
        }
        Schedule schedule = getSchedule(ticket.getScheduleId());
        if (LocalDateTime.now().isAfter(schedule.getDepartTime().plusHours(2))) {
            throw new BizException("该票已过期");
        }
        if (ticketDao.markChecked(ticket.getId(), LocalDateTime.now(), checkerId) == 0) {
            throw new BizException("船票状态已变更，请刷新后重试");
        }
    }

    @Override
    @Transactional
    public void recalcOrderStatus(Long orderId) {
        Order order = orderDao.findById(orderId);
        if (order == null) {
            return;
        }
        List<Ticket> tickets = ticketDao.listByOrder(orderId);
        List<Ticket> active = tickets.stream()
                .filter(t -> "UNPAID".equals(t.getStatus())
                        || "PAID".equals(t.getStatus())
                        || "CHECKED".equals(t.getStatus()))
                .toList();

        String status;
        if (!active.isEmpty()) {
            boolean allChecked = active.stream().allMatch(t -> "CHECKED".equals(t.getStatus()));
            boolean anyPaid = active.stream().anyMatch(t -> "PAID".equals(t.getStatus()));
            if (allChecked) {
                Schedule schedule = order.getScheduleId() == null ? null : scheduleDao.findById(order.getScheduleId());
                status = schedule != null && "FINISHED".equals(schedule.getStatus()) ? "FINISHED" : "CHECKED";
            } else if (anyPaid) {
                status = "PAID";
            } else {
                status = "UNPAID";
            }
        } else if (tickets.stream().anyMatch(t -> "REFUNDED".equals(t.getStatus()))) {
            status = "REFUNDED";
        } else if (tickets.stream().anyMatch(t -> "CANCELLED".equals(t.getStatus()))) {
            status = "CANCELLED";
        } else {
            status = "UNPAID";
        }
        if (!status.equals(order.getStatus())) {
            orderDao.updateStatus(orderId, status);
        }

        // 订单有效金额与所属班次由有效票推导
        if (!active.isEmpty()) {
            BigDecimal amount = active.stream()
                    .map(Ticket::getPrice)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            Set<Long> scheduleIds = active.stream().map(Ticket::getScheduleId).collect(Collectors.toSet());
            Long scheduleId = scheduleIds.size() == 1 ? scheduleIds.iterator().next() : order.getScheduleId();
            boolean amountChanged = order.getTotalAmount() == null
                    || amount.compareTo(order.getTotalAmount()) != 0;
            boolean scheduleChanged = !Objects.equals(scheduleId, order.getScheduleId());
            if (amountChanged || scheduleChanged) {
                orderDao.updateAmountAndSchedule(orderId, amount, scheduleId);
            }
        }
    }

    @Override
    public Order getById(Long id) {
        return orderDao.findById(id);
    }

    @Override
    public Order getByOrderNo(String orderNo) {
        return orderDao.findByOrderNo(orderNo);
    }

    @Override
    public List<Order> listByUser(Long userId, String status, int page, int size) {
        int offset = (page - 1) * size;
        return orderDao.listByUser(userId, status, offset, size);
    }

    @Override
    public long countByUser(Long userId, String status) {
        return orderDao.countByUser(userId, status);
    }

    @Override
    public List<Order> search(String date, Long scheduleId, String passengerName, Long sellerId, int page, int size) {
        int offset = (page - 1) * size;
        return orderDao.search(date, scheduleId, passengerName, sellerId, offset, size);
    }

    @Override
    public long countSearch(String date, Long scheduleId, String passengerName, Long sellerId) {
        return orderDao.countSearch(date, scheduleId, passengerName, sellerId);
    }

    @Override
    public List<Ticket> listTicketsByOrder(Long orderId) {
        return ticketDao.listByOrder(orderId);
    }

    @Override
    public List<Ticket> listTicketsBySchedule(Long scheduleId) {
        return ticketDao.listBySchedule(scheduleId);
    }

    @Override
    public List<Ticket> listMyTickets(Long userId) {
        return ticketDao.listByUser(userId, null);
    }

    private void checkRefundPermission(Order order, Long operatorId, String operatorRole) {
        if ("ADMIN".equals(operatorRole)) {
            return;
        }
        if ("SELLER".equals(operatorRole)) {
            if (!Objects.equals(order.getSellerId(), operatorId)) {
                throw new BizException("只能退自己售出的订单");
            }
            return;
        }
        // 乘客：只能退本人订单
        if (!Objects.equals(order.getUserId(), operatorId)) {
            throw new BizException("无权操作该订单");
        }
    }

    private void cancelAndRelease(Order order) {
        for (Ticket t : ticketDao.listByOrder(order.getId())) {
            if (!"UNPAID".equals(t.getStatus())) {
                continue;
            }
            if (ticketDao.updateStatusIf(t.getId(), "UNPAID", "CANCELLED") == 0) {
                continue;
            }
            scheduleSeatDao.releaseForOrder(t.getScheduleId(), t.getSeatNo(), order.getId());
        }
        orderDao.cancelIfUnpaid(order.getId());
    }

    private void notifyUser(Long userId, String type, String title, String content) {
        if (userId == null) {
            return;
        }
        Notification n = new Notification();
        n.setUserId(userId);
        n.setType(type);
        n.setTitle(title);
        n.setContent(content);
        notificationDao.insert(n);
    }

    private String genTicketNo() {
        return genNo("T");
    }

    /** 单调递增序列，保证同一毫秒内的单号不重复 */
    private String genNo(String prefix) {
        int seq = Math.floorMod(NO_SEQ.getAndIncrement(), 1000);
        return prefix + NO_FMT.format(LocalDateTime.now()) + String.format("%03d", seq);
    }

    /**
     * 座位锁定失败的具体原因。
     * lock() 返回 0 有两种可能：座位在本班次不存在，或被他人锁定/已售。
     * 区分开才能给用户准确提示（任务书要求按不同失败原因给出明确提示）。
     */
    private String seatLockFailureReason(Long scheduleId, String seatNo) {
        ScheduleSeat seat = scheduleSeatDao.findByScheduleAndSeat(scheduleId, seatNo);
        if (seat == null) {
            return "座位 " + seatNo + " 在该班次不存在，请刷新座位图后重试";
        }
        if ("SOLD".equals(seat.getStatus())) {
            return "座位 " + seatNo + " 已售出，请选择其他座位";
        }
        return "座位 " + seatNo + " 已被他人锁定，请选择其他座位";
    }

    private Schedule getSchedule(Long id) {
        Schedule s = scheduleDao.findById(id);
        if (s == null || s.getDeleted() == 1) {
            throw new BizException("班次不存在");
        }
        return s;
    }

    private Schedule lockSchedule(Long id) {
        Schedule s = scheduleDao.findByIdForUpdate(id);
        if (s == null || s.getDeleted() == 1) {
            throw new BizException("班次不存在");
        }
        return s;
    }
}
