// 通用请求：统一处理"未登录被重定向到登录页"的情况
// 后端接口约定：HTTP 400/500 仍返回 JSON（{code,msg,data}），业务结果一律看 code
function api(url, method, body) {
    return fetch(url, {
        method: method || 'GET',
        headers: {'Content-Type': 'application/json'},
        credentials: 'same-origin',
        body: body ? JSON.stringify(body) : undefined
    }).then(function (r) {
        var contentType = r.headers.get('content-type') || '';
        if (contentType.indexOf('application/json') === -1) {
            // 拿到 HTML 说明会话已失效被重定向，直接跳登录页，避免 JSON 解析异常
            window.location.href = '/login';
            return Promise.reject(new Error('未登录或会话已失效'));
        }
        return r.json();
    });
}

// 只取 data 的简化版：失败时抛出带 msg 的错误，供 try/catch 或 .catch 使用
function apiData(url, method, body) {
    return api(url, method, body).then(function (res) {
        if (res.code === 401) {
            window.location.href = '/login';
            throw new Error(res.msg || '未登录');
        }
        if (res.code !== 0) {
            throw new Error(res.msg || '操作失败');
        }
        return res.data;
    });
}

function logout() {
    api('/logout', 'POST').then(() => {
        window.location.href = '/login';
    });
}

// 状态中文映射
const STATUS_MAP = {
    'UNPAID': '待支付', 'PAID': '已支付', 'CHECKED': '已检票',
    'FINISHED': '已完成', 'CANCELLED': '已取消', 'REFUNDED': '已退票',
    'RESCHEDULED': '已改签',
    'PENDING': '待发布', 'SELLING': '售票中', 'DEPARTED': '已发船'
};
const ROLE_MAP = {'ADMIN': '管理员', 'SELLER': '售票员', 'PASSENGER': '乘客'};
const SHIP_TYPE_MAP = {'NORMAL': '普通船', 'HIGHSPEED': '高速船', 'LUXURY': '豪华船'};

function statusText(s) { return STATUS_MAP[s] || s; }
// 船票状态：已支付未检票显示“待检票”，已过发船时间显示“已过期”
function ticketStatusText(s, departTime) {
    if (s === 'PAID') {
        if (departTime) {
            var dt = new Date(String(departTime).replace(' ', 'T'));
            if (!isNaN(dt.getTime()) && dt < new Date()) return '已过期';
        }
        return '待检票';
    }
    return STATUS_MAP[s] || s;
}
function roleText(r) { return ROLE_MAP[r] || r; }
function shipTypeText(t) { return SHIP_TYPE_MAP[t] || t; }

// 分页渲染
function renderPagination(containerId, page, total, size, callback) {
    var totalPages = Math.ceil(total / size) || 1;
    var html = '';
    html += '<button ' + (page <= 1 ? 'disabled' : '') + ' onclick="goPage(' + (page - 1) + ')">上一页</button>';
    for (var i = 1; i <= totalPages; i++) {
        if (i < page - 2 || i > page + 2) continue;
        html += '<button class="' + (i === page ? 'active' : '') + '" onclick="goPage(' + i + ')">' + i + '</button>';
    }
    html += '<button ' + (page >= totalPages ? 'disabled' : '') + ' onclick="goPage(' + (page + 1) + ')">下一页</button>';
    document.getElementById(containerId).innerHTML = html;
    window._goPage = callback;
}
function goPage(p) { if (window._goPage) window._goPage(p); }
