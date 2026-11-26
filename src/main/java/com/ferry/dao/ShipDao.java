package com.ferry.dao;

import com.ferry.entity.Ship;
import org.apache.ibatis.annotations.Param;
import java.util.List;

public interface ShipDao {
    List<Ship> searchPage(@Param("shipName") String shipName, @Param("offset") int offset, @Param("size") int size);
    int count(@Param("shipName") String shipName);
    Ship findById(@Param("id") Long id);
    int insert(Ship ship);
    int update(Ship ship);
    int logicDelete(@Param("id") Long id);
    int countUnfinishedSchedule(@Param("shipId") Long shipId);
    int countSchedules(@Param("shipId") Long shipId);
    List<Ship> listAll();
}
