"""时间同步模块 — 获取中国标准时间 (CST, UTC+8)

时间源优先级:
  1. gold-api.com 响应中的 timestamp（如果 API 请求成功）
  2. HTTP Date 头（百度/其他中国站点，如果网络可达）
  3. 系统时间（如果系统时区 = UTC+8 则直接使用）
  4. 系统时间 + 用户配置的手动偏移（兜底）
"""
import logging
import time
import urllib.request
import ssl
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# 中国标准时间偏移
CST_OFFSET = timedelta(hours=8)
CST_TZ = timezone(CST_OFFSET, 'CST')

# 网络时间源（按优先级）
TIME_SOURCES = [
    # 方案 A: gold-api.com 返回的更新时间（当数据获取成功时可用）
    # 方案 B: 百度首页 Date 头
    {'url': 'https://www.baidu.com', 'type': 'header'},
]

# 缓存
_offset_lock = None  # (server_ts_local, server_dt_utc)
_fallback_offset = None  # float hours


def _parse_http_date(date_str):
    """解析 HTTP Date 头 → datetime (UTC)"""
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return None


def _fetch_http_date(url, timeout=3):
    """获取 HTTP 响应的 Date 头"""
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        r = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        date_str = r.headers.get('Date')
        if date_str:
            dt = _parse_http_date(date_str)
            if dt:
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception as e:
        logger.debug(f"HTTP时间同步 {url}: {e}")
    return None


def calibrate(timeout=3):
    """尝试从网络获取准确时间，返回 (成功布尔, 描述)"""
    global _offset_lock

    # 尝试 HTTP Date
    for src in TIME_SOURCES:
        utc_dt = _fetch_http_date(src['url'], timeout=timeout)
        if utc_dt:
            local_now = datetime.now()
            # server UTC time vs local time → 计算偏移
            offset = utc_dt - local_now
            _offset_lock = (time.time(), utc_dt)
            cst_time = local_now + offset + CST_OFFSET
            logger.info(f"⏰ 时间已同步: 服务器={utc_dt}, 本地={local_now}, 偏移={offset.total_seconds():+.0f}s")
            return True, cst_time.strftime('%Y-%m-%d %H:%M:%S')

    logger.warning("⏰ 网络时间源不可达，使用系统时间")
    return False, None


def now():
    """返回校准后的中国标准时间 (CST, UTC+8) 的 datetime"""
    global _offset_lock

    cst_now = datetime.now(CST_TZ)

    # 如果有网络校准偏移且未过期（5分钟内），应用偏移
    if _offset_lock is not None:
        cache_time, server_utc = _offset_lock
        if time.time() - cache_time < 300:  # 缓存5分钟
            elapsed = datetime.now() - (datetime.fromtimestamp(cache_time) +
                                        (datetime.now() - datetime.fromtimestamp(cache_time)))
            # 更简单：直接用初始偏移
            offset = server_utc - datetime.fromtimestamp(cache_time)
            return (cst_now + offset).replace(tzinfo=CST_TZ)

    return cst_now


def strftime(fmt='%Y-%m-%d %H:%M:%S'):
    """返回校准后的时间字符串（CST）"""
    return now().strftime(fmt)


def strdate():
    """返回校准后的日期字符串"""
    return now().strftime('%Y-%m-%d')


# 启动时自动校准（非阻塞，失败不影响启动）
try:
    calibrate(timeout=2)
except Exception:
    pass
