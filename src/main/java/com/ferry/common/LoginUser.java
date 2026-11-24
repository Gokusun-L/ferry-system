package com.ferry.common;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 当前登录用户上下文（存入 Session）
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LoginUser {
    private Long id;
    private String username;
    private String name;
    private String phone;
    private String idCard;
    private String role; // ADMIN / SELLER / PASSENGER
}
