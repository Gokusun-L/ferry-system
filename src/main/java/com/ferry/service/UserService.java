package com.ferry.service;

import com.ferry.common.LoginUser;
import com.ferry.entity.User;
import java.util.List;
import java.util.Map;

public interface UserService {
    void register(User user);
    LoginUser login(String username, String password);
    User getById(Long id);
    List<User> search(String username, String role, String name, int page, int size);
    long count(String username, String role, String name);
    void createUser(User user, String operatorRole);
    void updateUser(User user);
    void resetPassword(Long id, String newPassword);
    void toggleStatus(Long id);
    void updateProfile(User user);
    void changePassword(Long id, String oldPassword, String newPassword);
    boolean isUsernameTaken(String username);
    boolean isPhoneTaken(String phone);
}
