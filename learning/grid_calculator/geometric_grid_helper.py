#!/usr/bin/env python3
"""
# 等比网格辅助脚本

## 概述

该脚本用于在已知最高价、最低价、网格数量、单网格收益率四个参数中的任意三个条件下，推导剩余参数，并计算最低价相对最高价的跌幅百分比，帮助评估等比网格策略的价格区间。

## 输入参数

- `--max-price` (`-M`)：最高价，需大于 0。
- `--min-price` (`-m`)：最低价，需大于 0。
- `--grids` (`-g`)：网格数量，至少为 2。
- `--grid-return-pct` (`-r`)：单网格收益率，需大于 0（例如 0.01 表示 1%）。

请确保命令行仅提供其中的三个参数，脚本会自动推导剩余参数。

## 使用示例

- 已知区间上下限与网格数量，计算单网格收益率：

```bash
python3 learning/grid_calculator/geometric_grid_helper.py -M 30000 -m 15000 -g 12
```

- 已知涨跌范围与单网格收益率，推导网格数量：

```bash
python3 learning/grid_calculator/geometric_grid_helper.py -M 32000 -m 16000 -r 0.02
```

- 不提供最高价时，可通过最低价、网格数量和单网格收益率计算最高价：

```bash
python3 learning/grid_calculator/geometric_grid_helper.py -m 12000 -g 10 -r 0.015
```

## 输出说明

- 输出最高价、最低价、网格数量、单网格收益率，并给出跌幅百分比。
- 若输入不满足条件（例如提供的参数数量不为三个或存在非正数），脚本会在终端输出错误信息并终止执行。
"""

import argparse
import math
import sys


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数。

    Returns:
        argparse.Namespace: 解析后的参数对象。
    """
    parser = argparse.ArgumentParser(
        description=(
            "根据最高价、最低价、网格数量、单网格收益率四个参数中的任意三个推导剩余参数，"
            "并计算最低价相对于最高价的跌幅百分比。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例
--------

示例 1：已知最高价、最低价与网格数量，求单网格收益率
  python3 learning/grid_calculator/geometric_grid_helper.py -M 30000 -m 15000 -g 12

示例 2：已知最高价、最低价与单网格收益率，推导网格数量
  python3 learning/grid_calculator/geometric_grid_helper.py -M 32000 -m 16000 -r 0.02

示例 3：已知最低价、网格数量与单网格收益率，推导最高价
  python3 learning/grid_calculator/geometric_grid_helper.py -m 12000 -g 10 -r 0.015

注意事项
--------
- 参数需满足正数约束：价格 > 0，网格数量 ≥ 2，单网格收益率 > 0。
- 命令行必须恰好提供四个参数中的三个，否则程序将报错退出。
""",
    )
    parser.add_argument(
        "--max-price",
        "-M",
        type=float,
        help="最高价（max_price），需大于 0",
    )
    parser.add_argument(
        "--min-price",
        "-m",
        type=float,
        help="最低价（min_price），需大于 0",
    )
    parser.add_argument(
        "--grids",
        "-g",
        type=int,
        help="网格数量（num_grids），需大于等于 2",
    )
    parser.add_argument(
        "--grid-return-pct",
        "-r",
        type=float,
        help="单网格收益率（grid_return_pct），需大于 0（例如 0.01 表示 1%%）",
    )
    return parser.parse_args()


def compute_drawdown_pct(min_price: float, max_price: float) -> float:
    """
    计算最低价相对于最高价的跌幅百分比。

    Args:
        min_price (float): 等比网格最低价。
        max_price (float): 等比网格最高价。

    Returns:
        float: 跌幅百分比。
    """
    return (1.0 - min_price / max_price) * 100.0


def ensure_positive(value: float, name: str) -> None:
    """确保提供的参数为正数。"""
    if value is not None and value <= 0:
        print(f"错误: {name} 必须大于 0", file=sys.stderr)
        raise SystemExit(1)


def ensure_num_grids(num_grids: int) -> None:
    """确保网格数量为正整数。"""
    if num_grids is not None and num_grids < 2:
        print("错误: 网格数量 num_grids 必须至少为 2", file=sys.stderr)
        raise SystemExit(1)


