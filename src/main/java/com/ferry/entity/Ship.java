package com.ferry.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class Ship {
    private Long id;
    private String shipName;
    private Integer totalSeats;
    private String shipType;
    private String description;
    private Integer deleted;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
