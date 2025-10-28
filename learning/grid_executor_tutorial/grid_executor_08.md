# 第 8 章：实战应用示例

## 8.1 基础网格策略

### 8.1.1 简单的现货网格

```python
import time
from decimal import Decimal
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.strategy_v2.executors.grid_executor.data_types import GridExecutorConfig
from hummingbot.strategy_v2.executors.position_executor.data_types import TripleBarrierConfig
from hummingbot.strategy_v2.executors.executor_orchestrator import ExecutorOrchestrator


class SimpleSpotGrid(ScriptStrategyBase):
    """
    简单的现货网格策略

    特点：
    - 固定价格区间
    - 均匀网格分布
    - 基础风险管理
    """

    # 策略参数
    connector_name = "binance"
    trading_pair = "BTC-USDT"

    # 网格参数
    grid_start_price = Decimal("40000")
    grid_end_price = Decimal("42000")
    total_amount = Decimal("1000")  # 1000 USDT

    # 风险参数
    stop_loss = Decimal("0.05")      # 5% 止损
    take_profit = Decimal("0.01")    # 1% 层级止盈
    time_limit = 86400               # 24 小时

    def __init__(self, connectors):
        super().__init__(connectors)

        # 创建 Executor Orchestrator
        self.executor_orchestrator = ExecutorOrchestrator(
            strategy=self,
            executors_update_interval=1.0,
        )

        self.grid_created = False

    def on_tick(self):
        """
        每个 tick 执行（通常 1 秒）
        """
        # 只创建一次网格
        if not self.grid_created:
            self.create_grid_executor()
            self.grid_created = True

        # 显示状态
        if self.executor_orchestrator.active_executors:
            self.display_status()

    def create_grid_executor(self):
        """
        创建 Grid Executor
        """
        # Triple Barrier 配置
        triple_barrier = TripleBarrierConfig(
            stop_loss=self.stop_loss,
            take_profit=self.take_profit,
            time_limit=self.time_limit,
            open_order_type=OrderType.LIMIT_MAKER,
            take_profit_order_type=OrderType.LIMIT_MAKER,
        )

        # Grid Executor 配置
        config = GridExecutorConfig(
            timestamp=time.time(),
            connector_name=self.connector_name,
            trading_pair=self.trading_pair,
            side=TradeType.BUY,
            start_price=self.grid_start_price,
            end_price=self.grid_end_price,
            limit_price=self.grid_start_price * Decimal("0.95"),  # 5% 下方保护
            total_amount_quote=self.total_amount,
            min_spread_between_orders=Decimal("0.002"),  # 0.2%
            min_order_amount_quote=Decimal("10"),
            max_open_orders=5,
            leverage=1,  # 现货不使用杠杆
            triple_barrier_config=triple_barrier,
        )

        # 创建 Executor
        from hummingbot.strategy_v2.executors.grid_executor.grid_executor import GridExecutor

        executor = GridExecutor(
            strategy=self,
            config=config,
            update_interval=1.0,
        )

        # 添加到 Orchestrator
        self.executor_orchestrator.active_executors[config.id] = executor

        # 启动 Executor
        executor.start()

        self.logger().info(f"Grid Executor created: {config.id}")

    def display_status(self):
        """
        显示策略状态
        """
        for executor_id, executor in self.executor_orchestrator.active_executors.items():
            info = executor.get_custom_info()

            self.logger().info(
                f"Grid Status - "
                f"Net PnL: {executor.get_net_pnl_quote():.2f} USDT "
                f"({executor.get_net_pnl_pct():.2%}), "
                f"Position: {info['position_size_quote']:.2f} USDT, "
                f"Active Levels: {len(info['levels_by_state'].get('OPEN_ORDER_PLACED', []))} open, "
                f"{len(info['levels_by_state'].get('CLOSE_ORDER_PLACED', []))} close"
            )
```

### 8.1.2 运行策略

```bash
# 在 Hummingbot 中运行
start --script simple_spot_grid.py
```

