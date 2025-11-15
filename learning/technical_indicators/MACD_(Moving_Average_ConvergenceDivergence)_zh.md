# MACD（Moving Average Convergence Divergence，指数平滑移动平均汇聚背离）

## 定义

[MACD](https://www.tradingview.com/scripts/macd/) 是技术分析中极受欢迎的指标，可用来识别某一资产整体趋势的多个方面。它尤其擅长衡量动能、趋势方向以及持续时间。MACD 之所以信息量大，是因为它结合了两种不同类型的指标。首先，MACD 通过两条不同周期的移动平均线（它们属于滞后指标）来识别趋势方向与持续时间。随后，MACD 计算两条移动平均线之间的差值（MACD 线）以及该差值的指数移动平均线（信号线），并将两线差值绘制为在零轴上下振荡的柱状图。柱状图能够很好地反映某个资产的动能。

## 历史

MACD 的发展可以分成两个阶段。

1. 20 世纪 70 年代，Gerald Appel 创建了 MACD 线。
2. 1986 年，Thomas Aspray 在 [Apple](https://www.tradingview.com/chart/AAPL/) 的 [MACD](https://www.tradingview.com/chart/macd/) 中加入了柱状图功能。

Aspray 的贡献在于帮助交易者提前预判（并因此减少滞后）潜在的 MACD 金叉或死叉，这些交叉是该指标的核心。

## 计算方法

```text
MACD Line: (12-day EMA - 26-day EMA)
Signal Line: 9-day EMA of MACD Line
MACD Histogram: MACD Line - Signal Line
```

## 基础概念

要全面理解 MACD，需要先拆解它由哪些组成部分构成。

### 三个主要组成部分

1. MACD 线  
   MACD 线通过“短周期 EMA 减去长周期 EMA”得到。最常见的参数是 12 日短周期和 26 日长周期，但交易者可以自行调整。
2. 信号线  
   信号线是对第一部分 MACD 线再做一次 EMA 计算的结果。交易者可自行选择信号线的周期，其中 9 日最常见。
3. MACD 柱状图  
   随着时间推移，MACD 线与信号线之间的差值不断变化。柱状图将这一差值可视化，方便阅读，该差值围绕零轴上下振荡。

常见的解释是：当 MACD 为正且柱状图数值扩大，代表上涨动能增强；当 MACD 为负且柱状图数值缩小，代表下跌动能增强。

## 观察要点

MACD 通常用于识别三类基础信号：信号线交叉、零轴交叉以及背离。

### 信号线交叉

信号线交叉是 MACD 最常见的信号。需要先意识到，信号线本质上是“指标的指标”，即对 MACD 线做移动平均，因此信号线滞后于 MACD 线。当 MACD 线穿越信号线时，往往意味着可能出现较强的行情。

行情力度决定了交叉持续时间。识别走势强弱并区分真假信号是一项需要经验的技能。

第一类交叉是看涨信号线交叉，即 MACD 线向上穿越信号线。第二类交叉是看跌信号线交叉，即 MACD 线向下跌破信号线。

### 零轴交叉

零轴交叉与信号线交叉类似，但此处关注的是零轴。当 MACD 线穿越零轴并由负转正时，即为看涨零轴交叉；当 MACD 线穿越零轴由正转负时，即为看跌零轴交叉。

### 背离

背离是 MACD 产生的另一个信号。当 MACD 与价格走势不一致时，就出现了背离。

例如，当价格创新低但 MACD 创出更高的低点时，为看涨背离。价格走势反映当前趋势，但动能变化（由 MACD 体现）有时会领先于显著反转。

看跌背离则相反：价格创新高，但 MACD 创出更低的高点。

## 总结

MACD 之所以有价值，是因为它几乎相当于两个指标合一。它既能识别趋势，又能衡量动能。MACD 将两种滞后指标与更敏捷、更具前瞻性的动能维度结合起来，这种多功能性让它长期深受各类交易者与分析师青睐。

尽管 MACD 优势明显，交易者仍需保持谨慎。MACD 并不擅长处理所有任务，却可能诱使交易者滥用。例如，有人会尝试用 MACD 来寻找超买或超卖，这并不可取。记住，MACD 没有固定上下限，一种资产的“高位”或“低位”水平，未必适用于另一种资产。

只要投入足够的时间和经验，任何希望分析图表数据的人都能熟练运用 MACD。

## 输入参数

![MACD 输入设置面板](https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43582659297/original/5seE1I7MyTBagK6wWN3VXX9hUUfcSGuqzQ.png?1758803823)

### Fast Length

短周期 EMA 的时间窗口，默认 12 日。

### Slow Length

长周期 EMA 的时间窗口，默认 26 日。

### Source

决定每根 K 线中参与计算的数据。默认使用收盘价。

### Signal Smoothing

对 MACD 线做 EMA（即信号线）时的周期长度，默认 9 日。

### Simple Ma (Oscillator)

### Simple Ma (Signal Line)

## 样式

![MACD 样式设置面板](https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43582659386/original/dpOvO3Qzwf1NO7FH4n0Rzbi0SesbhbJv8w.png?1758803842)

### Histogram

可切换柱状图显示与否，并可控制柱状图当前数值的价格线。还可以设置颜色、线宽以及展示类型（默认柱状图）。

### MACD

可切换 MACD 线显示与否，并可显示当前数值的价格线。也可以设置颜色、线宽及展示类型（默认折线）。

### Signal

可切换信号线显示与否，并可显示当前数值的价格线。也可以设置颜色、线宽及展示类型（默认折线）。

### Precision

设置指标输出数值的小数位数。数值越高，保留的小数位越多。
