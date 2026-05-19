# 📊 每日贵金属投资日报 (Daily Precious Metals Investment Report)

## 项目简介
自动获取全球贵金属实时行情数据，进行技术面分析，生成精美的 HTML 投资日报。

覆盖的贵金属品种:
- 🥇 **黄金** (Gold) — GOLD
- 🥈 **白银** (Silver) — SILVER
- 🔷 **铂金** (Platinum) — PLATINUM
- 🔶 **钯金** (Palladium) — PALLADIUM

## 功能特性
- ✅ **实时行情获取** — 自动从多个免费数据源获取贵金属价格
- ✅ **技术指标分析** — RSI、移动平均线(MA5/MA20)、支撑/阻力位、趋势判断
- ✅ **市场情绪评估** — 综合涨跌比、平均涨跌幅判断市场情绪
- ✅ **精美可视化图表** — 价格对比柱状图 + 近5日趋势折线图 (matplotlib)
- ✅ **HTML 日报输出** — 深色主题、响应式设计、适合打印的现代日报模板
- ✅ **投资建议** — 基于技术面的自动化投资建议

## 项目结构
```
precious-metals-report
├── src/
│   ├── main.py          # 程序入口 - 协调数据获取、分析、报告生成
│   ├── fetcher.py       # 数据获取器 - 多源获取贵金属实时行情
│   ├── analyzer.py      # 分析器 - 技术指标计算、市场情绪分析
│   └── reporter.py      # 报告生成器 - Jinja2模板渲染 + 图表生成
├── config/
│   └── settings.yaml    # 配置文件
├── templates/
│   └── report.html      # HTML日报模板 (支持Jinja2)
├── reports/             # 生成的日报输出目录
├── requirements.txt     # 项目依赖
└── README.md
```

## 安装指南

### 1. 安装 Python 3.10+
确保已安装 Python，然后安装依赖:
```bash
pip install -r requirements.txt
```

### 2. 配置
编辑 `config/settings.yaml` 进行配置:
```yaml
data_source: "yfinance"         # 数据源
report_template: "templates/report.html"  # 模板路径
output_dir: "reports"           # 输出目录
log_level: "INFO"               # 日志级别
```

## 使用方式
```bash
python src/main.py
```
程序将自动：
1. 获取黄金、白银、铂金、钯金的实时价格
2. 计算技术指标 (RSI、均线、支撑阻力位)
3. 生成带图表的精美 HTML 日报
4. 保存至 `reports/` 目录

### 定时运行 (Windows 任务计划程序)
可设置每日自动运行:
```bash
schtasks /create /tn "PreciousMetalsReport" /tr "python D:\AI WORK\precious-metals-report\src\main.py" /sc daily /st 09:00
```

## 日报预览
生成的日报包含以下模块:
| 模块 | 内容 |
|------|------|
| 📊 市场情绪 | 整体看涨/看跌/震荡判断 |
| 💰 实时行情表 | 最新价、开盘价、最高/最低价、涨跌幅 |
| 📈 价格图表 | 价格对比柱状图 + 5日趋势图 |
| 🔧 技术分析 | RSI、MA5/MA20、支撑/阻力位、趋势 |
| 📝 投资建议 | 基于技术面的自动化建议 |

## 技术栈
- **Python 3.10+** — 核心开发语言
- **yfinance / requests** — 数据获取
- **pandas / numpy** — 数据处理与分析
- **matplotlib** — 图表生成
- **Jinja2** — HTML模板引擎

## 贡献
欢迎提交 Issue 或 Pull Request！

## 许可
MIT License