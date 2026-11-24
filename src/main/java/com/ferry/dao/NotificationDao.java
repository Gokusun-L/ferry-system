package com.ferry.dao;

import com.ferry.entity.Notification;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface NotificationDao {
    int insert(Notification notification);
    List<Notification> listByUser(@Param("userId") Long userId, @Param("offset") int offset, @Param("limit") int limit);
    long countUnread(@Param("userId") Long userId);
    long countByUser(@Param("userId") Long userId);
    int markAllRead(@Param("userId") Long userId);
}
