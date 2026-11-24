package com.ferry.dao;

import com.ferry.entity.Schedule;
import org.apache.ibatis.annotations.Param;
import java.time.LocalDateTime;
import java.util.List;

public interface ScheduleDao {
    List<Schedule> search(@Param("routeId") Long routeId, @Param("shipId") Long shipId,
                          @Param("date") String date, @Param("status") String status,
                          @Param("offset") int offset, @Param("limit") int limit);
    long count(@Param("routeId") Long routeId, @Param("shipId") Long shipId,
               @Param("date") String date, @Param("status") String status);
    Schedule findById(@Param("id") Long id);
    /** 事务内锁定班次行，用于串行化同一班次的购票/改签校验 */
    Schedule findByIdForUpdate(@Param("id") Long id);
    int insert(Schedule schedule);
    int insertBatch(@Param("list") List<Schedule> list);
    int update(Schedule schedule);
    int updateStatus(@Param("id") Long id, @Param("status") String status);
    int logicDelete(@Param("id") Long id);
    int incrementSold(@Param("id") Long id, @Param("count") int count);
    int decrementSold(@Param("id") Long id, @Param("count") int count);
    /** 同一艘船同一时间冲突检查 */
    int countConflict(@Param("shipId") Long shipId, @Param("departTime") LocalDateTime departTime,
                      @Param("arriveTime") LocalDateTime arriveTime, @Param("excludeId") Long excludeId);
    int countUnfinishedOrder(@Param("scheduleId") Long scheduleId);
    List<Schedule> listForPortSearch(@Param("departPort") String departPort, @Param("arrivePort") String arrivePort,
                                     @Param("date") String date);
    /** 已发船但未完成的班次，供定时任务 */
    List<Schedule> listDepartedUnfinished();
    /** 已到发船时间但仍在售票的班次，供定时任务 */
    List<Schedule> listSellingToDepart(@Param("now") LocalDateTime now);
}
