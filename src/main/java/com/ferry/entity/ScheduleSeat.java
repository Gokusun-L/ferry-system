package com.ferry.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class ScheduleSeat {
    private Long id;
    private Long scheduleId;
    private String seatNo;
    private String status; // AVAILABLE / LOCKED / SOLD
    private Long orderId;
    private LocalDateTime lockTime;
    private Long lockUserId;
}
