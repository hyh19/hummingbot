# 第 3 章：参数配置完全指南

## 本章导航

- [返回索引](grid_strike_tutorial_index.md)
- [上一章：策略原理详解](grid_strike_tutorial_02.md)
- [下一章：快速开始使用指南](grid_strike_tutorial_04.md)

## 3.1 参数总览

GridStrike 策略的配置分为六大类：

| 类别 | 参数数量 | 作用 |
|------|---------|------|
| 账户配置 | 3 | 交易所、交易对、杠杆和仓位模式 |
| 网格边界 | 4 | 定义网格的价格范围和方向 |
| 资金配置 | 3 | 资金分配和订单规模 |
| 执行控制 | 5 | 订单执行策略和时机 |
| 风险管理 | 7+ | 止盈止损和订单类型 |
| 高级选项 | 2 | K 线数据和初始仓位 |

## 3.2 账户配置

### 3.2.1 connector_name（交易所名称）

**类型**：字符串（str）

**说明**：指定要使用的交易所连接器名称。

**可选值**：

- `"binance_perpetual"` - 币安永续合约
- `"bybit_perpetual"` - Bybit 永续合约
- `"okx_perpetual"` - OKX 永续合约
- `"gate_io_perpetual"` - Gate.io 永续合约
- 其他支持的期货交易所

**示例**：

```python
connector_name = "binance_perpetual"
```

**注意事项**：

- 必须先在 Hummingbot 中配置对应交易所的 API
- 不同交易所的交易规则可能不同
- 建议选择流动性好、手续费低的交易所

### 3.2.2 trading_pair（交易对）

**类型**：字符串（str）

**说明**：指定要交易的期货合约交易对。

**格式**：`BASE-QUOTE`（例如：`WLD-USDT`）

**示例**：

```python
trading_pair = "WLD-USDT"
```

**选择建议**：

1. **流动性**：选择交易量大、订单簿深度好的交易对
2. **波动性**：选择波动率适中的品种（3%-10% 日波动）
3. **资金费率**：避免资金费率过高的品种
4. **熟悉度**：优先选择自己了解的项目

**常见交易对**：

- `BTC-USDT`：主流币，流动性最好，波动相对稳定
- `ETH-USDT`：流动性好，波动适中
- `WLD-USDT`：中等流动性，波动较大
- `ARB-USDT`、`OP-USDT`：Layer2 代币，波动适中

### 3.2.3 leverage（杠杆倍数）

**类型**：整数（int）

**默认值**：20

**说明**：期货合约的杠杆倍数。

**取值范围**：1-125（取决于交易所和交易对）

**示例**：

```python
leverage = 20  # 20倍杠杆
```

**影响**：

| 杠杆倍数 | 收益放大 | 风险放大 | 保证金占用 | 强平风险 | 适用人群 |
|---------|---------|---------|-----------|---------|---------|
| 5x | 低 | 低 | 高 | 很低 | 保守型 |
| 10x | 中低 | 中低 | 中高 | 低 | 稳健型 |
| 20x | 中 | 中 | 中 | 中 | 均衡型 |
| 50x | 高 | 高 | 低 | 高 | 激进型 |
| 100x+ | 极高 | 极高 | 极低 | 极高 | 不推荐 |

**计算示例**：

```
订单金额：200 USDT
杠杆倍数：20x
实际持仓价值：200 × 20 = 4000 USDT
所需保证金：4000 / 20 = 200 USDT

如果价格上涨 1%：
收益 = 4000 × 0.01 = 40 USDT
收益率 = 40 / 200 = 20%

如果价格下跌 1%：
亏损 = 4000 × 0.01 = 40 USDT
亏损率 = 40 / 200 = 20%
```

**推荐设置**：

- **新手**：5-10x，先熟悉策略
- **有经验者**：10-20x，平衡收益和风险
- **专业交易者**：20-50x，严格风控

**风险提示**：

- 杠杆越高，强平风险越大
- 建议始终设置止损
- 保持足够的保证金余额

### 3.2.4 position_mode（仓位模式）

**类型**：枚举（PositionMode）

**默认值**：`PositionMode.HEDGE`

**说明**：期货合约的仓位模式。

**可选值**：

1. **HEDGE（双向持仓模式）**
   - 可以同时持有多仓和空仓
   - 适合对冲策略
   - GridStrike 推荐使用

