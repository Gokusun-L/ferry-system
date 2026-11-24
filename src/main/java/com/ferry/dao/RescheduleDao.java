package com.ferry.dao;

import com.ferry.entity.Reschedule;
import org.apache.ibatis.annotations.Param;
import java.util.List;

public interface RescheduleDao {
    int insert(Reschedule reschedule);
    List<Reschedule> listByOldTicket(@Param("oldTicketId") Long oldTicketId);
}
