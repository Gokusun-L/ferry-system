package com.ferry.service;

import com.ferry.entity.Schedule;
import java.time.LocalDate;
import java.util.List;

public interface ScheduleService {
    List<Schedule> search(Long routeId, Long shipId, String date, String status, int page, int size);
    long count(Long routeId, Long shipId, String date, String status);
    Schedule getById(Long id);
    void create(Schedule schedule);
    List<Schedule> batchCreate(Long routeId, Long shipId, LocalDate startDate, LocalDate endDate,
                               int hour, int minute, java.math.BigDecimal price);
    void update(Schedule schedule);
    /** 发布班次：PENDING -> SELLING */
    void publish(Long id);
    void cancel(Long id);
    void delete(Long id);
    List<Schedule> listForPortSearch(String departPort, String arrivePort, String date);
}