2. **ONEWAY（单向持仓模式）**
   - 只能持有一个方向的仓位
   - 简单直接
   - 部分交易所不支持

**示例**：

```python
from hummingbot.core.data_type.common import PositionMode

position_mode = PositionMode.HEDGE
```

**对比**：

| 特性 | HEDGE 模式 | ONEWAY 模式 |
|-----|-----------|-------------|
| 同时做多做空 | 支持 | 不支持 |
| 仓位管理 | 复杂 | 简单 |
| 对冲能力 | 强 | 无 |
| 交易所支持 | 大部分支持 | 全部支持 |
| GridStrike 兼容性 | 完全兼容 | 兼容 |

**推荐**：使用 `HEDGE` 模式，灵活性更高。

## 3.3 网格边界

### 3.3.1 side（交易方向）

**类型**：枚举（TradeType）

**默认值**：`TradeType.BUY`

**说明**：网格的交易方向（做多或做空）。

**可选值**：

1. **TradeType.BUY（做多网格）**
   - 在低价买入，高价卖出
   - 适合看涨或震荡行情
   - 期待价格上涨

2. **TradeType.SELL（做空网格）**
   - 在高价卖出，低价买回
   - 适合看跌或震荡行情
   - 期待价格下跌

**示例**：

```python
from hummingbot.core.data_type.common import TradeType

side = TradeType.BUY  # 做多网格
```

**做多网格示例**：

```
Side = BUY
价格区间：2.00 - 2.20 USDT

订单分布：
2.20 ← 卖出（平仓）
2.18 ← 卖出（平仓）
2.16 ← 卖出（平仓）
2.14 ← 买入（开仓）
2.12 ← 买入（开仓）
2.10 ← 买入（开仓）
...
2.00 ← 买入（开仓）

逻辑：在下方买入，在上方卖出获利
```

**做空网格示例**：

```
Side = SELL
价格区间：2.00 - 2.20 USDT

订单分布：
2.20 ← 卖出（开仓）
2.18 ← 卖出（开仓）
2.16 ← 卖出（开仓）
2.14 ← 买入（平仓）
2.12 ← 买入（平仓）
2.10 ← 买入（平仓）
...
2.00 ← 买入（平仓）

逻辑：在上方卖出，在下方买回获利
```

### 3.3.2 start_price（起始价格）

**类型**：Decimal

**默认值**：`Decimal("0.58")`

**说明**：网格的起始价格（下边界）。

**可更新**：是（运行时可调整）

**示例**：

```python
start_price = Decimal("2.00")
```

**设置建议**：

1. **基于支撑位**：设置在近期明显的支撑位下方
2. **基于波动范围**：根据历史波动率计算
3. **预留缓冲**：不要设置得太紧，留出波动空间

**计算方法**：

```python
# 方法1：基于当前价格和预期波动
current_price = 2.10
expected_drop = 0.10  # 预期下跌10%
start_price = current_price * (1 - expected_drop)  # 1.89

# 方法2：基于历史支撑位
support_level = 2.00
buffer = 0.02  # 2%缓冲
start_price = support_level * (1 - buffer)  # 1.96

# 方法3：基于波动率
volatility = 0.15  # 15%日波动
start_price = current_price * (1 - volatility / 2)  # 1.94
```

**注意事项**：

- 价格必须大于 0
- 必须小于 `end_price`
- 考虑交易对的最小价格增量

### 3.3.3 end_price（结束价格）

**类型**：Decimal

**默认值**：`Decimal("0.95")`

**说明**：网格的结束价格（上边界）。

**可更新**：是（运行时可调整）

**示例**：

```python
end_price = Decimal("2.20")
```

**设置建议**：

1. **基于阻力位**：设置在近期明显的阻力位上方
2. **基于波动范围**：根据历史波动率计算
3. **预留缓冲**：不要设置得太紧，留出波动空间

**与 start_price 的关系**：

```python
# 网格总宽度
grid_width = end_price - start_price

# 网格宽度百分比
grid_width_pct = (end_price - start_price) / start_price

# 推荐宽度：10%-30%
# 太窄：捕获机会少
# 太宽：资金利用率低
```

**示例设置**：

```python
# 保守型：宽网格（20%）
start_price = Decimal("2.00")
end_price = Decimal("2.40")  # 2.00 * 1.20

# 均衡型：中等网格（15%）
start_price = Decimal("2.00")
end_price = Decimal("2.30")  # 2.00 * 1.15

# 激进型：窄网格（10%）
start_price = Decimal("2.00")
end_price = Decimal("2.20")  # 2.00 * 1.10
```

