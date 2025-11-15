# 相对强弱指数（RSI）

## 定义

Relative Strength Index（RSI）是一种广泛使用的动量振荡指标，用于衡量价格变动的速度（速度）与变化幅度（大小）。当 RSI 以图形方式呈现时，能够直观地同时观察某个市场当前与历史的强弱。该强弱基于指定交易周期内的收盘价，从而产生一个可靠的价格与动量变化度量。由于现金结算工具（股指）与杠杆类金融产品（整个衍生品领域）愈发流行，RSI 被证明是衡量价格走势的有效指标。

## 历史

J. Welles Wilder Jr. 是 RSI 的发明者。他曾是一名海军机械师，之后在职业生涯中转向机械工程。经历数年商品交易后，Wilder 专注于技术分析研究。1978 年，他出版了《New Concepts in Technical Trading Systems》，在这本著作中首次发布了新的动量振荡指标——Relative Strength Index，也就是 RSI。

多年来，RSI 始终备受欢迎，被视为全球技术分析师的核心工具之一。一些研究者在 Wilder 的基础上继续深化发展，其中较为知名的例子是 Andrew Cardwell，他使用 RSI 进行趋势确认。

## 计算方法

```text
RSI = 100 – 100 / (1 + RS)
RS = n 日上涨的平均涨幅 / n 日下跌的平均跌幅
```

以下是一个实际示例，展示如何用 Pine Script 的 rsi() 内置函数进行长式写法复现。

```pine
change = change(close)
gain = change >= 0 ? change : 0.0
loss = change < 0 ? (-1) * change : 0.0
avgGain = rma(gain, 14)
avgLoss = rma(loss, 14)
rs = avgGain / avgLoss
rsi = 100 - (100 / (1 + rs))
```

上例中的 `rsi` 与 `rsi(close, 14)` 完全一致。

## 基础概念

如前所述，RSI 是一个动量振荡指标。作为振荡指标，它在固定区间内运行。RSI 的取值范围在 0 到 100 之间。RSI 越接近 0，价格动能越弱；相反，越接近 100，动能越强。

- 14 日期是最常见的设定，但交易者也会使用多种不同周期。

## 关注要点

### 超买和超卖

Wilder 认为，当价格快速上涨、动能显著增强时，相关金融资产或商品最终会被视为超买，可能出现卖出机会。同理，当价格迅速下跌、动能显著减弱时，该资产会被视为超卖，可能出现买入机会。

Wilder 提出的 RSI 数值区间如下：当 RSI 高于 70 时视为超买，低于 30 时视为超卖。

RSI 介于 30 与 70 之间通常被视为中性区间，接近 50 则表示“无趋势”。

部分交易者认为 Wilder 的区间过宽，会自行调整。例如，有人把高于 80 定义为超买，低于 20 定义为超卖，这完全取决于交易者个人偏好。

## 背离

当价格行为与 RSI 所显示的趋势出现偏差时，就会产生 RSI 背离。背离常被解读为潜在的反转信号，分为看跌与看涨两类。

- **看涨 RSI 背离**：价格创出新低，但 RSI 却形成更高的低点。
- **看跌 RSI 背离**：价格创出新高，但 RSI 却形成更低的高点。

Wilder 认为，看跌背离意味着卖出机会，而看涨背离意味着买入机会。

## 失败摆动

失败摆动是 Wilder 认为能够提高反转概率的另一种现象。需要注意的是，失败摆动完全独立于价格，只依赖 RSI。本结构包含四个“步骤”，可分为看涨（买入机会）和看跌（卖出机会）。

### 看涨失败摆动

1. RSI 跌破 30（视为超卖）。
2. RSI 回升并重新站上 30。
3. RSI 回落但保持在 30 之上（仍然高于超卖区）。
4. RSI 突破前高。

### 看跌失败摆动