## 8.2 永续合约网格策略

### 8.2.1 高杠杆网格

```python
import time
from decimal import Decimal
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.strategy.script_strategy_base import ScriptStrategyBase
from hummingbot.strategy_v2.executors.grid_executor.data_types import GridExecutorConfig
from hummingbot.strategy_v2.executors.position_executor.data_types import (
    TripleBarrierConfig,
    TrailingStop
)
from hummingbot.strategy_v2.executors.executor_orchestrator import ExecutorOrchestrator


class PerpetualGrid(ScriptStrategyBase):
    """
    永续合约网格策略

    特点：
    - 使用杠杆提高资金效率
    - 追踪止损保护利润
    - 动态激活范围
    """

    # 交易所配置
    connector_name = "binance_perpetual"
    trading_pair = "BTC-USDT"

    # 网格参数
    grid_start_price = Decimal("40000")
    grid_end_price = Decimal("41000")
    total_amount = Decimal("500")  # 500 USDT 保证金
    leverage = 10                  # 10 倍杠杆

    # 执行参数
    max_open_orders = 10
    activation_bounds = Decimal("0.01")  # 1% 激活范围

    def __init__(self, connectors):
        super().__init__(connectors)
        self.executor_orchestrator = ExecutorOrchestrator(
            strategy=self,
            executors_update_interval=1.0,
        )
        self.grid_created = False

    def on_tick(self):
        if not self.grid_created:
            self.create_perpetual_grid()
            self.grid_created = True

    def create_perpetual_grid(self):
        """
        创建永续合约网格
        """
        # 配置追踪止损
        trailing_stop = TrailingStop(
            activation_price=Decimal("0.03"),  # 3% 激活
            trailing_delta=Decimal("0.01"),    # 1% 回撤触发
        )

        # Triple Barrier 配置
        triple_barrier = TripleBarrierConfig(
            stop_loss=Decimal("0.03"),           # 3% 止损
            take_profit=Decimal("0.005"),        # 0.5% 层级止盈
            trailing_stop=trailing_stop,
            open_order_type=OrderType.LIMIT_MAKER,
            take_profit_order_type=OrderType.LIMIT_MAKER,
        )

        # Grid Executor 配置
        config = GridExecutorConfig(
            timestamp=time.time(),
            connector_name=self.connector_name,
            trading_pair=self.trading_pair,
            side=TradeType.BUY,
            start_price=self.grid_start_price,
            end_price=self.grid_end_price,
            limit_price=self.grid_start_price * Decimal("0.97"),  # 3% 下方保护
            total_amount_quote=self.total_amount,
            min_spread_between_orders=Decimal("0.001"),  # 0.1%
            min_order_amount_quote=Decimal("20"),
            max_open_orders=self.max_open_orders,
            activation_bounds=self.activation_bounds,
            leverage=self.leverage,
            triple_barrier_config=triple_barrier,
        )

        # 创建并启动 Executor
        from hummingbot.strategy_v2.executors.grid_executor.grid_executor import GridExecutor

        executor = GridExecutor(strategy=self, config=config, update_interval=1.0)
        self.executor_orchestrator.active_executors[config.id] = executor
        executor.start()

        self.logger().info(
            f"Perpetual Grid created with {self.leverage}x leverage, "
            f"effective capital: {self.total_amount * self.leverage} USDT"
        )
```

## 8.3 与 Controller 集成

### 8.3.1 基础 Grid Controller