### 3.3.4 limit_price（限价保护）

**类型**：Decimal

**默认值**：`Decimal("0.55")`

**说明**：开仓订单的限价保护价格，防止在不利价格成交。

**可更新**：是（运行时可调整）

**作用**：

- **做多网格**：开仓买单不会在高于 `limit_price` 的价格成交
- **做空网格**：开仓卖单不会在低于 `limit_price` 的价格成交

**示例**（做多网格）：

```python
start_price = Decimal("2.00")
end_price = Decimal("2.20")
limit_price = Decimal("1.95")  # 保护价格设在 start_price 下方
```

**设置建议**：

```python
# 做多网格：limit_price < start_price
limit_price = start_price * Decimal("0.95")  # 低于起始价5%

# 做空网格：limit_price > end_price
limit_price = end_price * Decimal("1.05")  # 高于结束价5%
```

**实际效果**：

```
场景：做多网格，价格突然大幅下跌

配置：
- start_price = 2.00
- limit_price = 1.95

如果价格跌到 1.90：
- 网格订单不会成交（保护价格 1.95）
- 避免在不利价格买入
- 等待价格回升到 1.95 以上
```

## 3.4 资金配置

### 3.4.1 total_amount_quote（总资金量）

**类型**：Decimal

**默认值**：`Decimal("1000")`

**说明**：分配给单个 GridExecutor 的总资金（以报价资产计价）。

**可更新**：是（运行时可调整）

**示例**：

```python
total_amount_quote = Decimal("1000")  # 1000 USDT
```

**资金分配**：

```python
# 单个网格层级的资金
num_levels = (end_price - start_price) / min_spread_between_orders
amount_per_level = total_amount_quote / num_levels

# 示例
total_amount_quote = 1000 USDT
num_levels = 10
amount_per_level = 1000 / 10 = 100 USDT
```

**考虑杠杆后的实际持仓**：

```python
# 单层级实际持仓价值
position_value = amount_per_level * leverage

# 示例（20x杠杆）
amount_per_level = 100 USDT
leverage = 20
position_value = 100 × 20 = 2000 USDT
```

**设置建议**：

1. **账户总资金的 10%-30%**：不要全仓单策略
2. **考虑保证金需求**：留出缓冲应对波动
3. **考虑网格数量**：确保单层级资金不低于最小订单金额

**风险控制**：

```python
# 最大可能亏损（全部层级触发止损）
max_loss = total_amount_quote * leverage * stop_loss

# 示例
total_amount_quote = 1000 USDT
leverage = 20
stop_loss = 0.01  # 1%
max_loss = 1000 × 20 × 0.01 = 200 USDT

# 确保账户资金能承受最大亏损
account_balance >= total_amount_quote + max_loss
```

### 3.4.2 min_spread_between_orders（最小订单间距）

**类型**：Decimal

**默认值**：`Decimal("0.001")`（0.1%）

**说明**：网格层级之间的最小价格间距（以比例表示）。

**可更新**：是（运行时可调整）

**示例**：

```python
min_spread_between_orders = Decimal("0.005")  # 0.5%
```

**影响**：

```python
# 网格层级数量
num_levels = (end_price - start_price) / (start_price * min_spread_between_orders)

# 示例1：小间距
start_price = 2.00
end_price = 2.20
min_spread = 0.001  # 0.1%
num_levels = (2.20 - 2.00) / (2.00 × 0.001) = 100 层

# 示例2：大间距
min_spread = 0.01  # 1%
num_levels = (2.20 - 2.00) / (2.00 × 0.01) = 10 层
```

**对比分析**：

| 间距大小 | 层级数量 | 单层资金 | 成交频率 | 单次收益 | 手续费占比 | 适用场景 |
|---------|---------|---------|---------|---------|-----------|---------|
| 0.1% | 多 | 小 | 高 | 小 | 高 | 高频波动 |
| 0.5% | 中 | 中 | 中 | 中 | 中 | 均衡 |
| 1.0% | 少 | 大 | 低 | 大 | 低 | 低频波动 |

**设置建议**：

