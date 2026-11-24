package com.ferry.service.impl;

import com.ferry.common.BizException;
import com.ferry.dao.RouteDao;
import com.ferry.entity.Route;
import com.ferry.service.RouteService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class RouteServiceImpl implements RouteService {

    private final RouteDao routeDao;

    @Override
    public List<Route> search(String routeName, String departPort, String arrivePort, int page, int size) {
        int offset = (page - 1) * size;
        return routeDao.search(routeName, departPort, arrivePort, offset, size);
    }

    @Override
    public long count(String routeName, String departPort, String arrivePort) {
        return routeDao.count(routeName, departPort, arrivePort);
    }

    @Override
    public Route getById(Long id) {
        Route route = routeDao.findById(id);
        if (route == null || route.getDeleted() == 1) {
            throw new BizException("航线不存在");
        }
        return route;
    }

    @Override
    public void create(Route route) {
        validate(route, null);
        routeDao.insert(route);
    }

    @Override
    public void update(Route route) {
        getById(route.getId());
        validate(route, route.getId());
        routeDao.update(route);
    }

    private void validate(Route route, Long excludeId) {
        if (route.getRouteName() == null || route.getRouteName().trim().isEmpty()) {
            throw new BizException("航线名称不能为空");
        }
        if (route.getDepartPort() == null || route.getDepartPort().trim().isEmpty()
                || route.getArrivePort() == null || route.getArrivePort().trim().isEmpty()) {
            throw new BizException("出发港和到达港不能为空");
        }
        if (route.getDepartPort().equals(route.getArrivePort())) {
            throw new BizException("出发港和到达港不能相同");
        }
        if (route.getDuration() == null || route.getDuration() <= 0) {
            throw new BizException("航行时长必须大于0");
        }
        if (routeDao.countSameRoute(route.getDepartPort(), route.getArrivePort(),
                route.getRouteName(), excludeId) > 0) {
            throw new BizException("已存在相同出发港、到达港和航线名称的航线");
        }
    }

    @Override
    public void delete(Long id) {
        getById(id);
        int unfinished = routeDao.countUnfinishedSchedule(id);
        if (unfinished > 0) {
            throw new BizException("该航线下有未完成班次，不允许删除");
        }
        routeDao.logicDelete(id);
    }

    @Override
    public List<Route> listAll() {
        return routeDao.listAll();
    }
}