```python
import time
from decimal import Decimal
from typing import List
from hummingbot.core.data_type.common import OrderType, TradeType
from hummingbot.strategy_v2.controllers.controller_base import ControllerBase, ControllerConfigBase
from hummingbot.strategy_v2.executors.grid_executor.data_types import GridExecutorConfig
from hummingbot.strategy_v2.executors.position_executor.data_types import TripleBarrierConfig
from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, StopExecutorAction
from pydantic import Field


class BasicGridControllerConfig(ControllerConfigBase):
    """
    基础网格 Controller 配置
    """
    controller_type: str = "basic_grid"

    connector_name: str = Field(default="binance_perpetual")
    trading_pair: str = Field(default="BTC-USDT")

    # 网格参数
    grid_range_pct: Decimal = Field(default=Decimal("0.02"))  # 2% 区间
    total_amount_quote: Decimal = Field(default=Decimal("1000"))

    # 风险参数
    stop_loss: Decimal = Field(default=Decimal("0.05"))
    take_profit: Decimal = Field(default=Decimal("0.01"))

    leverage: int = Field(default=10)


class BasicGridController(ControllerBase):
    """
    基础网格 Controller

    功能：
    - 监控市场价格
    - 在价格区间内创建网格
    - 管理网格生命周期
    """

    def __init__(self, config: BasicGridControllerConfig, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.config = config

    async def update_processed_data(self):
        """
        更新市场数据
        """
        # 获取市价
        self.mid_price = self.market_data_provider.get_price_by_type(
            self.config.connector_name,
            self.config.trading_pair,
            PriceType.MidPrice
        )

    def determine_executor_actions(self) -> List:
        """
        决定是否创建或停止 Executor
        """
        actions = []

        # 如果没有活跃的 Executor，创建一个
        if len(self.executors_info) == 0:
            actions.append(self.create_grid_executor())
        else:
            # 检查现有 Executor 状态
            for executor_id, executor_info in self.executors_info.items():
                if executor_info.is_done:
                    # 如果 Executor 完成，创建新的
                    actions.append(self.create_grid_executor())

        return actions

    def create_grid_executor(self) -> CreateExecutorAction:
        """
        创建 Grid Executor
        """
        # 计算网格边界
        start_price = self.mid_price * (1 - self.config.grid_range_pct / 2)
        end_price = self.mid_price * (1 + self.config.grid_range_pct / 2)
        limit_price = start_price * Decimal("0.95")

        # Triple Barrier 配置
        triple_barrier = TripleBarrierConfig(
            stop_loss=self.config.stop_loss,
            take_profit=self.config.take_profit,
            open_order_type=OrderType.LIMIT_MAKER,
            take_profit_order_type=OrderType.LIMIT_MAKER,
        )

        # Grid Executor 配置
        config = GridExecutorConfig(
            timestamp=time.time(),
            controller_id=self.config.id,
            connector_name=self.config.connector_name,
            trading_pair=self.config.trading_pair,
            side=TradeType.BUY,
            start_price=start_price,
            end_price=end_price,
            limit_price=limit_price,
            total_amount_quote=self.config.total_amount_quote,
            leverage=self.config.leverage,
            triple_barrier_config=triple_barrier,
        )

        return CreateExecutorAction(
            controller_id=self.config.id,
            executor_config=config
        )
```

### 8.3.2 使用 Controller 的策略

```python
from hummingbot.strategy_v2.strategy_v2_base import StrategyV2Base


class GridControllerStrategy(StrategyV2Base):
    """
    使用 Controller 的网格策略
    """

    def __init__(self, connectors):
        # Controller 配置
        controller_config = BasicGridControllerConfig(
            id="grid_btc",
            connector_name="binance_perpetual",
            trading_pair="BTC-USDT",
            grid_range_pct=Decimal("0.02"),
            total_amount_quote=Decimal("1000"),
            leverage=10,
        )

        # 创建 Controller
        controller = BasicGridController(config=controller_config)

        # 初始化策略
        super().__init__(
            connectors=connectors,
            controllers=[controller],
        )
```

## 8.4 多网格并行运行

### 8.4.1 多交易对网格

