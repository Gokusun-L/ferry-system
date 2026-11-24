package com.ferry.dao;

import com.ferry.entity.ScheduleSeat;
import org.apache.ibatis.annotations.Param;
import java.util.List;

public interface ScheduleSeatDao {
    int insertBatch(@Param("list") List<ScheduleSeat> list);
    List<ScheduleSeat> listBySchedule(@Param("scheduleId") Long scheduleId);

    /**
     * 锁定座位（并发安全）：AVAILABLE，或已被同一用户锁定的座位可再次锁定。
     * 返回受影响行数，0 表示座位已被他人占用
     */
    int lock(@Param("scheduleId") Long scheduleId, @Param("seatNo") String seatNo,
             @Param("orderId") Long orderId, @Param("lockUserId") Long lockUserId,
             @Param("lockTime") java.time.LocalDateTime lockTime);

    /** 锁定->已售 */
    int markSold(@Param("scheduleId") Long scheduleId, @Param("seatNo") String seatNo,
                 @Param("orderId") Long orderId);

    /** 释放座位（锁定->可售，或已售->可售） */
    int release(@Param("scheduleId") Long scheduleId, @Param("seatNo") String seatNo);

    /** 仅释放属于指定订单的座位 */
    int releaseForOrder(@Param("scheduleId") Long scheduleId, @Param("seatNo") String seatNo,
                        @Param("orderId") Long orderId);

    /** 用户主动取消选座：仅释放本人锁定且未关联订单的座位 */
    int unlock(@Param("scheduleId") Long scheduleId, @Param("seatNo") String seatNo,
               @Param("lockUserId") Long lockUserId);

    /** 释放指定订单锁定的所有座位 */
    int releaseByOrder(@Param("orderId") Long orderId);

    /** 超时锁定座位（锁定时间超过5分钟） */
    List<ScheduleSeat> listExpiredLock(@Param("now") java.time.LocalDateTime now);

    /** 批量释放超时锁定座位 */
    int releaseExpiredLocks(@Param("now") java.time.LocalDateTime now);

    /** 释放某班次全部座位（班次取消时） */
    int releaseAllBySchedule(@Param("scheduleId") Long scheduleId);

    /** 删除某班次座位记录（换船重建时，需无订单） */
    int deleteBySchedule(@Param("scheduleId") Long scheduleId);

    ScheduleSeat findByScheduleAndSeat(@Param("scheduleId") Long scheduleId, @Param("seatNo") String seatNo);
    int countAvailable(@Param("scheduleId") Long scheduleId);
}
