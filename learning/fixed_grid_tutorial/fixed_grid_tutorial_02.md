# 第 2 章：策略原理详解

## 本章导航

- [返回索引](fixed_grid_tutorial_index.md)
- [上一章：概述与简介](fixed_grid_tutorial_01.md)
- [下一章：参数配置完全指南](fixed_grid_tutorial_03.md)

## 2.1 网格交易核心概念

### 2.1.1 价格网格

价格网格是策略的基础，它将交易价格区间划分为多个等距或非等距的层级。

**基本构成**：

- **网格上限**（`grid_price_ceiling`）：价格区间的最高点
- **网格下限**（`grid_price_floor`）：价格区间的最低点
- **网格层级数**（`n_levels`）：将区间划分为多少层
- **网格间距**：相邻两层之间的价格差

**示例**：

```text
网格上限：0.33 USDT  ←─── 第 8 层（最高层）
              │
            0.32571     ←─── 第 7 层
              │
            0.32143     ←─── 第 6 层
              │
            0.31714     ←─── 第 5 层
              │
当前价格 →  0.31286     ←─── 第 4 层（当前所在层级）
              │
            0.30857     ←─── 第 3 层
              │
            0.30429     ←─── 第 2 层
              │
网格下限：0.30 USDT   ←─── 第 1 层（最低层）

计算说明：
  网格间距 = (0.33 - 0.30) / (8 - 1) ≈ 0.00429 USDT
  第 i 层价格 = 0.30 + 0.00429 × (i - 1)
```

### 2.1.2 网格级别（Level）

**级别定义**：当前市场价格所处的网格层级位置。

- 级别从 1 开始编号（对应网格下限）
- 最高级别为 `n_levels`（对应网格上限）
- 级别决定了在哪些层级放置买单和卖单

**规则**：

- 在当前级别**之下**放置买单
- 在当前级别**之上**放置卖单
- 当前级别本身不放置订单

### 2.1.3 订单分布

对于 8 层网格，假设当前在第 4 层：

```text
第 8 层：卖单（数量 A8）
第 7 层：卖单（数量 A7）
第 6 层：卖单（数量 A6）
第 5 层：卖单（数量 A5）
第 4 层：当前位置（无订单）← 当前级别
第 3 层：买单（数量 A3）
第 2 层：买单（数量 A2）
第 1 层：买单（数量 A1）
```

## 2.2 价格网格构建算法

Fixed Grid 策略支持两种网格构建方式：等距网格和缩放网格。

### 2.2.1 等距网格（默认）

当 `spread_scale_factor = 1.0` 时，网格间距相等。

**计算公式**：

```text
网格间距 = (上限 - 下限) / (层级数 - 1)
第 i 层价格 = 下限 + 网格间距 × (i - 1)
```

**代码实现**（对应源码第 50-61 行）：

```python
# 计算最小间距
minimum_spread = (grid_price_ceiling - grid_price_floor) / (n_levels - 1)

# 构建价格层级
price_levels = []
for i in range(n_levels):
    price = grid_price_floor + minimum_spread * i
    price_levels.append(price)
```

**示例**（8 层网格，区间 0.30-0.33）：

```text
间距 = (0.33 - 0.30) / (8 - 1) = 0.00429

第 1 层：0.30000
第 2 层：0.30429
第 3 层：0.30857
第 4 层：0.31286
第 5 层：0.31714
第 6 层：0.32143
第 7 层：0.32571
第 8 层：0.33000
```

### 2.2.2 缩放网格（高级）

当 `spread_scale_factor ≠ 1.0` 时，网格间距按比例缩放。

**设计思想**：

- 靠近中间价格的网格间距更小（交易频繁）
- 远离中间价格的网格间距更大（极端价格交易少）

**数学原理**：

使用等比数列构建网格间距，缩放因子为 `spread_scale_factor`。

```text
设中间层为 m = n_levels / 2

下半部分（第 1 层到第 m 层）：
  间距从大到小递减

上半部分（第 m+1 层到第 n_levels 层）：
  间距从小到大递增
```

**核心代码**（对应源码第 50-61 行）：

```50:61:scripts/community/fixed_grid.py
self.minimum_spread = (self.grid_price_ceiling - self.grid_price_floor) / (1 + 2 * sum([pow(self.spread_scale_factor, n) for n in range(1, int(self.n_levels / 2))]))
self.price_levels.append(self.grid_price_floor)
for i in range(2, int(self.n_levels / 2) + 1):
    price = self.grid_price_floor + self.minimum_spread * sum([pow(self.spread_scale_factor, int(self.n_levels / 2) - n) for n in range(1, i)])
    self.price_levels.append(price)
for i in range(1, int(self.n_levels / 2) + 1):
    self.order_amount_levels.append(self.order_amount * pow(self.amount_scale_factor, int(self.n_levels / 2) - i))

for i in range(int(self.n_levels / 2) + 1, self.n_levels + 1):
    price = self.price_levels[int(self.n_levels / 2) - 1] + self.minimum_spread * sum([pow(self.spread_scale_factor, n) for n in range(0, i - int(self.n_levels / 2))])
    self.price_levels.append(price)
    self.order_amount_levels.append(self.order_amount * pow(self.amount_scale_factor, i - int(self.n_levels / 2) - 1))
```

