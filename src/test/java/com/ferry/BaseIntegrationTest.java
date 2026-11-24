package com.ferry;

import com.ferry.entity.Route;
import com.ferry.entity.Schedule;
import com.ferry.entity.Ship;
import com.ferry.entity.User;
import com.ferry.service.RouteService;
import com.ferry.service.ScheduleService;
import com.ferry.service.ShipService;
import com.ferry.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 集成测试基类：连接真实 MySQL（ferry_test 库）。
 * 单线程用例继承本类，@Transactional 自动回滚，互不污染。
 *
 * 注意：并发用例不要继承本类（需要真实提交），见 ConcurrencyTest。
 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
public abstract class BaseIntegrationTest {

    private static final AtomicInteger SEQ = new AtomicInteger(0);

    @Autowired
    protected RouteService routeService;
    @Autowired
    protected ShipService shipService;
    @Autowired
    protected ScheduleService scheduleService;
    @Autowired
    protected UserService userService;

    /**
     * 造一个真实乘客用户并返回其主键。
     * 订单表 user_id/seller_id 有外键约束，下单必须用库中真实存在的用户。
     */
    protected Long newPassenger() {
        int n = SEQ.incrementAndGet();
        User u = new User();
        u.setUsername("test_p_" + n + "_" + System.nanoTime() % 100000);
        u.setPassword("123456");
        u.setName("测试乘客" + n);
        u.setPhone(String.format("139%08d", n % 100000000));
        u.setIdCard(null); // 注册允许不填身份证
        userService.register(u);
        return userService.login(u.getUsername(), "123456").getId();
    }

    /** 造一条可用航线 */
    protected Route newRoute() {
        int n = SEQ.incrementAndGet();
        Route r = new Route();
        r.setRouteName("测试航线-" + n);
        r.setDepartPort("测试港A-" + n);
        r.setArrivePort("测试港B-" + n);
        r.setDuration(60);
        r.setDescription("集成测试自动生成");
        routeService.create(r);
        return r;
    }

    /** 造一艘船（自动生成 4 列座位） */
    protected Ship newShip(int totalSeats) {
        int n = SEQ.incrementAndGet();
        Ship s = new Ship();
        s.setShipName("测试船-" + n);
        s.setTotalSeats(totalSeats);
        s.setShipType("NORMAL");
        s.setDescription("集成测试自动生成");
        shipService.create(s);
        return s;
    }

    /** 造一个售票中的班次（创建后发布） */
    protected Schedule newSellingSchedule(Route route, Ship ship, LocalDateTime depart, String price) {
        Schedule s = new Schedule();
        s.setRouteId(route.getId());
        s.setShipId(ship.getId());
        s.setDepartTime(depart);
        s.setPrice(new BigDecimal(price));
        scheduleService.create(s);
        scheduleService.publish(s.getId());
        return scheduleService.getById(s.getId());
    }
}
