package com.ferry.controller;

import com.ferry.common.LoginUser;
import com.ferry.common.Result;
import com.ferry.dao.NotificationDao;
import com.ferry.entity.Notification;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 站内通知：列表、未读数、全部已读
 */
@RestController
@RequestMapping("/api/notifications")
@RequiredArgsConstructor
public class NotificationController {

    private final NotificationDao notificationDao;

    @GetMapping
    public Result<Map<String, Object>> list(@RequestParam(defaultValue = "1") int page,
                                            @RequestParam(defaultValue = "10") int size,
                                            HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        int p = Math.max(page, 1);
        int s = Math.min(Math.max(size, 1), 50);
        List<Notification> list = notificationDao.listByUser(user.getId(), (p - 1) * s, s);
        Map<String, Object> data = new HashMap<>();
        data.put("list", list);
        data.put("total", notificationDao.countByUser(user.getId()));
        data.put("unread", notificationDao.countUnread(user.getId()));
        data.put("page", p);
        data.put("size", s);
        return Result.ok(data);
    }

    @GetMapping("/unread-count")
    public Result<Long> unreadCount(HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        return Result.ok(notificationDao.countUnread(user.getId()));
    }

    @PostMapping("/read-all")
    public Result<Void> readAll(HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        notificationDao.markAllRead(user.getId());
        return Result.ok();
    }
}
