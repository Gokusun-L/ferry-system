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
    /** 派生字段，不落库：锁定到期时间，供前端倒计时 */
    private LocalDateTime lockExpireTime;
}
