package com.ferry.service.impl;

import com.ferry.common.BizException;
import com.ferry.dao.ShipDao;
import com.ferry.dao.ShipSeatDao;
import com.ferry.entity.Ship;
import com.ferry.entity.ShipSeat;
import com.ferry.service.ShipService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ShipServiceImpl implements ShipService {

    private final ShipDao shipDao;
    private final ShipSeatDao shipSeatDao;

    @Override
    public List<Ship> search(String shipName, int page, int size) {
        int p = Math.max(page, 1);
        int s = Math.min(Math.max(size, 1), 100);
        return shipDao.searchPage(shipName, (p - 1) * s, s);
    }

    @Override
    public int count(String shipName) {
        return shipDao.count(shipName);
    }

    @Override
    public Ship getById(Long id) {
        Ship ship = shipDao.findById(id);
        if (ship == null || ship.getDeleted() == 1) {
            throw new BizException("船舶不存在");
        }
        return ship;
    }

    @Override
    @Transactional
    public void create(Ship ship) {
        if (ship.getTotalSeats() == null || ship.getTotalSeats() <= 0) {
            throw new BizException("总座位数必须大于0");
        }
        shipDao.insert(ship);
        // 自动生成座位：按 4 列（A/B/C/D）排布
        initSeats(ship);
    }

    @Override
    @Transactional
    public void update(Ship ship) {
        Ship exist = getById(ship.getId());
        if (ship.getTotalSeats() == null || ship.getTotalSeats() <= 0) {
            throw new BizException("总座位数必须大于0");
        }
        // 座位布局变更会影响已有班次的座位图与统计口径，存在班次时禁止修改座位数
        if (!exist.getTotalSeats().equals(ship.getTotalSeats()) && shipDao.countSchedules(ship.getId()) > 0) {
            throw new BizException("该船舶已有班次，不能修改总座位数");
        }
        shipDao.update(ship);
        // 座位数变化则重建座位
        if (!exist.getTotalSeats().equals(ship.getTotalSeats())) {
            shipSeatDao.deleteByShip(ship.getId());
            initSeats(ship);
        }
    }

    @Override
    public void delete(Long id) {
        getById(id);
        int unfinished = shipDao.countUnfinishedSchedule(id);
        if (unfinished > 0) {
            throw new BizException("该船舶有未完成班次，不允许删除");
        }
        shipDao.logicDelete(id);
    }

    @Override
    public List<Ship> listAll() {
        return shipDao.listAll();
    }

    /** 按 4 列生成座位号：1A,1B,1C,1D,2A,... */
    private void initSeats(Ship ship) {
        char[] cols = {'A', 'B', 'C', 'D'};
        List<ShipSeat> seats = new ArrayList<>();
        int rows = (ship.getTotalSeats() + 3) / 4;
        int seatCount = 0;
        for (int r = 1; r <= rows && seatCount < ship.getTotalSeats(); r++) {
            for (char c : cols) {
                if (seatCount >= ship.getTotalSeats()) break;
                ShipSeat s = new ShipSeat();
                s.setShipId(ship.getId());
                s.setSeatNo(r + String.valueOf(c));
                s.setRowNo(r);
                s.setColNo(String.valueOf(c));
                seats.add(s);
                seatCount++;
            }
        }
        if (!seats.isEmpty()) {
            shipSeatDao.insertBatch(seats);
        }
    }
}
