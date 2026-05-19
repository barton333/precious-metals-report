"""AI投资分析模块 - 基于技术指标生成趋势预测和投资建议"""
import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def analyze_product(metal_data):
    """对单个投资品种进行全面AI分析"""
    try:
        name = metal_data.get('name', '未知')
        price = metal_data.get('price', 0)
        rsi = metal_data.get('rsi')
        sma_5 = metal_data.get('sma_5')
        sma_20 = metal_data.get('sma_20')
        mom = metal_data.get('mom_pct')
        yoy = metal_data.get('yoy_pct')
        trend = metal_data.get('trend', '--')
        signal = metal_data.get('signal', '--')
        volatility = metal_data.get('volatility')
        support = metal_data.get('support_level')
        resistance = metal_data.get('resistance_level')
        change_pct = metal_data.get('change_pct', 0)
        unit = metal_data.get('unit', '')

        analysis = {
            'product_name': name,
            'current_price': price,
            'unit': unit,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'score': 50,  # 综合评分 0-100
        }

        # ── 趋势分析 ──
        trend_analysis = _analyze_trend(name, trend, rsi, sma_5, sma_20, price)
        analysis['trend_analysis'] = trend_analysis

        # ── RSI 分析 ──
        rsi_analysis = _analyze_rsi(name, rsi)
        analysis['rsi_analysis'] = rsi_analysis

        # ── 价格区间分析 ──
        range_analysis = _analyze_price_range(price, support, resistance, volatility)
        analysis['range_analysis'] = range_analysis

        # ── 动量分析 ──
        momentum = _analyze_momentum(change_pct, mom, yoy)
        analysis['momentum'] = momentum

        # ── 综合预测 ──
        prediction = _generate_prediction(name, price, trend_analysis, rsi_analysis,
                                          momentum, signal, volatility)
        analysis['prediction'] = prediction

        # ── 投资建议 ──
        advice = _generate_advice(prediction, signal, rsi)
        analysis['advice'] = advice

        # ── 综合评分 ──
        analysis['score'] = _calculate_score(rsi, momentum, trend_analysis, signal)

        return analysis

    except Exception as e:
        logger.error(f"AI分析失败 [{metal_data.get('name', '未知')}]: {e}")
        return {
            'product_name': metal_data.get('name', '未知'),
            'error': str(e),
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }


def _analyze_trend(name, trend, rsi, sma_5, sma_20, price):
    """分析趋势方向和强度"""
    parts = []

    # 短期趋势
    if trend and trend != '--':
        parts.append(f"短期趋势: {trend}")
        if '上升' in trend:
            parts.append("近期价格持续走高，多方力量占优。")
        elif '下降' in trend:
            parts.append("近期价格持续走低，空方力量占优。")
        else:
            parts.append("近期价格波动较小，处于整理阶段。")

    # 均线分析
    if sma_5 and sma_20 and price:
        if price > sma_20:
            parts.append(f"价格位于20日均线(${sma_20:.2f})上方，中期趋势偏多。")
        elif price < sma_20:
            parts.append(f"价格位于20日均线(${sma_20:.2f})下方，中期趋势偏空。")
    elif sma_5 and price:
        ratio = (price / sma_5 - 1) * 100
        if ratio > 1:
            parts.append(f"价格高于5日均线${sma_5:.2f}约{ratio:.1f}%，短期偏强。")
        elif ratio < -1:
            parts.append(f"价格低于5日均线${sma_5:.2f}约{abs(ratio):.1f}%，短期偏弱。")
        else:
            parts.append(f"价格围绕5日均线${sma_5:.2f}附近波动。")

    return ' '.join(parts) if parts else '数据不足以判断趋势。'


def _analyze_rsi(name, rsi):
    """分析RSI指标"""
    if rsi is None:
        return 'RSI数据不足，无法分析。'

    parts = [f"当前RSI值为{rsi:.1f}。"]
    if rsi >= 80:
        parts.append("⚠️ 处于严重超买区域，短期回调风险较大，建议谨慎追高。")
    elif rsi >= 70:
        parts.append("⚠️ 处于超买区域，短期可能面临回调压力，建议适当减仓。")
    elif rsi >= 60:
        parts.append("✅ 处于偏强区域，多头动能充足，趋势向好。")
    elif rsi >= 40:
        parts.append("➖ 处于中性区域，多空力量均衡，建议观望。")
    elif rsi >= 30:
        parts.append("⚠️ 处于偏弱区域，空头占优，建议等待企稳信号。")
    elif rsi >= 20:
        parts.append("💡 处于超卖区域，可能出现反弹机会，可关注逢低布局。")
    else:
        parts.append("💡 处于严重超卖区域，超跌反弹概率较大，可考虑分批建仓。")

    return ' '.join(parts)