```python
class MultiPairGrid(ScriptStrategyBase):
    """
    多交易对并行网格策略
    """

    # 交易对配置
    PAIRS = [
        {"pair": "BTC-USDT", "start": 40000, "end": 42000, "amount": 500},
        {"pair": "ETH-USDT", "start": 2000, "end": 2100, "amount": 300},
        {"pair": "SOL-USDT", "start": 100, "end": 110, "amount": 200},
    ]

    connector_name = "binance_perpetual"

    def __init__(self, connectors):
        super().__init__(connectors)
        self.executor_orchestrator = ExecutorOrchestrator(
            strategy=self,
            executors_update_interval=1.0,
        )
        self.grids_created = False

    def on_tick(self):
        if not self.grids_created:
            self.create_all_grids()
            self.grids_created = True

        self.display_all_grids_status()

    def create_all_grids(self):
        """
        为所有交易对创建网格
        """
        for pair_config in self.PAIRS:
            self.create_grid_for_pair(pair_config)

    def create_grid_for_pair(self, pair_config):
        """
        为单个交易对创建网格
        """
        triple_barrier = TripleBarrierConfig(
            stop_loss=Decimal("0.05"),
            take_profit=Decimal("0.01"),
            open_order_type=OrderType.LIMIT_MAKER,
            take_profit_order_type=OrderType.LIMIT_MAKER,
        )

        config = GridExecutorConfig(
            timestamp=time.time(),
            connector_name=self.connector_name,
            trading_pair=pair_config["pair"],
            side=TradeType.BUY,
            start_price=Decimal(str(pair_config["start"])),
            end_price=Decimal(str(pair_config["end"])),
            limit_price=Decimal(str(pair_config["start"])) * Decimal("0.95"),
            total_amount_quote=Decimal(str(pair_config["amount"])),
            leverage=10,
            triple_barrier_config=triple_barrier,
        )

        from hummingbot.strategy_v2.executors.grid_executor.grid_executor import GridExecutor

        executor = GridExecutor(strategy=self, config=config, update_interval=1.0)
        self.executor_orchestrator.active_executors[config.id] = executor
        executor.start()

        self.logger().info(f"Grid created for {pair_config['pair']}")

    def display_all_grids_status(self):
        """
        显示所有网格状态
        """
        total_pnl = Decimal("0")

        for executor_id, executor in self.executor_orchestrator.active_executors.items():
            pnl = executor.get_net_pnl_quote()
            total_pnl += pnl

            self.logger().info(
                f"{executor.config.trading_pair}: "
                f"PnL = {pnl:.2f} USDT ({executor.get_net_pnl_pct():.2%})"
            )

        self.logger().info(f"Total PnL: {total_pnl:.2f} USDT")
```

### 8.4.2 多方向网格（对冲）

```python
class HedgedGrid(ScriptStrategyBase):
    """
    对冲网格：同时运行 BUY 和 SELL 网格
    """

    connector_name = "binance_perpetual"
    trading_pair = "BTC-USDT"

    def __init__(self, connectors):
        super().__init__(connectors)
        self.executor_orchestrator = ExecutorOrchestrator(
            strategy=self,
            executors_update_interval=1.0,
        )
        self.grids_created = False

    def on_tick(self):
        if not self.grids_created:
            # 获取当前价格
            mid_price = self.connectors[self.connector_name].get_price_by_type(
                self.trading_pair,
                PriceType.MidPrice
            )

            # 创建 BUY 和 SELL 网格
            self.create_buy_grid(mid_price)
            self.create_sell_grid(mid_price)

            self.grids_created = True

    def create_buy_grid(self, mid_price):
        """
        创建 BUY 网格（下方）
        """
        triple_barrier = TripleBarrierConfig(
            stop_loss=Decimal("0.05"),
            take_profit=Decimal("0.01"),
            open_order_type=OrderType.LIMIT_MAKER,
            take_profit_order_type=OrderType.LIMIT_MAKER,
        )

        config = GridExecutorConfig(
            timestamp=time.time(),
            connector_name=self.connector_name,
            trading_pair=self.trading_pair,
            side=TradeType.BUY,
            start_price=mid_price * Decimal("0.98"),  # 下方 2%
            end_price=mid_price,
            limit_price=mid_price * Decimal("0.95"),
            total_amount_quote=Decimal("500"),
            leverage=10,
            triple_barrier_config=triple_barrier,
        )

        from hummingbot.strategy_v2.executors.grid_executor.grid_executor import GridExecutor

        executor = GridExecutor(strategy=self, config=config, update_interval=1.0)
        self.executor_orchestrator.active_executors[config.id] = executor
        executor.start()

        self.logger().info("BUY grid created")

    def create_sell_grid(self, mid_price):
        """
        创建 SELL 网格（上方）
        """
        triple_barrier = TripleBarrierConfig(
            stop_loss=Decimal("0.05"),
            take_profit=Decimal("0.01"),
            open_order_type=OrderType.LIMIT_MAKER,
            take_profit_order_type=OrderType.LIMIT_MAKER,
        )

        config = GridExecutorConfig(
            timestamp=time.time(),
            connector_name=self.connector_name,
            trading_pair=self.trading_pair,
            side=TradeType.SELL,
            start_price=mid_price * Decimal("1.02"),  # 上方 2%
            end_price=mid_price,
            limit_price=mid_price * Decimal("1.05"),
            total_amount_quote=Decimal("500"),
            leverage=10,
            triple_barrier_config=triple_barrier,
        )

        from hummingbot.strategy_v2.executors.grid_executor.grid_executor import GridExecutor

        executor = GridExecutor(strategy=self, config=config, update_interval=1.0)
        self.executor_orchestrator.active_executors[config.id] = executor
        executor.start()

        self.logger().info("SELL grid created")
```

