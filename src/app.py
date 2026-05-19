"""每日贵金属投资日报 - Web 交互式应用"""
import sys
import os
import json
import logging

# Add the src directory itself to path so 'from fetcher import ...' works
_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from flask import Flask, render_template, jsonify, request
from fetcher import Fetcher, INVESTMENT_ITEMS, CATEGORIES, DEFAULT_SELECTED
from analyzer import Analyzer
from analysis_ai import analyze_product

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
            static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))

# Global cache
_data_cache = None
_analyzed_cache = None
_ai_cache = {}       # {product_name: {fetch_time, result}}
_ai_cache_time = ''  # tracks the fetch_time of cached AI results


def ensure_static():
    """Ensure static directory exists"""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    os.makedirs(static_dir, exist_ok=True)


def get_all_data():
    """获取并缓存全量数据"""
    global _data_cache, _analyzed_cache
    fetcher = Fetcher()
    analyzer = Analyzer()

    raw = fetcher.fetch_data()
    if raw:
        _data_cache = raw
        _analyzed_cache = analyzer.analyze_data(raw)
    return _analyzed_cache


@app.route('/')
def index():
    """主页 - 渲染交互式日报"""
    ensure_static()
    data = get_all_data()
    if not data:
        return render_template('report.html',
                               metals=[],
                               market_trends={},
                               summary='',
                               fetch_time='',
                               fetch_date='',
                               categories=CATEGORIES,
                               all_products=INVESTMENT_ITEMS,
                               default_selected=DEFAULT_SELECTED,
                               error='无法获取数据')
    return render_template('report.html',
                           metals=data.get('metals', []),
                           market_trends=data.get('market_trends', {}),
                           summary=data.get('summary', ''),
                           fetch_time=data.get('fetch_time', ''),
                           fetch_date=data.get('fetch_date', ''),
                           categories=CATEGORIES,
                           all_products=INVESTMENT_ITEMS,
                           default_selected=DEFAULT_SELECTED)


@app.route('/api/data')
def api_data():
    """API: 获取选中品种的实时数据"""
    selected = request.args.getlist('selected')
    if not selected:
        selected = DEFAULT_SELECTED

    data = get_all_data()
    if not data:
        return jsonify({'error': '获取数据失败'}), 500

    metals = data.get('metals', [])
    filtered = [m for m in metals if m['name'] in selected]

    market = data.get('market_trends', {})
    # Recalculate for filtered set
    if filtered:
        changes = [m['change_pct'] for m in filtered]
        gainers = sum(1 for c in changes if c > 0)
        losers = sum(1 for c in changes if c < 0)
        avg = round(sum(changes) / len(changes), 2) if changes else 0
        strongest = max(filtered, key=lambda x: x['change_pct']) if filtered else None
        weakest = min(filtered, key=lambda x: x['change_pct']) if filtered else None

        if avg > 0.5:
            sentiment = '看涨 📈'
        elif avg < -0.5:
            sentiment = '看跌 📉'
        else:
            sentiment = '震荡/中性 ⚖️'

        market = {
            'overall_sentiment': sentiment,
            'total_gainers': gainers,
            'total_losers': losers,
            'avg_change_pct': avg,
            'strongest': strongest,
            'weakest': weakest,
        }

    return jsonify({
        'metals': filtered,
        'market_trends': market,
        'summary': data.get('summary', ''),
        'fetch_time': data.get('fetch_time', ''),
        'fetch_date': data.get('fetch_date', ''),
    })


@app.route('/api/products')
def api_products():
    """API: 获取所有可用品种列表"""
    products = []
    for key, info in INVESTMENT_ITEMS.items():
        products.append({
            'key': key,
            'name': info['name'],
            'category': info['category'],
            'unit': info['unit'],
        })
    return jsonify({
        'categories': CATEGORIES,
        'products': products,
        'default_selected': DEFAULT_SELECTED,
    })


@app.route('/api/history')
def api_history():
    """API: 获取选中品种的1月历史走势数据"""
    selected = request.args.getlist('selected')
    if not selected:
        selected = DEFAULT_SELECTED

    data = get_all_data()
    if not data:
        return jsonify({'error': '获取数据失败'}), 500

    # Need raw data with history_1m DataFrames
    global _data_cache
    if _data_cache is None:
        fetcher = Fetcher()
        _data_cache = fetcher.fetch_data()

    if not _data_cache:
        return jsonify({'error': '无数据'}), 500

    result = {}
    for metal in _data_cache.get('metals', []):
        if metal['name'] in selected:
            hist = metal.get('history_1m')
            if hist is not None and not hist.empty:
                dates = hist.index.strftime('%Y-%m-%d').tolist()
                closes = [round(v, 2) for v in hist['Close'].tolist()]
                result[metal['name']] = {
                    'name': metal['full_name'],
                    'dates': dates,
                    'closes': closes,
                }
    return jsonify({'history': result})


@app.route('/api/analyze/<product_name>')
def api_analyze(product_name):
    """API: 对指定品种进行AI分析（带缓存，数据不变时复用结果）"""
    global _ai_cache, _ai_cache_time

    data = get_all_data()
    if not data:
        return jsonify({'error': '数据不可用'}), 500

    current_time = data.get('fetch_time', '')

    # 数据时间变了 → 清空整个缓存
    if current_time != _ai_cache_time:
        _ai_cache = {}
        _ai_cache_time = current_time

    # 缓存命中
    if product_name in _ai_cache:
        return jsonify(_ai_cache[product_name])

    # 查找品种数据
    metals = data.get('metals', [])
    target = None
    for m in metals:
        if m['name'] == product_name:
            target = m
            break

    if not target:
        return jsonify({'error': f'未找到品种: {product_name}'}), 404

    # 执行分析并缓存
    result = analyze_product(target)
    _ai_cache[product_name] = result
    return jsonify(result)


@app.route('/api/refresh')
def api_refresh():
    """API: 强制刷新数据"""
    global _data_cache, _analyzed_cache, _ai_cache, _ai_cache_time
    _data_cache = None
    _analyzed_cache = None
    _ai_cache = {}
    _ai_cache_time = ''
    data = get_all_data()
    if data:
        return jsonify({'status': 'ok', 'fetch_time': data.get('fetch_time', '')})
    return jsonify({'error': '刷新失败'}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("📊 每日贵金属投资日报 - Web 交互版")
    print("=" * 50)
    print(f"🌐 访问地址: http://127.0.0.1:5000")
    print(f"📡 自动刷新: 每5分钟更新行情、走势图")
    print(f"🤖 AI分析: 点击品种旁的AI按钮")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
