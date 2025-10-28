# 第 4 章：快速开始使用指南

## 本章导航

- [返回索引](grid_strike_tutorial_index.md)
- [上一章：参数配置完全指南](grid_strike_tutorial_03.md)
- [下一章：使用示例](grid_strike_tutorial_05.md)

## 4.1 环境准备

### 4.1.1 Hummingbot 安装

GridStrike 策略需要运行在 Hummingbot 环境中。

**检查 Hummingbot 版本**：

```bash
# 进入 Hummingbot 目录
cd hummingbot

# 检查版本
./start

# 在 Hummingbot 命令行中
>>> version
Hummingbot version: 2.0.0+
```

**要求**：

- Hummingbot 版本 >= 2.0.0（支持 Strategy_v2 框架）
- Python 版本 >= 3.10
- 足够的系统资源（建议至少 2GB RAM）

### 4.1.2 交易所 API 配置

GridStrike 支持各大期货交易所，这里以 Binance 永续合约为例。

**步骤 1：获取 API 密钥**

1. 登录 Binance 账户
2. 进入 API 管理页面
3. 创建新的 API 密钥
4. 启用"期货交易"权限
5. 保存 API Key 和 Secret

**步骤 2：在 Hummingbot 中配置**

```bash
# 启动 Hummingbot
./start

# 配置交易所
>>> connect binance_perpetual

# 按提示输入
Enter your Binance Perpetual API key: [您的 API Key]
Enter your Binance Perpetual secret key: [您的 Secret]

# 确认连接
>>> balance
```

**安全提示**：

- 不要启用"提币"权限
- 建议绑定 IP 白名单
- 定期轮换 API 密钥
- 初次使用建议用测试网

### 4.1.3 验证 Strategy_v2 环境

**检查 GridStrike 控制器**：

```bash
# 在系统终端（非 Hummingbot 内）
cd hummingbot

# 检查文件是否存在
ls controllers/generic/grid_strike.py

# 应该能看到文件
controllers/generic/grid_strike.py
```

**检查依赖**：

```python
# 在 Python 环境中测试导入
python
>>> from controllers.generic.grid_strike import GridStrike, GridStrikeConfig
>>> print("GridStrike 导入成功！")
```

## 4.2 创建策略配置

### 4.2.1 使用配置文件（推荐）

Strategy_v2 支持使用 YAML 配置文件。

**步骤 1：创建配置目录**

```bash
cd hummingbot
mkdir -p conf/controllers/generic/
```

**步骤 2：创建配置文件**

创建文件 `conf/controllers/generic/grid_strike_wld.yml`：

```yaml
controller_name: grid_strike
controller_type: generic

# 账户配置
connector_name: binance_perpetual
trading_pair: WLD-USDT
leverage: 20
position_mode: HEDGE

# 网格边界
side: BUY
start_price: 2.00
end_price: 2.20
limit_price: 1.95

# 资金配置
total_amount_quote: 1000
min_spread_between_orders: 0.005  # 0.5%
min_order_amount_quote: 10

# 执行控制
max_open_orders: 5
max_orders_per_batch: 2
order_frequency: 5
activation_bounds: null
keep_position: false

# 风险管理
triple_barrier_config:
  take_profit: 0.003  # 0.3%
  stop_loss: 0.01     # 1%
  time_limit: 7200    # 2小时
  open_order_type: LIMIT_MAKER
  take_profit_order_type: LIMIT_MAKER
  stop_loss_order_type: MARKET
  time_limit_order_type: MARKET
```

### 4.2.2 使用 Python 脚本

创建文件 `scripts/grid_strike_wld.py`：

