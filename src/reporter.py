import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import io
import base64
import os
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from fetcher import INVESTMENT_ITEMS, CATEGORIES, DEFAULT_SELECTED, CATEGORY_ICONS

logger = logging.getLogger(__name__)

# Try to use Chinese font if available
CHINESE_FONT = None
for font_name in ['Microsoft YaHei', 'SimHei', 'PingFang SC', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei']:
    try:
        font = fm.findfont(font_name, fallback_to_default=False)
        if font and 'dejavu' not in font.lower():
            CHINESE_FONT = font_name
            break
    except Exception:
        continue

plt.rcParams['font.family'] = CHINESE_FONT if CHINESE_FONT else 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False


class Reporter:
    def __init__(self, template_path, output_dir='reports'):
        self.template_path = template_path
        self.output_dir = output_dir
        template_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
        )
        self.template = self.env.get_template(template_file)

    def generate_report(self, analyzed_data):
        """使用Jinja2模板生成HTML日报"""
        try:
            metals = analyzed_data.get('metals', [])
            market_trends = analyzed_data.get('market_trends', {})
            summary = analyzed_data.get('summary', '')
            fetch_time = analyzed_data.get('fetch_time', '')
            fetch_date = analyzed_data.get('fetch_date', '')

            # Separate metals and oil
            precious_metals = [m for m in metals if m.get('category') not in ('能源',)]
            oil = [m for m in metals if m.get('category') == '能源']

            # Generate charts
            price_chart = self._generate_price_chart(metals)
            trend_chart_5d = self._generate_trend_chart(metals, days=5, title='近5日价格走势')
            trend_chart_1m = self._generate_trend_chart(metals, days=22, title='近1月价格走势')

            html_content = self.template.render(
                metals=metals,
                precious_metals=precious_metals,
                oil=oil,
                market_trends=market_trends,
                summary=summary,
                fetch_time=fetch_time,
                fetch_date=fetch_date,
                price_chart=price_chart,
                trend_chart_5d=trend_chart_5d,
                trend_chart_1m=trend_chart_1m,
                categories=CATEGORIES,
                all_products=INVESTMENT_ITEMS,
                category_icons=CATEGORY_ICONS,
                default_selected=DEFAULT_SELECTED,
            )
            return html_content
        except Exception as e:
            logger.error(f"生成日报失败: {e}")
            return None

    def _fig_to_base64(self, fig):
        """将matplotlib图形转为base64字符串"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=120, bbox_inches='tight',
                    facecolor='#1a1a3e', edgecolor='none')
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_b64

    def _generate_price_chart(self, items):
        """生成价格对比柱状图（含原油）"""
        try:
            # Separate metals and oil for coloring
            metals = [m for m in items if m.get('category') not in ('能源',)]
            oil_list = [m for m in items if m.get('category') == '能源']

            names = [m['name'] for m in items]
            prices = [m['price'] for m in items]
            changes = [m['change_pct'] for m in items]

            # Assign colors: gold→FFD700, silver→C0C0C0, platinum→E5E4E2, palladium→A8A8A8, oil→#4ECDC4
            color_map = {'黄金': '#FFD700', '白银': '#C0C0C0', '铂金': '#E5E4E2',
                        '钯金': '#A8A8A8', '原油': '#4ECDC4'}
            bar_colors = [color_map.get(n, '#888') for n in names]
            change_colors = ['#51cf66' if c >= 0 else '#ff6b6b' for c in changes]

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5),
                                           gridspec_kw={'width_ratios': [1, 1]})
            fig.patch.set_facecolor('#1a1a3e')

            # Price bar chart
            bars = ax1.bar(names, prices, color=bar_colors,
                           width=0.5, edgecolor='white', linewidth=0.5)
            unit_label = '价格 (USD)'
            ax1.set_ylabel(unit_label, color='#aaa', fontsize=9)
            ax1.set_title('当前价格对比', color='#FFD700', fontsize=12, fontweight='bold')
            ax1.tick_params(colors='#aaa', labelsize=9)
            ax1.set_facecolor('#24243e')
            for spine in ['bottom', 'left']:
                ax1.spines[spine].set_color('#555')
            for spine in ['top', 'right']:
                ax1.spines[spine].set_visible(False)
            ax1.grid(axis='y', alpha=0.15, color='#888')

            for bar, price in zip(bars, prices):
                off = max(prices) * 0.01
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + off,
                        f'${price:,.2f}', ha='center', va='bottom', color='white', fontsize=8)

            # Change % bar chart
            bars2 = ax2.bar(names, changes, color=change_colors, width=0.5,
                           edgecolor='white', linewidth=0.5)
            ax2.set_ylabel('涨跌幅 (%)', color='#aaa', fontsize=9)
            ax2.set_title('涨跌幅对比', color='#FFD700', fontsize=12, fontweight='bold')
            ax2.tick_params(colors='#aaa', labelsize=9)
            ax2.set_facecolor('#24243e')
            for spine in ['bottom', 'left']:
                ax2.spines[spine].set_color('#555')
            for spine in ['top', 'right']:
                ax2.spines[spine].set_visible(False)
            ax2.grid(axis='y', alpha=0.15, color='#888')
            ax2.axhline(y=0, color='#555', linewidth=0.8)

            max_abs = max(abs(c) for c in changes) if changes else 1
            for bar, chg in zip(bars2, changes):
                y_pos = bar.get_height() + max_abs * 0.05 * (1 if chg >= 0 else -1)
                ax2.text(bar.get_x() + bar.get_width()/2, y_pos,
                        f'{chg:+.2f}%', ha='center',
                        va='bottom' if chg >= 0 else 'top',
                        color='white', fontsize=8)

            plt.tight_layout(pad=2)
            return self._fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"生成价格图表失败: {e}")
            return None

    def _generate_trend_chart(self, items, days=5, title='近5日价格走势'):
        """生成价格趋势折线图"""
        try:
            hist_key = 'history_5d' if days <= 5 else 'history_1y'

            fig, ax = plt.subplots(figsize=(10, 4.5))
            fig.patch.set_facecolor('#1a1a3e')

            colors_map = {'黄金': '#FFD700', '白银': '#C0C0C0',
                         '铂金': '#E5E4E2', '钯金': '#A8A8A8',
                         '原油': '#4ECDC4'}
            markers_map = {'黄金': 'o', '白银': 's', '铂金': '^',
                          '钯金': 'D', '原油': 'v'}

            for item in items:
                hist = item.get(hist_key)
                if hist is None or len(hist) < 2:
                    continue
                # Slice to the right number of days when using full history
                if days > 5 and len(hist) > days:
                    hist = hist.tail(days)

                closes = hist['Close'].values
                color = colors_map.get(item['name'], '#888')
                marker = markers_map.get(item['name'], 'o')
                ax.plot(range(len(closes)), closes, color=color,
                       marker=marker, linewidth=2, markersize=5,
                       label=item['name'], markerfacecolor=color,
                       markeredgecolor='white', markeredgewidth=0.5)

            ax.set_ylabel('价格 (USD)', color='#aaa', fontsize=10)
            ax.set_title(title, color='#FFD700', fontsize=13, fontweight='bold')
            ax.tick_params(colors='#aaa', labelsize=9)
            ax.set_facecolor('#24243e')
            for spine in ['bottom', 'left']:
                ax.spines[spine].set_color('#555')
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)
            ax.grid(alpha=0.15, color='#888')

            # X-tick labels (apply same tail slice as data)
            if items and len(items) > 0:
                sample = items[0].get(hist_key)
                if sample is not None:
                    if days > 5 and len(sample) > days:
                        sample = sample.tail(days)
                    dates = sample.index.strftime('%m/%d')
                    ax.set_xticks(range(len(dates)))
                    ax.set_xticklabels(dates, rotation=45 if days > 5 else 0, fontsize=8)

            # Legend
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, facecolor='#2a2a4e', edgecolor='#555',
                         labelcolor='white', fontsize=9, loc='upper left')

            plt.tight_layout(pad=2)
            return self._fig_to_base64(fig)
        except Exception as e:
            logger.warning(f"生成趋势图表 {title} 失败: {e}")
            return None