1. RSI 升破 70（视为超买）。
2. RSI 回落并跌回 70 以下。
3. RSI 小幅回升但仍低于 70（仍位于超买区下方）。
4. RSI 跌破前低。

[![RSI 失败摆动示意图](https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43082660571/original/WKS_3gphxBKhB9W-S4ETRfWhfdG43ntOsw.png?1572957289)](https://www.tradingview.com/wiki/File:Failureswingnoted.jpg)

## Cardwell 的趋势确认

单一指标并非灵丹妙药，大多数情况下仍需结合背景解读。前文提到的 Andrew Cardwell 就是在 Wilder 的 RSI 诠释基础上继续拓展的研究者之一。他的研究让 RSI 不仅可用于预判反转，也能用于确认趋势。

### 上升趋势与下降趋势

Cardwell 在研究 Wilder 的背离观点时做出以下观察：

- 看涨背离只会出现在下降趋势中。
- 看跌背离只会出现在上升趋势中。
- 无论看涨还是看跌背离，通常只会带来短暂的价格修正，而非真正的趋势反转。

换言之，背离更适合作为趋势确认工具，而非纯粹的反转信号。

### 反转

Cardwell 还提出了正向与负向反转，它们与背离恰好相反。

- **正向反转**：价格走出更高的低点，但 RSI 创出更低的低点，随后价格上行。正向反转只会出现在上升趋势中。
- **负向反转**：价格形成更低的高点，但 RSI 创出更高的高点，随后价格下行。负向反转只会出现在下降趋势中。

正向与负向反转可以概括为价格表现优于动量。由于它们只发生在指定的趋势内，因此同样可用于趋势确认。

## 总结

四十多年来，Relative Strength Index（RSI）一直是严肃技术分析师的核心工具之一。Wilder 对动量的研究为后续图表分析师与研究者深入探索 RSI 模型与价格关联奠定了基础。RSI 属于交易者武器库中最出色的指标之一。仅凭一个 RSI 数值就判定市场方向，是新手才会犯的错误。Wilder 认为，看涨背离意味着市场即将上行；而 Cardwell 认为，这更可能是下降趋势中的短暂修正。与所有指标一样，交易者在依赖 RSI 做出决策之前，应投入时间研究与实测。当 RSI 被正确置于背景中，它就能成为衡量价格、速度与市场深度的核心指标。

## 输入参数

![RSI 设置面板](https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/43558022607/original/FGXKgHoKpvAlGve6fYHX2BRLRLsNSUYdHQ.png?1747310574)

### RSI 长度

计算 RSI 时使用的柱数，默认为 14。

### 数据源

决定计算中使用的柱数据。默认使用收盘价。

### 计算背离

勾选后，指标会额外高亮 RSI 方向与价格方向出现背离的区段，并标注其为看涨或看跌信号。

基于背离条件设置的提醒只有在启用该选项时才会触发。

### 平滑设置

可在 TradingView 帮助中心的“平滑”章节了解更多输入参数：[https://www.tradingview.com/support/solutions/43000742042/](https://www.tradingview.com/support/solutions/43000742042/)

### 计算设置

可在“计算”章节了解更多输入参数：[https://www.tradingview.com/support/solutions/43000591555/](https://www.tradingview.com/support/solutions/43000591555/)

## 延伸阅读

- [如何在 TradingView 上进行交易](https://www.tradingview.com/support/solutions/43000756695-how-to-trade-on-tradingview/)
- [模拟交易主要功能](https://www.tradingview.com/support/solutions/43000516466-paper-trading-main-functionality/)
- [技术分析基础](https://www.tradingview.com/support/solutions/43000759577-the-technical-analysis-essentials-with-tradingview/)
- [基本面分析简介](https://www.tradingview.com/support/solutions/43000759574-introduction-to-fundamental-analysis-on-tradingview/)
- [组合：跟踪资产，掌握交易](https://www.tradingview.com/support/solutions/43000760937-tradingview-portfolios-track-your-assets-know-your-trades/)
