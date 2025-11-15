#!/usr/bin/env python3
"""
# 抵押品计算工具

## 概述

该命令行工具用于根据借出报价资产数量、初始质押率与质押资产的报价计算所需质押的基础资产数量，并可依据强平质押率推导强平价格。适用于杠杆借贷、场外撮合等需要快速评估抵押资金占用的场景。

## 输入参数

- `--borrow-amount`：借出的报价资产数量，必须为正数。
- `--borrow-asset`：报价资产符号，将自动转换为大写展示。
- `--initial-margin`：初始质押率，介于 0 与 1 之间（例如 0.5 表示 50%）。
- `--collateral-asset`：质押资产符号，将自动转换为大写展示。
- `--collateral-price`：质押资产以报价资产计价的价格，必须为正数。
- `--liquidation-margin`：强平质押率，介于 0 与 1 之间（例如 0.96 表示 96%）。
- `--precision`：输出小数位数，默认 8 位，可按需要调整。

## 输出内容

程序会打印借出数量、初始质押率、质押资产价格、所需质押数量以及基于强平质押率计算得到的强平价格，便于复制到表格或报告中。所有金额与数量均采用用户指定的精度，确保与上游业务流程保持一致。

## 使用示例

```bash
python3 collateral_calculator.py \
  --borrow-amount 50000 \
  --borrow-asset usdt \
  --initial-margin 0.5 \
  --liquidation-margin 0.96 \
  --collateral-asset btc \
  --collateral-price 100000 \
  --precision 6
```

以上命令会输出借出 50000 USDT、价位 100000 USDT/BTC、初始质押率 50% 时所需的 BTC 数量。
"""
from __future__ import annotations

import argparse
import sys
from typing import Callable


def _positive_float(name: str) -> Callable[[str], float]:
    def validator(raw: str) -> float:
        try:
            value = float(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"{name} 需要是数字，收到：{raw}") from exc
        if value <= 0:
            raise argparse.ArgumentTypeError(f"{name} 需要大于 0，收到：{value}")
        return value

    return validator


def _margin(raw: str) -> float:
    value = _positive_float("初始质押率")(raw)
    if value > 1:
        raise argparse.ArgumentTypeError(f"初始质押率需要介于 0 和 1 之间，收到：{value}")
    return value


def parse_args() -> argparse.Namespace:
    """
    构造命令行解析器并返回解析后的参数。

    Returns:
        argparse.Namespace: 含所有命令行参数的命名空间。
    """
    parser = argparse.ArgumentParser(
        description="计算质押借币时所需的基础资产数量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例
--------

示例 1：默认精度
  python3 collateral_calculator.py --borrow-amount 20000 --borrow-asset usdt --initial-margin 0.6 --liquidation-margin 0.9 --collateral-asset eth --collateral-price 3500

示例 2：指定输出位数
  python3 collateral_calculator.py --borrow-amount 50000 --borrow-asset usdt --initial-margin 0.5 --liquidation-margin 0.96 --collateral-asset btc --collateral-price 100000 --precision 6

字段说明
--------
- 借出数量和质押价格使用报价资产计价。
- 质押数量使用基础资产计价，精度由 --precision 控制。
""",
    )
    parser.add_argument(
        "--borrow-amount",
        required=True,
        type=_positive_float("借出报价资产数量"),
        help="需要借出的报价资产数量，例如 50000",
    )
    parser.add_argument(
        "--borrow-asset",
        required=True,
        type=str,
        help="借出的报价资产符号，例如 USDT",
    )
    parser.add_argument(
        "--initial-margin",
        required=True,
        type=_margin,
        help="初始质押率，0-1 之间的小数，例如 0.5",
    )
    parser.add_argument(
        "--collateral-asset",
        required=True,
        type=str,
        help="质押的基础资产符号，例如 BTC",
    )
    parser.add_argument(
        "--collateral-price",
        required=True,
        type=_positive_float("基础资产报价"),
        help="质押基础资产以报价资产计价的价格，例如 100000",
    )
    parser.add_argument(
        "--liquidation-margin",
        required=True,
        type=_margin,
        help="强平质押率，0-1 之间的小数，例如 0.96",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=8,
        help="输出保留的小数位数，默认 8",
    )

    return parser.parse_args()


def calculate_collateral_amount(
    borrowed_amount: float,
    initial_margin: float,
    collateral_price: float,
) -> float:
    """
    根据借出数量、初始质押率及质押资产价格计算所需基础资产数量。

    Args:
        borrowed_amount: 借出的报价资产数量。
        initial_margin: 初始质押率（0-1 之间）。
        collateral_price: 质押资产的报价。

    Returns:
        float: 所需质押的基础资产数量。
    """
    return borrowed_amount / (initial_margin * collateral_price)


def calculate_liquidation_price(
    borrowed_amount: float,
    collateral_amount: float,
    liquidation_margin: float,
) -> float:
    """
    根据借出数量、已质押数量与强平质押率计算强平价格。

    Args:
        borrowed_amount: 借出的报价资产数量。
        collateral_amount: 已质押的基础资产数量。
        liquidation_margin: 强平质押率（0-1 之间）。

    Returns:
        float: 触发强平时的基础资产价格。
    """
    return borrowed_amount / (collateral_amount * liquidation_margin)


def format_summary(
    borrow_amount: float,
    borrow_asset: str,
    initial_margin: float,
    liquidation_margin: float,
    collateral_price: float,
    collateral_asset: str,
    collateral_amount: float,
    liquidation_price: float,
    precision: int,
) -> str:
    """
    构造命令行输出，便于复制或重定向。

    Args:
        borrow_amount: 借出的报价资产数量。
        borrow_asset: 报价资产符号（大写）。
        initial_margin: 初始质押率。
        liquidation_margin: 强平质押率。
        collateral_price: 质押资产价格。
        collateral_asset: 质押资产符号（大写）。
        collateral_amount: 计算得到的质押资产数量。
        liquidation_price: 基于强平质押率计算得到的价格。
        precision: 输出的数字精度。

    Returns:
        str: 多行文本，展示输入与计算结果。
    """
    lines = [
        f"借出资产数量：{borrow_amount:.{precision}f} {borrow_asset}",
        f"初始质押率：{initial_margin:.6f}",
        f"强平质押率：{liquidation_margin:.6f}",
        f"质押资产价格：{collateral_price:.{precision}f} {borrow_asset}/{collateral_asset}",
        f"所需质押数量：{collateral_amount:.{precision}f} {collateral_asset}",
        f"强平价格：{liquidation_price:.{precision}f} {borrow_asset}/{collateral_asset}",
    ]
    return "\n".join(lines)


def main() -> int:
    """
    解析命令行参数并输出抵押品计算结果。
    """
    args = parse_args()
    borrow_asset = args.borrow_asset.upper()
    collateral_asset = args.collateral_asset.upper()
    collateral_amount = calculate_collateral_amount(
        borrowed_amount=args.borrow_amount,
        initial_margin=args.initial_margin,
        collateral_price=args.collateral_price,
    )
    liquidation_price = calculate_liquidation_price(
        borrowed_amount=args.borrow_amount,
        collateral_amount=collateral_amount,
        liquidation_margin=args.liquidation_margin,
    )
    summary = format_summary(
        borrow_amount=args.borrow_amount,
        borrow_asset=borrow_asset,
        initial_margin=args.initial_margin,
        liquidation_margin=args.liquidation_margin,
        collateral_price=args.collateral_price,
        collateral_asset=collateral_asset,
        collateral_amount=collateral_amount,
        liquidation_price=liquidation_price,
        precision=args.precision,
    )

    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
