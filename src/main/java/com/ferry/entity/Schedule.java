package com.ferry.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class Schedule {
    private Long id;
    private Long routeId;
    private Long shipId;
    private LocalDateTime departTime;
    private LocalDateTime arriveTime;
    private BigDecimal price;
    private String status;
    private Integer soldCount;
    private Integer deleted;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    // 关联查询冗余字段
    private String routeName;
    private String departPort;
    private String arrivePort;
    private String shipName;
    private String shipType;
    private Integer totalSeats;
    private Integer remainingSeats;
}
