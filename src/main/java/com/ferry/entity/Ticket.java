package com.ferry.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class Ticket {
    private Long id;
    private String ticketNo;
    private Long orderId;
    private Long scheduleId;
    private String seatNo;
    private String passengerName;
    private String idCard;
    private String phone;
    private BigDecimal price;
    private String status; // UNPAID/PAID/CHECKED/REFUNDED/CANCELLED/RESCHEDULED
    private LocalDateTime checkTime;
    private Long checkerId;

    // 关联字段
    private String routeName;
    private String departPort;
    private String arrivePort;
    private String shipName;
    private LocalDateTime departTime;
    private String checkerName;
}
