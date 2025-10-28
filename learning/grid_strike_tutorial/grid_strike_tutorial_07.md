# 第 7 章：高级功能与扩展

## 本章导航

- [返回索引](grid_strike_tutorial_index.md)
- [上一章：代码实现深度解析](grid_strike_tutorial_06.md)
- [下一章：最佳实践与注意事项](grid_strike_tutorial_08.md)

## 7.1 Activation Bounds 延迟激活机制

### 7.1.1 概念说明

Activation Bounds（激活边界）是一种优化机制，只有当价格接近某个网格层级时才创建订单，而不是一次性创建所有层级的订单。

**优势**：

- 减少不必要的挂单
- 降低资金占用
- 提高订单成交率
- 减少订单取消和重建

### 7.1.2 工作原理

```python
activation_bounds = Decimal("0.01")  # 1%

# 对于某个网格层级
level_price = 2.00
current_price = 2.05

# 激活范围
activation_high = level_price * (1 + activation_bounds) = 2.02
activation_low = level_price * (1 - activation_bounds) = 1.98

# 判断是否激活
is_activated = activation_low <= current_price <= activation_high
```

**激活逻辑**：

```python
def should_activate_level(level_price, current_price, activation_bounds):
    if activation_bounds is None:
        return True  # 无激活边界，始终激活
    
    distance = abs(current_price - level_price) / level_price
    return distance <= activation_bounds
```

### 7.1.3 配置示例

**不使用激活边界**：

```yaml
activation_bounds: null

# 效果：立即创建所有网格层级的订单
# 场景：资金充足，希望最大化覆盖率
```

**使用激活边界**：

```yaml
activation_bounds: 0.01  # 1%

# 效果：只创建当前价格±1%范围内的订单
# 场景：资金有限，动态跟随价格
```

### 7.1.4 实战案例

**场景**：WLD-USDT，当前价格 2.10

```yaml
start_price: 2.00
end_price: 2.30
min_spread_between_orders: 0.01  # 1%
max_open_orders: 10
activation_bounds: 0.02  # 2%
```

**网格层级分布**：

```
Price 2.30 (15%高于当前) - 未激活 ✗
Price 2.28 (8.6%高于当前) - 未激活 ✗
...
Price 2.14 (1.9%高于当前) - 激活 ✓
Price 2.12 (0.95%高于当前) - 激活 ✓
Price 2.10 (当前价格) - 激活 ✓
Price 2.08 (0.95%低于当前) - 激活 ✓
Price 2.06 (1.9%低于当前) - 激活 ✓
Price 2.04 (2.9%低于当前) - 未激活 ✗
...
Price 2.00 (4.8%低于当前) - 未激活 ✗
```

**效果**：

- 只创建 5 个层级的订单（±2% 范围）
- 节省资金 50%
- 订单更集中在当前价格附近

### 7.1.5 参数调优

| activation_bounds | 激活层级数 | 资金占用 | 覆盖率 | 适用场景 |
|------------------|----------|---------|-------|---------|
| null | 全部 | 高 | 最高 | 资金充足 |
| 0.005 (0.5%) | 很少 | 很低 | 低 | 极限节约 |
| 0.01 (1%) | 少 | 低 | 中低 | 资金紧张 |
| 0.02 (2%) | 中 | 中 | 中 | 均衡 |
| 0.05 (5%) | 多 | 高 | 高 | 追求覆盖 |

**推荐设置**：

```python
# 高波动市场
activation_bounds = Decimal("0.01")  # 1%，紧跟价格

# 低波动市场
activation_bounds = Decimal("0.03")  # 3%，适度覆盖

# 资金充足
activation_bounds = None  # 全部激活
```

## 7.2 Keep Position 保留仓位模式

### 7.2.1 概念说明

Keep Position 控制 GridExecutor 关闭时是否平仓现有仓位。

**默认行为（keep_position=False）**：

```python
# 执行器关闭时
1. 取消所有开仓订单
2. 取消所有平仓订单
3. 市价平掉所有仓位
4. 执行器终止
```

**保留仓位（keep_position=True）**：

```python
# 执行器关闭时
1. 取消所有开仓订单
2. 取消所有平仓订单
3. 保留仓位不平仓
4. 仓位转为"held position"
5. 执行器终止
```

