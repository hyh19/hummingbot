# 第 7 章：高级功能与扩展

## 本章导航

- [返回索引](fixed_grid_tutorial_index.md)
- [上一章：代码实现深度解析](fixed_grid_tutorial_06.md)
- [下一章：最佳实践与注意事项](fixed_grid_tutorial_08.md)

## 7.1 网格间距缩放深入

### 7.1.1 缩放因子的数学原理

回顾 `spread_scale_factor` 的计算公式：

```python
minimum_spread = (ceiling - floor) / (1 + 2 * sum([pow(factor, n) for n in range(1, m)]))
```

其中 `m = n_levels / 2`

**等比数列求和公式**：

```text
当 factor = s，需要计算：
S = s¹ + s² + s³ + ... + s^(m-1)

等比数列求和：
S = s × (1 - s^(m-1)) / (1 - s)  当 s ≠ 1

分母 = 1 + 2S
```

**不同缩放因子的效果**：

| 缩放因子 | 特点 | 适用场景 |
|---------|------|---------|
| 1.0 | 等距分布 | 标准配置，适合大多数情况 |
| 1.1-1.2 | 轻度缩放 | 价格主要在中间波动 |
| 1.2-1.4 | 中度缩放 | 明显的中心聚集 |
| 1.4+ | 强度缩放 | 极度集中在中心 |
| < 1.0 | 反向缩放 | 两端密集（少用） |

### 7.1.2 自定义缩放曲线

**目标**：实现非对称缩放，例如下方密集、上方稀疏。

**修改思路**：

在 `__init__` 方法中，分别设置上下半部分的缩放因子：

```python
class FixedGridCustom(FixedGrid):
    def __init__(self, connectors):
        # 设置不同的缩放因子
        self.lower_spread_scale = Decimal(1.3)  # 下方密集
        self.upper_spread_scale = Decimal(1.1)  # 上方稀疏
        
        # 调用父类初始化（需要修改）
        super().__init__(connectors)
        
        # 重新计算价格层级
        self._recalculate_price_levels()
    
    def _recalculate_price_levels(self):
        """自定义价格层级计算"""
        mid_level = int(self.n_levels / 2)
        mid_price = (self.grid_price_ceiling + self.grid_price_floor) / 2
        
        # 计算下半部分
        lower_range = mid_price - self.grid_price_floor
        lower_sum = sum([pow(self.lower_spread_scale, n) 
                        for n in range(mid_level)])
        lower_unit = lower_range / lower_sum
        
        # 计算上半部分
        upper_range = self.grid_price_ceiling - mid_price
        upper_sum = sum([pow(self.upper_spread_scale, n) 
                        for n in range(mid_level)])
        upper_unit = upper_range / upper_sum
        
        # 重建价格层级...
```

### 7.1.3 动态调整网格间距

**场景**：根据实时波动率动态调整网格密度。

**实现思路**：

```python
import numpy as np

class DynamicGridSpacing(FixedGrid):
    def __init__(self, connectors):
        self.price_history = []
        self.volatility_window = 100  # 100 个周期
        super().__init__(connectors)
    
    def on_tick(self):
        # 记录价格历史
        current_price = self.connectors[self.exchange].get_price_by_type(
            self.trading_pair, self.price_source)
        self.price_history.append(float(current_price))
        
        # 保持固定窗口大小
        if len(self.price_history) > self.volatility_window:
            self.price_history.pop(0)
        
        # 计算波动率
        if len(self.price_history) >= self.volatility_window:
            returns = np.diff(self.price_history) / self.price_history[:-1]
            volatility = np.std(returns)
            
            # 根据波动率调整缩放因子
            if volatility > 0.05:  # 高波动
                self.spread_scale_factor = Decimal(1.3)
            elif volatility < 0.02:  # 低波动
                self.spread_scale_factor = Decimal(1.1)
            else:  # 中等波动
                self.spread_scale_factor = Decimal(1.2)
            
            # 重新计算网格（每隔一段时间）
            if self.should_recalculate_grid():
                self._recalculate_grid()
        
        # 调用父类逻辑
        super().on_tick()
```

## 7.2 订单数量缩放应用

### 7.2.1 金字塔式加仓策略

**理念**：价格越极端，订单越大，实现"越跌越买、越涨越卖"。

**实现**：使用 `amount_scale_factor > 1.0`