def _analyze_price_range(price, support, resistance, volatility):
    """分析价格区间"""
    parts = []
    if support and resistance:
        range_width = ((resistance - support) / support) * 100
        parts.append(f"当前运行区间: ${support:.2f} ~ ${resistance:.2f}，区间宽度{range_width:.1f}%。")
        current_pos = ((price - support) / (resistance - support)) * 100
        if current_pos < 20:
            parts.append("价格接近支撑位，关注支撑有效性。")
        elif current_pos > 80:
            parts.append("价格接近阻力位，关注突破情况。")
        else:
            parts.append("价格处于区间中部，方向尚不明朗。")

        # 突破分析
        if price >= resistance:
            parts.append("⚠️ 价格已突破阻力位，可能进一步上扬，但也需警惕假突破。")
        elif price <= support:
            parts.append("⚠️ 价格已跌破支撑位，可能进一步下探。")

    if volatility:
        parts.append(f"近5日波动率: {volatility:.2f}，波动性{'较大' if volatility > price * 0.02 else '正常'}。")

    return ' '.join(parts) if parts else '价格区间数据不足。'


def _analyze_momentum(change_pct, mom, yoy):
    """分析动量"""
    result = {'daily': None, 'monthly': None, 'yearly': None, 'summary': ''}
    parts = []

    if change_pct is not None:
        result['daily'] = change_pct
        if abs(change_pct) > 2:
            parts.append(f"日涨跌幅{change_pct:+.2f}%，波动较大。")
        else:
            parts.append(f"日涨跌幅{change_pct:+.2f}%。")

    if mom is not None:
        result['monthly'] = mom
        parts.append(f"月环比{mom:+.2f}%")
        if mom > 3:
            parts.append("，月线强势上涨。")
        elif mom < -3:
            parts.append("，月线明显下跌。")
        else:
            parts.append("，月线变化温和。")

    if yoy is not None:
        result['yearly'] = yoy
        yearly_word = '大涨' if yoy > 15 else '上涨' if yoy > 3 else '震荡' if yoy > -3 else '下跌' if yoy > -15 else '大跌'
        parts.append(f"同比{yearly_word}({yoy:+.2f}%)。")

    result['summary'] = ' '.join(parts)
    return result


def _generate_prediction(name, price, trend_analysis, rsi_analysis, momentum, signal, volatility):
    """生成本来走势预测"""
    parts = []
    confidence = '中'

    # 基于RSI的预测
    rsi = None
    for word in rsi_analysis.split():
        try:
            rsi = float(word.replace('。', ''))
        except ValueError:
            continue

    # 综合判断方向
    bullish_signals = 0
    bearish_signals = 0

    if '上升' in trend_analysis:
        bullish_signals += 1
    if '下降' in trend_analysis:
        bearish_signals += 1

    if momentum.get('daily', 0) > 0.5:
        bullish_signals += 1
    elif momentum.get('daily', 0) < -0.5:
        bearish_signals += 1

    if momentum.get('monthly') and momentum['monthly'] > 2:
        bullish_signals += 1
    elif momentum.get('monthly') and momentum['monthly'] < -2:
        bearish_signals += 1

    if rsi and rsi < 35:
        bullish_signals += 1  # 超卖反弹预期
    elif rsi and rsi > 65:
        bearish_signals += 1  # 超买回调预期

    net = bullish_signals - bearish_signals
    if net >= 2:
        direction = '看涨 📈'
        confidence = '高'
        parts.append(f"综合分析，{name}未来短期趋势偏向看涨。")
    elif net <= -2:
        direction = '看跌 📉'
        confidence = '高'
        parts.append(f"综合分析，{name}未来短期趋势偏向看跌。")
    elif net >= 1:
        direction = '谨慎看涨 📈'
        confidence = '中'
        parts.append(f"综合分析，{name}未来短期趋势可能小幅上行。")
    elif net <= -1:
        direction = '谨慎看跌 📉'
        confidence = '中'
        parts.append(f"综合分析，{name}未来短期趋势可能小幅下行。")
    else:
        direction = '震荡整理 ⚖️'
        confidence = '低'
        parts.append(f"多空信号交织，{name}短期可能维持震荡格局。")

    # 关键价位预测
    price_change = abs(momentum.get('daily', 0)) if momentum.get('daily') else 1
    estimated_move = max(price * 0.01, price * abs(price_change) / 100 * 3)

    target_up = round(price + estimated_move, 2)
    target_down = round(price - estimated_move, 2)

    parts.append(f"预计未来3-5个交易日关键价位: 上方目标${target_up}，下方支撑${target_down}。")

    # 波动性提示
    if volatility and price > 0 and volatility / price > 0.02:
        parts.append("近期波动率偏高，建议控制仓位风险。")

    return {
        'direction': direction,
        'confidence': confidence,
        'target_up': target_up,
        'target_down': target_down,
        'detail': ' '.join(parts),
        'signal_strength': net,
    }


