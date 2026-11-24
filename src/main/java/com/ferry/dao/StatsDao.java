package com.ferry.dao;

import org.apache.ibatis.annotations.Param;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 统计报表 DAO（聚合查询，考核重点）
 */
public interface StatsDao {

    /** 按日期统计：每日售票量、退票量、售票金额 */
    List<Map<String, Object>> statsByDate(@Param("start") LocalDate start, @Param("end") LocalDate end);

    /** 按日/周/月统计：售票量、退票量、金额 */
    List<Map<String, Object>> statsByPeriod(@Param("start") LocalDate start, @Param("end") LocalDate end,
                                            @Param("groupBy") String groupBy);

    /** 按航线统计售票量与金额 */
    List<Map<String, Object>> statsByRoute(@Param("start") LocalDate start, @Param("end") LocalDate end);

    /** 按班次统计售票数、退票数、收入 */
    List<Map<String, Object>> statsBySchedule(@Param("start") LocalDate start, @Param("end") LocalDate end);

    /** 售票员业绩排名 */
    List<Map<String, Object>> statsBySeller(@Param("start") LocalDate start, @Param("end") LocalDate end);

    /** 某售票员个人业绩 */
    Map<String, Object> statsSingleSeller(@Param("sellerId") Long sellerId,
                                          @Param("start") LocalDate start, @Param("end") LocalDate end);

    /** 班次上座率 */
    List<Map<String, Object>> scheduleOccupancy();

    /** 航线平均上座率排名 */
    List<Map<String, Object>> routeOccupancy();

    /** 时间段（早/午/晚班）上座率对比 */
    List<Map<String, Object>> occupancyByPeriod();

    /** 低上座率预警（<50%） */
    List<Map<String, Object>> lowOccupancy(@Param("threshold") double threshold);

    /** 收入统计：总/退票损失/净收入 */
    Map<String, Object> incomeSummary(@Param("start") LocalDate start, @Param("end") LocalDate end);

    /** 退票统计：退票率、退票金额、原因分布 */
    List<Map<String, Object>> refundStats(@Param("start") LocalDate start, @Param("end") LocalDate end);
}