```python
# 基于交易手续费
taker_fee = 0.0005  # 0.05%
maker_fee = 0.0002  # 0.02%
total_fee = taker_fee + maker_fee  # 0.07%

# 最小间距应该 > 手续费的 3-5 倍
min_spread = total_fee * 5 = 0.0007 * 5 = 0.0035  # 0.35%

# 基于波动率
daily_volatility = 0.05  # 5%日波动
min_spread = daily_volatility / 10 = 0.005  # 0.5%

# 基于市场噪音
price = 2.00
tick_size = 0.001  # 交易所最小价格单位
min_spread = tick_size / price * 10 = 0.005  # 0.5%
```

**注意事项**：

- 间距过小：手续费侵蚀利润，订单数量过多
- 间距过大：捕获机会少，资金利用率低
- 需要结合止盈比例设置

### 3.4.3 min_order_amount_quote（最小订单金额）

**类型**：Decimal

**默认值**：`Decimal("5")`

**说明**：单个订单的最小金额（以报价资产计价）。

**可更新**：是（运行时可调整）

**示例**：

```python
min_order_amount_quote = Decimal("10")  # 最小10 USDT
```

**作用**：

- 确保订单满足交易所最小下单量要求
- 避免订单金额过小导致手续费占比过高
- 控制网格层级数量

**与网格层级的关系**：

```python
# 计算理论层级数量
theoretical_levels = (end_price - start_price) / min_spread_between_orders

# 计算单层级资金
amount_per_level = total_amount_quote / theoretical_levels

# 如果单层级资金 < min_order_amount_quote
if amount_per_level < min_order_amount_quote:
    # 实际层级数量会被限制
    actual_levels = total_amount_quote / min_order_amount_quote
```

**示例计算**：

```python
total_amount_quote = 500 USDT
theoretical_levels = 100
amount_per_level = 500 / 100 = 5 USDT

min_order_amount_quote = 10 USDT

# 5 < 10，不满足最小订单要求
# 实际层级 = 500 / 10 = 50 层
```

**设置建议**：

```python
# 基于交易所要求
exchange_min = 5 USDT  # 交易所最小下单金额
buffer = 1.2  # 20% 缓冲
min_order_amount_quote = exchange_min * buffer = 6 USDT

# 基于手续费效率
fee_rate = 0.001  # 0.1%
target_fee_ratio = 0.1  # 手续费不超过10%
min_order_amount_quote = fee_rate / target_fee_ratio = 0.01  # 需要至少让手续费占比合理
```

**常见交易所要求**：

| 交易所 | 最小下单金额（USDT） |
|--------|-------------------|
| Binance | 5-10 |
| Bybit | 5 |
| OKX | 5 |
| Gate.io | 5 |

## 3.5 执行控制

### 3.5.1 max_open_orders（最大开仓订单数）

**类型**：整数（int）

**默认值**：2

**说明**：GridExecutor 同时存在的最大开仓订单数量。

**可更新**：是（运行时可调整）

**示例**：

```python
max_open_orders = 5  # 最多5个开仓订单
```

**作用**：

- 限制同时下单数量，避免过度分散资金
- 控制风险敞口
- 降低交易所 API 压力

**与网格层级的关系**：

```python
# 理论层级数量
theoretical_levels = (end_price - start_price) / min_spread_between_orders

# 实际创建的层级 = min(theoretical_levels, max_open_orders)
actual_levels = min(theoretical_levels, max_open_orders)
```

**示例**：

```python
配置：
- start_price = 2.00
- end_price = 2.20
- min_spread = 0.01  # 1%
- max_open_orders = 5

理论层级 = (2.20 - 2.00) / (2.00 * 0.01) = 10 层

实际创建 = min(10, 5) = 5 层
```

**设置建议**：

| 风格 | max_open_orders | 资金分散度 | 风险 | 适用场景 |
|-----|----------------|-----------|------|---------|
| 保守 | 2-3 | 低 | 低 | 小资金，高杠杆 |
| 均衡 | 5-10 | 中 | 中 | 中等资金 |
| 激进 | 10-20 | 高 | 高 | 大资金，低杠杆 |

### 3.5.2 max_orders_per_batch（每批最大订单数）

**类型**：整数（int），可选

**默认值**：1

**说明**：每次最多创建的订单数量，用于分批下单。

**可更新**：是（运行时可调整）

**示例**：

```python
max_orders_per_batch = 3  # 每次最多下3个订单
```

**作用**：

- 避免同时下太多订单导致交易所限流
- 降低瞬时资金占用
- 分散订单创建时间

**执行逻辑**：

