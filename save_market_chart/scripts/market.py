"""
市场全景可视化工具

从 MySQL 数据库读取资金流向、资金费率、未平仓量数据，使用 matplotlib 绑制双子图。

用法:
    python market_dashboard.py              # 默认显示 BTCUSDT 最近 24 小时，1分钟周期
    python market_dashboard.py --symbol ETHUSDT --hours 48 --interval 5M
"""

import os
import argparse
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
import pymysql
from dotenv import load_dotenv


class MarketDashboard:
    """市场全景可视化器"""

    def __init__(self, symbol: str = 'BTCUSDT', interval: str = '1M'):
        self.symbol = symbol
        self.interval = interval
        self.connection = None
        self._load_config()
        self._setup_chinese_font()

    def _load_config(self):
        """从环境变量加载数据库配置"""
        load_dotenv()
        self.db_config = {
            'host': os.environ.get('MYSQL_HOST', 'localhost'),
            'port': int(os.environ.get('MYSQL_PORT', 3306)),
            'user': os.environ.get('MYSQL_USER', 'root'),
            'password': os.environ.get('MYSQL_PASSWORD', ''),
            'database': os.environ.get('MYSQL_DATABASE', 'stock'),
            'charset': 'utf8mb4'
        }

    def _setup_chinese_font(self):
        """设置中文字体支持"""
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

    def _format_symbol_for_kline(self) -> str:
        """将 BTCUSDT 格式转换为 BTC-USDT 格式"""
        # 去掉 USDT 后缀，重新拼接
        if self.symbol.endswith('USDT'):
            base = self.symbol[:-4]  # BTCUSDT -> BTC
            return f"{base}-USDT"
        return self.symbol

    def _format_symbol_for_perp(self) -> str:
        """将 BTCUSDT 格式转换为 BTC-USDT-PERP 格式"""
        return self._format_symbol_for_kline() + '-PERP'

    def _interval_to_seconds(self) -> int:
        """将 interval 字符串转换为秒数"""
        interval_map = {
            '1M': 60,
            '5M': 300,
            '15M': 900,
            '30M': 1800,
            '60M': 3600,
            '1H': 3600,
            '4H': 14400,
            'DAY': 86400,
            '1D': 86400,
        }
        return interval_map.get(self.interval, 60)

    def fetch_klines_and_flow(self, hours: int = 24) -> tuple:
        """
        从数据库 crypto_kline 表获取 K 线数据和资金流向数据（一次查询）

        返回:
            (kline_df, flow_df) 元组
        """
        if not self.connection:
            raise RuntimeError("请先调用 connect() 建立数据库连接")

        start_time = datetime.now() - timedelta(hours=hours)
        kline_symbol = self._format_symbol_for_kline()

        query = """
            SELECT bar_time as event_time, open, high, low, close, volume,
                   large_buy_vol + small_buy_vol as buy_volume,
                   large_sell_vol + small_sell_vol as sell_volume,
                   large_buy_vol + small_buy_vol - large_sell_vol - small_sell_vol as net_flow
            FROM crypto_kline
            WHERE symbol = %s AND exchange = 'BINANCE' AND kline_type = %s
                  AND bar_time >= %s
            ORDER BY bar_time ASC
        """

        try:
            kline_type = f'K_{self.interval}'
            df = pd.read_sql(
                query, self.connection,
                params=(kline_symbol, kline_type, start_time),
                parse_dates=['event_time']
            )

            # K线数据
            kline_df = df[['event_time', 'open', 'high', 'low', 'close', 'volume']].copy()
            kline_df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            }, inplace=True)

            # 资金流向数据
            flow_df = df[['event_time', 'buy_volume', 'sell_volume', 'net_flow']].copy()

            print(f"✅ K线数据({self.interval}): {len(kline_df)} 条, 资金流向: {len(flow_df)} 条")
            return kline_df, flow_df
        except Exception as e:
            print(f"⚠️ K线/资金流向数据获取失败: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = pymysql.connect(**self.db_config)
            print(f"✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()

    def fetch_data(self, hours: int = 24) -> tuple:
        """
        从数据库读取数据

        返回:
            (kline_df, macro_df, flow_df, liq_df, ratio_df) 元组
        """
        if not self.connection:
            raise RuntimeError("请先调用 connect() 建立数据库连接")

        start_time = datetime.now() - timedelta(hours=hours)
        perp_symbol = self._format_symbol_for_perp()

        # 获取K线数据和资金流向数据（一次查询）
        kline_df, flow_df = self.fetch_klines_and_flow(hours)

        # 查询宏观指标 (使用 PERP symbol)
        query_macro = """
            SELECT event_time, mark_price, open_interest, funding_rate
            FROM macro_indicators
            WHERE symbol = %s AND event_time >= %s
            ORDER BY event_time ASC
        """
        macro_df = pd.read_sql(
            query_macro, self.connection,
            params=(perp_symbol, start_time),
            parse_dates=['event_time']
        )

        # 查询爆仓数据 (使用 PERP symbol)
        query_liq = """
            SELECT event_time, side, price, value_usd
            FROM liquidations
            WHERE symbol = %s AND event_time >= %s
            ORDER BY event_time ASC
        """
        liq_df = pd.read_sql(
            query_liq, self.connection,
            params=(perp_symbol, start_time),
            parse_dates=['event_time']
        )

        # 查询多空比数据 (使用 PERP symbol)
        query_ratio = """
            SELECT event_time, global_account_ratio, top_position_ratio
            FROM long_short_ratio
            WHERE symbol = %s AND event_time >= %s
            ORDER BY event_time ASC
        """
        ratio_df = pd.read_sql(
            query_ratio, self.connection,
            params=(perp_symbol, start_time),
            parse_dates=['event_time']
        )

        print(f"✅ 宏观指标: {len(macro_df)} 条, 爆仓: {len(liq_df)} 条, 多空比: {len(ratio_df)} 条")
        return kline_df, macro_df, flow_df, liq_df, ratio_df

    def plot(self, hours: int = 24):
        """绑制双子图"""
        kline_df, macro_df, flow_df, liq_df, ratio_df = self.fetch_data(hours)

        if kline_df.empty and macro_df.empty and flow_df.empty:
            print("⚠️ 无数据")
            return

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(16, 12),
            sharex=True,  # 共享X轴
            gridspec_kw={'height_ratios': [1, 1]}
        )

        fig.suptitle(f"{self.symbol} Market Dashboard ({self.interval}, last {hours} Hours)", fontsize=16, fontweight='bold')

        # ========== 上图: K线价格、买入/卖出量、累计净流量、爆仓 ==========
        # 绘制K线价格（左Y轴）
        if not kline_df.empty:
            color_close = 'black'

            ax1.plot(kline_df['event_time'], kline_df['Close'],
                     color=color_close, linewidth=2.0, label='Close Price')
            ax1.set_ylabel('Price (USDT)', fontsize=11)

        # 右Y轴1: 买入/卖出量柱状图
        ax1_flow = None
        if not flow_df.empty:
            ax1_flow = ax1.twinx()
            color_buy = '#27AE60'
            color_sell = '#E74C3C'

            # 计算柱宽（根据 interval 参数，系数0.8让柱子更密集）
            bar_width = self._interval_to_seconds() / 86400 * 0.8

            # 阶梯填充图: 买入/卖出 (代替柱状图以解决高密度显示问题)
            ax1_flow.fill_between(flow_df['event_time'], flow_df['buy_volume'], 0,
                                  step='mid', alpha=0.5, color=color_buy, label='Buy Volume')
            ax1_flow.fill_between(flow_df['event_time'], -flow_df['sell_volume'], 0,
                                  step='mid', alpha=0.5, color=color_sell, label='Sell Volume')
            ax1_flow.set_ylabel('Volume (BTC)', fontsize=11)
            ax1_flow.spines['right'].set_position(('outward', 60))

        # 右Y轴2: 累计净流量折线
        ax1_cumsum = None
        if not flow_df.empty:
            ax1_cumsum = ax1.twinx()
            color_cumsum = '#F39C12'  # 橙色

            cumsum_net = flow_df['net_flow'].cumsum()
            ax1_cumsum.plot(flow_df['event_time'], cumsum_net,
                            color=color_cumsum, linewidth=2.0, linestyle='-', label='Cumulative Net Flow')
            ax1_cumsum.set_ylabel('Cumulative Net Flow (BTC)', color=color_cumsum, fontsize=11)
            ax1_cumsum.tick_params(axis='y', labelcolor=color_cumsum)

        # 爆仓散点图
        if not liq_df.empty:
            color_liq_short = '#2ECC71'  # 绿色 - 空头爆仓 (BUY)
            color_liq_long = '#E74C3C'   # 红色 - 多头爆仓 (SELL)

            # 分离空头和多头爆仓
            liq_short = liq_df[liq_df['side'] == 'BUY']   # 空头爆仓
            liq_long = liq_df[liq_df['side'] == 'SELL']   # 多头爆仓

            # 计算散点大小 (基于金额)
            def calc_sizes(values, scale=0.5, min_size=20, max_size=500):
                """根据金额计算散点大小"""
                sizes = np.sqrt(values / 1000) * scale * 100
                return np.clip(sizes, min_size, max_size)

            # 绘制空头爆仓 (绿色)
            if len(liq_short) > 0:
                ax1.scatter(liq_short['event_time'], liq_short['price'],
                            s=calc_sizes(liq_short['value_usd'].values),
                            c=color_liq_short, alpha=0.5, edgecolors='white', linewidths=0.5)

            # 绘制多头爆仓 (红色)
            if len(liq_long) > 0:
                ax1.scatter(liq_long['event_time'], liq_long['price'],
                            s=calc_sizes(liq_long['value_usd'].values),
                            c=color_liq_long, alpha=0.5, edgecolors='white', linewidths=0.5)

        ax1.set_title('Price / Flow / Liquidations', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.3)

        # 上图图例
        legend_elements_top = [
            plt.Line2D([0], [0], color='black', linewidth=2.0, label='Close Price'),
            Patch(facecolor='#27AE60', alpha=0.5, label='Buy Volume'),
            Patch(facecolor='#E74C3C', alpha=0.5, label='Sell Volume'),
            plt.Line2D([0], [0], color='#F39C12', linewidth=2.0, label='Cumulative Net Flow'),
            plt.scatter([], [], c='#2ECC71', s=50, alpha=0.5, label='Short Liq'),
            plt.scatter([], [], c='#E74C3C', s=50, alpha=0.5, label='Long Liq'),
        ]
        ax1.legend(handles=legend_elements_top, loc='upper left', fontsize=9)

        # ========== 下图: 资金费率、未平仓合约量、多空比 ==========
        if not macro_df.empty:
            # 未平仓量（左Y轴）
            color_oi = '#3498DB'
            ax2.plot(macro_df['event_time'], macro_df['open_interest'] / 1e3,
                     color=color_oi, linewidth=2.0, label='Open Interest')
            ax2.set_ylabel('OI (K BTC)', color=color_oi, fontsize=11)
            ax2.tick_params(axis='y', labelcolor=color_oi)

            # 资金费率填充图（右Y轴1）
            ax2_fr = ax2.twinx()
            color_fr_pos = '#E74C3C'  # 红色 - 正费率
            color_fr_neg = '#9B59B6'  # 紫色 - 负费率

            funding_pct = macro_df['funding_rate'] * 100
            
            # 分别填充正负费率以支持不同颜色
            ax2_fr.fill_between(macro_df['event_time'], funding_pct, 0, 
                                where=(funding_pct >= 0), step='mid',
                                alpha=0.6, color=color_fr_pos, label='+Funding Rate')
            ax2_fr.fill_between(macro_df['event_time'], funding_pct, 0, 
                                where=(funding_pct < 0), step='mid',
                                alpha=0.6, color=color_fr_neg, label='-Funding Rate')

            ax2_fr.set_ylabel('Funding Rate (%)', fontsize=11)
            ax2_fr.axhline(y=0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)

            # 设置资金费率 Y 轴范围，确保 0 在中间
            funding_max = max(abs(funding_pct.min()), abs(funding_pct.max())) * 1.2
            ax2_fr.set_ylim(-funding_max, funding_max)

            # 右Y轴2: 多空比折线
            ax2_fr.spines['right'].set_position(('outward', 60))

        # 绘制多空比数据（右Y轴2）
        if not ratio_df.empty:
            ax2_ratio = ax2.twinx()
            color_global = '#E67E22'   # 橙色 - 全球账户多空比
            color_top = '#16A085'      # 青色 - 大户持仓多空比

            ax2_ratio.plot(ratio_df['event_time'], ratio_df['global_account_ratio'],
                           color=color_global, linewidth=1.5, label='Global Account Ratio')
            ax2_ratio.plot(ratio_df['event_time'], ratio_df['top_position_ratio'],
                           color=color_top, linewidth=1.5, label='Top Position Ratio')

            # 1.0参考线（大于1看多，小于1看空）
            ax2_ratio.axhline(y=1.0, color='gray', linestyle='--', linewidth=1.0, alpha=0.7)

            ax2_ratio.set_ylabel('Long/Short Ratio', fontsize=11)

            # 设置多空比 Y 轴范围
            ratio_min = min(ratio_df['global_account_ratio'].min(),
                           ratio_df['top_position_ratio'].min()) * 0.9
            ratio_max = max(ratio_df['global_account_ratio'].max(),
                           ratio_df['top_position_ratio'].max()) * 1.1
            ax2_ratio.set_ylim(ratio_min, ratio_max)

        ax2.set_title('Open Interest / Funding Rate / Long/Short Ratio', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.3)

        # 下图图例
        legend_elements_bottom = [
            plt.Line2D([0], [0], color='#3498DB', linewidth=2.0, label='Open Interest'),
            Patch(facecolor='#E74C3C', alpha=0.6, label='+Funding Rate'),
            Patch(facecolor='#9B59B6', alpha=0.6, label='-Funding Rate'),
            plt.Line2D([0], [0], color='#E67E22', linewidth=1.5, label='Global Account Ratio'),
            plt.Line2D([0], [0], color='#16A085', linewidth=1.5, label='Top Position Ratio'),
        ]
        ax2.legend(handles=legend_elements_bottom, loc='upper left', fontsize=9)

        # 格式化X轴
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.xticks(rotation=45)

        plt.tight_layout()
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='市场全景可视化工具')
    parser.add_argument('--symbol', '-s', default='BTCUSDT', help='交易对')
    parser.add_argument('--hours', '-H', type=int, default=48, help='显示最近多少小时')
    parser.add_argument('--interval', '-i', default='1M',
                        help='K线周期 (如 1M, 5M, 15M, 60M DAY  等)')

    args = parser.parse_args()

    dashboard = MarketDashboard(symbol=args.symbol, interval=args.interval)
    if dashboard.connect():
        try:
            dashboard.plot(hours=args.hours)
        finally:
            dashboard.close()


if __name__ == "__main__":
    main()