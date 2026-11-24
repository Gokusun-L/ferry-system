package com.ferry.service.impl;

import com.ferry.dao.StatsDao;
import com.ferry.service.StatsService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class StatsServiceImpl implements StatsService {

    private final StatsDao statsDao;
    private static final double LOW_THRESHOLD = 50.0;

    @Override
    public List<Map<String, Object>> statsByDate(LocalDate start, LocalDate end) {
        return statsDao.statsByDate(start, end);
    }

    @Override
    public List<Map<String, Object>> statsByPeriod(LocalDate start, LocalDate end, String groupBy) {
        String g = "week".equals(groupBy) || "month".equals(groupBy) ? groupBy : "day";
        return statsDao.statsByPeriod(start, end, g);
    }

    @Override
    public List<Map<String, Object>> statsByRoute(LocalDate start, LocalDate end) {
        return statsDao.statsByRoute(start, end);
    }

    @Override
    public List<Map<String, Object>> statsBySchedule(LocalDate start, LocalDate end) {
        return statsDao.statsBySchedule(start, end);
    }

    @Override
    public List<Map<String, Object>> statsBySeller(LocalDate start, LocalDate end) {
        return statsDao.statsBySeller(start, end);
    }

    @Override
    public Map<String, Object> statsSingleSeller(Long sellerId, LocalDate start, LocalDate end) {
        return statsDao.statsSingleSeller(sellerId, start, end);
    }

    @Override
    public List<Map<String, Object>> scheduleOccupancy() {
        return statsDao.scheduleOccupancy();
    }

    @Override
    public List<Map<String, Object>> routeOccupancy() {
        return statsDao.routeOccupancy();
    }

    @Override
    public List<Map<String, Object>> occupancyByPeriod() {
        return statsDao.occupancyByPeriod();
    }

    @Override
    public List<Map<String, Object>> lowOccupancy() {
        return statsDao.lowOccupancy(LOW_THRESHOLD);
    }

    @Override
    public Map<String, Object> incomeSummary(LocalDate start, LocalDate end) {
        return statsDao.incomeSummary(start, end);
    }

    @Override
    public List<Map<String, Object>> refundStats(LocalDate start, LocalDate end) {
        return statsDao.refundStats(start, end);
    }
}
