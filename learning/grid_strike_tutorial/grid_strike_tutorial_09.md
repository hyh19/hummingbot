# 第 9 章：故障排查

## 本章导航

- [返回索引](grid_strike_tutorial_index.md)
- [上一章：最佳实践与注意事项](grid_strike_tutorial_08.md)
- [下一章：参考资源](grid_strike_tutorial_10.md)

## 9.1 常见错误及解决方案

### 9.1.1 "Insufficient balance" 错误

**错误信息**：

```
ERROR: Insufficient balance to create grid executor
Available: 50 USDT, Required: 100 USDT
```

**原因分析**：

1. 账户余额不足以支持网格订单
2. 保证金被其他持仓占用
3. 配置的 `total_amount_quote` 过大

**解决方案**：

**方案 1：充值**

```bash
# 向交易所账户充值 USDT
# 确保余额 >= 所需保证金 × 3
```

**方案 2：降低资金配置**

```yaml
# 原配置
total_amount_quote: 2000

# 新配置
total_amount_quote: 500  # 降低到账户可承受范围
```

**方案 3：提高杠杆（谨慎）**

```yaml
# 原配置
leverage: 10
total_amount_quote: 1000
# 所需保证金: 1000 / 10 = 100 USDT

# 新配置
leverage: 20
total_amount_quote: 1000
# 所需保证金: 1000 / 20 = 50 USDT
```

**方案 4：平掉其他仓位**

```bash
# 在交易所平掉不必要的持仓
# 释放保证金
```

**预防措施**：

```python
# 启动前检查余额
def check_balance_before_start(config):
    margin_required = config.total_amount_quote / config.leverage
    buffer = margin_required * 3
    
    available_balance = get_available_balance()
    
    if available_balance < buffer:
        print(f"警告: 余额不足")
        print(f"所需: {buffer} USDT")
        print(f"可用: {available_balance} USDT")
        return False
    
    return True
```

### 9.1.2 "Price out of bounds" 警告

**错误信息**：

```
WARNING: Current price 2.25 is out of grid bounds [2.00, 2.20]
No executor will be created until price returns to bounds.
```

**原因分析**：

- 当前价格超出网格区间
- Controller 不会创建新的 GridExecutor
- 策略处于等待状态

**解决方案**：

**方案 1：调整网格区间**

```yaml
# 原配置
start_price: 2.00
end_price: 2.20

# 当前价格: 2.25

# 新配置（向上移动）
start_price: 2.10
end_price: 2.30
```

**方案 2：等待价格回归**

```bash
# 如果判断价格会回落，等待即可
# Controller 会在价格回到区间后自动创建执行器
```

**方案 3：修改策略方向**

```yaml
# 如果价格持续上涨，可以改为做空网格

# 原配置（做多）
side: BUY
start_price: 2.00
end_price: 2.20

# 新配置（做空）
side: SELL
start_price: 2.25
end_price: 2.45
```

**预防措施**：

```python
# 设置警报
def alert_price_out_of_bounds(price, start, end):
    if price < start:
        distance = (start - price) / price
        if distance > 0.05:  # 超出5%
            send_alert(f"价格严重低于网格下限: {price}")
    elif price > end:
        distance = (price - end) / price
        if distance > 0.05:  # 超出5%
            send_alert(f"价格严重高于网格上限: {price}")
```

### 9.1.3 Executor 创建失败

**错误信息**：

```
ERROR: Failed to create GridExecutor
Error: Invalid configuration - start_price must be less than end_price
```

**原因分析**：

- 配置参数错误
- `start_price >= end_price`
- `min_spread_between_orders <= 0`
- 其他配置验证失败

**解决方案**：

**检查参数逻辑**：

```python
# 检查列表
checks = [
    ("start_price < end_price", config.start_price < config.end_price),
    ("limit_price valid", config.limit_price > 0),
    ("total_amount_quote > 0", config.total_amount_quote > 0),
    ("min_spread > 0", config.min_spread_between_orders > 0),
    ("max_open_orders > 0", config.max_open_orders > 0),
    ("leverage > 0", config.leverage > 0),
]

for check_name, result in checks:
    if not result:
        print(f"❌ {check_name} failed")
```

**常见错误**：

```yaml
# 错误1: 起始价高于结束价
start_price: 2.20
end_price: 2.00  # ❌ 应该 > start_price

# 错误2: 间距为负数或零
min_spread_between_orders: 0  # ❌ 应该 > 0

# 错误3: 总资金为零
total_amount_quote: 0  # ❌ 应该 > 0

# 错误4: 杠杆为零
leverage: 0  # ❌ 应该 > 0
```

**修正配置**：

