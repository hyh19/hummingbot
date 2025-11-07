import os
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import Field, field_validator

from hummingbot.connector.connector_base import ConnectorBase
from hummingbot.core.clock import Clock
from hummingbot.core.data_type.common import OrderType, PositionMode, PriceType, TradeType
from hummingbot.data_feed.candles_feed.data_types import CandlesConfig
from hummingbot.strategy.strategy_v2_base import StrategyV2Base, StrategyV2ConfigBase
from hummingbot.strategy_v2.executors.position_executor.data_types import PositionExecutorConfig, TripleBarrierConfig
from hummingbot.strategy_v2.models.executor_actions import CreateExecutorAction, StopExecutorAction


class ThreeCandlesTrendConfig(StrategyV2ConfigBase):
    """
    三连阳/三连阴趋势策略配置类
    """

    script_file_name: str = os.path.basename(__file__)
    markets: Dict[str, List[str]] = {}
    candles_config: List[CandlesConfig] = []
    controllers_config: List[str] = []

    # 交易所配置
    exchange: str = Field(default="binance_perpetual")
    trading_pair: str = Field(default="BTC-USDT")

    # K 线数据源配置
    candles_exchange: str = Field(default="binance_perpetual")
    candles_pair: str = Field(default="BTC-USDT")
    candles_interval: str = Field(default="1h")
    candles_length: int = Field(default=10, gt=0)  # 需要至少 3 根，多保留一些用于分析

    # 策略参数
    trade_direction: str = Field(default="LONG")  # LONG 或 SHORT
    min_candle_body_pct: Decimal = Field(default=Decimal("0.001"), gt=0)  # K 线实体最小幅度 0.1%
    leverage: int = Field(default=50, gt=0)
    order_amount_quote: Decimal = Field(default=Decimal("10"), gt=0)
    position_mode: PositionMode = Field(default="ONEWAY")

    # 风险管理参数
    stop_loss: Decimal = Field(default=Decimal("0.01"), gt=0)  # 止损 1%
    take_profit: Decimal = Field(default=Decimal("0.02"), gt=0)  # 止盈 2%

    # 实盘控制
    is_live_trading: bool = Field(default=False)  # 是否执行真实下单

    @property
    def triple_barrier_config(self) -> TripleBarrierConfig:
        """
        三重屏障配置，用于自动止盈止损
        """
        return TripleBarrierConfig(
            stop_loss=self.stop_loss,
            take_profit=self.take_profit,
            open_order_type=OrderType.LIMIT,
            take_profit_order_type=OrderType.LIMIT,
            stop_loss_order_type=OrderType.MARKET,
        )

    @field_validator("position_mode", mode="before")
    @classmethod
    def validate_position_mode(cls, v: str) -> PositionMode:
        if v.upper() in PositionMode.__members__:
            return PositionMode[v.upper()]
        raise ValueError(f"Invalid position mode: {v}. Valid options are: {', '.join(PositionMode.__members__)}")

    @field_validator("trade_direction", mode="before")
    @classmethod
    def validate_trade_direction(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ["LONG", "SHORT"]:
            raise ValueError(f"Invalid trade direction: {v}. Valid options are: LONG, SHORT")
        return v_upper


class ThreeCandlesTrendStrategy(StrategyV2Base):
    """
    三连阳/三连阴趋势跟踪策略

    策略逻辑:
    - 做多条件: 连续 3 根 K 线都是阳线，实体幅度达标，收盘价和开盘价都逐根升高
    - 做空条件: 连续 3 根 K 线都是阴线，实体幅度达标，收盘价和开盘价都逐根降低
    - 风险控制: 同时只允许持有一个仓位，通过止盈止损自动平仓
    """

    account_config_set = False

    @classmethod
    def init_markets(cls, config: ThreeCandlesTrendConfig):
        """
        初始化交易市场
        """
        cls.markets = {config.exchange: {config.trading_pair}}

    def __init__(self, connectors: Dict[str, ConnectorBase], config: ThreeCandlesTrendConfig):
        """
        初始化策略
        """
        # 如果没有配置 K 线数据源，自动添加
        if len(config.candles_config) == 0:
            config.candles_config.append(
                CandlesConfig(
                    connector=config.candles_exchange,
                    trading_pair=config.candles_pair,
                    interval=config.candles_interval,
                    max_records=config.candles_length,
                )
            )
        super().__init__(connectors, config)
        self.config = config
        self.current_signal = None  # 当前信号: 1 (做多)，-1 (做空)，None (无信号)

    def start(self, clock: Clock, timestamp: float) -> None:
        """
        启动策略，调用父类方法完成初始化
        """
        super().start(clock, timestamp)

    def apply_initial_setting(self):
        """
        应用初始设置: 设置杠杆和持仓模式
        """
        if not self.account_config_set:
            for connector_name, connector in self.connectors.items():
                if self.is_perpetual(connector_name):
                    # 设置持仓模式
                    connector.set_position_mode(self.config.position_mode)
                    # 设置杠杆
                    for trading_pair in self.market_data_provider.get_trading_pairs(connector_name):
                        connector.set_leverage(trading_pair, self.config.leverage)
            self.account_config_set = True

    def create_actions_proposal(self) -> List[CreateExecutorAction]:
        """
        创建执行器动作提议

        流程:
        1. 检查是否已有持仓，有则不开新仓
        2. 获取开仓信号
        3. 根据 trade_direction 过滤信号
        4. 生成开仓动作
        """
        create_actions = []

        # 检查是否已有活跃持仓
        active_executors = self.get_active_executors(self.config.exchange, self.config.trading_pair)
        if len(active_executors) > 0:
            # 已有持仓，不再开新仓
            return create_actions

        # 获取信号
        signal = self.get_signal(self.config.candles_exchange, self.config.candles_pair)
        self.current_signal = signal

        if signal is None:
            # 无信号
            return create_actions

        # 获取当前市场价格
        mid_price = self.market_data_provider.get_price_by_type(
            self.config.exchange, self.config.trading_pair, PriceType.MidPrice
        )

        # 根据 trade_direction 过滤信号
        if signal == 1 and self.config.trade_direction == "LONG":
            # 做多信号，且策略允许做多
            if not self.config.is_live_trading:
                message = (
                    f"检测到做多信号 (交易对: {self.config.trading_pair}, 价格: {mid_price:.4f})，"
                    "当前为模拟模式，未执行真实下单。"
                )
                self.logger().info(message)
                self.notify(message)
                return create_actions

            create_actions.append(
                CreateExecutorAction(
                    executor_config=PositionExecutorConfig(
                        timestamp=self.current_timestamp,
                        connector_name=self.config.exchange,
                        trading_pair=self.config.trading_pair,
                        side=TradeType.BUY,
                        entry_price=mid_price,
                        amount=self.config.order_amount_quote / mid_price,
                        triple_barrier_config=self.config.triple_barrier_config,
                        leverage=self.config.leverage,
                    )
                )
            )
        elif signal == -1 and self.config.trade_direction == "SHORT":
            # 做空信号，且策略允许做空
            if not self.config.is_live_trading:
                message = (
                    f"检测到做空信号 (交易对: {self.config.trading_pair}, 价格: {mid_price:.4f})，"
                    "当前为模拟模式，未执行真实下单。"
                )
                self.logger().info(message)
                self.notify(message)
                return create_actions

            create_actions.append(
                CreateExecutorAction(
                    executor_config=PositionExecutorConfig(
                        timestamp=self.current_timestamp,
                        connector_name=self.config.exchange,
                        trading_pair=self.config.trading_pair,
                        side=TradeType.SELL,
                        entry_price=mid_price,
                        amount=self.config.order_amount_quote / mid_price,
                        triple_barrier_config=self.config.triple_barrier_config,
                        leverage=self.config.leverage,
                    )
                )
            )

        return create_actions

    def stop_actions_proposal(self) -> List[StopExecutorAction]:
        """
        停止执行器动作提议

        本策略依赖 TripleBarrierConfig 自动止盈止损，不需要手动平仓
        """
        return []

    def get_active_executors(self, connector_name: str, trading_pair: str) -> List:
        """
        获取指定交易对的活跃执行器列表

        Args:
            connector_name: 交易所名称
            trading_pair: 交易对

        Returns:
            活跃的执行器列表
        """
        active_executors = self.filter_executors(
            executors=self.get_all_executors(),
            filter_func=lambda e: (
                e.connector_name == connector_name and e.trading_pair == trading_pair and e.is_active
            ),
        )
        return active_executors

    def get_signal(self, connector_name: str, trading_pair: str) -> Optional[int]:
        """
        获取交易信号

        Args:
            connector_name: K 线数据源交易所
            trading_pair: K 线数据源交易对

        Returns:
            1: 做多信号 (三连阳)
            -1: 做空信号 (三连阴)
            None: 无信号
        """
        try:
            # 获取 K 线数据
            candles = self.market_data_provider.get_candles_df(
                connector_name, trading_pair, self.config.candles_interval, self.config.candles_length
            )

            if candles is None or len(candles) < 3:
                # K 线数据不足
                return None

            candles = candles.copy()

            candles_interval_seconds = None
            try:
                candles_feed = self.market_data_provider.get_candles_feed(
                    CandlesConfig(
                        connector=connector_name,
                        trading_pair=trading_pair,
                        interval=self.config.candles_interval,
                        max_records=self.config.candles_length,
                    )
                )
                candles_interval_seconds = getattr(candles_feed, "interval_in_seconds", None)
            except Exception:
                # 无法获取蜡烛图周期时忽略，使用退化方案
                candles_interval_seconds = None

            if "timestamp" in candles.columns and candles_interval_seconds:
                timestamps = candles["timestamp"].astype(float)
                # 处理毫秒级时间戳
                if timestamps.max() > 1e12:
                    timestamps = timestamps / 1000

                current_time = int(self.current_timestamp)
                interval_start = current_time - (current_time % candles_interval_seconds)
                candles = candles.loc[timestamps < interval_start]
            else:
                # 无法准确定位当前 K 线时，直接移除最后一根
                candles = candles.iloc[:-1]

            if candles is None or len(candles) < 3:
                return None

            last_3 = candles.tail(3)
            opens = last_3["open"].values
            closes = last_3["close"].values
            candle_lines = "\n".join(
                [f"  #{index + 1}: open={opens[index]:.4f}, close={closes[index]:.4f}" for index in range(3)]
            )
            self.logger().info(
                "最近 3 根 K 线数据 (%s %s %s):\n%s",
                connector_name,
                trading_pair,
                self.config.candles_interval,
                candle_lines,
            )

            # 检查三连阳 (做多信号)
            if self.check_three_bullish_candles(candles):
                return 1

            # 检查三连阴 (做空信号)
            if self.check_three_bearish_candles(candles):
                return -1

            return None

        except Exception as e:
            self.logger().error(f"获取信号时发生错误: {e}")
            return None

    def check_three_bullish_candles(self, candles) -> bool:
        """
        检查是否满足三连阳条件

        条件:
        1. 最近 3 根 K 线都是阳线 (close > open)
        2. 每根 K 线实体幅度达标 ((close - open) / open >= min_candle_body_pct)
        3. 收盘价逐根升高 (close[i] > close[i-1] > close[i-2])
        4. 开盘价逐根升高 (open[i] > open[i-1] > open[i-2])

        Args:
            candles: K 线数据 DataFrame

        Returns:
            是否满足三连阳条件
        """
        if len(candles) < 3:
            return False

        # 获取最近 3 根已完成 K 线
        last_3 = candles.tail(3).dropna(subset=["open", "close"])
        if len(last_3) < 3:
            return False
        opens = last_3["open"].values
        closes = last_3["close"].values

        min_body_pct = float(self.config.min_candle_body_pct)
        bullish_flags = [closes[i] > opens[i] for i in range(3)]
        body_pcts = [(closes[i] - opens[i]) / opens[i] for i in range(3)]
        body_flags = [body_pcts[i] >= min_body_pct for i in range(3)]
        closes_increasing = closes[0] < closes[1] < closes[2]
        opens_increasing = opens[0] < opens[1] < opens[2]

        bullish_condition = all(bullish_flags)
        body_condition = all(body_flags)
        result = bullish_condition and body_condition and closes_increasing and opens_increasing

        self.logger().info(
            "三连阳判定结果: %s\n  阳线达标: %s\n  实体达标: %s\n  收盘递增: %s\n  开盘递增: %s",
            result,
            bullish_condition,
            body_condition,
            closes_increasing,
            opens_increasing,
        )

        return result

    def check_three_bearish_candles(self, candles) -> bool:
        """
        检查是否满足三连阴条件

        条件:
        1. 最近 3 根 K 线都是阴线 (close < open)
        2. 每根 K 线实体幅度达标 ((open - close) / open >= min_candle_body_pct)
        3. 收盘价逐根降低 (close[i] < close[i-1] < close[i-2])
        4. 开盘价逐根降低 (open[i] < open[i-1] < open[i-2])

        Args:
            candles: K 线数据 DataFrame

        Returns:
            是否满足三连阴条件
        """
        if len(candles) < 3:
            return False

        # 获取最近 3 根已完成 K 线
        last_3 = candles.tail(3).dropna(subset=["open", "close"])
        if len(last_3) < 3:
            return False
        opens = last_3["open"].values
        closes = last_3["close"].values

        min_body_pct = float(self.config.min_candle_body_pct)
        bearish_flags = [closes[i] < opens[i] for i in range(3)]
        body_pcts = [(opens[i] - closes[i]) / opens[i] for i in range(3)]
        body_flags = [body_pcts[i] >= min_body_pct for i in range(3)]
        closes_decreasing = closes[0] > closes[1] > closes[2]
        opens_decreasing = opens[0] > opens[1] > opens[2]

        bearish_condition = all(bearish_flags)
        body_condition = all(body_flags)
        result = bearish_condition and body_condition and closes_decreasing and opens_decreasing

        self.logger().info(
            "三连阴判定结果: %s\n  阴线达标: %s\n  实体达标: %s\n  收盘递减: %s\n  开盘递减: %s",
            result,
            bearish_condition,
            body_condition,
            closes_decreasing,
            opens_decreasing,
        )

        return result

    def format_status(self) -> str:
        """
        格式化策略状态信息
        """
        if not self.ready_to_trade:
            return "Market connectors are not ready."

        lines = []

        # 显示余额信息
        balance_df = self.get_balance_df()
        lines.extend(["", "  账户余额:"] + ["    " + line for line in balance_df.to_string(index=False).split("\n")])

        # 显示策略配置
        lines.extend(
            [
                "",
                "  策略配置:",
                f"    交易所: {self.config.exchange}",
                f"    交易对: {self.config.trading_pair}",
                f"    K 线周期: {self.config.candles_interval}",
                f"    交易方向: {self.config.trade_direction}",
                f"    最小实体幅度: {self.config.min_candle_body_pct:.2%}",
                f"    杠杆倍数: {self.config.leverage}x",
                f"    开仓金额: {self.config.order_amount_quote} USDT",
                f"    止损: {self.config.stop_loss:.2%}",
                f"    止盈: {self.config.take_profit:.2%}",
            ]
        )

        # 显示当前信号
        signal_text = "无信号"
        if self.current_signal == 1:
            signal_text = "做多信号 (三连阳)"
        elif self.current_signal == -1:
            signal_text = "做空信号 (三连阴)"

        lines.extend(
            [
                "",
                f"  当前信号: {signal_text}",
            ]
        )

        # 显示活跃持仓
        active_executors = self.get_active_executors(self.config.exchange, self.config.trading_pair)
        if len(active_executors) > 0:
            lines.extend(["", "  活跃持仓:"])
            for executor in active_executors:
                side_text = "做多" if executor.side == TradeType.BUY else "做空"
                lines.append(
                    f"    [{executor.id[:8]}] {side_text} | "
                    f"数量: {executor.amount:.4f} | "
                    f"入场价: {executor.config.entry_price:.2f} | "
                    f"PnL: {executor.net_pnl_quote:.2f} USDT ({executor.net_pnl_pct:.2%})"
                )
        else:
            lines.extend(["", "  当前无持仓"])

        # 显示活跃订单
        try:
            orders_df = self.active_orders_df()
            if not orders_df.empty:
                lines.extend(
                    ["", "  活跃订单:"] + ["    " + line for line in orders_df.to_string(index=False).split("\n")]
                )
        except ValueError:
            pass

        return "\n".join(lines)