**示例**（`spread_scale_factor = 1.2`）：

```text
第 1 层：0.30000
第 2 层：0.30350  ← 间距较大
第 3 层：0.30620  ← 间距中等
第 4 层：0.30850  ← 间距较小
第 5 层：0.31150  ← 间距较小（中心）
第 6 层：0.31480  ← 间距中等
第 7 层：0.31930  ← 间距较大
第 8 层：0.33000
```

### 2.2.3 网格间距选择建议

| 波动性 | 建议网格层数 | 建议间距 | 缩放因子 |
|--------|-------------|---------|---------|
| 低（1%-3%） | 6-10 层 | 0.3%-0.5% | 1.0 |
| 中（3%-6%） | 8-15 层 | 0.5%-1.0% | 1.0-1.2 |
| 高（6%+） | 12-20 层 | 1.0%-2.0% | 1.2-1.5 |

## 2.3 订单数量计算

### 2.3.1 等额订单（默认）

当 `amount_scale_factor = 1.0` 时，每层订单数量相同。

```python
for i in range(n_levels):
    order_amount_levels[i] = order_amount
```

**优点**：

- 简单直观
- 资金分配均匀
- 适合大多数场景

### 2.3.2 缩放订单（高级）

当 `amount_scale_factor ≠ 1.0` 时，订单数量按比例缩放。

**设计思想**：

- 靠近中间价格：订单数量小（成交频繁，降低单次风险）
- 远离中间价格：订单数量大（成交概率低，提高单次收益）

**计算逻辑**（对应源码第 56、61 行）：

```python
# 下半部分（从中间向下，数量递增）
for i in range(1, m + 1):
    amount = order_amount * pow(amount_scale_factor, m - i)
    order_amount_levels.append(amount)

# 上半部分（从中间向上，数量递增）
for i in range(m + 1, n_levels + 1):
    amount = order_amount * pow(amount_scale_factor, i - m - 1)
    order_amount_levels.append(amount)
```

**示例**（`amount_scale_factor = 1.3`，`order_amount = 10`）：

```text
第 1 层：10 × 1.3³ = 21.97  ← 远离中心，数量大
第 2 层：10 × 1.3² = 16.90
第 3 层：10 × 1.3¹ = 13.00
第 4 层：10 × 1.3⁰ = 10.00  ← 中心，数量基准
第 5 层：10 × 1.3⁰ = 10.00
第 6 层：10 × 1.3¹ = 13.00
第 7 层：10 × 1.3² = 16.90
第 8 层：10 × 1.3³ = 21.97  ← 远离中心，数量大
```

## 2.4 库存平衡原理

### 2.4.1 理想库存模型

在每个网格级别，策略需要特定的基础资产和报价资产配比。

**计算逻辑**（对应源码第 63-67 行）：

```63:67:scripts/community/fixed_grid.py
for i in range(1, self.n_levels + 1):
    self.base_inv_levels.append(sum(self.order_amount_levels[i:self.n_levels]))
    self.quote_inv_levels.append(sum([self.price_levels[n] * self.order_amount_levels[n] for n in range(0, i - 1)]))
for i in range(self.n_levels):
    self.quote_inv_levels_current_price.append(self.quote_inv_levels[i] / self.price_levels[i])
```

**含义解释**：

1. **base_inv_levels[i]**：在第 i 层时，需要的基础资产数量
   - 等于第 i+1 层到最高层的所有卖单数量之和
   - 因为这些卖单都需要持有基础资产

2. **quote_inv_levels[i]**：在第 i 层时，需要的报价资产数量
   - 等于第 1 层到第 i-1 层的所有买单价值之和
   - 因为这些买单都需要报价资产

**示例**（8 层网格，每层 10 ENJ）：

```text
在第 4 层时：
  需要 ENJ：第 5-8 层卖单总和 = 10+10+10+10 = 40 ENJ
  需要 USDT：第 1-3 层买单价值 = 价格1×10 + 价格2×10 + 价格3×10
```

### 2.4.2 库存检查与再平衡

**检查时机**：每个交易周期开始时（`on_tick` 方法）