### 7.2.2 使用场景

**适合 keep_position=True 的场景**：

1. **看好后市**
   ```
   场景：做多网格，触发止盈关闭
   逻辑：认为价格还会继续上涨
   操作：保留仓位，手动择机卖出
   ```

2. **手动管理**
   ```
   场景：希望自行决定平仓时机
   逻辑：不想被动市价平仓
   操作：保留仓位，根据市场调整
   ```

3. **多策略组合**
   ```
   场景：网格策略+趋势策略
   逻辑：网格建仓后由趋势策略管理
   操作：GridExecutor 关闭后，仓位由其他策略接管
   ```

**适合 keep_position=False 的场景**：

1. **严格风控**
   ```
   场景：触发止损
   逻辑：立即退出，避免更大亏损
   操作：市价平仓，清空仓位
   ```

2. **自动化运行**
   ```
   场景：无人值守运行
   逻辑：不希望留有未管理的仓位
   操作：自动平仓，策略完全自治
   ```

3. **避免隔夜风险**
   ```
   场景：日内交易策略
   逻辑：不持仓过夜
   操作：每日收盘前平仓
   ```

### 7.2.3 配置示例

**保守配置（不保留）**：

```yaml
keep_position: false
triple_barrier_config:
  time_limit: 3600  # 1小时后自动平仓
  stop_loss: 0.01   # 触发止损自动平仓
```

**激进配置（保留）**：

```yaml
keep_position: true
triple_barrier_config:
  take_profit: 0.01  # 止盈后保留仓位
  stop_loss: null    # 不设止损
  time_limit: null   # 无时间限制
```

### 7.2.4 注意事项

**风险**：

- 保留的仓位无人管理，可能面临额外风险
- 需要手动平仓或由其他策略接管
- 可能产生资金费率支出

**建议**：

- 仅在有明确后续计划时使用
- 设置警报监控保留的仓位
- 准备好手动平仓的操作流程

## 7.3 Dynamic Config Update 动态参数调整

### 7.3.1 可更新参数列表

标记为 `is_updatable=True` 的参数可以在运行时动态调整：

```python
# 网格边界
start_price: Decimal
end_price: Decimal
limit_price: Decimal

# 资金配置
total_amount_quote: Decimal
min_spread_between_orders: Decimal
min_order_amount_quote: Decimal

# 执行控制
max_open_orders: int
max_orders_per_batch: int
order_frequency: int
activation_bounds: Optional[Decimal]
keep_position: bool
```

### 7.3.2 更新方法

**方法 1：修改配置文件**

```bash
# 1. 编辑配置文件
vim conf/controllers/generic/grid_strike_wld.yml

# 2. 修改参数
start_price: 2.10  # 从 2.00 改为 2.10

# 3. 重载配置（如果支持）
>>> reload_config
```

**方法 2：程序化更新**

```python
# 在策略代码中动态更新
class CustomGridStrike(ScriptStrategyBase):
    def on_tick(self):
        # 根据市场条件调整参数
        current_volatility = self.calculate_volatility()
        
        if current_volatility > 0.10:  # 高波动
            self.controller.config.min_spread_between_orders = Decimal("0.01")
            self.controller.config.take_profit = Decimal("0.008")
        else:  # 低波动
            self.controller.config.min_spread_between_orders = Decimal("0.005")
            self.controller.config.take_profit = Decimal("0.003")
```

### 7.3.3 实战场景

**场景 1：价格突破，调整网格区间**

```python
# 原始配置
start_price = 2.00
end_price = 2.20

# 价格上涨到 2.25，调整区间
if current_price > end_price:
    config.start_price = Decimal("2.10")
    config.end_price = Decimal("2.30")
```

**场景 2：波动率变化，调整间距**

```python
# 计算日波动率
daily_volatility = calculate_daily_volatility()

# 根据波动率调整间距
if daily_volatility < 0.03:  # 低波动
    config.min_spread_between_orders = Decimal("0.002")
elif daily_volatility > 0.10:  # 高波动
    config.min_spread_between_orders = Decimal("0.01")
```

**场景 3：账户余额变化，调整资金**

