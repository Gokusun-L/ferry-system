package com.ferry.service;

import com.ferry.entity.Route;
import java.util.List;

public interface RouteService {
    List<Route> search(String routeName, String departPort, String arrivePort, int page, int size);
    long count(String routeName, String departPort, String arrivePort);
    Route getById(Long id);
    void create(Route route);
    void update(Route route);
    void delete(Long id);
    List<Route> listAll();
}