```python
# 配置示例
amount_scale_factor = Decimal(1.3)
order_amount = Decimal(10.0)

# 效果（8 层网格）：
# 第 1 层（最低）：10 × 1.3³ = 21.97（大单）
# 第 2 层：10 × 1.3² = 16.90
# 第 3 层：10 × 1.3¹ = 13.00
# 第 4 层：10 × 1.3⁰ = 10.00（中间）
# 第 5 层：10 × 1.3⁰ = 10.00
# 第 6 层：10 × 1.3¹ = 13.00
# 第 7 层：10 × 1.3² = 16.90
# 第 8 层（最高）：10 × 1.3³ = 21.97（大单）
```

**优点**：

- 极端价格获得更多仓位
- 平均成本更优
- 反弹时利润更大

**风险**：

- 需要更多资金
- 极端价格风险更大
- 可能长时间无法成交

### 7.2.2 反向缩放：中间加重

**场景**：确信价格会在中间区域频繁波动。

**实现思路**：

```python
class CenterWeightedGrid(FixedGrid):
    def __init__(self, connectors):
        super().__init__(connectors)
        self._recalculate_amount_levels()
    
    def _recalculate_amount_levels(self):
        """重新计算订单数量：中间大，两端小"""
        mid = int(self.n_levels / 2)
        self.order_amount_levels = []
        
        for i in range(self.n_levels):
            # 距离中心的距离
            distance_from_center = abs(i - mid)
            # 距离越远，数量越小
            factor = 1.0 / (1.0 + distance_from_center * 0.3)
            amount = self.order_amount * Decimal(str(factor))
            self.order_amount_levels.append(amount)
```

**效果**（8 层，基础 10）：

```text
第 0 层：10 / (1 + 4×0.3) = 4.5（小）
第 1 层：10 / (1 + 3×0.3) = 5.3
第 2 层：10 / (1 + 2×0.3) = 6.3
第 3 层：10 / (1 + 1×0.3) = 7.7
第 4 层：10 / (1 + 0×0.3) = 10.0（中心，最大）
第 5 层：10 / (1 + 1×0.3) = 7.7
第 6 层：10 / (1 + 2×0.3) = 6.3
第 7 层：10 / (1 + 3×0.3) = 5.3
```

### 7.2.3 资金利用率优化

**问题**：固定数量导致部分资金闲置。

**解决方案**：根据剩余资金动态调整订单数量。

```python
class DynamicAmountGrid(FixedGrid):
    def create_grid_proposal(self):
        """动态调整订单数量以提高资金利用率"""
        market, trading_pair, base_asset, quote_asset = \
            self.get_market_trading_pair_tuples()[0]
        
        available_base = market.get_available_balance(base_asset)
        available_quote = market.get_available_balance(quote_asset)
        
        buys = []
        sells = []
        
        # 计算卖单（使用可用基础资产）
        num_sell_levels = self.n_levels - self.current_level - 1
        if num_sell_levels > 0 and available_base > 0:
            amount_per_sell = available_base / Decimal(str(num_sell_levels))
            
            for i in range(self.current_level + 1, self.n_levels):
                price = self.price_levels[i]
                # 使用动态数量
                size = min(amount_per_sell, self.order_amount_levels[i])
                if size > 0:
                    sell_order = OrderCandidate(
                        trading_pair=self.trading_pair,
                        is_maker=True,
                        order_type=OrderType.LIMIT,
                        order_side=TradeType.SELL,
                        amount=size,
                        price=price
                    )
                    sells.append(sell_order)
        
        # 类似处理买单...
        
        return buys + sells
```

## 7.3 自动库存再平衡优化

### 7.3.1 智能再平衡时机

**问题**：库存轻微偏差就触发再平衡，成本高。

**优化**：设置偏差阈值，只在偏差较大时才再平衡。

```python
class SmartRebalance(FixedGrid):
    def __init__(self, connectors):
        super().__init__(connectors)
        self.rebalance_threshold = Decimal(0.1)  # 10% 偏差阈值
    
    def on_tick(self):
        # 计算库存偏差
        market, trading_pair, base_asset, quote_asset = \
            self.get_market_trading_pair_tuples()[0]
        
        base_balance = Decimal(str(market.get_balance(base_asset)))
        quote_balance = Decimal(str(market.get_balance(quote_asset)))
        
        required_base = Decimal(str(self.base_inv_levels[self.current_level]))
        required_quote = Decimal(str(
            self.quote_inv_levels_current_price[self.current_level]))
        
        # 计算偏差比例
        if required_base > 0:
            base_deviation = abs(base_balance - required_base) / required_base
        else:
            base_deviation = Decimal(0)
        
        if required_quote > 0:
            quote_deviation = abs(quote_balance - required_quote) / required_quote
        else:
            quote_deviation = Decimal(0)
        
        # 只有偏差超过阈值才触发再平衡
        if base_deviation > self.rebalance_threshold or \
           quote_deviation > self.rebalance_threshold:
            self.inv_correct = False
        else:
            self.inv_correct = True
        
        # 继续执行原逻辑
        super().on_tick()
```

