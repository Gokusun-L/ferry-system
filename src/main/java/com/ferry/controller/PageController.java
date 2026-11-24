package com.ferry.controller;

import com.ferry.common.LoginUser;
import com.ferry.common.RequireRole;
import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * 页面跳转控制器
 */
@Controller
public class PageController {

    @GetMapping("/")
    public String index(HttpSession session, Model model) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        if (user == null) {
            return "redirect:/login";
        }
        model.addAttribute("user", user);
        switch (user.getRole()) {
            case "ADMIN":
                return "admin/home";
            case "SELLER":
                return "seller/home";
            default:
                return "passenger/home";
        }
    }

    // ===== 管理员页面 =====
    @RequireRole("ADMIN")
    @GetMapping("/admin/users")
    public String adminUsers(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "admin/users";
    }

    @RequireRole("ADMIN")
    @GetMapping("/admin/routes")
    public String adminRoutes(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "admin/routes";
    }

    @RequireRole("ADMIN")
    @GetMapping("/admin/ships")
    public String adminShips(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "admin/ships";
    }

    @RequireRole("ADMIN")
    @GetMapping("/admin/schedules")
    public String adminSchedules(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "admin/schedules";
    }

    @RequireRole("ADMIN")
    @GetMapping("/admin/orders")
    public String adminOrders(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "admin/orders";
    }

    @RequireRole("ADMIN")
    @GetMapping("/admin/stats")
    public String adminStats(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "admin/stats";
    }

    // ===== 售票员页面 =====
    @RequireRole({"ADMIN", "SELLER"})
    @GetMapping("/seller/sell")
    public String sellerSell(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "seller/sell";
    }

    @RequireRole({"ADMIN", "SELLER"})
    @GetMapping("/seller/checkin")
    public String sellerCheckin(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "seller/checkin";
    }

    @RequireRole({"ADMIN", "SELLER"})
    @GetMapping("/seller/refund")
    public String sellerRefund(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "seller/refund";
    }

    @RequireRole({"ADMIN", "SELLER"})
    @GetMapping("/seller/stats")
    public String sellerStats(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "seller/stats";
    }

    // ===== 乘客页面 =====
    @RequireRole("PASSENGER")
    @GetMapping("/passenger/search")
    public String passengerSearch(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "passenger/search";
    }

    @RequireRole("PASSENGER")
    @GetMapping("/passenger/orders")
    public String passengerOrders(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "passenger/orders";
    }

    @RequireRole("PASSENGER")
    @GetMapping("/passenger/tickets")
    public String passengerTickets(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "passenger/tickets";
    }

    @GetMapping("/profile")
    public String profile(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "profile";
    }

    @GetMapping("/notifications")
    public String notifications(HttpSession session, Model model) {
        model.addAttribute("user", session.getAttribute("loginUser"));
        return "notifications";
    }
}
