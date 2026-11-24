package com.ferry.service;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public interface StatsService {
    List<Map<String, Object>> statsByDate(LocalDate start, LocalDate end);
    List<Map<String, Object>> statsByPeriod(LocalDate start, LocalDate end, String groupBy);
    List<Map<String, Object>> statsByRoute(LocalDate start, LocalDate end);
    List<Map<String, Object>> statsBySchedule(LocalDate start, LocalDate end);
    List<Map<String, Object>> statsBySeller(LocalDate start, LocalDate end);
    Map<String, Object> statsSingleSeller(Long sellerId, LocalDate start, LocalDate end);
    List<Map<String, Object>> scheduleOccupancy();
    List<Map<String, Object>> routeOccupancy();
    List<Map<String, Object>> occupancyByPeriod();
    List<Map<String, Object>> lowOccupancy();
    Map<String, Object> incomeSummary(LocalDate start, LocalDate end);
    List<Map<String, Object>> refundStats(LocalDate start, LocalDate end);
}