```python
场景：需要创建10个开仓订单

如果 max_orders_per_batch = 3：
- 第1批：创建 3 个订单（Level 0-2）
- 第2批：创建 3 个订单（Level 3-5）
- 第3批：创建 3 个订单（Level 6-8）
- 第4批：创建 1 个订单（Level 9）
```

**与 order_frequency 配合**：

```python
max_orders_per_batch = 3
order_frequency = 5  # 5秒刷新一次

执行时间线：
- T=0s: 创建订单 0-2
- T=5s: 创建订单 3-5
- T=10s: 创建订单 6-8
- T=15s: 创建订单 9
```

**设置建议**：

- **小型网格（<5层）**：`None`（不限制）或 `max_open_orders`
- **中型网格（5-10层）**：2-3
- **大型网格（>10层）**：3-5

### 3.5.3 order_frequency（订单刷新频率）

**类型**：整数（int）

**默认值**：3（秒）

**说明**：订单刷新的时间间隔（秒）。

**可更新**：是（运行时可调整）

**示例**：

```python
order_frequency = 5  # 每5秒检查一次订单
```

**作用**：

- 控制订单创建和取消的频率
- 避免频繁操作导致手续费增加
- 减少交易所 API 调用

**执行逻辑**：

```python
if current_time - last_order_time < order_frequency:
    return  # 跳过本次，不下单

# 否则，检查并创建/取消订单
```

**对比分析**：

| 频率 | 响应速度 | API 压力 | 手续费 | 适用场景 |
|------|---------|---------|--------|---------|
| 1-2秒 | 快 | 高 | 高 | 高波动市场 |
| 3-5秒 | 中 | 中 | 中 | 一般市场 |
| 10秒+ | 慢 | 低 | 低 | 低波动市场 |

**设置建议**：

```python
# 基于市场波动率
daily_volatility = 0.05  # 5%

if daily_volatility > 0.10:  # 高波动
    order_frequency = 2
elif daily_volatility > 0.05:  # 中等波动
    order_frequency = 5
else:  # 低波动
    order_frequency = 10
```

### 3.5.4 activation_bounds（激活边界）

**类型**：Decimal，可选

**默认值**：`None`

**说明**：网格层级的激活边界，用于延迟订单创建。

**可更新**：是（运行时可调整）

**示例**：

```python
activation_bounds = Decimal("0.002")  # 0.2%
```

**作用**：

- 只有当价格接近网格层级时才创建订单
- 减少不必要的订单
- 降低资金占用

**激活逻辑**（做多网格）：

```python
level_price = 2.00
activation_bounds = 0.002  # 0.2%
current_price = 2.05

# 激活范围
activation_high = level_price * (1 + activation_bounds) = 2.004
activation_low = level_price * (1 - activation_bounds) = 1.996

# 只有当价格在 [1.996, 2.004] 范围内时才创建订单
if activation_low <= current_price <= activation_high:
    create_order_at_level(level_price)
```

**示例场景**：

```
配置：
- start_price = 2.00
- end_price = 2.20
- activation_bounds = 0.01  # 1%

当前价格 = 2.15

激活的层级：
- Level at 2.14 (在 1% 范围内) ✓
- Level at 2.15 (在 1% 范围内) ✓
- Level at 2.16 (在 1% 范围内) ✓
- Level at 2.00 (超出 1% 范围) ✗
- Level at 2.20 (超出 1% 范围) ✗
```

**设置建议**：

- **None**：不使用激活边界，创建所有层级（推荐新手）
- **0.5%-1%**：中等激活范围，平衡订单数量和覆盖率
- **1%-2%**：窄激活范围，最小化资金占用

### 3.5.5 keep_position（保留仓位）

**类型**：布尔值（bool）

**默认值**：`False`

**说明**：GridExecutor 关闭时是否保留仓位。

**可更新**：是（运行时可调整）

**示例**：

```python
keep_position = True  # 关闭时保留仓位
```

**作用**：

| keep_position | 关闭时行为 | 适用场景 |
|--------------|----------|---------|
| False | 市价平仓所有仓位 | 严格风控，不留隔夜仓位 |
| True | 保留仓位不平仓 | 看好后市，继续持有 |

**使用场景**：

**False（默认）**：

```
场景：触发止损或时间限制

执行：
1. 取消所有开仓订单
2. 取消所有平仓订单
3. 市价平掉所有仓位
4. GridExecutor 关闭
```

**True**：

