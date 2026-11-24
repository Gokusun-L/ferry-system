package com.ferry.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class ShipSeat {
    private Long id;
    private Long shipId;
    private String seatNo;
    private Integer rowNo;
    private String colNo;
}