```python
# 检查账户余额
available_balance = get_available_balance()

# 调整投入资金
if available_balance > 5000:
    config.total_amount_quote = Decimal("2000")
elif available_balance > 2000:
    config.total_amount_quote = Decimal("1000")
else:
    config.total_amount_quote = Decimal("500")
```

## 7.4 Multi-Grid Strike 多网格组合

### 7.4.1 概念说明

Multi-Grid Strike 是 GridStrike 的扩展版本，支持同时运行多个网格，每个网格有独立的配置。

**文件**：`controllers/generic/multi_grid_strike.py`

**优势**：

- 分散风险：不同价格区间的网格
- 灵活配置：每个网格独立参数
- 提高覆盖：覆盖更广的价格范围
- 策略组合：做多网格 + 做空网格

### 7.4.2 配置结构

```yaml
controller_name: multi_grid_strike
controller_type: generic

# 公共配置
connector_name: binance_perpetual
trading_pair: WLD-USDT
leverage: 20
total_amount_quote: 3000  # 总资金

# 多个网格配置
grids:
  - grid_id: grid_1
    start_price: 2.00
    end_price: 2.10
    limit_price: 1.95
    side: BUY
    amount_quote_pct: 0.33  # 占总资金 33%
    enabled: true
    
  - grid_id: grid_2
    start_price: 2.10
    end_price: 2.20
    limit_price: 2.05
    side: BUY
    amount_quote_pct: 0.33  # 占总资金 33%
    enabled: true
    
  - grid_id: grid_3
    start_price: 2.20
    end_price: 2.30
    limit_price: 2.15
    side: BUY
    amount_quote_pct: 0.34  # 占总资金 34%
    enabled: true
```

### 7.4.3 实战案例

**场景：分层网格覆盖宽幅区间**

```yaml
# 目标：覆盖 2.00-2.40 USDT 区间（20%波动）
# 策略：分为 4 个子网格

total_amount_quote: 4000

grids:
  # 底部网格（2.00-2.10）
  - grid_id: bottom_grid
    start_price: 2.00
    end_price: 2.10
    side: BUY
    amount_quote_pct: 0.25  # 1000 USDT
    enabled: true
  
  # 中下网格（2.10-2.20）
  - grid_id: mid_low_grid
    start_price: 2.10
    end_price: 2.20
    side: BUY
    amount_quote_pct: 0.25  # 1000 USDT
    enabled: true
  
  # 中上网格（2.20-2.30）
  - grid_id: mid_high_grid
    start_price: 2.20
    end_price: 2.30
    side: BUY
    amount_quote_pct: 0.25  # 1000 USDT
    enabled: true
  
  # 顶部网格（2.30-2.40）
  - grid_id: top_grid
    start_price: 2.30
    end_price: 2.40
    side: BUY
    amount_quote_pct: 0.25  # 1000 USDT
    enabled: true
```

**场景：双向网格（同时做多和做空）**

```yaml
total_amount_quote: 2000

grids:
  # 做多网格（低价区）
  - grid_id: long_grid
    start_price: 2.00
    end_price: 2.15
    side: BUY
    amount_quote_pct: 0.5  # 1000 USDT
    enabled: true
  
  # 做空网格（高价区）
  - grid_id: short_grid
    start_price: 2.15
    end_price: 2.30
    side: SELL
    amount_quote_pct: 0.5  # 1000 USDT
    enabled: true
```

### 7.4.4 动态启用/禁用

```yaml
# 根据价格动态启用网格
grids:
  - grid_id: grid_1
    enabled: true   # 当前价格在此区间，启用
  
  - grid_id: grid_2
    enabled: false  # 价格远离此区间，禁用
  
  - grid_id: grid_3
    enabled: true   # 价格接近此区间，启用
```

## 7.5 自定义扩展开发

### 7.5.1 继承 GridStrike

创建自定义控制器：

