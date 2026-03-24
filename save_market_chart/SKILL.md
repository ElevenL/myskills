---
name: save_market_chart
description: 使用选定的交易对和时间范围生成市场全景图，并将其保存到指定的文件路径。
---
# Save Market Chart Skill

这个 Skill 提供了一个快捷脚本，能够复用 `market.py` 中的查库、计算和绘图逻辑，并将最终生成的折线图保存到指定的本地文件，而不是在桌面环境中弹窗显示。

当你需要“将市场全景图保存为图片”时，你可以调用此 Skill 中的脚本。

## 用法

1. 确保你位于项目的根目录（即 `market.py` 所在的目录）。
2. 使用 `python` 执行本 Skill 下的 `scripts/save_chart.py`。
3. 提供 `--symbol`、`--hours` 参数（可选），以及必填的 `--output` 参数。

### 示例命令

```powershell
# 默认保存 BTCUSDT 最近 48 小时的图表到当前目录的 chart.png
python .agents/skills/save_market_chart/scripts/save_chart.py --output chart.png

# 指定交易对和时间，并保存到绝对路径
python .agents/skills/save_market_chart/scripts/save_chart.py --symbol ETHUSDT --hours 48 --output C:/Users/Eleven/Desktop/eth_chart.png
```

### 参数说明

- `--symbol` 或 `-s`: 交易对，默认 `BTCUSDT`。
- `--hours` 或 `-H`: 显示最近的多少小时，默认 `48`。
- `--output` 或 `-o`: **必填**。图片保存的目标路径（相对或绝对路径，如 `result.png`）。
