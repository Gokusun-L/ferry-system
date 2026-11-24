package com.ferry.dao;

import com.ferry.entity.Route;
import org.apache.ibatis.annotations.Param;
import java.util.List;

public interface RouteDao {
    List<Route> search(@Param("routeName") String routeName, @Param("departPort") String departPort,
                       @Param("arrivePort") String arrivePort, @Param("offset") int offset, @Param("limit") int limit);
    long count(@Param("routeName") String routeName, @Param("departPort") String departPort, @Param("arrivePort") String arrivePort);
    Route findById(@Param("id") Long id);
    int insert(Route route);
    int update(Route route);
    int logicDelete(@Param("id") Long id);
    int countUnfinishedSchedule(@Param("routeId") Long routeId);
    /**
     * 同出发港+到达港+航线名 的有效航线数（excludeId 用于编辑时排除自身）
     * 任务书要求：同一出发港口、到达港口和航线名称的组合应避免重复
     */
    int countSameRoute(@Param("departPort") String departPort, @Param("arrivePort") String arrivePort,
                       @Param("routeName") String routeName, @Param("excludeId") Long excludeId);
    List<Route> listAll();
}
