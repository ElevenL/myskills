#!/usr/bin/env python3
"""
期货日线行情数据获取工具
支持外盘期货和内盘期货历史行情数据获取
"""

import argparse
import json
import sys
from datetime import datetime

try:
    import akshare as ak
except ImportError:
    print(json.dumps({"error": "akshare not installed. Run: pip install akshare"}))
    sys.exit(1)


def get_foreign_futures(symbol: str, limit: int = 50) -> dict:
    """
    获取外盘期货历史行情数据

    Args:
        symbol: 合约代码 (如 S=美豆, C=玉米, W=小麦)
        limit: 返回数据条数，默认50条

    Returns:
        dict: 包含数据或错误信息
    """
    try:
        df = ak.futures_foreign_hist(symbol=symbol)

        # 重命名列
        df = df.rename(columns={'position': 'hold', 's': 'settle'})

        # 确保日期为字符串格式
        df['date'] = df['date'].astype(str)

        # 添加合约代码
        df['symbol'] = symbol

        # 选择输出列
        columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'hold', 'symbol']
        available_cols = [col for col in columns if col in df.columns]
        df = df[available_cols]

        # 按日期倒序排列并限制条数
        df = df.sort_values('date', ascending=False)
        if limit:
            df = df.head(limit)

        records = df.to_dict('records')

        return {
            "success": True,
            "type": "foreign",
            "symbol": symbol,
            "count": len(records),
            "data": records
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }


def get_domestic_futures(symbol: str, limit: int = 50) -> dict:
    """
    获取内盘期货历史行情数据

    Args:
        symbol: 合约代码 (如 M2605=豆粕2025年5月)
        limit: 返回数据条数，默认50条

    Returns:
        dict: 包含数据或错误信息
    """
    try:
        df = ak.futures_zh_daily_sina(symbol=symbol)

        # 确保日期为字符串格式
        if 'date' in df.columns:
            df['date'] = df['date'].astype(str)

        # 重命名持仓量列
        if 'position' in df.columns:
            df = df.rename(columns={'position': 'hold'})

        # 添加合约代码
        df['symbol'] = symbol

        # 选择输出列
        columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'hold', 'symbol']
        available_cols = [col for col in columns if col in df.columns]
        df = df[available_cols]

        # 按日期倒序排列并限制条数
        df = df.sort_values('date', ascending=False)
        if limit:
            df = df.head(limit)

        records = df.to_dict('records')

        return {
            "success": True,
            "type": "domestic",
            "symbol": symbol,
            "count": len(records),
            "data": records
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "symbol": symbol
        }


def main():
    parser = argparse.ArgumentParser(
        description='获取期货日线行情数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 获取美豆最近100条日线数据
  python futures_hist.py --type foreign --symbol S --limit 100

  # 获取豆粕2605合约全部日线数据
  python futures_hist.py --type domestic --symbol M2605

  # 获取美玉米最近50条数据
  python futures_hist.py --type foreign --symbol C --limit 50
        """
    )

    parser.add_argument(
        '--type', '-t',
        choices=['foreign', 'domestic'],
        required=True,
        help='期货类型: foreign(外盘) 或 domestic(内盘)'
    )

    parser.add_argument(
        '--symbol', '-s',
        required=True,
        help='合约代码 (如: S=美豆, M2605=豆粕2605)'
    )

    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=50,
        help='返回数据条数 (默认: 50)'
    )

    parser.add_argument(
        '--output', '-o',
        choices=['json', 'table'],
        default='json',
        help='输出格式: json 或 table (默认: json)'
    )

    args = parser.parse_args()

    # 获取数据
    if args.type == 'foreign':
        result = get_foreign_futures(args.symbol, args.limit)
    else:
        result = get_domestic_futures(args.symbol, args.limit)

    # 输出结果
    if args.output == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get('success'):
            print(f"\n合约: {result['symbol']} ({result['type']})")
            print(f"数据条数: {result['count']}")
            print("-" * 60)
            for record in result['data'][:10]:  # 表格模式只显示前10条
                print(f"{record.get('date', 'N/A'):12} | "
                      f"开:{record.get('open', 'N/A'):8} | "
                      f"高:{record.get('high', 'N/A'):8} | "
                      f"低:{record.get('low', 'N/A'):8} | "
                      f"收:{record.get('close', 'N/A'):8}")
            if result['count'] > 10:
                print(f"... 还有 {result['count'] - 10} 条数据")
        else:
            print(f"错误: {result.get('error', 'Unknown error')}")

    # 返回码
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()