```
场景：触发止损或时间限制

执行：
1. 取消所有开仓订单
2. 取消所有平仓订单
3. 保留现有仓位（不平仓）
4. GridExecutor 关闭
5. 仓位成为"held position"，可由策略后续处理
```

**注意事项**：

- 保留仓位会增加风险敞口
- 需要手动管理保留的仓位
- 适合有经验的交易者

## 3.6 风险管理（Triple Barrier）

### 3.6.1 take_profit（止盈比例）

**类型**：Decimal

**默认值**：`Decimal("0.001")`（0.1%）

**说明**：每个网格层级的止盈比例。

**示例**：

```python
triple_barrier_config = TripleBarrierConfig(
    take_profit=Decimal("0.003")  # 0.3% 止盈
)
```

**计算方式**：

```python
# 做多
entry_price = 2.00
take_profit = 0.003  # 0.3%
take_profit_price = entry_price * (1 + take_profit) = 2.006

# 做空
entry_price = 2.00
take_profit = 0.003
take_profit_price = entry_price * (1 - take_profit) = 1.994
```

**对比分析**：

| 止盈比例 | 成交频率 | 单次收益 | 累积收益 | 风险 | 适用场景 |
|---------|---------|---------|---------|------|---------|
| 0.1% | 很高 | 很小 | 高 | 低 | 高频波动 |
| 0.3% | 高 | 小 | 中高 | 中低 | 一般波动 |
| 0.5% | 中 | 中 | 中 | 中 | 均衡 |
| 1.0% | 低 | 大 | 中低 | 高 | 低频波动 |

**与网格间距的关系**：

```python
# 止盈应该 >= 网格间距 + 手续费

min_spread = 0.005  # 0.5% 网格间距
fee = 0.001  # 0.1% 总手续费
take_profit >= min_spread + fee = 0.006  # 至少 0.6%

# 推荐：止盈 = 网格间距的 50%-100%
take_profit = min_spread * 0.7 = 0.0035  # 0.35%
```

**设置建议**：

```python
# 方法1：基于网格间距
take_profit = min_spread_between_orders * Decimal("0.6")

# 方法2：基于手续费
taker_fee = 0.0005
maker_fee = 0.0002
take_profit = (taker_fee + maker_fee) * Decimal("3")  # 手续费的3倍

# 方法3：基于波动率
daily_volatility = 0.05
take_profit = daily_volatility / Decimal("10")  # 日波动的1/10
```

### 3.6.2 stop_loss（止损比例）

**类型**：Decimal，可选

**默认值**：`None`（不设置止损）

**说明**：每个网格层级的止损比例。

**示例**：

```python
triple_barrier_config = TripleBarrierConfig(
    stop_loss=Decimal("0.01")  # 1% 止损
)
```

**计算方式**：

```python
# 做多
entry_price = 2.00
stop_loss = 0.01  # 1%
stop_loss_price = entry_price * (1 - stop_loss) = 1.98

# 做空
entry_price = 2.00
stop_loss = 0.01
stop_loss_price = entry_price * (1 + stop_loss) = 2.02
```

**对比分析**：

| 止损比例 | 触发频率 | 单次亏损 | 风险保护 | 适用场景 |
|---------|---------|---------|---------|---------|
| None | 无 | 不限 | 无 | 不推荐 |
| 0.5% | 很高 | 很小 | 很强 | 极端保守 |
| 1.0% | 高 | 小 | 强 | 保守 |
| 2.0% | 中 | 中 | 中 | 均衡 |
| 5.0% | 低 | 大 | 弱 | 激进 |

**与止盈的关系**：

```python
# 推荐：止损 = 止盈的 2-5 倍

take_profit = 0.003  # 0.3%
stop_loss = take_profit * 3 = 0.009  # 0.9%

# 风险收益比
risk_reward_ratio = stop_loss / take_profit = 3:1
```

**设置建议**：

```python
# 保守型
stop_loss = Decimal("0.01")  # 1%

# 均衡型
stop_loss = Decimal("0.02")  # 2%

# 激进型
stop_loss = Decimal("0.05")  # 5%

# 不设置（不推荐）
stop_loss = None
```

**重要提示**：

- 使用杠杆时**强烈建议设置止损**
- 止损过小可能频繁触发
- 止损过大无法有效保护资金

### 3.6.3 time_limit（时间限制）

**类型**：整数（int），可选

**默认值**：`None`（无时间限制）

**说明**：持仓的最大时间（秒）。