```yaml
# 正确配置
start_price: 2.00
end_price: 2.20
limit_price: 1.95
total_amount_quote: 1000
min_spread_between_orders: 0.005
max_open_orders: 5
leverage: 20
```

### 9.1.4 订单被拒绝

**错误信息**：

```
ERROR: Order rejected by exchange
Reason: Order size is below minimum
```

**原因分析**：

1. 订单金额低于交易所最小限制
2. 价格精度不符合要求
3. 数量精度不符合要求
4. 超过交易所限制（如杠杆限制）

**解决方案**：

**方案 1：增加最小订单金额**

```yaml
# 原配置
min_order_amount_quote: 5

# 新配置
min_order_amount_quote: 15  # 增加到交易所最小值以上
```

**方案 2：减少网格层级**

```yaml
# 原配置
total_amount_quote: 500
max_open_orders: 50
# 单层级资金: 500 / 50 = 10 USDT (可能低于最小值)

# 新配置
max_open_orders: 20
# 单层级资金: 500 / 20 = 25 USDT
```

**方案 3：检查交易规则**

```python
# 获取交易规则
trading_rules = exchange.get_trading_rules("WLD-USDT")

print(f"最小订单金额: {trading_rules.min_order_size}")
print(f"最小价格增量: {trading_rules.min_price_increment}")
print(f"最小数量增量: {trading_rules.min_base_amount_increment}")
print(f"最大杠杆: {trading_rules.max_leverage}")
```

**常见交易所限制**：

| 交易所 | 最小订单（USDT） | 价格精度 | 数量精度 | 最大杠杆 |
|--------|----------------|---------|---------|---------|
| Binance | 5-10 | 0.001 | 0.001 | 125x |
| Bybit | 5 | 0.01 | 0.01 | 100x |
| OKX | 5 | 0.001 | 0.001 | 125x |

## 9.2 日志分析技巧

### 9.2.1 Controller 日志解读

**日志示例**：

```
2025-10-25 10:30:15 INFO GridStrike: Determining executor actions
2025-10-25 10:30:15 INFO GridStrike: Mid price: 2.1200, Bounds: [2.00, 2.20]
2025-10-25 10:30:15 INFO GridStrike: Active executors: 0, Inside bounds: True
2025-10-25 10:30:15 INFO GridStrike: Creating GridExecutor with config: {...}
2025-10-25 10:30:15 INFO ExecutorOrchestrator: Created GridExecutor abc123
```

**关键信息**：

1. **Mid price**：当前市场中间价
2. **Bounds**：网格区间
3. **Active executors**：活跃执行器数量
4. **Inside bounds**：价格是否在区间内

**异常模式**：

```
# 模式1: 价格持续超出边界
10:30:15 INFO Mid price: 2.25, Inside bounds: False
10:30:20 INFO Mid price: 2.26, Inside bounds: False
10:30:25 INFO Mid price: 2.27, Inside bounds: False

# 诊断: 价格突破网格上限，需要调整区间

# 模式2: 执行器频繁创建和关闭
10:30:15 INFO Creating GridExecutor abc123
10:30:45 INFO GridExecutor abc123 closed (TAKE_PROFIT)
10:31:00 INFO Creating GridExecutor abc456
10:31:30 INFO GridExecutor abc456 closed (TAKE_PROFIT)

# 诊断: 止盈设置可能过小，或市场波动大
```

### 9.2.2 Executor 日志解读

**日志示例**：

```
2025-10-25 10:30:16 INFO GridExecutor[abc123]: Initializing
2025-10-25 10:30:16 INFO GridExecutor[abc123]: Generated 5 grid levels
2025-10-25 10:30:16 INFO GridExecutor[abc123]: Level 0: price=2.00, amount=200
2025-10-25 10:30:16 INFO GridExecutor[abc123]: Level 1: price=2.05, amount=200
...
2025-10-25 10:30:17 INFO GridExecutor[abc123]: Placing open order at level 0
2025-10-25 10:30:18 INFO GridExecutor[abc123]: Order placed: buy_order_123
2025-10-25 10:32:45 INFO GridExecutor[abc123]: Order filled: buy_order_123
2025-10-25 10:32:46 INFO GridExecutor[abc123]: Placing close order at level 0
2025-10-25 10:35:12 INFO GridExecutor[abc123]: Close order filled: sell_order_456
2025-10-25 10:35:12 INFO GridExecutor[abc123]: Level 0 completed
2025-10-25 10:35:13 INFO GridExecutor[abc123]: Realized PnL: +15.5 USDT
```

**关键信息**：

1. **Grid levels**：网格层级数量和价格
2. **Order placed/filled**：订单创建和成交
3. **Realized PnL**：已实现盈亏