## 8.5 性能优化技巧

### 8.5.1 优化网格参数

```python
def optimize_grid_parameters(market_volatility: Decimal):
    """
    根据市场波动率动态调整网格参数
    """
    # 基础参数
    base_grid_range = Decimal("0.02")  # 2%
    base_take_profit = Decimal("0.01")  # 1%

    # 根据波动率调整
    if market_volatility > Decimal("0.05"):  # 高波动
        grid_range = base_grid_range * Decimal("1.5")
        take_profit = base_take_profit * Decimal("1.5")
        max_open_orders = 3
    elif market_volatility < Decimal("0.01"):  # 低波动
        grid_range = base_grid_range * Decimal("0.5")
        take_profit = base_take_profit * Decimal("0.5")
        max_open_orders = 10
    else:  # 正常波动
        grid_range = base_grid_range
        take_profit = base_take_profit
        max_open_orders = 5

    return {
        "grid_range": grid_range,
        "take_profit": take_profit,
        "max_open_orders": max_open_orders,
    }
```

### 8.5.2 资金管理优化

```python
def calculate_optimal_amount(
    total_capital: Decimal,
    num_grids: int,
    risk_per_grid: Decimal = Decimal("0.1")
) -> Decimal:
    """
    计算每个网格的最优资金分配

    Args:
        total_capital: 总资金
        num_grids: 网格数量
        risk_per_grid: 每个网格的风险比例（默认 10%）

    Returns:
        每个网格分配的资金
    """
    # 预留安全边际
    usable_capital = total_capital * Decimal("0.9")

    # 平均分配
    base_amount = usable_capital / num_grids

    # 考虑风险
    amount_per_grid = min(
        base_amount,
        total_capital * risk_per_grid
    )

    return amount_per_grid
```

### 8.5.3 订单频率控制

```python
def get_optimal_order_frequency(market_conditions: dict) -> int:
    """
    根据市场条件优化订单频率

    Args:
        market_conditions: 包含交易量、价格变化等信息

    Returns:
        订单频率（秒）
    """
    # 高交易量 → 低频率（避免过度交易）
    if market_conditions["volume_24h"] > 1000000000:  # 10 亿
        return 30  # 30 秒

    # 低交易量 → 高频率（捕捉机会）
    elif market_conditions["volume_24h"] < 100000000:  # 1 亿
        return 5  # 5 秒

    # 正常
    else:
        return 10  # 10 秒
```

## 8.6 常见问题和解决方案

### 8.6.1 订单被拒绝

**问题**：订单因价格或数量不符合交易规则被拒绝

**解决方案**：