```python
from decimal import Decimal
from controllers.generic.grid_strike import GridStrike, GridStrikeConfig

class AdaptiveGridStrike(GridStrike):
    """
    自适应 GridStrike：根据波动率动态调整网格间距
    """
    
    def __init__(self, config: GridStrikeConfig, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.volatility_window = 100  # 计算波动率的窗口
    
    async def update_processed_data(self):
        """
        计算市场波动率
        """
        # 获取历史K线数据
        candles = await self.get_candles(
            self.config.connector_name,
            self.config.trading_pair,
            "1m",
            self.volatility_window
        )
        
        # 计算波动率
        returns = [
            (candles[i].close - candles[i-1].close) / candles[i-1].close
            for i in range(1, len(candles))
        ]
        volatility = Decimal(str(np.std(returns)))
        
        # 根据波动率调整间距
        if volatility < Decimal("0.01"):  # 低波动
            self.config.min_spread_between_orders = Decimal("0.002")
        elif volatility < Decimal("0.03"):  # 中等波动
            self.config.min_spread_between_orders = Decimal("0.005")
        else:  # 高波动
            self.config.min_spread_between_orders = Decimal("0.01")
```

### 7.5.2 添加技术指标

```python
class RSIGridStrike(GridStrike):
    """
    基于 RSI 的 GridStrike：只在 RSI 超卖时创建执行器
    """
    
    def __init__(self, config: GridStrikeConfig, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
    
    async def update_processed_data(self):
        """
        计算 RSI 指标
        """
        candles = await self.get_candles(
            self.config.connector_name,
            self.config.trading_pair,
            "5m",
            self.rsi_period + 10
        )
        
        # 计算 RSI
        self.current_rsi = self.calculate_rsi(candles, self.rsi_period)
    
    def determine_executor_actions(self):
        """
        只在 RSI 超卖时创建执行器
        """
        # RSI 检查
        if self.config.side == TradeType.BUY:
            if self.current_rsi > self.rsi_oversold:
                return []  # RSI 未超卖，不创建
        elif self.config.side == TradeType.SELL:
            if self.current_rsi < self.rsi_overbought:
                return []  # RSI 未超买，不创建
        
        # 调用父类方法
        return super().determine_executor_actions()
    
    def calculate_rsi(self, candles, period):
        """
        计算 RSI 指标
        """
        closes = [candle.close for candle in candles]
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return Decimal(str(rsi))
```

### 7.5.3 添加风险管理

```python
class SmartGridStrike(GridStrike):
    """
    智能 GridStrike：添加每日最大亏损限制
    """
    
    def __init__(self, config: GridStrikeConfig, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.daily_max_loss = Decimal("500")  # 每日最大亏损
        self.daily_pnl = Decimal("0")
        self.today_date = None
    
    def determine_executor_actions(self):
        """
        检查是否达到每日最大亏损
        """
        # 重置每日 PnL
        current_date = datetime.now().date()
        if self.today_date != current_date:
            self.today_date = current_date
            self.daily_pnl = Decimal("0")
        
        # 累计今日 PnL
        for executor in self.executors_info:
            if executor.is_closed_today():
                self.daily_pnl += executor.realized_pnl_quote
        
        # 检查是否达到最大亏损
        if self.daily_pnl <= -self.daily_max_loss:
            self.logger().warning(
                f"Daily max loss reached: {self.daily_pnl}. "
                "Stopping new executor creation."
            )
            return []  # 停止创建新执行器
        
        # 调用父类方法
        return super().determine_executor_actions()
```

## 7.6 本章小结

本章介绍了 GridStrike 的高级功能和扩展方法：

**Activation Bounds**：

- 延迟激活机制，节省资金
- 根据价格动态创建订单
- 推荐设置 1%-2%

**Keep Position**：

- 控制执行器关闭时是否平仓
- 适合有后续计划的场景
- 需要谨慎使用

**Dynamic Config Update**：

- 运行时动态调整参数
- 适应市场变化
- 提高策略灵活性

**Multi-Grid Strike**：

- 同时运行多个网格
- 分散风险，提高覆盖
- 支持双向网格

**自定义扩展**：

- 继承 GridStrike 实现自定义逻辑
- 添加技术指标过滤
- 增强风险管理

**开发建议**：

- 从简单扩展开始
- 充分测试后再实盘
- 保持代码清晰易读
- 记录参数调整日志

准备好了吗？下一章我们将学习 [最佳实践与注意事项](grid_strike_tutorial_08.md)，掌握实战中的关键技巧。

---

[返回索引](grid_strike_tutorial_index.md) | [上一章：代码实现深度解析](grid_strike_tutorial_06.md) | [下一章：最佳实践与注意事项](grid_strike_tutorial_08.md)