**异常模式**：

```
# 模式1: 订单长时间未成交
10:30:17 INFO Placing open order at level 0
10:35:17 INFO Order still pending: buy_order_123
10:40:17 INFO Order still pending: buy_order_123

# 诊断: 价格偏离，订单无法成交，可能需要取消

# 模式2: 频繁触发止损
10:30:45 INFO TripleBarrier triggered: STOP_LOSS
10:30:45 INFO Closing executor with loss: -25.5 USDT
10:31:00 INFO Created new executor
10:31:30 INFO TripleBarrier triggered: STOP_LOSS

# 诊断: 止损设置过小，或市场单边行情
```

### 9.2.3 订单事件追踪

**订单生命周期**：

```
1. OrderCreated
   → 订单已提交到交易所

2. OrderFilled (部分成交)
   → 订单部分成交

3. OrderCompleted
   → 订单完全成交

4. OrderCancelled
   → 订单被取消

5. OrderFailed
   → 订单失败（被交易所拒绝）
```

**追踪示例**：

```bash
# 查看特定订单的所有事件
>>> grep "buy_order_123" logs/hummingbot.log

10:30:17 INFO OrderCreated: buy_order_123, price=2.00, amount=98.5
10:32:45 INFO OrderFilled: buy_order_123, filled=50.0, remaining=48.5
10:33:12 INFO OrderFilled: buy_order_123, filled=98.5, remaining=0
10:33:12 INFO OrderCompleted: buy_order_123
```

## 9.3 调试方法

### 9.3.1 使用 status 命令

**基本用法**：

```bash
>>> status

# 查看策略整体状态
```

**重点检查**：

1. **Grid Configuration**
   - 网格参数是否正确
   - 价格是否在区间内

2. **Level Distribution**
   - 各状态层级数量
   - 是否有异常累积

3. **Performance Metrics**
   - 盈亏是否符合预期
   - 手续费占比

**诊断示例**：

```
# 异常1: 所有层级都是 NOT_ACTIVE
NOT_ACTIVE: 5
OPEN_ORDER_PLACED: 0
...

# 诊断: 订单未创建，可能价格超出边界或余额不足

# 异常2: 大量 OPEN_ORDER_PLACED 未成交
OPEN_ORDER_PLACED: 5
OPEN_ORDER_FILLED: 0

# 诊断: 订单价格可能偏离市场，无法成交
```

### 9.3.2 检查执行器状态

**查看执行器列表**：

```bash
>>> executors

# 输出
Executor ID          Controller    Status      PnL
grid_executor_123    grid_strike   RUNNING    +50.25
grid_executor_456    grid_strike   SHUTTING   -10.50
```

**状态说明**：

- `NOT_STARTED`：已创建但未启动
- `RUNNING`：正常运行中
- `SHUTTING_DOWN`：正在关闭
- `TERMINATED`：已终止

**异常诊断**：

```
# 异常1: 执行器状态卡在 SHUTTING_DOWN
grid_executor_123    grid_strike   SHUTTING   +50.25

# 可能原因:
# - 平仓订单未成交
# - 网络问题
# - 交易所限制

# 解决: 手动平仓或等待超时
```

### 9.3.3 验证配置参数

**配置检查清单**：

```python
def validate_config(config):
    """
    验证配置参数
    """
    errors = []
    
    # 1. 价格区间
    if config.start_price >= config.end_price:
        errors.append("start_price must be < end_price")
    
    # 2. 网格间距
    grid_width = config.end_price - config.start_price
    min_levels = grid_width / (config.start_price * config.min_spread_between_orders)
    if min_levels < 2:
        errors.append("Grid too narrow or spread too large")
    
    # 3. 资金配置
    if config.total_amount_quote <= 0:
        errors.append("total_amount_quote must be > 0")
    
    # 4. 单层级资金
    amount_per_level = config.total_amount_quote / config.max_open_orders
    if amount_per_level < config.min_order_amount_quote:
        errors.append(f"Amount per level ({amount_per_level}) < min_order_amount ({config.min_order_amount_quote})")
    
    # 5. 杠杆
    if config.leverage <= 0 or config.leverage > 125:
        errors.append("leverage must be in range (0, 125]")
    
    # 6. 止盈止损
    if config.triple_barrier_config.take_profit and config.triple_barrier_config.take_profit <= 0:
        errors.append("take_profit must be > 0 if set")
    
    return errors

# 使用
errors = validate_config(my_config)
if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ 配置验证通过")
```

## 9.4 紧急处理流程

### 9.4.1 快速停止策略

**方法 1：正常停止**

```bash
>>> stop

# 等待执行器完成
# 根据 keep_position 配置决定是否平仓
```

