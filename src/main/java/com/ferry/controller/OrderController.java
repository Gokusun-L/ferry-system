package com.ferry.controller;

import com.ferry.common.BizException;
import com.ferry.common.LoginUser;
import com.ferry.common.PageResult;
import com.ferry.common.RequireRole;
import com.ferry.common.Result;
import com.ferry.entity.Order;
import com.ferry.entity.Ticket;
import com.ferry.service.OrderService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 售票、订单、检票接口
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;

    /** 选座锁定 */
    @PostMapping("/seats/lock")
    public Result<Void> lockSeats(@RequestBody Map<String, Object> body, HttpSession session) {
        Long scheduleId = requireLong(body, "scheduleId");
        List<String> seatNos = requireSeatNos(body);
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        orderService.lockSeats(scheduleId, seatNos, user.getId());
        return Result.ok();
    }

    /** 下单：线上/线下身份由服务端会话决定，不信任请求体 */
    @PostMapping("/orders")
    public Result<Order> createOrder(@RequestBody Map<String, Object> body, HttpSession session) {
        Long scheduleId = requireLong(body, "scheduleId");
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        Long userId = null;
        Long sellerId = null;
        if ("PASSENGER".equals(user.getRole())) {
            userId = user.getId();
        } else {
            sellerId = user.getId();
        }
        List<Ticket> tickets = convertTickets(body.get("tickets"));
        Order order = orderService.createOrder(scheduleId, userId, sellerId, tickets);
        return Result.ok(order);
    }

    /** 支付 */
    @PostMapping("/orders/{id}/pay")
    public Result<Void> pay(@PathVariable Long id, HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        orderService.pay(id, user.getId());
        return Result.ok();
    }

    /** 取消订单 */
    @PostMapping("/orders/{id}/cancel")
    public Result<Void> cancel(@PathVariable Long id, HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        orderService.cancelOrder(id, user.getId());
        return Result.ok();
    }

    /** 退票 */
    @PostMapping("/orders/{id}/refund")
    public Result<Void> refund(@PathVariable Long id, @RequestBody Map<String, String> body, HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        String reason = body.get("reason");
        orderService.refund(id, user.getId(), user.getRole(), reason);
        return Result.ok();
    }

    /** 改签 */
    @PostMapping("/tickets/{id}/reschedule")
    public Result<Void> reschedule(@PathVariable Long id, @RequestBody Map<String, String> body, HttpSession session) {
        Long newScheduleId = requireLong(body, "newScheduleId");
        String newSeatNo = body.get("newSeatNo");
        if (newSeatNo == null || newSeatNo.isBlank()) {
            throw new BizException("请选择新座位");
        }
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        orderService.reschedule(id, newScheduleId, newSeatNo, user.getId());
        return Result.ok();
    }

    /** 检票 */
    @RequireRole({"ADMIN", "SELLER"})
    @PostMapping("/checkin")
    public Result<Void> checkin(@RequestBody Map<String, String> body, HttpSession session) {
        String code = body.get("ticketNo");
        if (code == null || code.isBlank()) {
            throw new BizException("请输入船票编号或订单号");
        }
        Long scheduleId = body.get("scheduleId") == null || body.get("scheduleId").isEmpty()
                ? null : Long.valueOf(body.get("scheduleId"));
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        orderService.checkIn(code, user.getId(), scheduleId);
        return Result.ok();
    }

    /** 我的订单 */
    @RequireRole("PASSENGER")
    @GetMapping("/orders/my")
    public Result<PageResult<Order>> myOrders(@RequestParam(defaultValue = "1") int page,
                                              @RequestParam(defaultValue = "10") int size,
                                              @RequestParam(required = false) String status,
                                              HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        return Result.ok(PageResult.of(
                orderService.listByUser(user.getId(), status, page, size),
                orderService.countByUser(user.getId(), status),
                page, size));
    }

    /** 订单列表（管理端） */
    @RequireRole({"ADMIN", "SELLER"})
    @GetMapping("/orders")
    public Result<PageResult<Order>> listOrders(@RequestParam(defaultValue = "1") int page,
                                                @RequestParam(defaultValue = "10") int size,
                                                @RequestParam(required = false) String date,
                                                @RequestParam(required = false) Long scheduleId,
                                                @RequestParam(required = false) String passengerName,
                                                HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        Long sellerId = "SELLER".equals(user.getRole()) ? user.getId() : null;
        return Result.ok(PageResult.of(
                orderService.search(date, scheduleId, passengerName, sellerId, page, size),
                orderService.countSearch(date, scheduleId, passengerName, sellerId),
                page, size));
    }

    /** 按订单号查询（售票员退票用，仅本人售出） */
    @RequireRole({"ADMIN", "SELLER"})
    @GetMapping("/orders/no/{orderNo}")
    public Result<Map<String, Object>> orderByNo(@PathVariable String orderNo, HttpSession session) {
        Order order = orderService.getByOrderNo(orderNo);
        if (order == null) {
            throw new BizException("订单不存在");
        }
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        if ("SELLER".equals(user.getRole()) && !user.getId().equals(order.getSellerId())) {
            throw new BizException("只能查询自己售出的订单");
        }
        Map<String, Object> data = new HashMap<>();
        data.put("order", order);
        data.put("tickets", orderService.listTicketsByOrder(order.getId()));
        return Result.ok(data);
    }

    /** 订单详情 */
    @GetMapping("/orders/{id}")
    public Result<Map<String, Object>> orderDetail(@PathVariable Long id, HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        Order order = orderService.getById(id);
        if (order == null) {
            throw new BizException("订单不存在");
        }
        // 乘客只能查看自己的订单；售票员只能查看自己售出的订单
        if ("PASSENGER".equals(user.getRole()) && !user.getId().equals(order.getUserId())) {
            throw new BizException("无权查看该订单");
        }
        if ("SELLER".equals(user.getRole()) && !user.getId().equals(order.getSellerId())) {
            throw new BizException("只能查看自己售出的订单");
        }
        List<Ticket> tickets = orderService.listTicketsByOrder(id);
        Map<String, Object> data = new HashMap<>();
        data.put("order", order);
        data.put("tickets", tickets);
        return Result.ok(data);
    }

    /** 班次座位图（全部座位三态） */
    @GetMapping("/schedules/{id}/seat-map")
    public Result<List<com.ferry.entity.ScheduleSeat>> seatMap(@PathVariable Long id) {
        return Result.ok(orderService.listSeatMap(id));
    }

    /** 取消选座锁定 */
    @PostMapping("/seats/unlock")
    public Result<Void> unlockSeats(@RequestBody Map<String, Object> body, HttpSession session) {
        Long scheduleId = requireLong(body, "scheduleId");
        List<String> seatNos = requireSeatNos(body);
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        orderService.unlockSeats(scheduleId, seatNos, user.getId());
        return Result.ok();
    }

    /** 我的船票 */
    @RequireRole("PASSENGER")
    @GetMapping("/tickets/my")
    public Result<List<Ticket>> myTickets(HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        return Result.ok(orderService.listMyTickets(user.getId()));
    }

    /** 班次检票记录 */
    @RequireRole({"ADMIN", "SELLER"})
    @GetMapping("/schedules/{id}/tickets")
    public Result<List<Ticket>> scheduleTickets(@PathVariable Long id) {
        return Result.ok(orderService.listTicketsBySchedule(id));
    }

    private List<Ticket> convertTickets(Object obj) {
        if (!(obj instanceof List<?> list) || list.isEmpty()) {
            throw new BizException("请至少添加一张船票");
        }
        List<Ticket> tickets = new ArrayList<>();
        for (Object item : list) {
            if (!(item instanceof Map<?, ?> m)) {
                throw new BizException("船票信息格式错误");
            }
            Ticket t = new Ticket();
            t.setSeatNo(requireText(m, "seatNo", "请选择座位"));
            t.setPassengerName(requireText(m, "passengerName", "请填写乘客姓名"));
            t.setIdCard(requireText(m, "idCard", "请填写乘客身份证号"));
            t.setPhone(m.get("phone") != null ? m.get("phone").toString() : null);
            tickets.add(t);
        }
        return tickets;
    }

    private Long requireLong(Map<?, ?> body, String key) {
        Object value = body.get(key);
        if (value == null || value.toString().isBlank()) {
            throw new BizException("参数不完整：" + key);
        }
        try {
            return Long.valueOf(value.toString());
        } catch (NumberFormatException e) {
            throw new BizException("参数格式错误：" + key);
        }
    }

    private List<String> requireSeatNos(Map<?, ?> body) {
        Object value = body.get("seatNos");
        if (!(value instanceof List<?> list) || list.isEmpty()) {
            throw new BizException("请选择座位");
        }
        List<String> seatNos = new ArrayList<>();
        for (Object seatNo : list) {
            if (seatNo == null || seatNo.toString().isBlank()) {
                throw new BizException("座位号不能为空");
            }
            seatNos.add(seatNo.toString());
        }
        return seatNos;
    }

    private String requireText(Map<?, ?> map, String key, String message) {
        Object value = map.get(key);
        if (value == null || value.toString().isBlank()) {
            throw new BizException(message);
        }
        return value.toString();
    }
}
