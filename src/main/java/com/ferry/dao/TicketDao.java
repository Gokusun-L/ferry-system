package com.ferry.dao;

import com.ferry.entity.Ticket;
import org.apache.ibatis.annotations.Param;
import java.util.List;

public interface TicketDao {
    int insert(Ticket ticket);
    int insertBatch(@Param("list") List<Ticket> list);
    Ticket findById(@Param("id") Long id);
    Ticket findByTicketNo(@Param("ticketNo") String ticketNo);
    List<Ticket> listByOrder(@Param("orderId") Long orderId);
    List<Ticket> listBySchedule(@Param("scheduleId") Long scheduleId);
    List<Ticket> listByUser(@Param("userId") Long userId, @Param("status") String status);
    int updateStatus(@Param("id") Long id, @Param("status") String status);
    /** 条件更新：仅当前状态等于 from 时才更新为 to，返回受影响行数 */
    int updateStatusIf(@Param("id") Long id, @Param("from") String from, @Param("to") String to);
    int markChecked(@Param("id") Long id, @Param("checkTime") java.time.LocalDateTime checkTime, @Param("checkerId") Long checkerId);
    /** 一人一班次一票校验 */
    int countByScheduleAndIdCard(@Param("scheduleId") Long scheduleId, @Param("idCard") String idCard);
}