```python
from decimal import Decimal
from hummingbot.core.data_type.common import OrderType, PositionMode, TradeType
from hummingbot.strategy_v2.controllers import ControllerConfigBase
from hummingbot.strategy_v2.executors.position_executor.data_types import TripleBarrierConfig
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase


class GridStrikeWLD(ScriptStrategyBase):
    """
    GridStrike 策略示例 - WLD-USDT
    """
    
    # 导入 GridStrike 控制器
    markets = {"binance_perpetual": {"WLD-USDT"}}
    
    def __init__(self, connectors):
        super().__init__(connectors)
        
        # 配置 GridStrike
        from controllers.generic.grid_strike import GridStrikeConfig
        
        self.controller_config = GridStrikeConfig(
            controller_name="grid_strike",
            connector_name="binance_perpetual",
            trading_pair="WLD-USDT",
            
            # 账户配置
            leverage=20,
            position_mode=PositionMode.HEDGE,
            
            # 网格边界
            side=TradeType.BUY,
            start_price=Decimal("2.00"),
            end_price=Decimal("2.20"),
            limit_price=Decimal("1.95"),
            
            # 资金配置
            total_amount_quote=Decimal("1000"),
            min_spread_between_orders=Decimal("0.005"),
            min_order_amount_quote=Decimal("10"),
            
            # 执行控制
            max_open_orders=5,
            max_orders_per_batch=2,
            order_frequency=5,
            keep_position=False,
            
            # 风险管理
            triple_barrier_config=TripleBarrierConfig(
                take_profit=Decimal("0.003"),
                stop_loss=Decimal("0.01"),
                time_limit=7200,
                open_order_type=OrderType.LIMIT_MAKER,
                take_profit_order_type=OrderType.LIMIT_MAKER,
                stop_loss_order_type=OrderType.MARKET,
                time_limit_order_type=OrderType.MARKET
            )
        )
    
    def on_tick(self):
        """
        Strategy_v2 会自动运行控制器
        这里不需要额外逻辑
        """
        pass
```

## 4.3 启动策略

### 4.3.1 使用 V2 策略启动

Strategy_v2 有专门的启动命令。

**步骤 1：启动 Hummingbot**

```bash
./start
```

**步骤 2：导入策略**

```bash
# 如果使用配置文件
>>> import strategy_v2

# 如果使用 Python 脚本
>>> import scripts.grid_strike_wld
```

**步骤 3：启动策略**

```bash
>>> start --script scripts/grid_strike_wld.py
```

或者使用配置文件：

```bash
>>> start --config conf/controllers/generic/grid_strike_wld.yml
```

**步骤 4：确认启动**

```bash
# 查看状态
>>> status

# 应该看到类似输出
Grid Configuration:
Start: 2.0000 | End: 2.2000 | Side: BUY | Limit: 1.9500 | Mid Price: 2.1200
Max Orders: 5   | Inside bounds: 1

Grid Status: [executor_id] (RunnableStatus.RUNNING)
...
```

### 4.3.2 启动检查清单

启动策略前，请确认：

- [ ] 交易所 API 已正确配置
- [ ] 账户余额充足（至少 total_amount_quote + 保证金缓冲）
- [ ] 杠杆已设置（在交易所端）
- [ ] 仓位模式已设置（HEDGE/ONEWAY）
- [ ] 网格价格区间合理（当前价格在区间内）
- [ ] 风险参数已设置（止盈、止损）

## 4.4 状态监控

### 4.4.1 查看策略状态

**基本状态命令**：

```bash
>>> status

# 输出示例
┌────────────────────────────────────────────────────────────────────────────┐
│ Grid Configuration:                                                         │
│ Start: 2.0000 | End: 2.2000 | Side: BUY | Limit: 1.9500 | Mid: 2.1200     │
│ Max Orders: 5   | Inside bounds: 1                                         │
└────────────────────────────────────────────────────────────────────────────┘

┌ Grid Status: grid_executor_abc123 (RUNNING) ──────────────────────────────┐
│ Level Distribution    │ Order Statistics      │ Performance Metrics        │
│ NOT_ACTIVE: 2         │ Total: 15             │ Buy Vol: 2500.0000        │
│ OPEN_ORDER_PLACED: 3  │ Filled: 12            │ Sell Vol: 2400.0000       │
│ OPEN_ORDER_FILLED: 0  │ Failed: 1             │ R. PnL: 150.2500          │
│ CLOSE_ORDER_PLACED: 0 │ Canceled: 2           │ R. Fees: 15.0000          │
│ COMPLETE: 5           │                       │ P. PnL: 0.0000            │
│                       │                       │ Position: 0.0000          │
├──────────────────────────────────────────────────────────────────────────  │
│ Open Liquidity: 0.0000 │ Close Liquidity: 0.0000                          │
└────────────────────────────────────────────────────────────────────────────┘
```

