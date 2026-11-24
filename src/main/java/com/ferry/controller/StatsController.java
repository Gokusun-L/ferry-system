package com.ferry.controller;

import com.ferry.common.LoginUser;
import com.ferry.common.RequireRole;
import com.ferry.common.Result;
import com.ferry.service.StatsService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 统计报表接口
 */
@RestController
@RequestMapping("/api/stats")
@RequiredArgsConstructor
@RequireRole("ADMIN")
public class StatsController {

    private final StatsService statsService;

    @GetMapping("/by-date")
    public Result<List<Map<String, Object>>> byDate(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                                                    @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end) {
        return Result.ok(statsService.statsByDate(start, end));
    }

    @GetMapping("/period")
    public Result<List<Map<String, Object>>> byPeriod(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                                                      @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
                                                      @RequestParam(defaultValue = "day") String groupBy) {
        return Result.ok(statsService.statsByPeriod(start, end, groupBy));
    }

    @GetMapping("/by-route")
    public Result<List<Map<String, Object>>> byRoute(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                                                     @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end) {
        return Result.ok(statsService.statsByRoute(start, end));
    }

    @GetMapping("/by-schedule")
    public Result<List<Map<String, Object>>> bySchedule(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                                                        @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end) {
        return Result.ok(statsService.statsBySchedule(start, end));
    }

    @GetMapping("/by-seller")
    public Result<List<Map<String, Object>>> bySeller(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                                                      @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end) {
        return Result.ok(statsService.statsBySeller(start, end));
    }

    @RequireRole({"ADMIN", "SELLER"})
    @GetMapping("/my-performance")
    public Result<Map<String, Object>> myPerformance(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                                                     @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
                                                     HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        return Result.ok(statsService.statsSingleSeller(user.getId(), start, end));
    }

    @GetMapping("/schedule-occupancy")
    public Result<List<Map<String, Object>>> scheduleOccupancy() {
        return Result.ok(statsService.scheduleOccupancy());
    }

    @GetMapping("/route-occupancy")
    public Result<List<Map<String, Object>>> routeOccupancy() {
        return Result.ok(statsService.routeOccupancy());
    }

    @GetMapping("/period-occupancy")
    public Result<List<Map<String, Object>>> periodOccupancy() {
        return Result.ok(statsService.occupancyByPeriod());
    }

    @GetMapping("/low-occupancy")
    public Result<List<Map<String, Object>>> lowOccupancy() {
        return Result.ok(statsService.lowOccupancy());
    }

    @GetMapping("/income")
    public Result<Map<String, Object>> income(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                                              @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end) {
        return Result.ok(statsService.incomeSummary(start, end));
    }

    @GetMapping("/refund")
    public Result<List<Map<String, Object>>> refund(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                                                    @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end) {
        return Result.ok(statsService.refundStats(start, end));
    }
}
