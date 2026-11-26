package com.ferry.controller;

import com.ferry.common.LoginUser;
import com.ferry.common.PageResult;
import com.ferry.common.RequireRole;
import com.ferry.common.Result;
import com.ferry.entity.User;
import com.ferry.service.UserService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.ModelAndView;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    /** 注册页 */
    @GetMapping("/register")
    public ModelAndView registerPage() {
        return new ModelAndView("register");
    }

    /** 登录页 */
    @GetMapping("/login")
    public ModelAndView loginPage() {
        return new ModelAndView("login");
    }

    /** 注册 */
    @PostMapping("/register")
    public Result<Void> register(@RequestBody User user) {
        userService.register(user);
        return Result.ok();
    }

    /** 登录 */
    @PostMapping("/login")
    public Result<LoginUser> login(@RequestBody Map<String, String> body, HttpSession session) {
        LoginUser user = userService.login(body.get("username"), body.get("password"));
        session.setAttribute("loginUser", user);
        return Result.ok(user);
    }

    /** 退出登录 */
    @PostMapping("/logout")
    public Result<Void> logout(HttpSession session) {
        session.invalidate();
        return Result.ok();
    }

    /** 当前登录用户 */
    @GetMapping("/api/user/current")
    public Result<LoginUser> current(HttpSession session) {
        LoginUser user = (LoginUser) session.getAttribute("loginUser");
        if (user == null) {
            return Result.fail("未登录");
        }
        return Result.ok(user);
    }

    /** 用户列表（管理员） */
    @RequireRole("ADMIN")
    @GetMapping("/api/users")
    public Result<PageResult<User>> list(@RequestParam(defaultValue = "1") int page,
                                         @RequestParam(defaultValue = "10") int size,
                                         @RequestParam(required = false) String username,
                                         @RequestParam(required = false) String role,
                                         @RequestParam(required = false) String name) {
        return Result.ok(PageResult.of(
                userService.search(username, role, name, page, size),
                userService.count(username, role, name),
                page, size));
    }

    /** 新增用户（售票员/管理员） */
    @RequireRole("ADMIN")
    @PostMapping("/api/users")
    public Result<Void> create(@RequestBody User user, HttpSession session) {
        LoginUser operator = (LoginUser) session.getAttribute("loginUser");
        userService.createUser(user, operator.getRole());
        return Result.ok();
    }

    /** 编辑用户 */
    @RequireRole("ADMIN")
    @PutMapping("/api/users/{id}")
    public Result<Void> update(@PathVariable Long id, @RequestBody User user) {
        user.setId(id);
        userService.updateUser(user);
        return Result.ok();
    }

    /** 重置密码 */
    @RequireRole("ADMIN")
    @PutMapping("/api/users/{id}/password")
    public Result<Void> resetPassword(@PathVariable Long id, @RequestBody Map<String, String> body) {
        userService.resetPassword(id, body.get("password"));
        return Result.ok();
    }

    /** 禁用/启用 */
    @RequireRole("ADMIN")
    @PutMapping("/api/users/{id}/status")
    public Result<Void> toggleStatus(@PathVariable Long id) {
        userService.toggleStatus(id);
        return Result.ok();
    }

    /** 修改个人信息 */
    @PutMapping("/api/profile")
    public Result<Void> updateProfile(@RequestBody User user, HttpSession session) {
        LoginUser loginUser = (LoginUser) session.getAttribute("loginUser");
        user.setId(loginUser.getId());
        userService.updateProfile(user);
        // 同步 Session 中的登录信息
        User updated = userService.getById(loginUser.getId());
        session.setAttribute("loginUser", new LoginUser(updated.getId(), updated.getUsername(),
                updated.getName(), updated.getPhone(), updated.getIdCard(), updated.getRole()));
        return Result.ok();
    }

    /** 修改密码 */
    @PutMapping("/api/profile/password")
    public Result<Void> changePassword(@RequestBody Map<String, String> body, HttpSession session) {
        LoginUser loginUser = (LoginUser) session.getAttribute("loginUser");
        userService.changePassword(loginUser.getId(), body.get("oldPassword"), body.get("newPassword"));
        return Result.ok();
    }
}
