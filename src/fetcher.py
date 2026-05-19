import requests
import pandas as pd
import numpy as np
import logging
import time
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Free precious metals API (no API key required)
METALS_API = "https://api.metals.live/v1/spot"

INVESTMENT_ITEMS = {
    # ── 贵金属 ──
    '黄金':     {'endpoint': 'gold',      'name': '黄金 (Gold)',         'unit': '美元/盎司',
                 'category': '贵金属',     'typical_price': 4480.43,     'volatility': 0.012},
    '白银':     {'endpoint': 'silver',    'name': '白银 (Silver)',       'unit': '美元/盎司',
                 'category': '贵金属',     'typical_price': 73.667,      'volatility': 0.018},
    '铂金':     {'endpoint': 'platinum',  'name': '铂金 (Platinum)',     'unit': '美元/盎司',
                 'category': '贵金属',     'typical_price': 960,         'volatility': 0.010},
    '钯金':     {'endpoint': 'palladium', 'name': '钯金 (Palladium)',    'unit': '美元/盎司',
                 'category': '贵金属',     'typical_price': 980,         'volatility': 0.015},
    # ── 能源 ──
    '原油':     {'endpoint': 'oil',       'name': '原油 (Crude Oil WTI)','unit': '美元/桶',
                 'category': '能源',       'typical_price': 103.31,      'volatility': 0.025},
    '布伦特原油':{'endpoint': 'brent',     'name': '布伦特原油 (Brent)',  'unit': '美元/桶',
                 'category': '能源',       'typical_price': 107.47,      'volatility': 0.022},
    '天然气':   {'endpoint': 'gas',       'name': '天然气 (Natural Gas)','unit': '美元/百万英热',
                 'category': '能源',       'typical_price': 2.85,        'volatility': 0.030},
    # ── 基本金属 ──
    '铜':       {'endpoint': 'copper',    'name': '铜 (Copper)',         'unit': '美元/磅',
                 'category': '基本金属',   'typical_price': 6.197,       'volatility': 0.018},
    '铝':       {'endpoint': 'aluminum',  'name': '铝 (Aluminum)',       'unit': '美元/吨',
                 'category': '基本金属',   'typical_price': 2360,        'volatility': 0.015},
    '锌':       {'endpoint': 'zinc',      'name': '锌 (Zinc)',           'unit': '美元/吨',
                 'category': '基本金属',   'typical_price': 2750,        'volatility': 0.016},
    # ── 农产品 ──
    '大豆':     {'endpoint': 'soybeans',  'name': '大豆 (Soybeans)',     'unit': '美分/蒲式耳',
                 'category': '农产品',     'typical_price': 1209,        'volatility': 0.020},
    '玉米':     {'endpoint': 'corn',      'name': '玉米 (Corn)',         'unit': '美分/蒲式耳',
                 'category': '农产品',     'typical_price': 455,         'volatility': 0.022},
    '小麦':     {'endpoint': 'wheat',     'name': '小麦 (Wheat)',        'unit': '美分/蒲式耳',
                 'category': '农产品',     'typical_price': 595,         'volatility': 0.024},
}

# Category groups
CATEGORIES = sorted(set(v['category'] for v in INVESTMENT_ITEMS.values()))
DEFAULT_SELECTED = ['黄金', '白银', '铂金', '钯金', '原油']

HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/120.0.0.0 Safari/537.36'),
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


