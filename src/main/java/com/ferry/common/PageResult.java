package com.ferry.common;

import lombok.Data;

import java.util.List;

/**
 * 统一分页响应结构。
 * 所有分页接口返回 { list, total, page, size }，前端不再需要自己维护页码回显。
 */
@Data
public class PageResult<T> {
    private List<T> list;
    private long total;
    private int page;
    private int size;

    public static <T> PageResult<T> of(List<T> list, long total, int page, int size) {
        PageResult<T> r = new PageResult<>();
        r.list = list;
        r.total = total;
        r.page = page;
        r.size = size;
        return r;
    }
}