**状态解读**：

1. **Grid Configuration**：网格配置摘要
   - `Start/End`：网格价格范围
   - `Side`：交易方向
   - `Mid`：当前市场中间价
   - `Inside bounds`：价格是否在区间内（1=是，0=否）

2. **Level Distribution**：层级状态分布
   - `NOT_ACTIVE`：未激活的层级
   - `OPEN_ORDER_PLACED`：开仓订单已下但未成交
   - `OPEN_ORDER_FILLED`：开仓订单已成交，持有仓位
   - `CLOSE_ORDER_PLACED`：平仓订单已下但未成交
   - `COMPLETE`：已完成的层级（已平仓）

3. **Order Statistics**：订单统计
   - `Total`：总订单数
   - `Filled`：成交订单数
   - `Failed`：失败订单数
   - `Canceled`：取消订单数

4. **Performance Metrics**：性能指标
   - `Buy Vol`：买入总金额
   - `Sell Vol`：卖出总金额
   - `R. PnL`：已实现盈亏
   - `R. Fees`：已支付手续费
   - `P. PnL`：持仓盈亏
   - `Position`：当前持仓金额

### 4.4.2 查看订单

**活跃订单**：

```bash
>>> orders

# 输出示例
Exchange     Pair       Side  Type   Price   Amount   Age
binance_p..  WLD-USDT  buy   limit  2.0200  98.5    00:02:15
binance_p..  WLD-USDT  buy   limit  2.0100  99.0    00:02:15
binance_p..  WLD-USDT  buy   limit  2.0000  100.0   00:02:15
```

**订单历史**：

```bash
>>> history

# 查看成交历史
```

### 4.4.3 查看持仓

```bash
>>> balance

# 输出示例
Exchange      Asset     Total    Available  Allocated
binance_p..   USDT      5000.0   4000.0     1000.0
binance_p..   WLD       150.5    0.0        150.5
```

### 4.4.4 查看执行器详情

```bash
>>> executors

# 查看所有活跃的执行器
Executor ID              Controller    Status      PnL      Position
grid_executor_abc123     grid_strike   RUNNING    +150.25   0.0 USDT
```

### 4.4.5 实时监控建议

建议每 5-15 分钟检查一次策略状态：

1. **价格是否在网格区间内**
2. **执行器是否正常运行**
3. **订单成交情况**
4. **盈亏变化**
5. **保证金余额是否充足**

## 4.5 调整策略参数

### 4.5.1 动态调整参数

GridStrike 支持在运行时调整部分参数（标记为 `is_updatable=True` 的参数）。

**可调整的参数**：

- `start_price`
- `end_price`
- `limit_price`
- `total_amount_quote`
- `min_spread_between_orders`
- `min_order_amount_quote`
- `max_open_orders`
- `max_orders_per_batch`
- `order_frequency`
- `activation_bounds`
- `keep_position`

**调整方法**：

```bash
# 方法1：使用 config 命令（如果支持）
>>> config start_price 2.05

# 方法2：修改配置文件后重载
# 编辑 conf/controllers/generic/grid_strike_wld.yml
# 然后
>>> reload_config
```

**注意**：

- 参数调整会在下一个控制周期生效
- 某些参数（如杠杆、交易对）不可动态调整
- 调整参数可能影响现有执行器

### 4.5.2 调整示例场景

**场景 1：价格上涨，调高网格区间**

```yaml
# 原配置
start_price: 2.00
end_price: 2.20

# 新配置（价格涨到 2.15）
start_price: 2.10
end_price: 2.30
```

**场景 2：波动率降低，减少订单数量**

```yaml
# 原配置
max_open_orders: 5

# 新配置
max_open_orders: 3
```

**场景 3：增加资金投入**

```yaml
# 原配置
total_amount_quote: 1000

# 新配置
total_amount_quote: 1500
```

## 4.6 停止策略

### 4.6.1 正常停止

**命令**：

```bash
>>> stop
```

**执行流程**：

1. 停止 Controller，不再创建新执行器
2. 等待现有执行器完成（或触发风险屏障）
3. 根据 `keep_position` 配置决定是否平仓
4. 取消所有未成交订单
5. 关闭策略

