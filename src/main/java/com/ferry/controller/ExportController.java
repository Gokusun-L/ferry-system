package com.ferry.controller;

import com.alibaba.excel.EasyExcel;
import com.ferry.common.RequireRole;
import com.ferry.service.StatsService;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 报表导出 Excel
 */
@RestController
@RequestMapping("/api/export")
@RequiredArgsConstructor
@RequireRole("ADMIN")
public class ExportController {

    private final StatsService statsService;

    @GetMapping("/sales")
    public void exportSales(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
                            HttpServletResponse response) throws IOException {
        List<Map<String, Object>> data = statsService.statsByDate(start, end);
        List<List<String>> head = List.of(
                List.of("日期"), List.of("售票量"), List.of("退票量"), List.of("售票金额"), List.of("退票金额"));
        List<List<Object>> rows = new ArrayList<>();
        for (Map<String, Object> row : data) {
            rows.add(List.of(
                    String.valueOf(row.get("statDate")),
                    row.get("saleCount"),
                    row.get("refundCount"),
                    row.get("saleAmount"),
                    row.get("refundAmount")));
        }
        writeExcel(response, "售票统计", head, rows);
    }

    @GetMapping("/route")
    public void exportRoute(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                            @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
                            HttpServletResponse response) throws IOException {
        List<Map<String, Object>> data = statsService.statsByRoute(start, end);
        List<List<String>> head = List.of(List.of("航线"), List.of("售票量"), List.of("售票金额"));
        List<List<Object>> rows = new ArrayList<>();
        for (Map<String, Object> row : data) {
            rows.add(List.of(String.valueOf(row.get("routeName")), row.get("saleCount"), row.get("saleAmount")));
        }
        writeExcel(response, "航线统计", head, rows);
    }

    @GetMapping("/seller")
    public void exportSeller(@RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
                             @RequestParam @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
                             HttpServletResponse response) throws IOException {
        List<Map<String, Object>> data = statsService.statsBySeller(start, end);
        List<List<String>> head = List.of(List.of("售票员"), List.of("售票量"), List.of("售票金额"));
        List<List<Object>> rows = new ArrayList<>();
        for (Map<String, Object> row : data) {
            rows.add(List.of(String.valueOf(row.get("sellerName")), row.get("saleCount"), row.get("saleAmount")));
        }
        writeExcel(response, "售票员业绩", head, rows);
    }

    @GetMapping("/occupancy")
    public void exportOccupancy(HttpServletResponse response) throws IOException {
        List<Map<String, Object>> data = statsService.scheduleOccupancy();
        List<List<String>> head = List.of(
                List.of("航线"), List.of("发船时间"), List.of("船舶"), List.of("总座位数"),
                List.of("已售"), List.of("上座率%"));
        List<List<Object>> rows = new ArrayList<>();
        for (Map<String, Object> row : data) {
            rows.add(List.of(
                    String.valueOf(row.get("routeName")),
                    String.valueOf(row.get("departTime")),
                    String.valueOf(row.get("shipName")),
                    row.get("totalSeats"),
                    row.get("soldCount"),
                    row.get("occupancy")));
        }
        writeExcel(response, "上座率统计", head, rows);
    }

    private void writeExcel(HttpServletResponse response, String name,
                            List<List<String>> head, List<List<Object>> rows) throws IOException {
        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        response.setCharacterEncoding("utf-8");
        String fileName = URLEncoder.encode(name + ".xlsx", StandardCharsets.UTF_8).replaceAll("\\+", "%20");
        response.setHeader("Content-disposition", "attachment;filename*=utf-8''" + fileName);
        EasyExcel.write(response.getOutputStream()).head(head).sheet(name).doWrite(rows);
    }
}
