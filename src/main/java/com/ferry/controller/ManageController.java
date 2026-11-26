package com.ferry.controller;

import com.ferry.common.BizException;
import com.ferry.common.PageResult;
import com.ferry.common.RequireRole;
import com.ferry.common.Result;
import com.ferry.entity.Route;
import com.ferry.entity.Ship;
import com.ferry.entity.Schedule;
import com.ferry.service.RouteService;
import com.ferry.service.ShipService;
import com.ferry.service.ScheduleService;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 航线、船舶、班次管理接口
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class ManageController {

    private final RouteService routeService;
    private final ShipService shipService;
    private final ScheduleService scheduleService;

    // ===== 航线 =====
    @GetMapping("/routes")
    public Result<PageResult<Route>> listRoutes(@RequestParam(defaultValue = "1") int page,
                                                @RequestParam(defaultValue = "10") int size,
                                                @RequestParam(required = false) String routeName,
                                                @RequestParam(required = false) String departPort,
                                                @RequestParam(required = false) String arrivePort) {
        return Result.ok(PageResult.of(
                routeService.search(routeName, departPort, arrivePort, page, size),
                routeService.count(routeName, departPort, arrivePort),
                page, size));
    }

    @GetMapping("/routes/all")
    public Result<List<Route>> listAllRoutes() {
        return Result.ok(routeService.listAll());
    }

    @RequireRole("ADMIN")
    @PostMapping("/routes")
    public Result<Void> createRoute(@RequestBody Route route) {
        routeService.create(route);
        return Result.ok();
    }

    @RequireRole("ADMIN")
    @PutMapping("/routes/{id}")
    public Result<Void> updateRoute(@PathVariable Long id, @RequestBody Route route) {
        route.setId(id);
        routeService.update(route);
        return Result.ok();
    }

    @RequireRole("ADMIN")
    @DeleteMapping("/routes/{id}")
    public Result<Void> deleteRoute(@PathVariable Long id) {
        routeService.delete(id);
        return Result.ok();
    }

    // ===== 船舶 =====
    @GetMapping("/ships")
    public Result<PageResult<Ship>> listShips(@RequestParam(defaultValue = "1") int page,
                                              @RequestParam(defaultValue = "10") int size,
                                              @RequestParam(required = false) String shipName) {
        return Result.ok(PageResult.of(
                shipService.search(shipName, page, size),
                shipService.count(shipName),
                page, size));
    }

    @GetMapping("/ships/all")
    public Result<List<Ship>> listAllShips() {
        return Result.ok(shipService.listAll());
    }

    @RequireRole("ADMIN")
    @PostMapping("/ships")
    public Result<Void> createShip(@RequestBody Ship ship) {
        shipService.create(ship);
        return Result.ok();
    }

    @RequireRole("ADMIN")
    @PutMapping("/ships/{id}")
    public Result<Void> updateShip(@PathVariable Long id, @RequestBody Ship ship) {
        ship.setId(id);
        shipService.update(ship);
        return Result.ok();
    }

    @RequireRole("ADMIN")
    @DeleteMapping("/ships/{id}")
    public Result<Void> deleteShip(@PathVariable Long id) {
        shipService.delete(id);
        return Result.ok();
    }

    // ===== 班次 =====
    @GetMapping("/schedules")
    public Result<PageResult<Schedule>> listSchedules(@RequestParam(defaultValue = "1") int page,
                                                      @RequestParam(defaultValue = "10") int size,
                                                      @RequestParam(required = false) Long routeId,
                                                      @RequestParam(required = false) Long shipId,
                                                      @RequestParam(required = false) String date,
                                                      @RequestParam(required = false) String status) {
        return Result.ok(PageResult.of(
                scheduleService.search(routeId, shipId, date, status, page, size),
                scheduleService.count(routeId, shipId, date, status),
                page, size));
    }

    @GetMapping("/schedules/{id}")
    public Result<Schedule> getSchedule(@PathVariable Long id) {
        return Result.ok(scheduleService.getById(id));
    }

    @RequireRole("ADMIN")
    @PostMapping("/schedules")
    public Result<Void> createSchedule(@RequestBody Schedule schedule) {
        scheduleService.create(schedule);
        return Result.ok();
    }

    @RequireRole("ADMIN")
    @PostMapping("/schedules/batch")
    public Result<List<Schedule>> batchCreate(@RequestBody Map<String, Object> body) {
        if (body.get("routeId") == null || body.get("shipId") == null || body.get("startDate") == null
                || body.get("endDate") == null || body.get("hour") == null
                || body.get("minute") == null || body.get("price") == null) {
            throw new BizException("请完整填写批量生成参数");
        }
        try {
            Long routeId = Long.valueOf(body.get("routeId").toString());
            Long shipId = Long.valueOf(body.get("shipId").toString());
            LocalDate startDate = LocalDate.parse(body.get("startDate").toString());
            LocalDate endDate = LocalDate.parse(body.get("endDate").toString());
            int hour = Integer.parseInt(body.get("hour").toString());
            int minute = Integer.parseInt(body.get("minute").toString());
            BigDecimal price = new BigDecimal(body.get("price").toString());
            return Result.ok(scheduleService.batchCreate(routeId, shipId, startDate, endDate, hour, minute, price));
        } catch (NumberFormatException | DateTimeParseException e) {
            throw new BizException("批量生成参数格式错误");
        }
    }

    @RequireRole("ADMIN")
    @PutMapping("/schedules/{id}")
    public Result<Void> updateSchedule(@PathVariable Long id, @RequestBody Schedule schedule) {
        schedule.setId(id);
        scheduleService.update(schedule);
        return Result.ok();
    }

    @RequireRole("ADMIN")
    @PostMapping("/schedules/{id}/publish")
    public Result<Void> publishSchedule(@PathVariable Long id) {
        scheduleService.publish(id);
        return Result.ok();
    }

    @RequireRole("ADMIN")
    @PostMapping("/schedules/{id}/cancel")
    public Result<Void> cancelSchedule(@PathVariable Long id) {
        scheduleService.cancel(id);
        return Result.ok();
    }

    @RequireRole("ADMIN")
    @DeleteMapping("/schedules/{id}")
    public Result<Void> deleteSchedule(@PathVariable Long id) {
        scheduleService.delete(id);
        return Result.ok();
    }

    /** 乘客班次查询（按港口+日期） */
    @GetMapping("/schedules/search")
    public Result<List<Schedule>> searchForPassenger(@RequestParam(required = false) String departPort,
                                                     @RequestParam(required = false) String arrivePort,
                                                     @RequestParam(required = false) String date) {
        return Result.ok(scheduleService.listForPortSearch(departPort, arrivePort, date));
    }
}
