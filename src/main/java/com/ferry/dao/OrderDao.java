package com.ferry.dao;

import com.ferry.entity.Order;
import org.apache.ibatis.annotations.Param;
import java.util.List;

public interface OrderDao {
    int insert(Order order);
    Order findById(@Param("id") Long id);
    Order findByOrderNo(@Param("orderNo") String orderNo);
    int updateStatus(@Param("id") Long id, @Param("status") String status);
    /** 仅当订单当前为 UNPAID 时取消，返回受影响行数 */
    int cancelIfUnpaid(@Param("id") Long id);
    int markPaid(@Param("id") Long id, @Param("payTime") java.time.LocalDateTime payTime);
    /** 重算订单有效金额与所属班次（改签后） */
    int updateAmountAndSchedule(@Param("id") Long id, @Param("totalAmount") java.math.BigDecimal totalAmount,
                                @Param("scheduleId") Long scheduleId);
    /** 班次完成时，将已检票订单置为已完成 */
    int finishCheckedBySchedule(@Param("scheduleId") Long scheduleId);
    List<Order> listByUser(@Param("userId") Long userId, @Param("status") String status,
                           @Param("offset") int offset, @Param("limit") int limit);
    long countByUser(@Param("userId") Long userId, @Param("status") String status);
    List<Order> search(@Param("date") String date, @Param("scheduleId") Long scheduleId,
                       @Param("passengerName") String passengerName, @Param("sellerId") Long sellerId,
                       @Param("offset") int offset, @Param("limit") int limit);
    long countSearch(@Param("date") String date, @Param("scheduleId") Long scheduleId,
                     @Param("passengerName") String passengerName, @Param("sellerId") Long sellerId);
    /** 超时未支付订单 */
    List<Order> listExpiredUnpaid(@Param("now") java.time.LocalDateTime now);
    List<Order> listPaidBySchedule(@Param("scheduleId") Long scheduleId);
    /** 售票员业绩统计用 */
    List<Order> listPaidBySeller(@Param("sellerId") Long sellerId);
}
