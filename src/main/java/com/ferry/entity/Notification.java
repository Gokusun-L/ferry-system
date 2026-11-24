package com.ferry.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class Notification {
    private Long id;
    private Long userId;
    private String type; // SCHEDULE_CANCEL / REFUND_SUCCESS / RESCHEDULE
    private String title;
    private String content;
    private Integer isRead;
    private LocalDateTime createTime;
}