### 7.3.2 分批再平衡

**问题**：一次性大额再平衡影响市场价格。

**优化**：将再平衡订单拆分为多个小单。

```python
class GradualRebalance(FixedGrid):
    def __init__(self, connectors):
        super().__init__(connectors)
        self.rebalance_splits = 3  # 拆分为 3 单
        self.current_rebalance_step = 0
    
    def create_rebalance_proposal(self):
        """分批创建再平衡订单"""
        # 计算每批的数量
        size_per_step = self.rebalance_order_amount / Decimal(
            str(self.rebalance_splits))
        
        buys = []
        sells = []
        
        if self.rebalance_order_buy:
            # 只创建当前批次的订单
            ref_price = self.connectors[self.exchange].get_price_by_type(
                self.trading_pair, self.price_source)
            
            # 每批价格略有不同，避免集中
            price_adjustment = Decimal(str(
                1 - 0.001 * self.current_rebalance_step))
            price = ref_price * (Decimal("100") - self.rebalance_order_spread) \
                    / Decimal("100") * price_adjustment
            
            buy_order = OrderCandidate(
                trading_pair=self.trading_pair,
                is_maker=True,
                order_type=OrderType.LIMIT,
                order_side=TradeType.BUY,
                amount=size_per_step,
                price=price
            )
            buys.append(buy_order)
            
            # 更新步骤计数
            self.current_rebalance_step += 1
            if self.current_rebalance_step >= self.rebalance_splits:
                self.current_rebalance_step = 0
        
        # 类似处理卖单...
        
        return buys + sells
```

### 7.3.3 外部资金注入检测

**场景**：用户手动向账户充值，策略应自动检测并调整。

```python
class ExternalFundDetection(FixedGrid):
    def __init__(self, connectors):
        super().__init__(connectors)
        self.last_total_balance = None
    
    def on_tick(self):
        # 获取当前总资产
        market, trading_pair, base_asset, quote_asset = \
            self.get_market_trading_pair_tuples()[0]
        
        current_price = self.connectors[self.exchange].get_price_by_type(
            self.trading_pair, self.price_source)
        
        base_balance = float(market.get_balance(base_asset))
        quote_balance = float(market.get_balance(quote_asset))
        total_value = base_balance * float(current_price) + quote_balance
        
        # 首次记录
        if self.last_total_balance is None:
            self.last_total_balance = total_value
        else:
            # 检测资金注入（增加超过 5%）
            if total_value > self.last_total_balance * 1.05:
                msg = (f"External funds detected. Total value increased from "
                      f"{self.last_total_balance:.2f} to {total_value:.2f}")
                self.log_with_clock(logging.INFO, msg)
                self.notify_hb_app_with_timestamp(msg)
                
                # 触发网格重建
                self._rebuild_grid_with_new_funds()
                
                # 更新基准
                self.last_total_balance = total_value
        
        super().on_tick()
    
    def _rebuild_grid_with_new_funds(self):
        """根据新资金重建网格"""
        # 取消所有订单
        self.cancel_active_orders()
        
        # 可以选择增加 order_amount 或增加层级
        # 这里简单地增加订单数量
        self.order_amount = self.order_amount * Decimal(1.2)
        
        # 重新计算订单数量层级
        for i in range(len(self.order_amount_levels)):
            self.order_amount_levels[i] = self.order_amount_levels[i] * Decimal(1.2)
        
        # 下个 tick 会自动创建新订单
```

## 7.4 高级订单管理

### 7.4.1 订单分层执行

**场景**：大额订单拆分为多个小单，减少市场冲击。

