package com.ferry.dao;

import com.ferry.entity.ShipSeat;
import org.apache.ibatis.annotations.Param;
import java.util.List;

public interface ShipSeatDao {
    int insertBatch(@Param("list") List<ShipSeat> list);
    List<ShipSeat> listByShip(@Param("shipId") Long shipId);
    int deleteByShip(@Param("shipId") Long shipId);
}
