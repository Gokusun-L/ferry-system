package com.ferry.service.impl;

import com.ferry.common.BizException;
import com.ferry.common.LoginUser;
import com.ferry.dao.UserDao;
import com.ferry.entity.User;
import com.ferry.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserDao userDao;
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    private static final Pattern PHONE = Pattern.compile("^1[3-9]\\d{9}$");
    private static final Pattern ID_CARD = Pattern.compile("^\\d{17}[0-9Xx]$");
    private static final int MAX_FAIL = 5;
    private static final int LOCK_MINUTES = 10;

    @Override
    @Transactional
    public void register(User user) {
        if (user.getUsername() == null || user.getUsername().isBlank()) {
            throw new BizException("用户名不能为空");
        }
        user.setUsername(user.getUsername().trim());
        if (user.getPassword() == null || user.getPassword().length() < 6) {
            throw new BizException("密码长度不能少于6位");
        }
        if (isUsernameTaken(user.getUsername())) {
            throw new BizException("用户名已存在");
        }
        if (user.getPhone() == null || user.getPhone().isBlank()) {
            throw new BizException("手机号不能为空");
        }
        user.setPhone(user.getPhone().trim());
        if (!PHONE.matcher(user.getPhone()).matches()) {
            throw new BizException("手机号格式不正确");
        }
        if (isPhoneTaken(user.getPhone())) {
            throw new BizException("手机号已被注册");
        }
        if (user.getIdCard() != null && !user.getIdCard().isBlank()
                && !ID_CARD.matcher(user.getIdCard().trim()).matches()) {
            throw new BizException("身份证号格式不正确");
        }
        if (user.getName() == null || user.getName().isBlank()) {
            throw new BizException("姓名不能为空");
        }
        user.setName(user.getName().trim());
        if (user.getIdCard() != null) {
            user.setIdCard(user.getIdCard().trim().toUpperCase());
        }
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        user.setRole("PASSENGER");
        user.setStatus(1);
        user.setLoginFail(0);
        userDao.insert(user);
    }

    @Override
    public LoginUser login(String username, String password) {
        User user = userDao.findByUsername(username);
        if (user == null) {
            throw new BizException("用户名或密码错误");
        }
        if (user.getStatus() == 0) {
            throw new BizException("账号已被禁用");
        }
        // 锁定校验
        if (user.getLockUntil() != null) {
            if (user.getLockUntil().isAfter(LocalDateTime.now())) {
                throw new BizException("账号已锁定，请稍后再试");
            }
            // 锁定已过期，清零失败次数后重新计数
            userDao.resetLoginFail(user.getId());
            user.setLoginFail(0);
        }
        if (!passwordEncoder.matches(password, user.getPassword())) {
            // 密码错误，累加失败次数
            userDao.incrementLoginFail(user.getId());
            User updated = userDao.findById(user.getId());
            if (updated.getLoginFail() >= MAX_FAIL) {
                userDao.setLock(user.getId(), LocalDateTime.now().plusMinutes(LOCK_MINUTES));
                throw new BizException("密码错误次数过多，账号锁定10分钟");
            }
            throw new BizException("用户名或密码错误");
        }
        // 登录成功，重置失败次数
        userDao.resetLoginFail(user.getId());
        return new LoginUser(user.getId(), user.getUsername(), user.getName(),
                user.getPhone(), user.getIdCard(), user.getRole());
    }

    @Override
    public User getById(Long id) {
        User user = userDao.findById(id);
        if (user == null) {
            throw new BizException("用户不存在");
        }
        return user;
    }

    @Override
    public List<User> search(String username, String role, String name, int page, int size) {
        int offset = (page - 1) * size;
        return userDao.search(username, role, name, offset, size);
    }

    @Override
    public long count(String username, String role, String name) {
        return userDao.count(username, role, name);
    }

    @Override
    @Transactional
    public void createUser(User user, String operatorRole) {
        if (!"ADMIN".equals(operatorRole)) {
            throw new BizException("无权限创建用户");
        }
        if (user.getUsername() == null || user.getUsername().isBlank()) {
            throw new BizException("用户名不能为空");
        }
        user.setUsername(user.getUsername().trim());
        if (user.getPassword() == null || user.getPassword().length() < 6) {
            throw new BizException("密码长度不能少于6位");
        }
        if (isUsernameTaken(user.getUsername())) {
            throw new BizException("用户名已存在");
        }
        if (user.getPhone() == null || user.getPhone().isBlank()) {
            throw new BizException("手机号不能为空");
        }
        user.setPhone(user.getPhone().trim());
        if (!PHONE.matcher(user.getPhone()).matches()) {
            throw new BizException("手机号格式不正确");
        }
        if (isPhoneTaken(user.getPhone())) {
            throw new BizException("手机号已被使用");
        }
        if (user.getName() == null || user.getName().isBlank()) {
            throw new BizException("姓名不能为空");
        }
        user.setName(user.getName().trim());
        if (!"SELLER".equals(user.getRole()) && !"ADMIN".equals(user.getRole())) {
            throw new BizException("仅可创建售票员或管理员账号");
        }
        user.setPassword(passwordEncoder.encode(user.getPassword()));
        user.setStatus(1);
        user.setLoginFail(0);
        userDao.insert(user);
    }

    @Override
    public void updateUser(User user) {
        getById(user.getId());
        if (user.getName() != null) {
            String name = user.getName().trim();
            if (name.isEmpty()) {
                throw new BizException("姓名不能为空");
            }
            user.setName(name);
        }
        if (user.getPhone() != null && !user.getPhone().trim().isEmpty()) {
            String phone = user.getPhone().trim();
            if (!PHONE.matcher(phone).matches()) {
                throw new BizException("手机号格式不正确");
            }
            User phoneOwner = userDao.findByPhone(phone);
            if (phoneOwner != null && !phoneOwner.getId().equals(user.getId())) {
                throw new BizException("手机号已被使用");
            }
            user.setPhone(phone);
        }
        if (user.getIdCard() != null && !user.getIdCard().trim().isEmpty()) {
            String idCard = user.getIdCard().trim().toUpperCase();
            if (!idCard.matches("^\\d{17}[\\dX]$")) {
                throw new BizException("身份证号格式不正确");
            }
            user.setIdCard(idCard);
        }
        if (user.getRole() != null && !user.getRole().isEmpty()
                && !"ADMIN".equals(user.getRole()) && !"SELLER".equals(user.getRole())
                && !"PASSENGER".equals(user.getRole())) {
            throw new BizException("角色不合法");
        }
        userDao.update(user);
    }

    @Override
    public void resetPassword(Long id, String newPassword) {
        getById(id);
        if (newPassword == null || newPassword.length() < 6) {
            throw new BizException("密码长度不能少于6位");
        }
        userDao.updatePassword(id, passwordEncoder.encode(newPassword));
    }

    @Override
    public void toggleStatus(Long id) {
        User user = getById(id);
        userDao.updateStatus(id, user.getStatus() == 1 ? 0 : 1);
    }

    @Override
    public void updateProfile(User user) {
        User exist = getById(user.getId());
        String name = user.getName() == null ? null : user.getName().trim();
        if (name == null || name.isEmpty()) {
            throw new BizException("姓名不能为空");
        }
        if (user.getPhone() == null || !PHONE.matcher(user.getPhone()).matches()) {
            throw new BizException("手机号格式不正确");
        }
        User phoneOwner = userDao.findByPhone(user.getPhone());
        if (phoneOwner != null && !phoneOwner.getId().equals(user.getId())) {
            throw new BizException("手机号已被使用");
        }
        if (user.getIdCard() != null && !user.getIdCard().isEmpty()
                && !ID_CARD.matcher(user.getIdCard()).matches()) {
            throw new BizException("身份证号格式不正确");
        }
        exist.setName(name);
        exist.setPhone(user.getPhone());
        if (user.getIdCard() != null) {
            exist.setIdCard(user.getIdCard());
        }
        userDao.update(exist);
    }

    @Override
    public void changePassword(Long id, String oldPassword, String newPassword) {
        User user = getById(id);
        if (!passwordEncoder.matches(oldPassword, user.getPassword())) {
            throw new BizException("原密码错误");
        }
        if (newPassword == null || newPassword.length() < 6) {
            throw new BizException("新密码长度不能少于6位");
        }
        userDao.updatePassword(id, passwordEncoder.encode(newPassword));
    }

    @Override
    public boolean isUsernameTaken(String username) {
        return userDao.findByUsername(username) != null;
    }

    @Override
    public boolean isPhoneTaken(String phone) {
        return userDao.findByPhone(phone) != null;
    }
}