**检查逻辑**（对应源码第 96-130 行）：

```python 96:130:scripts/community/fixed_grid.py
base_balance = float(market.get_balance(base_asset))
quote_balance = float(market.get_balance(quote_asset) / self.price_levels[self.current_level])

if base_balance < self.base_inv_levels[self.current_level]:
    self.inv_correct = False
    msg = (f"WARNING: Insufficient {base_asset} balance for grid bot. Will attempt to rebalance")
    self.log_with_clock(logging.WARNING, msg)
    self.notify_hb_app_with_timestamp(msg)
    if base_balance + quote_balance < self.base_inv_levels[self.current_level] + self.quote_inv_levels_current_price[self.current_level]:
        msg = (f"WARNING: Insufficient {base_asset} and {quote_asset} balance for grid bot. Unable to rebalance."
               f"Please add funds or change grid parameters")
        self.log_with_clock(logging.WARNING, msg)
        self.notify_hb_app_with_timestamp(msg)
        return
    else:
        # Calculate additional base required with 5% tolerance
        base_required = (Decimal(self.base_inv_levels[self.current_level]) - Decimal(base_balance)) * Decimal(1.05)
        self.rebalance_order_buy = True
        self.rebalance_order_amount = Decimal(base_required)
elif quote_balance < self.quote_inv_levels_current_price[self.current_level]:
    self.inv_correct = False
    msg = (f"WARNING: Insufficient {quote_asset} balance for grid bot. Will attempt to rebalance")
    self.log_with_clock(logging.WARNING, msg)
    self.notify_hb_app_with_timestamp(msg)
    if base_balance + quote_balance < self.base_inv_levels[self.current_level] + self.quote_inv_levels_current_price[self.current_level]:
        msg = (f"WARNING: Insufficient {base_asset} and {quote_asset} balance for grid bot. Unable to rebalance."
               f"Please add funds or change grid parameters")
        self.log_with_clock(logging.WARNING, msg)
        self.notify_hb_app_with_timestamp(msg)
        return
    else:
        # Calculate additional quote required with 5% tolerance
        quote_required = (Decimal(self.quote_inv_levels_current_price[self.current_level]) - Decimal(quote_balance)) * Decimal(1.05)
        self.rebalance_order_buy = False
        self.rebalance_order_amount = Decimal(quote_required)
```

**再平衡策略**：

1. 检测到资产不足
2. 计算需要补充的数量（加 5% 容差）
3. 放置再平衡订单（买入或卖出）
4. 等待订单成交后恢复正常网格运行

## 2.5 订单执行逻辑

### 2.5.1 初始订单创建

**触发条件**：策略启动或再平衡完成后

**创建逻辑**（对应源码第 145-166 行）：

```145:166:scripts/community/fixed_grid.py
def create_grid_proposal(self) -> List[OrderCandidate]:
    buys = []
    sells = []

    # Proposal will be created according to grid price levels
    for i in range(self.current_level):
        price = self.price_levels[i]
        size = self.order_amount_levels[i]
        if size > 0:
            buy_order = OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                       order_side=TradeType.BUY, amount=size, price=price)
            buys.append(buy_order)

    for i in range(self.current_level + 1, self.n_levels):
        price = self.price_levels[i]
        size = self.order_amount_levels[i]
        if size > 0:
            sell_order = OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                        order_side=TradeType.SELL, amount=size, price=price)
            sells.append(sell_order)

    return buys + sells
```

**要点**：

- 在当前级别以下创建所有买单
- 在当前级别以上创建所有卖单
- 所有订单都是限价单（Limit Order）

### 2.5.2 买单成交处理

**触发**：当价格下跌触及某一买单

**处理逻辑**（对应源码第 213-226 行）：

```213:226:scripts/community/fixed_grid.py
def did_complete_buy_order(self, event: BuyOrderCompletedEvent):
    if self.inv_correct is False:
        self.create_timestamp = self.current_timestamp + float(1.0)

    if self.inv_correct is True:
        # Set the new level
        self.current_level -= 1
        # Add sell order above current level
        price = self.price_levels[self.current_level + 1]
        size = self.order_amount_levels[self.current_level + 1]
        proposal = [OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                   order_side=TradeType.SELL, amount=size, price=price)]
        self.execute_orders_proposal(proposal)
```

**步骤**：

1. 买单成交 → 价格下跌
2. 当前级别下降 1 层（`current_level -= 1`）
3. 在新的当前级别上方放置卖单
4. 等待价格反弹触发卖单

**图示**：

```text
成交前：                  成交后：
第 5 层：卖单              第 5 层：卖单
第 4 层：当前位置           第 4 层：卖单（新增）
第 3 层：买单 ← 成交       第 3 层：当前位置（新）
第 2 层：买单              第 2 层：买单
```