def _generate_advice(prediction, signal, rsi):
    """生成投资建议"""
    advice = {'action': '持有', 'reason': '', 'risk_level': '中'}

    direction = prediction.get('direction', '')
    confidence = prediction.get('confidence', '中')

    if '看涨' in direction and confidence == '高':
        advice['action'] = '买入/加仓'
        advice['risk_level'] = '低'
        advice['reason'] = '多项技术指标共振向好，趋势明确，建议逢低布局。'
    elif '看涨' in direction:
        advice['action'] = '逢低买入'
        advice['risk_level'] = '中'
        advice['reason'] = '技术面偏多，但信号强度一般，建议分批建仓。'
    elif '看跌' in direction and confidence == '高':
        advice['action'] = '卖出/减仓'
        advice['risk_level'] = '高'
        advice['reason'] = '多项指标转空，下行风险加大，建议减仓避险。'
    elif '看跌' in direction:
        advice['action'] = '减仓观望'
        advice['risk_level'] = '中'
        advice['reason'] = '技术面偏空，但下跌动能有限，建议降低仓位。'
    else:
        advice['action'] = '持有观望'
        advice['risk_level'] = '中'
        advice['reason'] = '市场方向不明，建议保持当前仓位等待趋势明朗。'

    # 风险警示
    warnings = []
    if rsi and rsi > 75:
        warnings.append('RSI超买，警惕回调风险。')
    if rsi and rsi < 25:
        warnings.append('RSI超卖，存在反弹机会。')

    if warnings:
        advice['reason'] += ' 风险提示: ' + ' '.join(warnings)

    return advice


def _calculate_score(rsi, momentum, trend_analysis, signal):
    """计算综合评分 0-100"""
    score = 50

    # RSI评分
    if rsi:
        if 40 <= rsi <= 60:
            score += 5  # 中性区域加分
        elif rsi >= 70 or rsi <= 30:
            score -= 5  # 极端区域减分

    # 动量评分
    daily = momentum.get('daily', 0) if momentum else 0
    score += min(max(daily * 2, -10), 10)

    # 趋势评分
    if '上升' in trend_analysis:
        score += 10
    elif '下降' in trend_analysis:
        score -= 10

    # 信号评分
    if '超卖' in signal or '偏强' in signal:
        score += 10
    elif '超买' in signal or '偏弱' in signal:
        score -= 10

    return max(0, min(100, int(round(score))))


def get_available_analysis():
    """返回可用的分析功能列表"""
    return {
        'trend_analysis': '趋势分析 - 基于均线系统判断短期、中期趋势方向',
        'rsi_analysis': 'RSI分析 - 相对强弱指标判断超买超卖状态',
        'price_range': '价格区间 - 支撑位/阻力位识别与突破判断',
        'momentum': '动量分析 - 日/月/年多周期动量对比',
        'prediction': '趋势预测 - 综合多指标的未来3-5日走势预测',
        'risk_assessment': '风险评估 - 波动率与仓位管理建议',
    }