```python
class LayeredOrders(FixedGrid):
    def __init__(self, connectors):
        super().__init__(connectors)
        self.order_split_count = 3  # 每层拆分为 3 单
    
    def create_grid_proposal(self):
        """创建分层订单"""
        buys = []
        sells = []
        
        # 创建买单
        for i in range(self.current_level):
            price = self.price_levels[i]
            total_size = self.order_amount_levels[i]
            
            # 拆分为多个小单
            size_per_order = total_size / Decimal(str(self.order_split_count))
            
            for j in range(self.order_split_count):
                # 每个小单价格略有差异
                price_offset = Decimal(str(0.0001 * j))
                adjusted_price = price * (Decimal(1) - price_offset)
                
                if size_per_order > 0:
                    buy_order = OrderCandidate(
                        trading_pair=self.trading_pair,
                        is_maker=True,
                        order_type=OrderType.LIMIT,
                        order_side=TradeType.BUY,
                        amount=size_per_order,
                        price=adjusted_price
                    )
                    buys.append(buy_order)
        
        # 类似处理卖单...
        
        return buys + sells
```

### 7.4.2 订单有效期管理

**场景**：防止订单长时间未成交占用资金。

```python
from datetime import datetime, timedelta

class OrderExpiration(FixedGrid):
    def __init__(self, connectors):
        super().__init__(connectors)
        self.order_expiration_time = 3600  # 1 小时
        self.order_creation_times = {}
    
    def execute_orders_proposal(self, proposal):
        """执行订单并记录时间"""
        for order in proposal:
            order_id = self.place_order(self.exchange, order)
            # 记录订单创建时间
            self.order_creation_times[order_id] = datetime.now()
    
    def on_tick(self):
        """检查并取消过期订单"""
        current_time = datetime.now()
        expired_orders = []
        
        for order in self.get_active_orders(connector_name=self.exchange):
            order_id = order.client_order_id
            if order_id in self.order_creation_times:
                creation_time = self.order_creation_times[order_id]
                age = (current_time - creation_time).total_seconds()
                
                # 订单超过有效期
                if age > self.order_expiration_time:
                    expired_orders.append(order_id)
        
        # 取消过期订单
        for order_id in expired_orders:
            self.cancel(self.exchange, self.trading_pair, order_id)
            del self.order_creation_times[order_id]
            
            msg = f"Cancelled expired order: {order_id}"
            self.log_with_clock(logging.INFO, msg)
        
        super().on_tick()
```

### 7.4.3 防止订单堆积

**问题**：市场价格长时间停留在某个层级，订单重复创建。

**解决方案**：检测订单是否已存在。

```python
class NoDuplicateOrders(FixedGrid):
    def create_grid_proposal(self):
        """创建网格订单，避免重复"""
        existing_orders = self.get_active_orders(connector_name=self.exchange)
        
        # 记录已存在的订单价格和方向
        existing_positions = set()
        for order in existing_orders:
            key = (order.order_side, float(order.price))
            existing_positions.add(key)
        
        buys = []
        sells = []
        
        # 创建买单（检查是否已存在）
        for i in range(self.current_level):
            price = self.price_levels[i]
            size = self.order_amount_levels[i]
            
            key = (TradeType.BUY, float(price))
            if key not in existing_positions and size > 0:
                buy_order = OrderCandidate(
                    trading_pair=self.trading_pair,
                    is_maker=True,
                    order_type=OrderType.LIMIT,
                    order_side=TradeType.BUY,
                    amount=size,
                    price=price
                )
                buys.append(buy_order)
        
        # 类似处理卖单...
        
        return buys + sells
```

## 7.5 性能监控与日志增强

### 7.5.1 详细性能统计

