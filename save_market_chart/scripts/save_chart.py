import os
import sys
import argparse
import matplotlib

# 使用无界面的 Agg backend，防止弹出无用的窗口，同时提升后台出图稳定性
matplotlib.use('Agg')
import matplotlib.pyplot as plt

try:
    from market import MarketDashboard
except ImportError:
    print("❌ 无法导入 market 模块，请确保与本脚本位于同一目录。")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='市场全景可视化工具 - 后台保存图片版')
    parser.add_argument('--symbol', '-s', default='BTCUSDT', help='交易对 (默认 BTCUSDT)')
    parser.add_argument('--hours', '-H', type=int, default=48, help='显示最近多少小时 (默认 48)')
    parser.add_argument('--output', '-o', required=True, help='【必填】保存图片的目标路径 (如 chart.png 或 C:/path/to/chart.png)')

    args = parser.parse_args()

    dashboard = MarketDashboard(symbol=args.symbol)

    # 通过猴子补丁 (Monkey Patching) 重写 plt.show 方法以实现拦截：
    # 当 market.py 试图显示图表时，替换为静默保存图片并关闭画布。
    original_show = plt.show

    def custom_show(*cargs, **kwargs):
        # 确保目录存在
        output_dir = os.path.dirname(os.path.abspath(args.output))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # 保存图片
        plt.savefig(args.output, dpi=300, bbox_inches='tight')
        print(f"✅ 图表已成功保存至: {os.path.abspath(args.output)}")
        plt.close('all')

    plt.show = custom_show

    if dashboard.connect():
        try:
            print(f"正在为 {args.symbol} 获取过去 {args.hours} 小时的数据并生成图表...")
            dashboard.plot(hours=args.hours)
        finally:
            dashboard.close()
            plt.show = original_show
    else:
        print("❌ 无法连接数据库，终端程序已退出。")
        sys.exit(1)


if __name__ == "__main__":
    main()
