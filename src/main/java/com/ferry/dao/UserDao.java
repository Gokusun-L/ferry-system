package com.ferry.dao;

import com.ferry.entity.User;
import org.apache.ibatis.annotations.Param;
import java.util.List;

public interface UserDao {
    User findByUsername(@Param("username") String username);
    User findByPhone(@Param("phone") String phone);
    User findById(@Param("id") Long id);
    int insert(User user);
    int update(User user);
    int updatePassword(@Param("id") Long id, @Param("password") String password);
    int updateStatus(@Param("id") Long id, @Param("status") Integer status);
    int incrementLoginFail(@Param("id") Long id);
    int resetLoginFail(@Param("id") Long id);
    int setLock(@Param("id") Long id, @Param("lockUntil") java.time.LocalDateTime lockUntil);
    List<User> search(@Param("username") String username, @Param("role") String role,
                      @Param("name") String name, @Param("offset") int offset, @Param("limit") int limit);
    long count(@Param("username") String username, @Param("role") String role, @Param("name") String name);
}
