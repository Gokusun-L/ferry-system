package com.ferry.service;

import com.ferry.entity.Ship;
import java.util.List;

public interface ShipService {
    List<Ship> search(String shipName, int page, int size);
    int count(String shipName);
    Ship getById(Long id);
    void create(Ship ship);
    void update(Ship ship);
    void delete(Long id);
    List<Ship> listAll();
}