**方法 2：强制停止**

```bash
>>> exit --force

# 立即退出 Hummingbot
# 可能留有未取消的订单和未平的仓位
```

**方法 3：Ctrl+C**

```bash
# 在终端按 Ctrl+C
# 触发 Hummingbot 关闭流程
```

### 9.4.2 手动平仓

**场景**：策略异常，需要紧急平仓。

**步骤**：

```bash
# 1. 停止策略
>>> stop

# 2. 在交易所 Web 界面操作
# - 登录交易所
# - 找到持仓管理
# - 点击"一键平仓"或逐个平仓

# 3. 取消所有挂单
# - 找到当前委托
# - 点击"全部撤销"

# 4. 确认清空
# - 检查持仓：应该为 0
# - 检查挂单：应该为 0
```

**脚本化平仓**：

```python
def emergency_close_all():
    """
    紧急平仓脚本
    """
    # 1. 取消所有订单
    orders = exchange.get_open_orders()
    for order in orders:
        exchange.cancel_order(order.id)
    
    # 2. 平掉所有仓位
    positions = exchange.get_positions()
    for position in positions:
        if position.size > 0:
            # 市价平仓
            exchange.place_order(
                side="SELL" if position.side == "LONG" else "BUY",
                type="MARKET",
                amount=abs(position.size)
            )
    
    print("Emergency close completed")
```

### 9.4.3 恢复正常运行

**步骤**：

```bash
# 1. 分析问题原因
# - 查看日志
# - 检查配置
# - 确认账户状态

# 2. 修复问题
# - 调整配置参数
# - 充值账户（如果余额不足）
# - 等待市场条件改善

# 3. 重新启动
>>> start --script scripts/grid_strike_wld.py

# 4. 监控运行
# - 观察前 15 分钟
# - 确认订单正常创建和成交
# - 检查盈亏是否符合预期

# 5. 记录问题
# - 记录问题描述
# - 记录解决方案
# - 更新配置文档
```

## 9.5 常见问题 FAQ

### Q1: 策略运行一段时间后没有新订单

**可能原因**：

1. 价格超出网格边界
2. 执行器未关闭，Controller 不创建新的
3. 余额不足

**检查步骤**：

```bash
# 1. 查看当前价格和边界
>>> status
# 检查 "Inside bounds" 是否为 1

# 2. 查看执行器状态
>>> executors
# 确认是否有活跃执行器

# 3. 查看余额
>>> balance
# 确认 Available 余额充足
```

### Q2: 盈亏与预期不符

**可能原因**：

1. 手续费未充分考虑
2. 资金费率影响
3. 滑点影响
4. 部分订单未成交

**分析方法**：

```python
# 计算实际手续费
total_fees = realized_fees_quote

# 计算期望盈利
expected_profit = (
    num_completed_levels × 
    avg_amount_per_level × 
    leverage × 
    take_profit
)

# 对比
actual_profit = realized_pnl_quote
difference = actual_profit - expected_profit

# 分析差异来源
fee_impact = total_fees
funding_impact = estimate_funding_fees()
slippage_impact = difference - fee_impact - funding_impact
```

### Q3: 执行器频繁触发止损

**可能原因**：

1. 止损设置过小
2. 市场单边行情
3. 网格间距不合理

**解决方法**：

```yaml
# 方法1: 放宽止损
triple_barrier_config:
  stop_loss: 0.02  # 从 0.01 增加到 0.02

# 方法2: 扩大网格间距
min_spread_between_orders: 0.01  # 从 0.005 增加到 0.01

# 方法3: 暂停策略
# 等待市场恢复震荡
```

## 9.6 本章小结

本章介绍了 GridStrike 策略的故障排查方法：

**常见错误**：

- 余额不足：充值或降低配置
- 价格超界：调整网格区间
- 创建失败：检查配置参数
- 订单被拒：符合交易规则

**日志分析**：

- Controller 日志：决策逻辑
- Executor 日志：执行细节
- 订单事件：追踪订单生命周期

**调试方法**：

- status 命令：整体状态
- executors 命令：执行器状态
- 配置验证：参数检查

**紧急处理**：

- 快速停止：stop/exit
- 手动平仓：交易所操作
- 恢复运行：分析-修复-重启

**关键技能**：

- 读懂日志信息
- 识别异常模式
- 快速定位问题
- 有效解决故障

准备好了吗？下一章是最后一章 [参考资源](grid_strike_tutorial_10.md)，我们将提供学习资源和进阶路径。

---

[返回索引](grid_strike_tutorial_index.md) | [上一章：最佳实践与注意事项](grid_strike_tutorial_08.md) | [下一章：参考资源](grid_strike_tutorial_10.md)

