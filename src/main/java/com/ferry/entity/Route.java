package com.ferry.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class Route {
    private Long id;
    private String routeName;
    private String departPort;
    private String arrivePort;
    private Integer duration;
    private String description;
    private Integer deleted;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