```python
# 检查交易规则
trading_rules = executor.get_trading_rules(connector_name, trading_pair)

print(f"Min Order Size: {trading_rules.min_order_size}")
print(f"Min Notional: {trading_rules.min_notional_size}")
print(f"Price Increment: {trading_rules.min_price_increment}")
print(f"Amount Increment: {trading_rules.min_base_amount_increment}")

# 调整配置
config = GridExecutorConfig(
    # ...
    min_order_amount_quote=trading_rules.min_notional_size * Decimal("1.1"),  # 增加 10% 安全边际
)
```

### 8.6.2 激活范围设置不当

**问题**：网格层级从不激活或过度激活

**解决方案**：

```python
# 根据网格步长设置激活范围
step = (end_price - start_price) / start_price / num_levels
activation_bounds = step * 2  # 2 倍步长

# 或根据市场波动
volatility = calculate_volatility(trading_pair, period=24)
activation_bounds = volatility * 0.5
```

### 8.6.3 手续费过高

**问题**：频繁交易导致手续费侵蚀利润

**解决方案**：

```python
# 1. 使用 LIMIT_MAKER 订单（享受手续费返还）
triple_barrier = TripleBarrierConfig(
    open_order_type=OrderType.LIMIT_MAKER,
    take_profit_order_type=OrderType.LIMIT_MAKER,
)

# 2. 增加止盈距离
# 确保 take_profit > 双边手续费
maker_fee = Decimal("0.0002")
taker_fee = Decimal("0.0005")
min_profit = (maker_fee + taker_fee) * 2
take_profit = max(Decimal("0.01"), min_profit * Decimal("1.5"))

# 3. 降低订单频率
config = GridExecutorConfig(
    # ...
    order_frequency=30,  # 30 秒
)
```

### 8.6.4 网格无法覆盖价格波动

**问题**：价格经常超出网格范围

**解决方案**：

```python
# 1. 扩大网格范围
grid_range = calculate_volatility() * 3  # 3 倍波动率

# 2. 使用动态网格（Controller）
class DynamicGridController(ControllerBase):
    def determine_executor_actions(self):
        # 定期重新创建网格以跟随价格
        if time.time() - self.last_grid_time > 3600:  # 每小时
            # 停止旧网格
            for executor_id in self.executors_info:
                actions.append(StopExecutorAction(executor_id))

            # 创建新网格
            actions.append(self.create_grid_executor())

            self.last_grid_time = time.time()
```

### 8.6.5 资金不足

**问题**：无法创建足够的网格层级

**解决方案**：

```python
# 方法 1：减少总金额要求
config = GridExecutorConfig(
    # ...
    total_amount_quote=Decimal("100"),  # 降低要求
)

# 方法 2：使用杠杆（永续合约）
config = GridExecutorConfig(
    # ...
    leverage=10,  # 使用杠杆扩大资金效率
)

# 方法 3：增加最小订单金额
config = GridExecutorConfig(
    # ...
    min_order_amount_quote=Decimal("50"),  # 增大单笔金额，减少层级数
)
```

## 8.7 完整的生产级策略示例

