"""
市场全景可视化工具

从 MySQL 数据库读取资金流向、资金费率、未平仓量数据，使用 matplotlib 绑制双子图。

用法:
    python market_dashboard.py              # 默认显示 BTCUSDT 最近 24 小时
    python market_dashboard.py --symbol ETHUSDT --hours 48
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
import requests
from dotenv import load_dotenv


class MarketDashboard:
    """市场全景可视化器"""

    def __init__(self, symbol: str = 'BTCUSDT'):
        self.symbol = symbol
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

    def fetch_klines(self, hours: int = 24) -> pd.DataFrame:
        """
        从币安 API 获取 K 线数据

        返回:
            包含 Open, High, Low, Close 的 DataFrame
        """
        limit = (hours * 60) // 5  # 5分钟K线，计算需要的数量

        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": self.symbol,
            "interval": "5m",
            "limit": min(limit, 1000)  # 币安最大1000条
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            columns = ["Open time", "Open", "High", "Low", "Close", "Volume",
                       "Close time", "Quote asset volume", "Number of trades",
                       "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"]
            df = pd.DataFrame(response.json(), columns=columns)

            df['Open time'] = pd.to_datetime(df['Open time'], unit='ms', utc=True)
            df['Open time'] = df['Open time'].dt.tz_convert('Asia/Shanghai')  # 转换为北京时间
            df['Open time'] = df['Open time'].dt.tz_localize(None)  # 移除时区信息，便于绑图
            df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].apply(pd.to_numeric)
            df.rename(columns={'Open time': 'event_time'}, inplace=True)

            print(f"✅ K线数据: {len(df)} 条")
            return df[['event_time', 'Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            print(f"⚠️ K线数据获取失败: {e}")
            return pd.DataFrame()

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
            (kline_df, macro_df, flow_df, liq_df) 元组
        """
        if not self.connection:
            raise RuntimeError("请先调用 connect() 建立数据库连接")

        start_time = datetime.now() - timedelta(hours=hours)

        # 获取K线数据
        kline_df = self.fetch_klines(hours)

        # 查询宏观指标
        query_macro = """
            SELECT event_time, mark_price, open_interest, funding_rate
            FROM macro_indicators
            WHERE symbol = %s AND event_time >= %s
            ORDER BY event_time ASC
        """
        macro_df = pd.read_sql(
            query_macro, self.connection,
            params=(self.symbol, start_time),
            parse_dates=['event_time']
        )

        # 查询资金流向
        query_flow = """
            SELECT event_time, buy_volume, sell_volume, net_flow
            FROM flow_stats
            WHERE symbol = %s AND event_time >= %s
            ORDER BY event_time ASC
        """
        flow_df = pd.read_sql(
            query_flow, self.connection,
            params=(self.symbol, start_time),
            parse_dates=['event_time']
        )

        # 查询爆仓数据
        query_liq = """
            SELECT event_time, side, price, value_usd
            FROM liquidations
            WHERE symbol = %s AND event_time >= %s
            ORDER BY event_time ASC
        """
        liq_df = pd.read_sql(
            query_liq, self.connection,
            params=(self.symbol, start_time),
            parse_dates=['event_time']
        )

        # 聚合为5分钟粒度
        if not macro_df.empty:
            macro_df.set_index('event_time', inplace=True)
            macro_df = macro_df.resample('5min').agg({
                'mark_price': 'last',
                'open_interest': 'last',
                'funding_rate': 'last'
            }).dropna()
            macro_df.reset_index(inplace=True)

        if not flow_df.empty:
            flow_df.set_index('event_time', inplace=True)
            flow_df = flow_df.resample('5min').agg({
                'buy_volume': 'sum',
                'sell_volume': 'sum',
                'net_flow': 'sum'
            }).dropna()
            flow_df.reset_index(inplace=True)

        print(f"✅ 宏观指标: {len(macro_df)} 条, 资金流向: {len(flow_df)} 条, 爆仓: {len(liq_df)} 条")
        return kline_df, macro_df, flow_df, liq_df

    def plot(self, hours: int = 24):
        """绑制双子图"""
        kline_df, macro_df, flow_df, liq_df = self.fetch_data(hours)

        if kline_df.empty and macro_df.empty and flow_df.empty:
            print("⚠️ 无数据")
            return

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(16, 12),
            sharex=True,  # 共享X轴
            gridspec_kw={'height_ratios': [1, 1]}
        )

        fig.suptitle(f"{self.symbol} Market Dashboard (last {hours} Hours)", fontsize=16, fontweight='bold')

        # ========== 上图: K线、未平仓量、资金费率、爆仓 ==========
        # 绘制K线价格
        if not kline_df.empty:
            color_close = 'black'
            color_high = '#27AE60'   # 绿色
            color_low = '#E74C3C'    # 红色

            ax1.plot(kline_df['event_time'], kline_df['Close'],
                     color=color_close, linewidth=2.0, label='Close Price')
            ax1.plot(kline_df['event_time'], kline_df['High'],
                     color=color_high, linewidth=0.8, alpha=0.6, label='High Price')
            ax1.plot(kline_df['event_time'], kline_df['Low'],
                     color=color_low, linewidth=0.8, alpha=0.6, label='Low Price')
            ax1.set_ylabel('Price (USDT)', fontsize=11)

        # 绘制未平仓量和资金费率
        if not macro_df.empty:

            # 右Y轴1: 未平仓量
            ax1_oi = ax1.twinx()
            color_oi = '#3498DB'
            ax1_oi.plot(macro_df['event_time'], macro_df['open_interest'] / 1e3,
                        color=color_oi, linewidth=1.5, label='OI')
            ax1_oi.set_ylabel('OI (K BTC)', color=color_oi, fontsize=11)
            ax1_oi.tick_params(axis='y', labelcolor=color_oi)
            ax1_oi.spines['right'].set_position(('outward', 60))

            # 右Y轴2: 资金费率柱状图
            ax1_fr = ax1.twinx()
            color_fr_pos = '#E74C3C'  # 红色 - 正费率
            color_fr_neg = '#9B59B6'  # 紫色 - 负费率

            funding_pct = macro_df['funding_rate'] * 100
            colors_fr = [color_fr_pos if x >= 0 else color_fr_neg for x in funding_pct]

            # 计算柱宽
            if len(macro_df) > 1:
                time_diff = (macro_df['event_time'].iloc[1] - macro_df['event_time'].iloc[0]).total_seconds()
                bar_width_fr = time_diff / 86400 * 0.8
            else:
                bar_width_fr = 0.02

            ax1_fr.bar(macro_df['event_time'], funding_pct,
                       width=bar_width_fr, alpha=0.6, color=colors_fr)

            ax1_fr.set_ylabel('Funding Rate (%)', fontsize=11)
            ax1_fr.axhline(y=0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)

            # 设置资金费率 Y 轴范围，确保 0 在中间
            funding_max = max(abs(funding_pct.min()), abs(funding_pct.max())) * 1.2
            ax1_fr.set_ylim(-funding_max, funding_max)

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

            ax1.set_title('K Lines / OI / Funding Rate / liquidations', fontsize=12)
            ax1.grid(True, linestyle='--', alpha=0.3)

            # 图例
            legend_elements = [
                plt.Line2D([0], [0], color='black', linewidth=2.0, label='Close Price'),
                plt.Line2D([0], [0], color='#27AE60', linewidth=0.8, alpha=0.6, label='High Price'),
                plt.Line2D([0], [0], color='#E74C3C', linewidth=0.8, alpha=0.6, label='Low Price'),
                plt.Line2D([0], [0], color=color_oi, linewidth=1.5, label='OI'),
                Patch(facecolor=color_fr_pos, alpha=0.6, label='+Funding Rate'),
                Patch(facecolor=color_fr_neg, alpha=0.6, label='-Funding Rate'),
                plt.scatter([], [], c='#2ECC71', s=50, alpha=0.5, label='Short'),
                plt.scatter([], [], c='#E74C3C', s=50, alpha=0.5, label='Long'),
            ]
            ax1.legend(handles=legend_elements, loc='upper left', fontsize=9)

        # ========== 下图: 资金流向 ==========
        if not flow_df.empty:
            color_buy = '#27AE60'
            color_sell = '#E74C3C'
            color_net = '#9B59B6'
            color_cumsum = '#F39C12'  # 橙色 - 累计净流量

            # 计算柱宽
            if len(flow_df) > 1:
                time_diff = (flow_df['event_time'].iloc[1] - flow_df['event_time'].iloc[0]).total_seconds()
                bar_width = time_diff / 86400 * 0.35
            else:
                bar_width = 0.01

            # 柱状图: 买入/卖出
            ax2.bar(flow_df['event_time'], flow_df['buy_volume'],
                    width=bar_width, alpha=0.6, color=color_buy, label='Buy Volume')
            ax2.bar(flow_df['event_time'], -flow_df['sell_volume'],
                    width=bar_width, alpha=0.6, color=color_sell, label='Sell Volume')

            # 右Y轴: 净流量折线
            ax2_net = ax2.twinx()
            ax2_net.plot(flow_df['event_time'], flow_df['net_flow'],
                         color=color_net, linewidth=1.5, label='Net Flow')
            ax2_net.set_ylabel('Net Flow (BTC)', color=color_net, fontsize=11)
            ax2_net.tick_params(axis='y', labelcolor=color_net)
            ax2_net.axhline(y=0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)

            # 累计净流量虚线
            cumsum_net = flow_df['net_flow'].cumsum()
            ax2_net.plot(flow_df['event_time'], cumsum_net,
                         color=color_cumsum, linewidth=1.5, linestyle='--', label='Total Net Flow')

            y_max = max(flow_df['buy_volume'].max(), flow_df['sell_volume'].max()) * 1.1
            ax2.set_ylim(-y_max, y_max)
            ax2.set_ylabel('Volume (BTC)', fontsize=11)

            ax2.set_title('Flow', fontsize=12)
            ax2.grid(True, linestyle='--', alpha=0.3)
            ax2.axhline(y=0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)

            # 图例
            legend_elements = [
                Patch(facecolor=color_buy, alpha=0.6, label='Buy Volume'),
                Patch(facecolor=color_sell, alpha=0.6, label='Sell Volume'),
                plt.Line2D([0], [0], color=color_net, linewidth=1.5, label='Net Flow'),
                plt.Line2D([0], [0], color=color_cumsum, linewidth=1.5, linestyle='--', label='Total Net Flow'),
            ]
            ax2.legend(handles=legend_elements, loc='upper left', fontsize=9)

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

    args = parser.parse_args()

    dashboard = MarketDashboard(symbol=args.symbol)
    if dashboard.connect():
        try:
            dashboard.plot(hours=args.hours)
        finally:
            dashboard.close()


if __name__ == "__main__":
    main()