**预期时间**：

- 如果 `keep_position=False`：立即平仓，几秒内完成
- 如果 `keep_position=True`：等待执行器自然结束，可能需要几分钟到几小时

### 4.6.2 强制停止

如果需要立即停止：

```bash
>>> exit --force

# 或者直接关闭 Hummingbot
>>> exit
```

**警告**：

- 强制停止可能导致订单无法取消
- 可能留有未平仓的仓位
- 建议先用正常停止，实在需要再强制

### 4.6.3 紧急平仓

如果策略出现问题，需要紧急平仓所有仓位：

```bash
# 方法1：在 Hummingbot 中
>>> stop  # 先停止策略

# 方法2：直接在交易所平仓
# 登录交易所 Web 页面或 APP
# 找到持仓，一键平仓
```

## 4.7 常见启动问题

### 4.7.1 "Insufficient balance" 错误

**原因**：账户余额不足以支持网格订单。

**解决**：

1. 检查账户余额
   ```bash
   >>> balance
   ```

2. 计算所需资金
   ```python
   # 保证金需求
   required_margin = total_amount_quote / leverage
   
   # 示例
   total_amount_quote = 1000 USDT
   leverage = 20
   required_margin = 1000 / 20 = 50 USDT
   
   # 建议余额 = 保证金 × 3（缓冲）
   recommended_balance = 50 × 3 = 150 USDT
   ```

3. 充值或降低 `total_amount_quote`

### 4.7.2 "Price out of bounds" 警告

**原因**：当前价格不在网格区间内。

**解决**：

1. 检查当前价格
   ```bash
   >>> ticker WLD-USDT
   Current price: 2.25 USDT
   ```

2. 调整网格区间
   ```yaml
   # 原配置
   start_price: 2.00
   end_price: 2.20  # 当前价格 2.25 超出上限
   
   # 新配置
   start_price: 2.10
   end_price: 2.30
   ```

### 4.7.3 "Executor creation failed" 错误

**原因**：执行器创建失败，可能是参数错误或系统问题。

**解决**：

1. 检查日志
   ```bash
   >>> logs
   ```

2. 验证参数
   - `start_price < end_price`
   - `total_amount_quote > 0`
   - `min_spread_between_orders > 0`
   - `triple_barrier_config` 配置正确

3. 重启策略
   ```bash
   >>> stop
   >>> start --script scripts/grid_strike_wld.py
   ```

### 4.7.4 订单被拒绝

**原因**：订单不符合交易所规则。

**解决**：

1. 检查交易规则
   ```python
   # 最小下单量
   # 最小价格增量
   # 最大杠杆
   ```

2. 调整参数
   ```yaml
   # 增加最小订单金额
   min_order_amount_quote: 15  # 从 10 增加到 15
   
   # 调整价格精度
   # 确保 start_price、end_price 符合价格步长
   ```

## 4.8 本章小结

本章介绍了 GridStrike 策略的部署和运行流程：

**环境准备**：

1. 安装 Hummingbot >= 2.0.0
2. 配置交易所 API
3. 验证 Strategy_v2 环境

**创建配置**：

1. 使用 YAML 配置文件（推荐）
2. 或使用 Python 脚本

**启动策略**：

1. 使用 `start` 命令启动
2. 检查启动状态
3. 确认执行器运行

**监控运行**：

1. 使用 `status` 查看整体状态
2. 使用 `orders` 查看订单
3. 使用 `balance` 查看余额
4. 定期检查和调整

**停止策略**：

1. 正常停止：`stop`
2. 强制停止：`exit --force`
3. 紧急平仓：交易所操作

**常见问题**：

- 余额不足：充值或降低资金
- 价格超出：调整网格区间
- 订单被拒：检查交易规则

准备好了吗？下一章我们将学习 [使用示例](grid_strike_tutorial_05.md)，提供保守型、均衡型、激进型三种完整配置方案。

---

[返回索引](grid_strike_tutorial_index.md) | [上一章：参数配置完全指南](grid_strike_tutorial_03.md) | [下一章：使用示例](grid_strike_tutorial_05.md)