**示例**：

```python
triple_barrier_config = TripleBarrierConfig(
    time_limit=3600  # 1小时
)
```

**作用**：

- 避免长时间持仓
- 减少资金费率支出
- 提高资金周转率
- 控制隔夜风险

**常用时间**：

```python
time_limit = 1800   # 30分钟
time_limit = 3600   # 1小时
time_limit = 7200   # 2小时
time_limit = 14400  # 4小时
time_limit = 86400  # 24小时
```

**对比分析**：

| 时间限制 | 持仓灵活性 | 资金费率影响 | 强制平仓风险 | 适用场景 |
|---------|-----------|------------|------------|---------|
| None | 最高 | 高 | 无 | 长期持仓 |
| 1小时 | 很低 | 很低 | 高 | 短线交易 |
| 4小时 | 低 | 低 | 中高 | 日内交易 |
| 24小时 | 中 | 中 | 中 | 日线级别 |

**设置建议**：

```python
# 基于资金费率周期（通常8小时）
funding_period = 28800  # 8小时
time_limit = funding_period - 1800  # 提前30分钟平仓

# 基于交易风格
# 超短线
time_limit = 1800  # 30分钟

# 日内
time_limit = 14400  # 4小时

# 短期持有
time_limit = None  # 不限制
```

### 3.6.4 订单类型配置

TripleBarrier 支持为不同类型的订单配置订单类型。

**open_order_type（开仓订单类型）**

```python
triple_barrier_config = TripleBarrierConfig(
    open_order_type=OrderType.LIMIT_MAKER
)
```

**可选值**：

- `OrderType.LIMIT`：限价单（默认）
- `OrderType.LIMIT_MAKER`：Post-Only 限价单（推荐，Maker手续费）
- `OrderType.MARKET`：市价单（不推荐，滑点大）

**take_profit_order_type（止盈订单类型）**

```python
triple_barrier_config = TripleBarrierConfig(
    take_profit_order_type=OrderType.LIMIT_MAKER
)
```

**可选值**：

- `OrderType.LIMIT_MAKER`：Post-Only 限价单（推荐）
- `OrderType.LIMIT`：限价单
- `OrderType.MARKET`：市价单（快速成交）

**stop_loss_order_type（止损订单类型）**

```python
triple_barrier_config = TripleBarrierConfig(
    stop_loss_order_type=OrderType.MARKET
)
```

**可选值**：

- `OrderType.MARKET`：市价单（推荐，确保成交）
- `OrderType.LIMIT`：限价单（可能无法成交）

**time_limit_order_type（超时订单类型）**

```python
triple_barrier_config = TripleBarrierConfig(
    time_limit_order_type=OrderType.MARKET
)
```

**可选值**：

- `OrderType.MARKET`：市价单（推荐）
- `OrderType.LIMIT`：限价单

**推荐组合**：

```python
# 标准配置
TripleBarrierConfig(
    open_order_type=OrderType.LIMIT_MAKER,        # Maker 手续费
    take_profit_order_type=OrderType.LIMIT_MAKER,  # Maker 手续费
    stop_loss_order_type=OrderType.MARKET,         # 快速止损
    time_limit_order_type=OrderType.MARKET          # 快速平仓
)
```

### 3.6.5 完整配置示例

**保守型**：

```python
TripleBarrierConfig(
    take_profit=Decimal("0.002"),              # 0.2% 止盈
    stop_loss=Decimal("0.005"),                # 0.5% 止损
    time_limit=7200,                           # 2小时
    open_order_type=OrderType.LIMIT_MAKER,
    take_profit_order_type=OrderType.LIMIT_MAKER,
    stop_loss_order_type=OrderType.MARKET,
    time_limit_order_type=OrderType.MARKET
)
```

**均衡型**：

```python
TripleBarrierConfig(
    take_profit=Decimal("0.005"),              # 0.5% 止盈
    stop_loss=Decimal("0.015"),                # 1.5% 止损
    time_limit=14400,                          # 4小时
    open_order_type=OrderType.LIMIT_MAKER,
    take_profit_order_type=OrderType.LIMIT_MAKER,
    stop_loss_order_type=OrderType.MARKET,
    time_limit_order_type=OrderType.MARKET
)
```

**激进型**：

