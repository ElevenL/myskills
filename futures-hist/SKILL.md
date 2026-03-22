---
name: futures-hist
description: |
  获取期货日线行情数据工具。支持外盘和内盘期货历史行情数据获取。
  TRIGGER when: 用户需要获取期货历史行情、期货日线数据、外盘期货数据、内盘期货数据。
  Use when the user asks for futures historical data, futures daily quotes, or mentions futures symbols like "美豆", "豆粕", "S", "M2605", etc.
---

# Futures Historical Data

获取外盘和内盘期货日线行情数据。

## Quick Start

```python
# 获取外盘期货数据 (如美豆)
python scripts/futures_hist.py --type foreign --symbol S --limit 100

# 获取内盘期货数据 (如豆粕2605)
python scripts/futures_hist.py --type domestic --symbol M2605 --limit 100
```

## Parameters

| 参数 | 说明 | 示例 |
|------|------|------|
| `--type` | 期货类型: `foreign`(外盘) 或 `domestic`(内盘) | `foreign`, `domestic` |
| `--symbol` | 合约代码 | `S`(美豆), `M2605`(豆粕2605) |
| `--limit` | 返回数据条数 (可选，默认50条) | `100`, `50` |

## Supported Futures

### 外盘期货 (Foreign)
使用 `ak.futures_foreign_hist()` 获取，常见合约代码：
- `S` - 美豆 (Soybean)
- `C` - 美玉米 (Corn)
- `W` - 美麦 (Wheat)
- `BO` - 豆油 (Soybean Oil)
- `SM` - 豆粕 (Soybean Meal)

### 内盘期货 (Domestic)
使用 `ak.futures_zh_daily_sina()` 获取，合约代码格式为品种代码+交割月：
- `M2605` - 豆粕2025年5月合约
- `A2605` - 豆一2025年5月合约
- `Y2605` - 豆油2025年5月合约
- `C2605` - 玉米2025年5月合约

## Output Format

返回 JSON 格式数据，包含以下字段：

### 外盘期货字段
- `date` - 日期
- `open` - 开盘价
- `high` - 最高价
- `low` - 最低价
- `close` - 收盘价
- `hold` - 持仓量
- `volume` - 成交量
- `symbol` - 合约代码

### 内盘期货字段
- `date` - 日期
- `open` - 开盘价
- `high` - 最高价
- `low` - 最低价
- `close` - 收盘价
- `volume` - 成交量
- `hold` - 持仓量

## Examples

```bash
# 获取美豆最近100条日线数据
python scripts/futures_hist.py --type foreign --symbol S --limit 100

# 获取豆粕2605合约全部日线数据
python scripts/futures_hist.py --type domestic --symbol M2605

# 获取美玉米最近50条数据
python scripts/futures_hist.py --type foreign --symbol C --limit 50
```