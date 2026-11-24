package com.ferry.service;

import com.ferry.entity.Order;
import com.ferry.entity.Ticket;
import java.util.List;

public interface OrderService {
    /** 锁定座位（选座） */
    void lockSeats(Long scheduleId, List<String> seatNos, Long userId);
    /** 提交订单（下单） */
    Order createOrder(Long scheduleId, Long userId, Long sellerId, List<Ticket> tickets);
    /** 模拟支付 */
    void pay(Long orderId, Long userId);
    /** 取消订单 */
    void cancelOrder(Long orderId, Long userId);
    /** 退票（按角色校验归属：乘客本人 / 售票员本人售出 / 管理员） */
    void refund(Long orderId, Long operatorId, String operatorRole, String reason);
    /** 班次取消时全额退票（含已检票） */
    void refundForCancellation(Long orderId, Long operatorId);
    /** 按船票状态重算订单状态、有效金额与所属班次 */
    void recalcOrderStatus(Long orderId);
    /** 改签 */
    void reschedule(Long ticketId, Long newScheduleId, String newSeatNo, Long userId);
    /** 班次座位图（全部座位及其状态） */
    java.util.List<com.ferry.entity.ScheduleSeat> listSeatMap(Long scheduleId);
    /** 取消选座锁定（仅本人锁定） */
    void unlockSeats(Long scheduleId, java.util.List<String> seatNos, Long userId);
    /** 检票：支持船票编号或订单号，scheduleId 不为空时校验班次归属 */
    void checkIn(String code, Long checkerId, Long scheduleId);
    /** 查询 */
    Order getById(Long id);
    Order getByOrderNo(String orderNo);
    List<Order> listByUser(Long userId, String status, int page, int size);
    long countByUser(Long userId, String status);
    List<Order> search(String date, Long scheduleId, String passengerName, Long sellerId, int page, int size);
    long countSearch(String date, Long scheduleId, String passengerName, Long sellerId);
    List<Ticket> listTicketsByOrder(Long orderId);
    List<Ticket> listTicketsBySchedule(Long scheduleId);
    List<Ticket> listMyTickets(Long userId);
}
