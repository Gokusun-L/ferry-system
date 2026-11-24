package com.ferry.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class Reschedule {
    private Long id;
    private Long oldTicketId;
    private Long newTicketId;
    private Long oldScheduleId;
    private Long newScheduleId;
    private BigDecimal priceDiff;
    private LocalDateTime rescheduleTime;
}