```python
import time
from decimal import Decimal
from typing import List, Dict
from hummingbot.strategy_v2.strategy_v2_base import StrategyV2Base
from hummingbot.strategy_v2.controllers.controller_base import ControllerBase, ControllerConfigBase
from hummingbot.strategy_v2.executors.grid_executor.data_types import GridExecutorConfig
from hummingbot.strategy_v2.executors.position_executor.data_types import (
    TripleBarrierConfig,
    TrailingStop
)
from pydantic import Field


class ProductionGridConfig(ControllerConfigBase):
    """
    生产级网格配置
    """
    controller_type: str = "production_grid"

    # 交易所配置
    connector_name: str = Field(default="binance_perpetual")
    trading_pair: str = Field(default="BTC-USDT")

    # 资金配置
    total_capital: Decimal = Field(default=Decimal("10000"))
    capital_allocation_pct: Decimal = Field(default=Decimal("0.5"))  # 50% 资金

    # 网格配置
    grid_range_pct: Decimal = Field(default=Decimal("0.02"))
    min_spread: Decimal = Field(default=Decimal("0.001"))
    max_open_orders: int = Field(default=10)

    # 风险配置
    stop_loss_pct: Decimal = Field(default=Decimal("0.03"))
    take_profit_pct: Decimal = Field(default=Decimal("0.01"))
    trailing_activation: Decimal = Field(default=Decimal("0.02"))
    trailing_delta: Decimal = Field(default=Decimal("0.01"))

    # 执行配置
    leverage: int = Field(default=10)
    activation_bounds: Decimal = Field(default=Decimal("0.01"))
    order_frequency: int = Field(default=10)

    # 优化配置
    recreate_interval: int = Field(default=3600)  # 每小时重建
    enable_dynamic_params: bool = Field(default=True)


class ProductionGridController(ControllerBase):
    """
    生产级网格 Controller

    功能：
    - 动态参数调整
    - 风险管理
    - 性能监控
    - 自动重建
    """

    def __init__(self, config: ProductionGridConfig, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self.config = config
        self.last_grid_time = 0
        self.performance_history: List[Dict] = []

    async def update_processed_data(self):
        """
        更新市场数据和性能指标
        """
        # 获取价格
        self.mid_price = self.market_data_provider.get_price_by_type(
            self.config.connector_name,
            self.config.trading_pair,
            PriceType.MidPrice
        )

        # 计算波动率（简化版）
        self.volatility = self.calculate_volatility()

        # 更新性能历史
        self.update_performance_history()

    def calculate_volatility(self) -> Decimal:
        """
        计算市场波动率
        """
        # 实际应用中应使用历史价格数据计算
        # 这里简化为固定值
        return Decimal("0.02")

    def update_performance_history(self):
        """
        更新性能历史
        """
        for executor_id, executor_info in self.executors_info.items():
            if not executor_info.is_active:
                performance = {
                    "timestamp": time.time(),
                    "pnl": executor_info.net_pnl_quote,
                    "pnl_pct": executor_info.net_pnl_pct,
                    "filled_amount": executor_info.filled_amount_quote,
                }
                self.performance_history.append(performance)

    def determine_executor_actions(self) -> List:
        """
        决定 Executor 操作
        """
        actions = []

        # 如果没有活跃 Executor 或需要重建
        if len([e for e in self.executors_info.values() if e.is_active]) == 0:
            if time.time() - self.last_grid_time > self.config.recreate_interval:
                actions.append(self.create_optimized_grid())
                self.last_grid_time = time.time()

        return actions

    def create_optimized_grid(self) -> CreateExecutorAction:
        """
        创建优化的网格
        """
        # 动态调整参数
        if self.config.enable_dynamic_params:
            params = self.optimize_parameters()
        else:
            params = self.get_default_parameters()

        # 计算网格边界
        start_price = self.mid_price * (1 - params["grid_range"] / 2)
        end_price = self.mid_price * (1 + params["grid_range"] / 2)
        limit_price = start_price * Decimal("0.97")

        # 计算资金分配
        allocated_amount = self.config.total_capital * self.config.capital_allocation_pct

        # 创建追踪止损
        trailing_stop = TrailingStop(
            activation_price=self.config.trailing_activation,
            trailing_delta=self.config.trailing_delta,
        )

        # Triple Barrier 配置
        triple_barrier = TripleBarrierConfig(
            stop_loss=self.config.stop_loss_pct,
            take_profit=params["take_profit"],
            trailing_stop=trailing_stop,
            open_order_type=OrderType.LIMIT_MAKER,
            take_profit_order_type=OrderType.LIMIT_MAKER,
        )

        # Grid Executor 配置
        config = GridExecutorConfig(
            timestamp=time.time(),
            controller_id=self.config.id,
            connector_name=self.config.connector_name,
            trading_pair=self.config.trading_pair,
            side=TradeType.BUY,
            start_price=start_price,
            end_price=end_price,
            limit_price=limit_price,
            total_amount_quote=allocated_amount,
            min_spread_between_orders=params["min_spread"],
            max_open_orders=params["max_open_orders"],
            activation_bounds=self.config.activation_bounds,
            order_frequency=self.config.order_frequency,
            leverage=self.config.leverage,
            triple_barrier_config=triple_barrier,
        )

        return CreateExecutorAction(
            controller_id=self.config.id,
            executor_config=config
        )

    def optimize_parameters(self) -> Dict:
        """
        基于市场条件优化参数
        """
        params = {}

        # 根据波动率调整参数
        if self.volatility > Decimal("0.05"):  # 高波动
            params["grid_range"] = self.config.grid_range_pct * Decimal("1.5")
            params["take_profit"] = self.config.take_profit_pct * Decimal("1.5")
            params["min_spread"] = self.config.min_spread * Decimal("1.5")
            params["max_open_orders"] = max(5, self.config.max_open_orders // 2)
        elif self.volatility < Decimal("0.01"):  # 低波动
            params["grid_range"] = self.config.grid_range_pct * Decimal("0.7")
            params["take_profit"] = self.config.take_profit_pct * Decimal("0.7")
            params["min_spread"] = self.config.min_spread * Decimal("0.7")
            params["max_open_orders"] = min(20, self.config.max_open_orders * 2)
        else:  # 正常波动
            params = self.get_default_parameters()

        return params

    def get_default_parameters(self) -> Dict:
        """
        获取默认参数
        """
        return {
            "grid_range": self.config.grid_range_pct,
            "take_profit": self.config.take_profit_pct,
            "min_spread": self.config.min_spread,
            "max_open_orders": self.config.max_open_orders,
        }

    def to_format_status(self) -> List[str]:
        """
        格式化状态显示
        """
        lines = []

        # 基本信息
        lines.append(f"=== {self.config.id} ===")
        lines.append(f"Pair: {self.config.trading_pair}")
        lines.append(f"Mid Price: {self.mid_price:.2f}")
        lines.append(f"Volatility: {self.volatility:.2%}")

        # Executor 状态
        active_count = len([e for e in self.executors_info.values() if e.is_active])
        lines.append(f"Active Executors: {active_count}")

        # 性能统计
        if self.performance_history:
            total_pnl = sum([p["pnl"] for p in self.performance_history])
            avg_pnl_pct = sum([p["pnl_pct"] for p in self.performance_history]) / len(self.performance_history)
            lines.append(f"Total PnL: {total_pnl:.2f} USDT")
            lines.append(f"Avg PnL%: {avg_pnl_pct:.2%}")

        return lines
```