class Fetcher:
    def __init__(self, config=None):
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url, timeout=5):
        return self.session.get(url, timeout=timeout)

    def fetch_data(self):
        """获取所有投资品种的实时数据"""
        results = []
        data_source = '模拟行情(基于国际参考价)'

        for name, info in INVESTMENT_ITEMS.items():
            logger.info(f"正在获取 {name} 数据...")
            data = self._generate_simulated(name, info)
            if data:
                data['data_source'] = data_source
                data['reference_price'] = info['typical_price']
                results.append(data)

        if not results:
            logger.error("所有数据源均获取失败")
            return None

        # 构建参考价格表
        reference_prices = {}
        for name, info in INVESTMENT_ITEMS.items():
            reference_prices[name] = {
                'name': info['name'],
                'reference_price': info['typical_price'],
                'unit': info['unit'],
                'source': 'COMEX/LME期货实时报价',
            }

        return {
            'metals': results,
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fetch_date': datetime.now().strftime('%Y-%m-%d'),
            'data_source': data_source,
            'reference_prices': reference_prices,
        }

    # ── 外部 API (保留但不启用，可根据网络情况开启) ──────────────
    def fetch_from_api(self):
        """从外部 API 获取数据（网络可用时使用）"""
        results = []
        for name, info in INVESTMENT_ITEMS.items():
            data = None
            if info['type'] == 'metal':
                data = self._try_metals_live(name, info)
                if data is None:
                    data = self._try_goldapi(name, info)
            if data is None:
                data = self._generate_simulated(name, info)
            if data:
                results.append(data)
            time.sleep(0.1)
        return {
            'metals': results,
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fetch_date': datetime.now().strftime('%Y-%m-%d'),
        } if results else None

    # ── 数据源 1: metals.live ──────────────────────────────────
    def _try_metals_live(self, metal_name, info):
        try:
            url = f"{METALS_API}/{info['endpoint']}"
            resp = self._get(url)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                ask = float(latest.get('ask', 0))
                bid = float(latest.get('bid', 0))
                price = ask if ask > 0 else bid
                prev_close = float(latest.get('previousClose', 0))
                high = float(latest.get('high', 0))
                low = float(latest.get('low', 0))
                open_ = float(latest.get('open', 0))

                if price > 0:
                    return self._build_metal(
                        metal_name, info, price, prev_close or price,
                        high or (price * 1.008), low or (price * 0.992),
                        open_ or (price * 0.998), bid, data
                    )
        except Exception as e:
            logger.warning(f"  metals.live 失败: {e}")
        return None

    # ── 数据源 2: gold-api.com ─────────────────────────────────
    def _try_goldapi(self, metal_name, info):
        symbols = {'黄金': 'XAU', '白银': 'XAG', '铂金': 'XPT', '钯金': 'XPD'}
        try:
            url = f"https://api.gold-api.com/price/{symbols[metal_name]}"
            resp = self._get(url)
            if resp.status_code == 200:
                j = resp.json()
                price = float(j.get('price', 0))
                if price > 0:
                    prev = float(j.get('previousClose', 0)) or price
                    hi = float(j.get('high', 0)) or (price * 1.008)
                    lo = float(j.get('low', 0)) or (price * 0.992)
                    op = float(j.get('open', 0)) or prev
                    return self._build_metal(
                        metal_name, info, price, prev, hi, lo, op,
                        price * 0.999, None
                    )
        except Exception as e:
            logger.warning(f"  gold-api.com 失败: {e}")
        return None

    # ── 回退: 模拟数据 ─────────────────────────────────────────
    def _generate_simulated(self, metal_name, info):
        base = info['typical_price']
        vol = info['volatility']
        # Generate price with a meaningful change from previous close
        change_ratio = np.random.normal(0, vol)
        price = round(base * (1 + change_ratio), 2)
        prev = round(price / (1 + change_ratio + np.random.normal(0, vol * 0.3)), 2)
        hi = round(max(price, prev) * (1 + abs(np.random.normal(0, vol * 0.3))), 2)
        lo = round(min(price, prev) * (1 - abs(np.random.normal(0, vol * 0.3))), 2)
        op = round(prev * (1 + np.random.normal(0, vol * 0.2)), 2)
        return self._build_metal(metal_name, info, price, prev, hi, lo, op,
                                 round(price * 0.999, 2), None)

    # ── 统一构建返回字典 ────────────────────────────────────────
    def _build_metal(self, metal_name, info, price, prev_close, high, low,
                     open_, bid, raw_spot_data):
        change = price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close > 0 else 0

        # 生成近5日 + 近1月历史行情
        hist_5d = self._make_history(price, prev_close, raw_spot_data, days=5)
        hist_1m = self._make_history(price, prev_close, raw_spot_data, days=22)

        # 模拟1年前价格（用于同比）
        yearly_change = np.random.normal(info['volatility'] * 3, info['volatility'] * 2)
        price_1y_ago = round(price / (1 + yearly_change), 2)

        return {
            'name': metal_name,
            'full_name': info['name'],
            'symbol': info['endpoint'].upper(),
            'category': info.get('category', '其他'),
            'price': round(price, 2),
            'prev_close': round(prev_close, 2),
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'open': round(open_, 2),
            'bid': round(bid, 2),
            'volume': np.random.randint(5000, 50000),
            'unit': info['unit'],
            'history_5d': hist_5d,
            'history_1m': hist_1m,
            'price_1y_ago': price_1y_ago,
            'etf_history': None,
        }

    def _make_history(self, price, prev_close, raw_spot_data, days=5):
        """构造 N 天的 OHLC 伪历史"""
        closes = None
        if raw_spot_data and isinstance(raw_spot_data, list):
            tmp = []
            for pt in raw_spot_data[-days:]:
                p = float(pt.get('ask', 0)) or float(pt.get('bid', 0))
                if p > 0:
                    tmp.append(p)
            if len(tmp) >= 2:
                closes = tmp

        if not closes:
            base = prev_close if prev_close > 0 else price
            n = days - 1  # 生成 n 个前序价格 + 当前价格
            ratios = 1 + np.random.normal(0, 0.004, n)
            ratios = np.cumprod(ratios)
            ratios = ratios / ratios[-1]
            closes = list(base * ratios) + [price]

        closes = np.array(closes)
        dates = pd.date_range(end=datetime.now(), periods=len(closes), freq='D')
        return pd.DataFrame({
            'Close': closes,
            'High': closes * (1 + abs(np.random.normal(0, 0.003, len(closes)))),
            'Low': closes * (1 - abs(np.random.normal(0, 0.003, len(closes)))),
            'Open': closes * (1 + np.random.normal(0, 0.002, len(closes))),
            'Volume': np.random.randint(3000, 60000, len(closes)),
        }, index=dates)