```python
TripleBarrierConfig(
    take_profit=Decimal("0.01"),               # 1.0% 止盈
    stop_loss=Decimal("0.03"),                 # 3.0% 止损
    time_limit=None,                           # 不限时间
    open_order_type=OrderType.LIMIT_MAKER,
    take_profit_order_type=OrderType.LIMIT_MAKER,
    stop_loss_order_type=OrderType.MARKET,
    time_limit_order_type=OrderType.MARKET
)
```

## 3.7 高级选项

### 3.7.1 candles_config（K线配置）

**类型**：列表（List[CandlesConfig]）

**默认值**：`[]`（空列表）

**说明**：如果策略需要K线数据（例如技术指标），在此配置。

**示例**：

```python
from hummingbot.data_feed.candles_feed.data_types import CandlesConfig

candles_config = [
    CandlesConfig(
        connector="binance_perpetual",
        trading_pair="WLD-USDT",
        interval="1m",  # 1分钟K线
        max_records=100
    )
]
```

**GridStrike 默认不需要K线数据**，可保持为空。

### 3.7.2 initial_positions（初始仓位）

**类型**：列表（List[InitialPositionConfig]）

**默认值**：`[]`

**说明**：策略启动时的初始仓位配置（高级功能）。

**GridStrike 通常不使用此功能**。

## 3.8 配置模板

### 3.8.1 最小配置

```python
from decimal import Decimal
from hummingbot.core.data_type.common import OrderType, PositionMode, TradeType
from hummingbot.strategy_v2.executors.position_executor.data_types import TripleBarrierConfig

# 最小配置（使用大部分默认值）
config = GridStrikeConfig(
    connector_name="binance_perpetual",
    trading_pair="WLD-USDT",
    side=TradeType.BUY,
    start_price=Decimal("2.00"),
    end_price=Decimal("2.20"),
    limit_price=Decimal("1.95"),
    total_amount_quote=Decimal("1000"),
    triple_barrier_config=TripleBarrierConfig(
        take_profit=Decimal("0.003")
    )
)
```

### 3.8.2 完整配置

```python
config = GridStrikeConfig(
    # 账户配置
    connector_name="binance_perpetual",
    trading_pair="WLD-USDT",
    leverage=20,
    position_mode=PositionMode.HEDGE,
    
    # 网格边界
    side=TradeType.BUY,
    start_price=Decimal("2.00"),
    end_price=Decimal("2.20"),
    limit_price=Decimal("1.95"),
    
    # 资金配置
    total_amount_quote=Decimal("1000"),
    min_spread_between_orders=Decimal("0.005"),  # 0.5%
    min_order_amount_quote=Decimal("10"),
    
    # 执行控制
    max_open_orders=5,
    max_orders_per_batch=2,
    order_frequency=5,
    activation_bounds=Decimal("0.01"),
    keep_position=False,
    
    # 风险管理
    triple_barrier_config=TripleBarrierConfig(
        take_profit=Decimal("0.005"),
        stop_loss=Decimal("0.015"),
        time_limit=7200,
        open_order_type=OrderType.LIMIT_MAKER,
        take_profit_order_type=OrderType.LIMIT_MAKER,
        stop_loss_order_type=OrderType.MARKET,
        time_limit_order_type=OrderType.MARKET
    )
)
```

## 3.9 本章小结

本章详细讲解了 GridStrike 策略的所有配置参数：

**核心参数**：

1. **网格边界**：`start_price`、`end_price` 定义交易区间
2. **资金配置**：`total_amount_quote` 和 `min_spread_between_orders` 决定网格密度
3. **风险管理**：`take_profit`、`stop_loss` 控制盈亏
4. **杠杆**：放大收益和风险

**配置原则**：

- 网格间距 > 手续费的 3-5 倍
- 止盈 ≈ 网格间距的 50%-100%
- 止损 = 止盈的 2-5 倍
- 杠杆根据风险承受能力选择
- 预留足够的保证金应对波动

**常见组合**：

- 保守：低杠杆 + 小止盈 + 严格止损 + 短时间限制
- 均衡：中杠杆 + 中止盈 + 适度止损 + 中等时限
- 激进：高杠杆 + 大止盈 + 宽松止损 + 无时限

下一章我们将学习 [快速开始使用指南](grid_strike_tutorial_04.md)，实际部署和运行 GridStrike 策略。

---

[返回索引](grid_strike_tutorial_index.md) | [上一章：策略原理详解](grid_strike_tutorial_02.md) | [下一章：快速开始使用指南](grid_strike_tutorial_04.md)