## 8.8 小结

本章通过实战示例展示了 Grid Executor 的各种应用场景：

- **基础策略**：现货和永续合约网格
- **Controller 集成**：使用 Controller 管理网格生命周期
- **多网格策略**：并行运行多个网格
- **性能优化**：参数优化和资金管理
- **问题解决**：常见问题和解决方案
- **生产级实现**：完整的生产环境策略

通过学习这些示例，您应该能够：

1. 独立开发自定义网格策略
2. 优化网格参数以适应不同市场
3. 集成到更复杂的交易系统中
4. 处理实际交易中的各种问题

## 教程总结

恭喜您完成了 Grid Executor 技术教程的学习！通过 8 个章节，您已经：

- 理解了 Grid Executor 的架构设计和工作原理
- 掌握了所有配置参数和数据类型
- 深入学习了网格生成算法
- 了解了完整的订单生命周期管理
- 掌握了 Triple Barrier 风险管理系统
- 学会了计算和监控性能指标
- 理解了事件驱动的状态同步机制
- 能够开发实际的网格交易策略

继续探索和实践，您将能够开发出更加强大和稳定的量化交易策略！

---

**上一章**：[第 7 章：事件处理机制](grid_executor_07.md)

**返回目录**：[教程索引](grid_executor_index.md)