```python
from collections import deque

class PerformanceTracking(FixedGrid):
    def __init__(self, connectors):
        super().__init__(connectors)
        self.trade_history = deque(maxlen=100)  # 保留最近 100 笔
        self.performance_stats = {
            'total_trades': 0,
            'total_profit': Decimal(0),
            'total_fees': Decimal(0),
            'win_count': 0,
            'loss_count': 0
        }
    
    def did_fill_order(self, event):
        """记录每笔交易"""
        trade_record = {
            'timestamp': self.current_timestamp,
            'side': event.trade_type.name,
            'price': event.price,
            'amount': event.amount,
            'fee': event.trade_fee
        }
        self.trade_history.append(trade_record)
        
        # 更新统计
        self.performance_stats['total_trades'] += 1
        self.performance_stats['total_fees'] += Decimal(str(event.trade_fee.flat_fees[0][1]))
        
        super().did_fill_order(event)
    
    def calculate_performance_metrics(self):
        """计算性能指标"""
        if len(self.trade_history) < 2:
            return None
        
        # 计算往返盈利
        buys = [t for t in self.trade_history if t['side'] == 'BUY']
        sells = [t for t in self.trade_history if t['side'] == 'SELL']
        
        round_trips = min(len(buys), len(sells))
        total_profit = Decimal(0)
        
        for i in range(round_trips):
            buy_cost = Decimal(str(buys[i]['price'])) * Decimal(str(buys[i]['amount']))
            sell_revenue = Decimal(str(sells[i]['price'])) * Decimal(str(sells[i]['amount']))
            profit = sell_revenue - buy_cost
            total_profit += profit
            
            if profit > 0:
                self.performance_stats['win_count'] += 1
            else:
                self.performance_stats['loss_count'] += 1
        
        self.performance_stats['total_profit'] = total_profit
        
        return self.performance_stats
    
    def format_status(self):
        """增强状态输出"""
        base_status = super().format_status()
        
        # 添加性能统计
        stats = self.calculate_performance_metrics()
        if stats:
            perf_lines = [
                "",
                "  Performance:",
                f"    Total Trades: {stats['total_trades']}",
                f"    Total Profit: {stats['total_profit']:.2f} USDT",
                f"    Total Fees: {stats['total_fees']:.2f} USDT",
                f"    Win Rate: {stats['win_count']}/{stats['total_trades']} "
                f"({stats['win_count']/stats['total_trades']*100:.1f}%)",
                f"    Net Profit: {stats['total_profit'] - stats['total_fees']:.2f} USDT"
            ]
            base_status += "\n" + "\n".join(perf_lines)
        
        return base_status
```

### 7.5.2 实时告警系统

```python
class AlertSystem(FixedGrid):
    def __init__(self, connectors):
        super().__init__(connectors)
        self.alert_conditions = {
            'price_near_ceiling': False,
            'price_near_floor': False,
            'low_balance': False,
            'high_loss': False
        }
    
    def on_tick(self):
        """检查告警条件"""
        price = self.connectors[self.exchange].get_price_by_type(
            self.trading_pair, self.price_source)
        
        # 价格接近上限（距离小于 5%）
        distance_to_ceiling = (self.grid_price_ceiling - price) / price
        if distance_to_ceiling < Decimal(0.05):
            if not self.alert_conditions['price_near_ceiling']:
                self._send_alert("WARNING: Price approaching grid ceiling!")
                self.alert_conditions['price_near_ceiling'] = True
        else:
            self.alert_conditions['price_near_ceiling'] = False
        
        # 价格接近下限
        distance_to_floor = (price - self.grid_price_floor) / price
        if distance_to_floor < Decimal(0.05):
            if not self.alert_conditions['price_near_floor']:
                self._send_alert("WARNING: Price approaching grid floor!")
                self.alert_conditions['price_near_floor'] = True
        else:
            self.alert_conditions['price_near_floor'] = False
        
        # 检查余额（低于初始的 80%）
        # ... 其他告警条件
        
        super().on_tick()
    
    def _send_alert(self, message):
        """发送告警（可扩展为邮件、短信等）"""
        self.log_with_clock(logging.WARNING, message)
        self.notify_hb_app_with_timestamp(f"🚨 ALERT: {message}")
        
        # 可以在这里集成其他通知方式
        # send_email(message)
        # send_telegram(message)
```

## 7.6 本章小结

本章介绍了 Fixed Grid 策略的高级功能和扩展方法：

**核心扩展方向**：

1. **网格优化**：动态间距、非对称缩放、波动率自适应
2. **订单优化**：数量缩放、分层执行、有效期管理
3. **库存管理**：智能再平衡、分批执行、外部资金检测
4. **性能监控**：详细统计、实时告警、盈亏跟踪

**扩展原则**：

- 继承基础类，重写关键方法
- 保持核心逻辑不变，增强细节功能
- 充分测试再投入实盘
- 记录日志便于分析优化

**实践建议**：

- 从简单扩展开始（如调整阈值）
- 逐步尝试复杂功能（如动态调整）
- 小额资金测试新功能
- 对比扩展前后的性能

下一章我们将学习 [最佳实践与注意事项](fixed_grid_tutorial_08.md)，了解如何在实际运行中优化策略表现。

---

[返回索引](fixed_grid_tutorial_index.md) | [上一章：代码实现深度解析](fixed_grid_tutorial_06.md) | [下一章：最佳实践与注意事项](fixed_grid_tutorial_08.md)

