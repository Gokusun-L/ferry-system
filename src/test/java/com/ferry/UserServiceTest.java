package com.ferry;

import com.ferry.common.BizException;
import com.ferry.common.LoginUser;
import com.ferry.dao.UserDao;
import com.ferry.entity.User;
import com.ferry.service.UserService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 模块一测试：用户注册、登录、密码存储、锁定、禁用。
 */
@DisplayName("模块一 用户与权限")
class UserServiceTest extends BaseIntegrationTest {

    @Autowired
    private UserService userService;
    @Autowired
    private UserDao userDao;

    private User passenger(String username, String phone, String idCard) {
        User u = new User();
        u.setUsername(username);
        u.setPassword("123456");
        u.setName("测试乘客");
        u.setPhone(phone);
        u.setIdCard(idCard);
        return u;
    }

    @Test
    @DisplayName("TC-U01 注册成功：密码以 BCrypt 密文入库，角色强制为 PASSENGER")
    void register_storesBcryptAndForcesPassengerRole() {
        User u = passenger("test_reg_ok", "13711110001", "440100199001019001");
        // 恶意传入 ADMIN，应被强制改为 PASSENGER
        u.setRole("ADMIN");
        userService.register(u);

        User saved = userDao.findByUsername("test_reg_ok");
        assertNotNull(saved, "注册后应能查到用户");
        assertNotEquals("123456", saved.getPassword(), "数据库不得存明文密码");
        assertTrue(saved.getPassword().startsWith("$2a$"), "密码应为 BCrypt 密文，实际：" + saved.getPassword());
        assertEquals("PASSENGER", saved.getRole(), "自助注册角色必须为乘客");
        assertEquals(1, saved.getStatus());
    }

    @Test
    @DisplayName("TC-U02 注册失败：用户名重复")
    void register_duplicateUsername_rejected() {
        userService.register(passenger("test_reg_dup", "13711110002", "440100199001019002"));
        BizException ex = assertThrows(BizException.class,
                () -> userService.register(passenger("test_reg_dup", "13711110003", "440100199001019003")));
        assertTrue(ex.getMessage().contains("用户名已存在"), "实际提示：" + ex.getMessage());
    }

    @Test
    @DisplayName("TC-U03 注册失败：手机号格式非法")
    void register_badPhone_rejected() {
        BizException ex = assertThrows(BizException.class,
                () -> userService.register(passenger("test_reg_phone", "12345", "440100199001019004")));
        assertTrue(ex.getMessage().contains("手机号格式"), "实际提示：" + ex.getMessage());
    }

    @Test
    @DisplayName("TC-U04 注册失败：身份证号格式非法")
    void register_badIdCard_rejected() {
        BizException ex = assertThrows(BizException.class,
                () -> userService.register(passenger("test_reg_idcard", "13711110004", "123456")));
        assertTrue(ex.getMessage().contains("身份证号格式"), "实际提示：" + ex.getMessage());
    }

    @Test
    @DisplayName("TC-U05 登录成功：返回角色，失败次数清零")
    void login_success() {
        userService.register(passenger("test_login_ok", "13711110005", "440100199001019005"));
        LoginUser lu = userService.login("test_login_ok", "123456");
        assertEquals("test_login_ok", lu.getUsername());
        assertEquals("PASSENGER", lu.getRole());
        assertEquals(0, userDao.findByUsername("test_login_ok").getLoginFail().intValue());
    }

    @Test
    @DisplayName("TC-U06 登录失败：连续 5 次错误密码后锁定 10 分钟")
    void login_fiveFailures_locksAccount() {
        userService.register(passenger("test_login_lock", "13711110006", "440100199001019006"));
        for (int i = 1; i <= 4; i++) {
            assertThrows(BizException.class, () -> userService.login("test_login_lock", "wrong"));
        }
        // 第 5 次错误：触发锁定
        BizException fifth = assertThrows(BizException.class,
                () -> userService.login("test_login_lock", "wrong"));
        assertTrue(fifth.getMessage().contains("锁定"), "第5次应提示锁定，实际：" + fifth.getMessage());

        User locked = userDao.findByUsername("test_login_lock");
        assertNotNull(locked.getLockUntil(), "lock_until 应被写入");
        assertTrue(locked.getLockUntil().isAfter(java.time.LocalDateTime.now()), "锁定时间应晚于当前时间");

        // 锁定期内即使密码正确也拒绝
        BizException blocked = assertThrows(BizException.class,
                () -> userService.login("test_login_lock", "123456"));
        assertTrue(blocked.getMessage().contains("锁定"), "锁定期内应拒绝登录，实际：" + blocked.getMessage());
    }

    @Test
    @DisplayName("TC-U07 登录失败：账号被禁用")
    void login_disabledUser_rejected() {
        userService.register(passenger("test_login_disabled", "13711110007", "440100199001019007"));
        User u = userDao.findByUsername("test_login_disabled");
        userService.toggleStatus(u.getId());
        BizException ex = assertThrows(BizException.class,
                () -> userService.login("test_login_disabled", "123456"));
        assertTrue(ex.getMessage().contains("禁用"), "实际提示：" + ex.getMessage());
    }

    @Test
    @DisplayName("TC-U08 修改密码：原密码错误应拒绝，正确后新密码可登录")
    void changePassword_requiresOldPassword() {
        userService.register(passenger("test_pwd", "13711110008", "440100199001019008"));
        User u = userDao.findByUsername("test_pwd");

        BizException wrongOld = assertThrows(BizException.class,
                () -> userService.changePassword(u.getId(), "not-my-password", "654321"));
        assertTrue(wrongOld.getMessage().contains("原密码错误"), "实际：" + wrongOld.getMessage());

        userService.changePassword(u.getId(), "123456", "654321");
        assertNotNull(userService.login("test_pwd", "654321"), "新密码应可登录");
    }

    @Test
    @DisplayName("TC-U09 管理员创建用户：仅允许 SELLER/ADMIN，乘客角色被拒绝")
    void createUser_onlyStaffRoles() {
        User seller = passenger("test_seller_ok", "13711110009", null);
        seller.setRole("SELLER");
        userService.createUser(seller, "ADMIN");
        assertEquals("SELLER", userDao.findByUsername("test_seller_ok").getRole());

        User badRole = passenger("test_bad_role", "13711110010", null);
        badRole.setRole("PASSENGER");
        BizException ex = assertThrows(BizException.class, () -> userService.createUser(badRole, "ADMIN"));
        assertTrue(ex.getMessage().contains("售票员或管理员"), "实际：" + ex.getMessage());
    }
}
