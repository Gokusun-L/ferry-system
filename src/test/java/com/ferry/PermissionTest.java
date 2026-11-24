package com.ferry;

import com.ferry.common.LoginUser;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * 权限隔离测试：未登录拦截、角色越权拦截。
 * 验证任务书"不同角色登录后应只能访问其权限范围内的功能或数据"。
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@DisplayName("权限隔离")
class PermissionTest {

    @Autowired
    private MockMvc mockMvc;

    private MockHttpSession sessionOf(String role) {
        MockHttpSession session = new MockHttpSession();
        session.setAttribute("loginUser",
                new LoginUser(1L, "tester", "测试用户", "13700000000", "440100199001010000", role));
        return session;
    }

    @Test
    @DisplayName("TC-P01 未登录访问管理接口：重定向到登录页")
    void anonymous_redirectedToLogin() throws Exception {
        mockMvc.perform(get("/admin/users"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/login"));
    }

    @Test
    @DisplayName("TC-P02 未登录访问 API：重定向到登录页")
    void anonymousApi_redirectedToLogin() throws Exception {
        mockMvc.perform(get("/api/users"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/login"));
    }

    @Test
    @DisplayName("TC-P03 乘客访问管理员接口：返回 403 无权限")
    void passenger_cannotAccessAdminApi() throws Exception {
        mockMvc.perform(get("/api/users").session(sessionOf("PASSENGER")))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.code").value(403));
    }

    @Test
    @DisplayName("TC-P04 售票员访问管理员接口：返回 403 无权限")
    void seller_cannotAccessAdminApi() throws Exception {
        mockMvc.perform(get("/api/routes").session(sessionOf("SELLER")).param("page", "1"))
                .andExpect(status().isOk()); // 查询航线对售票员开放（只读）

        mockMvc.perform(get("/api/users").session(sessionOf("SELLER")))
                .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("TC-P05 管理员访问管理员接口：正常放行")
    void admin_canAccessAdminApi() throws Exception {
        mockMvc.perform(get("/api/users").session(sessionOf("ADMIN")).param("page", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value(0));
    }

    @Test
    @DisplayName("TC-P06 乘客访问管理员页面：重定向回首页")
    void passenger_pageRedirected() throws Exception {
        mockMvc.perform(get("/admin/users").session(sessionOf("PASSENGER")))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/"));
    }

    @Test
    @DisplayName("TC-P07 乘客访问管理端订单列表：返回 403（仅能看自己的订单）")
    void passenger_cannotListAllOrders() throws Exception {
        mockMvc.perform(get("/api/orders").session(sessionOf("PASSENGER")))
                .andExpect(status().isForbidden());

        // 自己的订单列表可以访问
        mockMvc.perform(get("/api/orders/my").session(sessionOf("PASSENGER")))
                .andExpect(status().isOk());
    }
}