def solve_parameters(
    max_price: float | None,
    min_price: float | None,
    num_grids: int | None,
    grid_return_pct: float | None,
) -> tuple[float, float, int, float]:
    """根据提供的任意三个参数推导第四个参数。"""

    # 计算提供的参数数量（非 None 值），用于确保只提供了四个参数中的三个
    provided_count = sum(value is not None for value in (max_price, min_price, num_grids, grid_return_pct))
    # 如果不是恰好提供三个参数，则报错并终止程序
    if provided_count != 3:
        print("错误: 必须恰好提供四个参数中的三个", file=sys.stderr)
        raise SystemExit(1)

    # 校验最高价必须为正
    ensure_positive(max_price, "最高价 max_price")
    # 校验最低价必须为正
    ensure_positive(min_price, "最低价 min_price")
    # 校验网格数量必须为正整数
    ensure_num_grids(num_grids)

    # 检查单网格收益率是否为正数（如果有提供）
    if grid_return_pct is not None:
        # 单网格收益率必须大于 0，否则报错
        if grid_return_pct <= 0:
            print("错误: 单网格收益率 grid_return_pct 必须大于 0", file=sys.stderr)
            raise SystemExit(1)

    # 若未提供 grid_return_pct，则 ratio 置为 None，否则 ratio = 1 + grid_return_pct
    ratio = None if grid_return_pct is None else 1.0 + grid_return_pct

    # 若未提供 grid_return_pct，通过其他三个参数来计算 grid_return_pct 和等比公比 ratio
    if grid_return_pct is None:
        # 检查是否提供了 max_price、min_price、num_grids
        if max_price is None or min_price is None or num_grids is None:
            print("错误: 计算单网格收益率需提供 max_price、min_price、num_grids", file=sys.stderr)
            raise SystemExit(1)
        # 最低价必须小于最高价
        if min_price >= max_price:
            print("错误: 最低价必须小于最高价", file=sys.stderr)
            raise SystemExit(1)
        # 网格数量必须大于等于 2
        if num_grids < 2:
            print("错误: 网格数量 num_grids 必须至少为 2", file=sys.stderr)
            raise SystemExit(1)
        # 计算等比公比 ratio
        ratio = (max_price / min_price) ** (1.0 / num_grids)
        # 推出grid_return_pct，即单网格收益率
        grid_return_pct = ratio - 1.0
        # 若单网格收益率小于等于 0，则报错
        if grid_return_pct <= 0:
            print("错误: 计算得到的单网格收益率不大于 0，输入参数不合法", file=sys.stderr)
            raise SystemExit(1)

    # 若未提供 num_grids，反解网格数量
    if num_grids is None:
        # 检查是否提供了 max_price、min_price
        if max_price is None or min_price is None:
            print("错误: 计算网格数量需提供 max_price、min_price、grid_return_pct", file=sys.stderr)
            raise SystemExit(1)
        # 最低价必须小于最高价
        if min_price >= max_price:
            print("错误: 最低价必须小于最高价", file=sys.stderr)
            raise SystemExit(1)
        # 计算等比公比 ratio
        ratio = 1.0 + grid_return_pct
        # 分子：ln(max_price / min_price)
        numerator = math.log(max_price / min_price)
        # 分母：ln(ratio)
        denominator = math.log(ratio)
        # 检查分母是否为零（单网格收益率太小）
        if math.isclose(denominator, 0.0, rel_tol=1e-12, abs_tol=1e-12):
            print("错误: 单网格收益率过小，无法计算网格数量", file=sys.stderr)
            raise SystemExit(1)
        # 推出浮点型网格数量
        num_grids_float = numerator / denominator
        # 四舍五入取最近的整数
        nearest = round(num_grids_float)
        # 如果计算结果不是整数（有误差），报错
        if not math.isclose(num_grids_float, nearest, rel_tol=1e-9, abs_tol=1e-9):
            print("错误: 计算得到的网格数量不是整数，请检查输入参数", file=sys.stderr)
            raise SystemExit(1)
        # 整数化
        num_grids = int(nearest)
        # 网格数量如果小于 2 也报错
        if num_grids < 2:
            print("错误: 计算得到的网格数量小于 2，请检查输入参数", file=sys.stderr)
            raise SystemExit(1)

    # 如果最高价没有提供，通过 min_price、ratio、num_grids 推出 max_price
    if max_price is None:
        ratio = 1.0 + grid_return_pct
        max_price = min_price * (ratio**num_grids)

    # 如果最低价没有提供，通过 max_price、ratio、num_grids 推出 min_price
    if min_price is None:
        ratio = 1.0 + grid_return_pct
        min_price = max_price / (ratio**num_grids)

    # 最终校验，如果最低价大于等于最高价则报错
    if min_price >= max_price:
        print("错误: 计算得到的最低价不应大于或等于最高价，请检查输入参数", file=sys.stderr)
        raise SystemExit(1)

    # 返回：最高价、最低价、网格数量、单网格收益率（全部已填充且为有效数值）
    return max_price, min_price, num_grids, grid_return_pct


def main() -> None:
    """
    命令行入口。
    """
    # 解析命令行参数
    args = parse_args()

    # 读取最高价参数
    max_price = args.max_price
    # 读取最低价参数
    min_price = args.min_price
    # 读取网格数量参数
    num_grids = args.grids
    # 读取单网格收益率参数
    grid_return_pct = args.grid_return_pct

    # 根据输入参数推导/校验最终的最高价、最低价、网格数量、单网格收益率
    max_price, min_price, num_grids, grid_return_pct = solve_parameters(
        max_price, min_price, num_grids, grid_return_pct
    )
    # 计算从最高价到最低价的跌幅百分比
    drawdown_pct = compute_drawdown_pct(min_price, max_price)

    print(f"最高价 (max_price): {max_price:,.6f}")
    print(f"最低价 (min_price): {min_price:,.6f}")
    print(f"网格数量 (num_grids): {num_grids}")
    print(f"单网格收益率 (grid_return_pct): {grid_return_pct:.6f} ({grid_return_pct * 100:.2f}%)")
    print(
        "从最高价 (max_price) "
        f"{max_price:,.6f} 到最低价 (min_price) {min_price:,.6f} 的跌幅 (drawdown_pct): "
        f"{drawdown_pct:,.2f}%"
    )


if __name__ == "__main__":
    main()