### 2.5.3 卖单成交处理

**触发**：当价格上涨触及某一卖单

**处理逻辑**（对应源码第 227-239 行）：

```227:239:scripts/community/fixed_grid.py
def did_complete_sell_order(self, event: SellOrderCompletedEvent):
    if self.inv_correct is False:
        self.create_timestamp = self.current_timestamp + float(1.0)

    if self.inv_correct is True:
        # Set the new level
        self.current_level += 1
        # Add buy order above current level
        price = self.price_levels[self.current_level - 1]
        size = self.order_amount_levels[self.current_level - 1]
        proposal = [OrderCandidate(trading_pair=self.trading_pair, is_maker=True, order_type=OrderType.LIMIT,
                                   order_side=TradeType.BUY, amount=size, price=price)]
        self.execute_orders_proposal(proposal)
```

**步骤**：

1. 卖单成交 → 价格上涨
2. 当前级别上升 1 层（`current_level += 1`）
3. 在新的当前级别下方放置买单
4. 等待价格回落触发买单

## 2.6 盈利模式分析

### 2.6.1 单次交易盈利

**基本原理**：低买高卖

```text
买入价格：P_buy（低层级）
卖出价格：P_sell（高层级）
单次利润：(P_sell - P_buy) × 数量 - 手续费
```

**示例**：

```text
在第 3 层买入：10 ENJ × 0.305 = 3.05 USDT
在第 4 层卖出：10 ENJ × 0.310 = 3.10 USDT
毛利润：3.10 - 3.05 = 0.05 USDT（1.64%）
手续费（0.1%）：0.00305 + 0.00310 = 0.00615 USDT
净利润：0.05 - 0.00615 = 0.04385 USDT（1.44%）
```

### 2.6.2 往返交易盈利

**往返定义**：价格从某层下跌再回升（或上涨再回落）

```text
价格波动：第 4 层 → 第 3 层 → 第 4 层

第 1 步（下跌）：
  - 第 3 层买单成交，买入 10 ENJ
  - 当前级别变为第 3 层
  - 在第 4 层放置卖单

第 2 步（回升）：
  - 第 4 层卖单成交，卖出 10 ENJ
  - 当前级别回到第 4 层
  - 完成一次往返套利
```

### 2.6.3 复利效应

策略不会自动提取利润，盈利会留在账户中继续参与交易，产生复利效应。

**示例**（简化计算）：

```text
初始资金：1000 USDT
每次往返收益率：1.5%
交易频率：每天 1 次往返

第 1 天后：1000 × 1.015 = 1015 USDT
第 30 天后：1000 × 1.015³⁰ ≈ 1566 USDT（+56.6%）
第 60 天后：1000 × 1.015⁶⁰ ≈ 2454 USDT（+145.4%）
```

**注意**：实际情况中交易频率和收益率会波动，以上仅为理论计算。

### 2.6.4 影响盈利的因素

1. **网格间距**
   - 间距大：单次利润高，但交易频率低
   - 间距小：交易频率高，但单次利润低

2. **市场波动性**
   - 波动频繁：往返次数多，盈利机会多
   - 波动稀少：往返次数少，盈利有限

3. **交易手续费**
   - 高手续费：侵蚀利润，甚至可能亏损
   - 低手续费：提高净收益率

4. **价格趋势**
   - 震荡：理想情况，盈利稳定
   - 单边：网格逐渐失效，盈利停滞

## 2.7 本章小结

本章深入讲解了 Fixed Grid 策略的核心原理：

**关键知识点**：

1. **价格网格**：将价格区间划分为多个层级，支持等距和缩放两种方式
2. **订单分布**：当前级别下方放买单，上方放卖单
3. **库存平衡**：每个级别需要特定的资产配比，不足时自动再平衡
4. **执行逻辑**：买单成交后级别下降并补卖单，卖单成交后级别上升并补买单
5. **盈利来源**：通过网格间的价格差和往返交易获利

**核心算法**：

- 网格价格计算支持缩放因子，可实现非均匀分布
- 订单数量计算支持缩放因子，可实现差异化配置
- 库存需求根据当前级别动态计算
- 自动检测并修正库存偏差

掌握这些原理后，您就能理解为什么某些参数配置更适合特定市场，以及如何根据市场变化调整策略。

下一章我们将详细学习 [参数配置完全指南](fixed_grid_tutorial_03.md)，了解每个参数的具体含义和最佳配置方法。

---

[返回索引](fixed_grid_tutorial_index.md) | [上一章：概述与简介](fixed_grid_tutorial_01.md) | [下一章：参数配置完全指南](fixed_grid_tutorial_03.md)
