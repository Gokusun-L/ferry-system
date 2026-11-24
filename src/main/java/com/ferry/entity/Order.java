package com.ferry.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class Order {
    private Long id;
    private String orderNo;
    private Long userId;
    private Long sellerId;
    private Long scheduleId;
    private BigDecimal totalAmount;
    private String status; // UNPAID/PAID/CHECKED/FINISHED/CANCELLED/REFUNDED
    private String channel; // ONLINE/OFFLINE
    private LocalDateTime createTime;
    private LocalDateTime payTime;

    // 关联字段
    private String routeName;
    private String departPort;
    private String arrivePort;
    private String shipName;
    private LocalDateTime departTime;
}
