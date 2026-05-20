import yaml
import os
import sys
import logging
from timesync import strdate as _ts_strdate
from fetcher import Fetcher
from analyzer import Analyzer
from reporter import Reporter


def setup_logging(level="INFO"):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def load_config(config_path='config/settings.yaml'):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.warning(f"配置文件 {config_path} 未找到，使用默认配置")
        return {}


def main():
    # Setup
    config = load_config()
    setup_logging(config.get('log_level', 'INFO'))
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("📊 每日贵金属投资日报生成器启动")
    logger.info("=" * 50)

    # Initialize components
    fetcher = Fetcher(config)
    analyzer = Analyzer()
    reporter = Reporter(config.get('report_template', 'templates/report.html'))

    # Step 1: Fetch data
    logger.info("🔍 步骤1/3: 正在获取贵金属实时数据...")
    raw_data = fetcher.fetch_data()
    if not raw_data:
        logger.error("❌ 获取数据失败，程序退出")
        sys.exit(1)
    logger.info(f"✅ 数据获取成功! 共获取 {len(raw_data.get('metals', []))} 个品种")

    # Step 2: Analyze data
    logger.info("📈 步骤2/3: 正在进行技术分析...")
    analyzed_data = analyzer.analyze_data(raw_data)
    logger.info("✅ 分析完成!")

    # Step 3: Generate report
    logger.info("📝 步骤3/3: 正在生成HTML日报...")
    html_report = reporter.generate_report(analyzed_data)
    if not html_report:
        logger.error("❌ 生成日报失败")
        sys.exit(1)

    # Save report
    output_dir = config.get('output_dir', 'reports')
    os.makedirs(output_dir, exist_ok=True)
    today = _ts_strdate().replace('-', '')
    output_path = os.path.join(output_dir, f'precious_metals_report_{today}.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_report)

    logger.info(f"✅ 日报已保存至: {output_path}")
    logger.info("=" * 50)
    logger.info("📊 报告完成!")
    logger.info("=" * 50)

    return output_path


if __name__ == '__main__':
    main()