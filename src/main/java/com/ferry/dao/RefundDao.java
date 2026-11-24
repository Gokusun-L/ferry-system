package com.ferry.dao;

import com.ferry.entity.Refund;
import org.apache.ibatis.annotations.Param;
import java.util.List;

public interface RefundDao {
    int insert(Refund refund);
    List<Refund> listByOrder(@Param("orderId") Long orderId);
}
