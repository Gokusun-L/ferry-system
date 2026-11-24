package com.ferry.entity;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class Refund {
    /** 业务类型：退票 */
    public static final String BIZ_REFUND = "REFUND";
    /** 业务类型：改签退还差价（不是退票，不计入退票量） */
    public static final String BIZ_RESCHEDULE_DIFF = "RESCHEDULE_DIFF";

    private Long id;
    private Long orderId;
    private Long ticketId;
    private BigDecimal refundAmount;
    private BigDecimal fee;
    private String reason;
    private LocalDateTime refundTime;
    private Long operatorId;
    private String bizType;
}
