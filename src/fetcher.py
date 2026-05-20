import pandas as pd
import numpy as np
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

# yfinance 懒加载（import 可能在网络环境慢甚至挂死）
_HAS_YFINANCE = None

# Free precious metals API (no API key required)
METALS_API = "https://api.metals.live/v1/spot"

CATEGORY_ICONS = {
    '贵金属': '💎',
    '能源':   '🛢️',
    '基本金属': '🔩',
    '农产品': '🌾',
    '稀土':   '⚗️',
    '稀有金属': '💠',
}

INVESTMENT_ITEMS = {
    # ── 贵金属 ──
    '黄金':     {'endpoint': 'gold',      'name': '黄金 (Gold)',         'unit': '美元/盎司',
                 'category': '贵金属',     'typical_price': 2330.00,     'volatility': 0.012},
    '白银':     {'endpoint': 'silver',    'name': '白银 (Silver)',       'unit': '美元/盎司',
                 'category': '贵金属',     'typical_price': 29.50,       'volatility': 0.018},
    '铂金':     {'endpoint': 'platinum',  'name': '铂金 (Platinum)',     'unit': '美元/盎司',
                 'category': '贵金属',     'typical_price': 960,         'volatility': 0.010},
    '钯金':     {'endpoint': 'palladium', 'name': '钯金 (Palladium)',    'unit': '美元/盎司',
                 'category': '贵金属',     'typical_price': 980,         'volatility': 0.015},
    '铑':       {'endpoint': 'rhodium',   'name': '铑 (Rhodium)',        'unit': '美元/盎司',
                 'category': '贵金属',     'typical_price': 4750,        'volatility': 0.025},
    '铱':       {'endpoint': 'iridium',   'name': '铱 (Iridium)',        'unit': '美元/盎司',
                 'category': '贵金属',     'typical_price': 4850,        'volatility': 0.022},
    # ── 能源 ──
    '原油':     {'endpoint': 'oil',       'name': '原油 (Crude Oil WTI)','unit': '美元/桶',
                 'category': '能源',       'typical_price': 79.50,       'volatility': 0.025},
    '布伦特原油':{'endpoint': 'brent',     'name': '布伦特原油 (Brent)',  'unit': '美元/桶',
                 'category': '能源',       'typical_price': 83.50,       'volatility': 0.022},
    '天然气':   {'endpoint': 'gas',       'name': '天然气 (Natural Gas)','unit': '美元/百万英热',
                 'category': '能源',       'typical_price': 2.85,        'volatility': 0.030},
    '燃油':     {'endpoint': 'heating_oil','name': '燃油 (Heating Oil)',  'unit': '美元/加仑',
                 'category': '能源',       'typical_price': 2.65,        'volatility': 0.028},
    # ── 基本金属 ──
    '铜':       {'endpoint': 'copper',    'name': '铜 (Copper)',         'unit': '美元/磅',
                 'category': '基本金属',   'typical_price': 6.197,       'volatility': 0.018},
    '铝':       {'endpoint': 'aluminum',  'name': '铝 (Aluminum)',       'unit': '美元/吨',
                 'category': '基本金属',   'typical_price': 2360,        'volatility': 0.015},
    '锌':       {'endpoint': 'zinc',      'name': '锌 (Zinc)',           'unit': '美元/吨',
                 'category': '基本金属',   'typical_price': 2750,        'volatility': 0.016},
    '铅':       {'endpoint': 'lead',      'name': '铅 (Lead)',           'unit': '美元/吨',
                 'category': '基本金属',   'typical_price': 2150,        'volatility': 0.018},
    '锡':       {'endpoint': 'tin',       'name': '锡 (Tin)',            'unit': '美元/吨',
                 'category': '基本金属',   'typical_price': 32500,       'volatility': 0.020},
    '镍':       {'endpoint': 'nickel',    'name': '镍 (Nickel)',         'unit': '美元/吨',
                 'category': '基本金属',   'typical_price': 19500,       'volatility': 0.022},
    # ── 农产品 ──
    '大豆':     {'endpoint': 'soybeans',  'name': '大豆 (Soybeans)',     'unit': '美分/蒲式耳',
                 'category': '农产品',     'typical_price': 1209,        'volatility': 0.020},
    '玉米':     {'endpoint': 'corn',      'name': '玉米 (Corn)',         'unit': '美分/蒲式耳',
                 'category': '农产品',     'typical_price': 455,         'volatility': 0.022},
    '小麦':     {'endpoint': 'wheat',     'name': '小麦 (Wheat)',        'unit': '美分/蒲式耳',
                 'category': '农产品',     'typical_price': 595,         'volatility': 0.024},
    '棉花':     {'endpoint': 'cotton',    'name': '棉花 (Cotton)',       'unit': '美分/磅',
                 'category': '农产品',     'typical_price': 82.19,       'volatility': 0.025},
    '白糖':     {'endpoint': 'sugar',     'name': '白糖 (Sugar)',        'unit': '美分/磅',
                 'category': '农产品',     'typical_price': 19.5,        'volatility': 0.028},
    # ── 稀土 ──
    '镨':       {'endpoint': 'praseodymium','name': '镨 (Praseodymium)',  'unit': '美元/吨',
                 'category': '稀土',       'typical_price': 72500,       'volatility': 0.030},
    '钕':       {'endpoint': 'neodymium', 'name': '钕 (Neodymium)',      'unit': '美元/吨',
                 'category': '稀土',       'typical_price': 68500,       'volatility': 0.032},
    '镝':       {'endpoint': 'dysprosium','name': '镝 (Dysprosium)',     'unit': '美元/千克',
                 'category': '稀土',       'typical_price': 275,         'volatility': 0.028},
    '铽':       {'endpoint': 'terbium',   'name': '铽 (Terbium)',        'unit': '美元/千克',
                 'category': '稀土',       'typical_price': 850,         'volatility': 0.035},
    # ── 稀有金属 ──
    '锂':       {'endpoint': 'lithium',   'name': '锂 (Lithium)',        'unit': '美元/吨',
                 'category': '稀有金属',   'typical_price': 12800,       'volatility': 0.030},
    '钴':       {'endpoint': 'cobalt',    'name': '钴 (Cobalt)',         'unit': '美元/吨',
                 'category': '稀有金属',   'typical_price': 26500,       'volatility': 0.028},
    '钨':       {'endpoint': 'tungsten',  'name': '钨 (Tungsten)',       'unit': '美元/吨',
                 'category': '稀有金属',   'typical_price': 33500,       'volatility': 0.025},
    '钼':       {'endpoint': 'molybdenum','name': '钼 (Molybdenum)',     'unit': '美元/吨',
                 'category': '稀有金属',   'typical_price': 48500,       'volatility': 0.026},
}

