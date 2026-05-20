import numpy as np
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Analyzer:
    def __init__(self):
        self.data = None

    def analyze_data(self, data):
        """对贵金属数据进行全面分析"""
        if not data or 'metals' not in data:
            return data

        analyzed_metals = []
        market_trends = {
            'overall_sentiment': '中性',
            'total_gainers': 0,
            'total_losers': 0,
            'avg_change_pct': 0,
            'strongest': None,
            'weakest': None,
        }

        total_change = 0
        for metal in data['metals']:
            analysis = self._analyze_single_metal(metal)
            analyzed_metals.append(analysis)

            total_change += metal['change_pct']
            if metal['change_pct'] > 0:
                market_trends['total_gainers'] += 1
            elif metal['change_pct'] < 0:
                market_trends['total_losers'] += 1

            # Track strongest and weakest (store cleaned analysis to avoid DataFrame serialization)
            if market_trends['strongest'] is None or metal['change_pct'] > market_trends['strongest']['change_pct']:
                market_trends['strongest'] = analysis
            if market_trends['weakest'] is None or metal['change_pct'] < market_trends['weakest']['change_pct']:
                market_trends['weakest'] = analysis

        market_trends['avg_change_pct'] = round(total_change / len(data['metals']), 2) if data['metals'] else 0

        # Determine overall sentiment
        if market_trends['avg_change_pct'] > 0.5:
            market_trends['overall_sentiment'] = '看涨 📈'
        elif market_trends['avg_change_pct'] < -0.5:
            market_trends['overall_sentiment'] = '看跌 📉'
        else:
            market_trends['overall_sentiment'] = '震荡/中性 ⚖️'

        result = {
            'metals': analyzed_metals,
            'market_trends': market_trends,
            'fetch_time': data.get('fetch_time', ''),
            'fetch_date': data.get('fetch_date', ''),
            'data_source': data.get('data_source', '参考数据'),
            'reference_prices': data.get('reference_prices', {}),
            'multi_sources': data.get('multi_sources', {}),
            'summary': self.generate_summary(analyzed_metals, market_trends),
        }
        return result

    def _analyze_single_metal(self, metal):
        """分析单个投资品种的技术指标"""
        hist_5d = metal.get('history_5d')
        hist_1y = metal.get('history_1y')
        etf_hist = metal.get('etf_history')

        analysis = {
            **metal,
            'sma_5': None,
            'sma_20': None,
            'sma_30': None,
            'support_level': None,
            'resistance_level': None,
            'volatility': None,
            'trend': '--',
            'rsi': None,
            'signal': '--',
            'etf_trend': None,
            # 同比 / 环比
            'mom_pct': None,       # 环比 (月环比)
            'yoy_pct': None,       # 同比 (年同比)
            'mom_direction': '--',
            'yoy_direction': '--',
        }

        # ── 环比 (MoM): 对比1月前价格 ──────────────────────────
        if hist_1y is not None and len(hist_1y) >= 22:
            price_1m_ago = hist_1y['Close'].iloc[-22]
            current_price = metal['price']
            mom = ((current_price - price_1m_ago) / price_1m_ago) * 100
            analysis['mom_pct'] = round(mom, 2)
            analysis['mom_direction'] = '上涨 ↑' if mom > 0 else '下跌 ↓' if mom < 0 else '持平 →'

        # ── 同比 (YoY): 对比1年前价格 ──────────────────────────
        price_1y_ago = metal.get('price_1y_ago')
        if price_1y_ago and price_1y_ago > 0:
            current_price = metal['price']
            yoy = ((current_price - price_1y_ago) / price_1y_ago) * 100
            analysis['yoy_pct'] = round(yoy, 2)
            analysis['yoy_direction'] = '上涨 ↑' if yoy > 0 else '下跌 ↓' if yoy < 0 else '持平 →'

        # ── 5日技术指标 ────────────────────────────────────────
        if hist_5d is not None and len(hist_5d) >= 2:
            closes = hist_5d['Close']
            analysis['sma_5'] = round(closes.mean(), 2)
            analysis['volatility'] = round(closes.std(), 2)
            analysis['resistance_level'] = round(closes.max(), 2)
            analysis['support_level'] = round(closes.min(), 2)

            if len(closes) >= 2:
                recent_trend = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100
                if recent_trend > 1:
                    analysis['trend'] = '短期上升 ↑'
                elif recent_trend < -1:
                    analysis['trend'] = '短期下降 ↓'
                else:
                    analysis['trend'] = '震荡 →'

            # RSI
            if len(closes) >= 5:
                gains = []
                losses = []
                for i in range(1, len(closes)):
                    diff = closes.iloc[i] - closes.iloc[i - 1]
                    if diff > 0:
                        gains.append(diff)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(diff))
                avg_gain = np.mean(gains) if gains else 0
                avg_loss = np.mean(losses) if losses else 0
                if avg_loss == 0:
                    analysis['rsi'] = 100
                else:
                    rs = avg_gain / avg_loss if avg_loss > 0 else 999
                    analysis['rsi'] = round(100 - (100 / (1 + rs)), 1)

                rsi = analysis['rsi']
                if rsi is not None:
                    if rsi >= 70:
                        analysis['signal'] = '超买 ⚠️'
                    elif rsi <= 30:
                        analysis['signal'] = '超卖 💡'
                    elif rsi >= 60:
                        analysis['signal'] = '偏强 ✅'
                    elif rsi <= 40:
                        analysis['signal'] = '偏弱 ⚠️'
                    else:
                        analysis['signal'] = '中性 ➖'

        # ── 20日均线 (从6月历史取最近20天) ───────────────────
        if hist_1y is not None and len(hist_1y) >= 20:
            closes_20 = hist_1y['Close'].tail(20)
            analysis['sma_20'] = round(closes_20.mean(), 2)
        if hist_1y is not None and len(hist_1y) >= 30:
            closes_30 = hist_1y['Close'].tail(30)
            analysis['sma_30'] = round(closes_30.mean(), 2)

        # ── ETF 中期趋势 ──────────────────────────────────────
        if etf_hist is not None and len(etf_hist) >= 20:
            etf_closes = etf_hist['Close']
            analysis['sma_20'] = round(etf_closes.tail(20).mean(), 2)
            etf_trend_pct = (etf_closes.iloc[-1] - etf_closes.iloc[-20]) / etf_closes.iloc[-20] * 100
            if etf_trend_pct > 3:
                analysis['etf_trend'] = '中期上升 ↑'
            elif etf_trend_pct < -3:
                analysis['etf_trend'] = '中期下降 ↓'
            else:
                analysis['etf_trend'] = '中期震荡 →'

        # Remove raw history data to keep result clean
        analysis.pop('history_5d', None)
        analysis.pop('history_1y', None)
        analysis.pop('etf_history', None)

        return analysis

    def generate_summary(self, analyzed_metals, market_trends):
        """生成市场总结"""
        summary_parts = []

        # Market overview
        summary_parts.append(
            f"今日贵金属市场整体情绪为【{market_trends['overall_sentiment']}】，"
            f"平均涨跌幅 {market_trends['avg_change_pct']:+.2f}%。"
        )

        # Strongest and weakest
        if market_trends['strongest']:
            s = market_trends['strongest']
            summary_parts.append(
                f"表现最强的是【{s['name']}】，涨幅 {s['change_pct']:+.2f}%，"
                f"当前价格 {s['price']} {s['unit']}。"
            )
        if market_trends['weakest']:
            w = market_trends['weakest']
            summary_parts.append(
                f"表现最弱的是【{w['name']}】，涨跌幅 {w['change_pct']:+.2f}%，"
                f"当前价格 {w['price']} {w['unit']}。"
            )

        # ── 原油行情 ──────────────────────────────────────────
        oil = None
        for m in analyzed_metals:
            if m.get('category') == '能源':
                oil = m
                break
        if oil:
            summary_parts.append(
                f"原油方面，当前价格 {oil['price']} {oil['unit']}，"
                f"日涨跌幅 {oil['change_pct']:+.2f}%，"
                f"环比 {oil.get('mom_pct', 0):+.2f}%，同比 {oil.get('yoy_pct', 0):+.2f}%。"
            )

        # ── 同比/环比亮点 ─────────────────────────────────────
        mom_leaders = sorted(
            [m for m in analyzed_metals if m.get('mom_pct') is not None],
            key=lambda x: abs(x['mom_pct']), reverse=True
        )
        if mom_leaders:
            top = mom_leaders[0]
            summary_parts.append(
                f"环比变化最大的是【{top['name']}】，月涨跌幅 {top['mom_pct']:+.2f}%。"
            )

        # Technical analysis signals
        buy_signals = []
        sell_warnings = []
        for m in analyzed_metals:
            if m.get('signal') == '超卖 💡' or m.get('signal') == '偏强 ✅':
                buy_signals.append(m['name'])
            if m.get('signal') == '超买 ⚠️' or m.get('signal') == '偏弱 ⚠️':
                sell_warnings.append(m['name'])

        if buy_signals:
            summary_parts.append(f"技术面关注: {'、'.join(buy_signals)} 出现买入信号。")
        if sell_warnings:
            summary_parts.append(f"技术面注意: {'、'.join(sell_warnings)} 出现预警信号。")

        # Investment suggestion
        if market_trends['avg_change_pct'] > 0.5:
            summary_parts.append("投资建议: 市场整体偏强，可关注回调后的入场机会，注意控制仓位。")
        elif market_trends['avg_change_pct'] < -0.5:
            summary_parts.append("投资建议: 市场整体偏弱，建议观望为主，等待企稳信号再考虑入场。")
        else:
            summary_parts.append("投资建议: 市场震荡整理，建议保持当前仓位，等待趋势明朗。同时关注原油价格波动对通胀预期的影响。")

        return ' '.join(summary_parts)