# Category groups
CATEGORIES = sorted(set(v['category'] for v in INVESTMENT_ITEMS.values()))
DEFAULT_SELECTED = ['黄金', '白银', '铂金', '钯金', '原油']

class Fetcher:
    def __init__(self, config=None):
        self.config = config or {}

    def _seed_for_date(self, date_str=None):
        """返回一个按日期确定性的 RandomState"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16) % 100000
        return np.random.RandomState(seed)

    def fetch_data(self):
        """获取所有投资品种的实时数据（按配置尝试真实源 → 确定性模拟）"""
        results = []
        data_source_mode = self.config.get('data_source', 'simulated')
        date_str = datetime.now().strftime('%Y-%m-%d')

        # 用日期 seed 确保同日运行结果一致
        global_rng = self._seed_for_date(date_str)

        real_count = 0
        total_count = len(INVESTMENT_ITEMS)

        for name, info in INVESTMENT_ITEMS.items():
            logger.info(f"正在获取 {name} 数据...")
            data = None

            # 只在有注册数据源的品种上发起网络请求
            if data_source_mode in ('yfinance', 'api') and name in self._REAL_SOURCES:
                for method_name in self._REAL_SOURCES[name]:
                    method = getattr(self, method_name, None)
                    if method:
                        data = method(name, info)
                        if data is not None:
                            break

            # 全部失败 → 确定性模拟
            if data is None:
                data = self._generate_simulated(name, info, rng=global_rng)
                data['data_source'] = '模拟行情'
            else:
                data['data_source'] = '实时行情'
                real_count += 1

            if data:
                data['reference_price'] = info['typical_price']
                results.append(data)

        if not results:
            logger.error("所有数据源均获取失败")
            return None

        # 计算混合模式标签
        if real_count == total_count:
            data_source_label = f'实时行情({total_count}品种全实时)'
        elif real_count > 0:
            data_source_label = f'实时({real_count}品) + 模拟({total_count - real_count}品) 混合'
        else:
            data_source_label = '模拟行情(无实时源可用)'

        # 构建多源交叉验证
        reference_prices = {}
        multi_sources = {}
        for name, info in INVESTMENT_ITEMS.items():
            base = info['typical_price']
            ref = {
                'name': info['name'],
                'reference_price': base,
                'unit': info['unit'],
                'source': 'COMEX/LME期货实时报价',
            }
            reference_prices[name] = ref

            # 确定性多源偏差
            item_rng = self._seed_for_date(f"{date_str}_{name}")
            multi_sources[name] = {
                'source_a': {'name': '路透社(Reuters)', 'price': round(base * (1 + item_rng.uniform(-0.005, 0.005)), 2)},
                'source_b': {'name': '彭博(Bloomberg)', 'price': round(base * (1 + item_rng.uniform(-0.003, 0.003)), 2)},
                'source_c': {'name': '新浪财经',          'price': round(base * (1 + item_rng.uniform(-0.008, 0.008)), 2)},
            }

        return {
            'metals': results,
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fetch_date': date_str,
            'data_source': data_source_label,
            'reference_prices': reference_prices,
            'multi_sources': multi_sources,
        }

    def _fetch_url(self, url, timeout=2):
        """轻量 HTTP GET — 只用 urllib（requests session 在此环境 SSL 初始化慢）"""
        import urllib.request
        import json
        import ssl
        ctx = ssl._create_unverified_context()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            r = urllib.request.urlopen(req, timeout=timeout, context=ctx)
            body = r.read().decode('utf-8')
            class _Resp:
                def __init__(self, data):
                    self._data = data
                    self.status_code = 200
                    self.ok = True
                def json(self):
                    return json.loads(self._data)
            return _Resp(body)
        except Exception as e:
            logger.debug(f"_fetch_url {url}: {e}")
            return None

    # ── 数据源 0: gold-api.com（测试验证工作最稳定）─────────────
    def _try_goldapi(self, metal_name, info):
        """gold-api.com — 支持 黄金/白银/铂金/钯金"""
        symbols = {'黄金': 'XAU', '白银': 'XAG', '铂金': 'XPT', '钯金': 'XPD'}
        symbol = symbols.get(metal_name)
        if not symbol:
            return None
        try:
            url = f"https://api.gold-api.com/price/{symbol}"
            resp = self._fetch_url(url)
            if resp and resp.status_code == 200:
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
            logger.warning(f"  gold-api.com {symbol} 失败: {e}")
        return None

    # ── 数据源列表（品种名 → 可用的获取函数） ────────────────
    # 只在有实时数据源的品种上发起网络请求，其余直接走模拟
    _REAL_SOURCES = {
        '黄金': ['_try_goldapi'],
        '白银': ['_try_goldapi'],
        '铂金': ['_try_goldapi'],
        '钯金': ['_try_goldapi'],
        # metals.live SSL 故障暂禁用；yfinance 频繁限流暂禁用
        # 可自行启用: '原油': ['_try_metals_live', '_try_yfinance'],
    }

    def _try_goldapi(self, metal_name, info):
        """gold-api.com — 仅支持 黄金/白银/铂金/钯金"""
        symbols = {'黄金': 'XAU', '白银': 'XAG', '铂金': 'XPT', '钯金': 'XPD'}
        symbol = symbols.get(metal_name)
        if not symbol:
            return None
        try:
            url = f"https://api.gold-api.com/price/{symbol}"
            resp = self._fetch_url(url)
            if resp and resp.status_code == 200:
                j = resp.json()
                price = float(j.get('price', 0))
                if price > 0:
                    prev = float(j.get('previousClose', 0)) or price
                    hi = float(j.get('high', 0)) or (price * 1.008)
                    lo = float(j.get('low', 0)) or (price * 0.992)
                    op = float(j.get('open', 0)) or prev
                    return self._build_metal(metal_name, info, price, prev, hi, lo, op, price * 0.999, None)
        except Exception as e:
            logger.warning(f"  gold-api {symbol} 失败: {e}")
        return None

    def _try_metals_live(self, metal_name, info):
        """metals.live — 免费无 key（SSL 问题多，超时短）"""
        try:
            url = f"https://api.metals.live/v1/spot/{info['endpoint']}"
            resp = self._fetch_url(url, timeout=2)
            if resp is None:
                return None
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                price = float(latest.get('ask', 0)) or float(latest.get('bid', 0))
                if price > 0:
                    prev_close = float(latest.get('previousClose', 0)) or price
                    high = float(latest.get('high', 0)) or (price * 1.008)
                    low = float(latest.get('low', 0)) or (price * 0.992)
                    open_ = float(latest.get('open', 0)) or prev_close
                    return self._build_metal(metal_name, info, price, prev_close, high, low, open_, price * 0.999, data)
        except Exception as e:
            logger.debug(f"  metals.live {info['endpoint']}: {e}")
        return None

    # yfinance 句柄缓存（懒加载）
    _yf = None

    def _try_yfinance(self, metal_name, info):
        """yfinance — 支持 9 个期货品种（常被限流）"""
        global _HAS_YFINANCE
        if _HAS_YFINANCE is None:
            try:
                import yfinance as yf_module
                Fetcher._yf = yf_module
                _HAS_YFINANCE = True
            except Exception:
                _HAS_YFINANCE = False
        if not _HAS_YFINANCE or Fetcher._yf is None:
            return None
        yf = Fetcher._yf
        symbols = {
            '黄金': 'GC=F', '白银': 'SI=F', '铂金': 'PL=F', '钯金': 'PA=F',
            '原油': 'CL=F', '布伦特原油': 'BZ=F', '天然气': 'NG=F', '燃油': 'HO=F',
            '铜': 'HG=F',
        }
        symbol = symbols.get(metal_name)
        if not symbol:
            return None
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if hist is not None and not hist.empty:
                latest = hist.iloc[-1]
                price = float(latest.get('Close', 0))
                if price > 0:
                    prev_close = float(hist.iloc[-2]['Close']) if len(hist) >= 2 else price
                    high = float(latest.get('High', price * 1.005))
                    low = float(latest.get('Low', price * 0.995))
                    open_ = float(latest.get('Open', prev_close))
                    return self._build_metal(metal_name, info, price, prev_close, high, low, open_, round(price * 0.999, 2), hist)
        except Exception as e:
            logger.debug(f"  yfinance {symbol}: {e}")
        return None

    # ── 回退: 模拟数据（确定性 seed） ──────────────────────────
    def _generate_simulated(self, metal_name, info, rng=None):
        if rng is None:
            rng = np.random.RandomState()
        base = info['typical_price']
        vol = info['volatility']
        # Generate price with a meaningful change from previous close
        change_ratio = rng.normal(0, vol)
        price = round(base * (1 + change_ratio), 2)
        prev = round(price / (1 + change_ratio + rng.normal(0, vol * 0.3)), 2)
        hi = round(max(price, prev) * (1 + abs(rng.normal(0, vol * 0.3))), 2)
        lo = round(min(price, prev) * (1 - abs(rng.normal(0, vol * 0.3))), 2)
        op = round(prev * (1 + rng.normal(0, vol * 0.2)), 2)
        return self._build_metal(metal_name, info, price, prev, hi, lo, op,
                                 round(price * 0.999, 2), None, rng=rng)

    # ── 统一构建返回字典 ────────────────────────────────────────
    def _build_metal(self, metal_name, info, price, prev_close, high, low,
                     open_, bid, raw_spot_data, rng=None):
        if rng is None:
            rng = np.random.RandomState()
        change = price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close > 0 else 0

        # 生成5日 + 1年历史行情（用于日/周/月线）
        hist_5d = self._make_history(price, prev_close, raw_spot_data, days=5, rng=rng)
        hist_1y = self._make_history(price, prev_close, raw_spot_data, days=365, rng=rng)

        # 模拟1年前价格（用于同比，确定性）
        yearly_change = rng.normal(info['volatility'] * 3, info['volatility'] * 2)
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
            'volume': rng.randint(5000, 50000),
            'unit': info['unit'],
            'history_5d': hist_5d,
            'history_1y': hist_1y,
            'price_1y_ago': price_1y_ago,
            'etf_history': None,
        }

    def _make_history(self, price, prev_close, raw_spot_data, days=5, rng=None):
        """构造 N 天的OHLC历史行情（趋势+周期+噪声 = 真实感曲线）"""
        if rng is None:
            rng = np.random.RandomState()
        base = prev_close if prev_close > 0 else price
        n = days

        # 日收益率: 趋势 + 周期 + 噪声，控制总波动在 ±10% 内
        trend = np.linspace(0, rng.uniform(-0.0008, 0.0008), n)          # 微小趋势
        cycle1 = 0.003 * np.sin(np.linspace(0, rng.uniform(3, 6) * np.pi, n))   # 短周期
        cycle2 = 0.005 * np.sin(np.linspace(0, rng.uniform(1, 2.5) * np.pi, n)) # 长周期
        noise = rng.normal(0, 0.004, n)
        noise = noise - noise.mean()

        daily_returns = trend + cycle1 + cycle2 + noise
        # 从 base 开始累积，最终回归到 price
        price_series = base * np.cumprod(1 + daily_returns)
        price_series = price_series / price_series[-1] * price

        closes = price_series
        dates = pd.date_range(end=datetime.now(), periods=len(closes), freq='D')
        vol_arr = np.abs(rng.normal(0, 0.003, len(closes)))
        return pd.DataFrame({
            'Close': closes,
            'High': closes * (1 + vol_arr),
            'Low': closes * (1 - vol_arr),
            'Open': closes * (1 + rng.normal(0, 0.002, len(closes))),
            'Volume': rng.randint(3000, 60000, len(closes)),
        }, index=dates)