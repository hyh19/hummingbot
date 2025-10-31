#!/usr/bin/env python3
"""
网格交易计算脚本

计算等差数列和等比数列两种网格交易的价格分布、资金分配和购买量。

功能说明：
==========
本脚本用于计算网格交易策略的参数，支持两种网格类型：
1. 等差数列网格：价格按固定金额差均匀分布
2. 等比数列网格：价格按固定百分比差均匀分布

输入参数：
----------
- trading_pair: 交易对，格式为"基础资产-报价资产"（例如：BTC-USDT）
- total_capital: 资金总额，以报价资产计价（例如：10000 USDT）
- min_price: 最低价，网格交易的价格区间下限
- max_price: 最高价，网格交易的价格区间上限
- num_grids: 网格数量 n，即买入订单的层级数量
- num_groups: 分组数量（可选），将网格按顺序分成指定数量的分组（必须是网格数量的因数）

输出内容：
----------
对于每种网格类型，输出以下信息：
1. 价格分布点：n+1 个价格点（从最低价到最高价）
   - 注意：最高价不包含买单，仅作为卖出参考点
2. 买入网格详情：n 个网格的详细信息
   - 每个网格的价格
   - 每个网格投入的报价资产数量
   - 每个网格购买的基础资产数量
   - 如果指定了分组数量，会在每组网格后显示该组的汇总信息（资金总额、购买量）
3. 汇总统计：
   - 总购买的基础资产数量
   - 总投入的报价资产数量
   - 平均价格（总投入资金 / 总购买的基础资产数量）
4. 对比分析：等比数列相对于等差数列的优势

使用方法：
----------
命令行使用：
  python3 grid_calculator.py --trading-pair BTC-USDT --capital 10000 --min-price 1000 --max-price 2000 --grids 10

参数说明：
  --trading-pair, -p: 交易对（必需）
  --capital, -c: 资金总额（必需）
  --min-price, -m: 最低价（必需）
  --max-price, -M: 最高价（必需）
  --grids, -g: 网格数量（必需）
  --groups, -G: 分组数量（可选），必须是网格数量的因数
  --output, -o: 输出文件路径（可选），如果未指定则根据命令行参数自动生成默认文件名

示例：
  # 计算 BTC-USDT 交易对，资金 10000 USDT，价格区间 1000-2000 USDT，10 个网格
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 10

  # 使用长选项
  python3 grid_calculator.py --trading-pair BTC-USDT --capital 10000 --min-price 1000 --max-price 2000 --grids 10

  # 计算 BTC-USDT 交易对，12 个网格分成 4 组（每组 3 个网格）
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 12 -G 4

  # 计算 ETH-USDT 交易对，资金 5000 USDT，价格区间 2000-3000 USDT，5 个网格
  python3 grid_calculator.py -p ETH-USDT -c 5000 -m 2000 -M 3000 -g 5

  # 将结果保存到指定文件
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 10 -o result.md

  # 不指定 output 参数，将自动生成默认文件名
  # 例如：btc_usdt_capital_10000_min_price_1000_max_price_2000_grids_10.md
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 10

输出格式：
----------
脚本以 Markdown 格式输出以下部分：
1. 输入参数摘要
2. 等差数列网格计算结果（价格分布、买入详情、汇总）
3. 等比数列网格计算结果（价格分布、买入详情、汇总）
4. 两种网格类型的对比总结

输出格式说明：
- 所有输出均为 Markdown 格式，可直接保存为 .md 文件
- 使用 --output/-o 参数可将结果保存到指定文件

注意事项：
----------
1. 价格分布点数量 = 网格数量 + 1（包括最低价和最高价）
2. 买入网格数量 = 网格数量（最高价不包含买单）
3. 所有买入网格的资金总和等于输入的资金总额
4. 每个网格购买的基础资产数量相同（等差数列和等比数列分别相同）
5. 等比数列通常在相同资金下能购买更多的基础资产

参考文档：
----------
- grid_purchase_quantity_comparison.md：等差数列与等比数列购买量比较
- geometric_sequence_spacing_proof.md：等比数列间距性质验证
- arithmetic_grid_tutorial/：等差数列网格教程
- geometric_grid_tutorial/：等比数列网格教程
"""

import argparse
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class GroupStats:
    """分组统计信息"""

    group_number: int  # 组别编号（从 1 开始）
    quote_amount: float  # 该组的资金总额（报价资产）
    base_amount: float  # 该组购买的基础资产数量


@dataclass
class GridResult:
    """网格计算结果"""

    grid_type: str  # "arithmetic" 或 "geometric"
    price_points: List[float]  # n+1 个价格点
    buy_prices: List[float]  # n 个买入价格
    quote_amounts: List[float]  # n 个网格投入的报价资产数量
    base_amounts: List[float]  # n 个网格购买的基础资产数量
    total_base_amount: float  # 总购买的基础资产数量
    total_quote_amount: float  # 总投入的报价资产数量
    average_price: float  # 平均价格 = 总投入资金 / 总购买的基础资产数量
    grid_returns: List[float]  # n 个网格的收益率（百分比），每个网格买入后到下一个价格点卖出的收益率


def calculate_arithmetic_grid(total_capital: float, min_price: float, max_price: float, num_grids: int) -> GridResult:
    """
    计算等差数列网格

    参数：
        total_capital: 资金总额（报价资产数量）
        min_price: 最低价
        max_price: 最高价
        num_grids: 网格数量 n

    返回：
        GridResult 对象

    说明：
        - 生成 n+1 个价格点（从最低价到最高价）
        - 只在 n 个层级买入（不包括最高价）
        - 计算逻辑：先计算买入层级的价格总和，然后根据总资金和价格总和计算每层购买量
        每层购买量 = 总资金 / 价格总和
        其中价格总和使用等差数列前 n 项和公式：S = n × (首项 + 末项) / 2
        注意：这里的末项是买入层级的最高价，不是价格分布的最高价
    """
    # 计算价格差（基于 n 个买入层级）
    # 价格分布为 n+1 个点，从 P_min 到 P_max
    # 买入层级为 n 个点，从 P_min 到某个价格
    # 买入层级的价格范围是 P_min 到 P_buy_max，其中 P_buy_max 是买入层级的最高价

    # 如果价格分布有 n+1 个点，买入层级有 n 个点
    # 价格差 = (P_max - P_min) / n
    price_diff = (max_price - min_price) / num_grids

    # 生成 n+1 个价格点（包括最高价）
    price_points = [min_price + i * price_diff for i in range(num_grids + 1)]
    # 确保最后一个价格点精确等于 max_price
    price_points[-1] = max_price

    # 买入层级：前 n 个价格点（不包括最高价）
    buy_prices = price_points[:num_grids]

    # 买入层级的最高价
    buy_max_price = buy_prices[-1]

    # 计算买入层级的价格总和
    # 这是等差数列前 n 项的和：S = n * (首项 + 末项) / 2
    price_sum = num_grids * (min_price + buy_max_price) / 2

    # 计算每层购买的基础资产数量
    # 原理：每个网格购买相同数量的基础资产，设每层购买量为 A
    # 则总资金 M = A × (P_1 + P_2 + ... + P_n) = A × price_sum
    # 因此：每层购买量 A = 总资金 / 价格总和
    base_amount_per_grid = total_capital / price_sum

    # 计算每个网格投入的报价资产数量和购买的基础资产数量
    quote_amounts = [base_amount_per_grid * price for price in buy_prices]
    base_amounts = [base_amount_per_grid] * num_grids

    # 计算总购买量
    total_base_amount = num_grids * base_amount_per_grid

    # 计算总投入资金
    total_quote_amount = sum(quote_amounts)

    # 计算平均价格
    average_price = total_quote_amount / total_base_amount if total_base_amount > 0 else 0.0

    # 计算每个网格的收益率
    # 对于每个买入网格 i，卖出价格是 price_points[i+1]
    grid_returns = []
    for i in range(len(buy_prices)):
        buy_price = buy_prices[i]
        sell_price = price_points[i + 1]  # 下一个价格点
        return_pct = (sell_price - buy_price) / buy_price * 100.0
        grid_returns.append(return_pct)

    return GridResult(
        grid_type="arithmetic",
        price_points=price_points,
        buy_prices=buy_prices,
        quote_amounts=quote_amounts,
        base_amounts=base_amounts,
        total_base_amount=total_base_amount,
        total_quote_amount=total_quote_amount,
        average_price=average_price,
        grid_returns=grid_returns,
    )


def calculate_geometric_grid(total_capital: float, min_price: float, max_price: float, num_grids: int) -> GridResult:
    """
    计算等比数列网格

    参数：
        total_capital: 资金总额（报价资产数量）
        min_price: 最低价
        max_price: 最高价
        num_grids: 网格数量 n

    返回：
        GridResult 对象

    说明：
        - 生成 n+1 个价格点（从最低价到最高价）
        - 只在 n 个层级买入（不包括最高价）
        - 计算逻辑：先计算买入层级的价格总和，然后根据总资金和价格总和计算每层购买量
        每层购买量 = 总资金 / 价格总和
        其中价格总和使用等比数列前 n 项和公式：S = P_min × (r^n - 1) / (r - 1)
        其中 r 是买入层级的公比，r = (买入层级最高价 / P_min)^(1/(n-1))
        注意：买入层级的最高价是价格分布的第 n 个点，不是最高价
    """
    # 计算公比
    # 价格分布有 n+1 个点，买入层级有 n 个点
    # 买入层级的最高价对应价格分布的第 n 个点
    # 如果价格分布从 P_min 到 P_max，共 n+1 个点
    # 那么买入层级从 P_min 到某个价格，共 n 个点
    # 公比 r = (买入层级最高价 / P_min)^(1/(n-1))
    # 但为了生成 n+1 个价格点，我们使用 r = (P_max / P_min)^(1/n)
    ratio = (max_price / min_price) ** (1.0 / num_grids)

    # 生成 n+1 个价格点（包括最高价）
    price_points = [min_price * (ratio**i) for i in range(num_grids + 1)]
    # 确保最后一个价格点精确等于 max_price
    price_points[-1] = max_price

    # 买入层级：前 n 个价格点（不包括最高价）
    buy_prices = price_points[:num_grids]

    # 买入层级的最高价
    buy_max_price = buy_prices[-1]

    # 计算买入层级的公比（基于 n 个买入层级）
    # 买入层级从 P_min 到 buy_max_price，共 n 个点
    # 公比 r_buy = (buy_max_price / P_min)^(1/(n-1))
    if num_grids > 1:
        ratio_buy = (buy_max_price / min_price) ** (1.0 / (num_grids - 1))
    else:
        ratio_buy = 1.0

    # 计算买入层级的价格总和
    # 这是等比数列前 n 项的和：S = P_min * (r^n - 1) / (r - 1)
    if abs(ratio_buy - 1.0) < 1e-10:
        # 如果公比接近 1，使用等差数列近似
        price_sum = num_grids * min_price
    else:
        price_sum = min_price * (ratio_buy**num_grids - 1) / (ratio_buy - 1)

    # 计算每层购买的基础资产数量
    # 原理：每个网格购买相同数量的基础资产，设每层购买量为 B
    # 则总资金 M = B × (P_1 + P_2 + ... + P_n) = B × price_sum
    # 因此：每层购买量 B = 总资金 / 价格总和
    base_amount_per_grid = total_capital / price_sum

    # 计算每个网格投入的报价资产数量和购买的基础资产数量
    quote_amounts = [base_amount_per_grid * price for price in buy_prices]
    base_amounts = [base_amount_per_grid] * num_grids

    # 计算总购买量
    total_base_amount = num_grids * base_amount_per_grid

    # 计算总投入资金
    total_quote_amount = sum(quote_amounts)

    # 计算平均价格
    average_price = total_quote_amount / total_base_amount if total_base_amount > 0 else 0.0

    # 计算每个网格的收益率
    # 对于每个买入网格 i，卖出价格是 price_points[i+1]
    grid_returns = []
    for i in range(len(buy_prices)):
        buy_price = buy_prices[i]
        sell_price = price_points[i + 1]  # 下一个价格点
        return_pct = (sell_price - buy_price) / buy_price * 100.0
        grid_returns.append(return_pct)

    return GridResult(
        grid_type="geometric",
        price_points=price_points,
        buy_prices=buy_prices,
        quote_amounts=quote_amounts,
        base_amounts=base_amounts,
        total_base_amount=total_base_amount,
        total_quote_amount=total_quote_amount,
        average_price=average_price,
        grid_returns=grid_returns,
    )


def calculate_group_stats(grid_result: GridResult, num_groups: int) -> List[GroupStats]:
    """
    计算分组统计信息

    参数：
        grid_result: 网格计算结果
        num_groups: 分组数量

    返回：
        包含每个分组统计信息的列表
    """
    num_grids = len(grid_result.buy_prices)
    grids_per_group = num_grids // num_groups
    group_stats = []

    for group_idx in range(num_groups):
        start_idx = group_idx * grids_per_group
        end_idx = start_idx + grids_per_group

        # 计算该组的资金总额和购买量
        group_quote_amount = sum(grid_result.quote_amounts[start_idx:end_idx])
        group_base_amount = sum(grid_result.base_amounts[start_idx:end_idx])

        group_stats.append(
            GroupStats(
                group_number=group_idx + 1,
                quote_amount=group_quote_amount,
                base_amount=group_base_amount,
            )
        )

    return group_stats


def generate_default_filename(
    trading_pair: str,
    total_capital: float,
    min_price: float,
    max_price: float,
    num_grids: int,
    num_groups: Optional[int] = None,
) -> str:
    """
    根据命令行参数生成默认文件名

    参数：
        trading_pair: 交易对
        total_capital: 资金总额
        min_price: 最低价
        max_price: 最高价
        num_grids: 网格数量
        num_groups: 分组数量（可选）

    返回：
        文件名（全小写+下划线格式，扩展名为 .md）
    """
    # 将交易对转换为小写并替换连字符为下划线
    pair_name = trading_pair.lower().replace("-", "_")

    # 构建文件名各部分
    parts = [
        pair_name,
        f"capital_{int(total_capital)}",
        f"min_price_{int(min_price)}",
        f"max_price_{int(max_price)}",
        f"grids_{num_grids}",
    ]

    # 如果有分组，添加分组信息
    if num_groups is not None:
        parts.append(f"groups_{num_groups}")

    # 组合文件名
    filename = "_".join(parts) + ".md"
    return filename


def format_output(
    trading_pair: str,
    total_capital: float,
    min_price: float,
    max_price: float,
    num_grids: int,
    arithmetic_result: GridResult,
    geometric_result: GridResult,
    num_groups: Optional[int] = None,
) -> str:
    """
    格式化输出结果为 Markdown 格式

    参数：
        trading_pair: 交易对
        total_capital: 资金总额
        min_price: 最低价
        max_price: 最高价
        num_grids: 网格数量
        arithmetic_result: 等差数列网格结果
        geometric_result: 等比数列网格结果
        num_groups: 分组数量（可选）

    返回：
        Markdown 格式的字符串
    """
    base_asset, quote_asset = trading_pair.split("-")
    lines = []

    # 一级标题
    lines.append("# 网格交易计算结果")
    lines.append("")

    # 输入参数
    lines.append("## 输入参数")
    lines.append("")
    lines.append(f"- **交易对**: {trading_pair}")
    lines.append(f"- **资金总额**: {total_capital:,.2f} {quote_asset}")
    lines.append(f"- **价格区间**: {min_price:,.2f} - {max_price:,.2f} {quote_asset}")
    lines.append(f"- **网格数量**: {num_grids}")
    lines.append(f"- **价格分布点数量**: {num_grids + 1}")
    if num_groups is not None:
        lines.append(f"- **分组数量**: {num_groups}（每组 {num_grids // num_groups} 个网格）")
    lines.append("")

    # 输出等比数列网格结果
    lines.append("## 等比数列网格")
    lines.append("")

    # 价格分布点
    lines.append(f"### 价格分布点（共 {len(geometric_result.price_points)} 个）")
    lines.append("")
    price_table_rows = []
    for i, price in enumerate(geometric_result.price_points):
        marker = "（最高价，不含买单）" if i == len(geometric_result.price_points) - 1 else ""
        price_table_rows.append(f"| {i+1} | {price:,.4f} {quote_asset} | {marker} |")
    lines.append("| 序号 | 价格 | 备注 |")
    lines.append("|------|------|------|")
    lines.extend(price_table_rows)
    lines.append("")

    # 买入网格详情
    lines.append(f"### 买入网格详情（共 {len(geometric_result.buy_prices)} 个）")
    lines.append("")
    lines.append(f"| 层级 | 价格 ({quote_asset}) | 投入资金 ({quote_asset}) | 购买量 ({base_asset}) | 收益率 (%) |")
    lines.append("|------|------|------|------|------|")

    total_quote_check = 0
    geometric_avg_return = (
        sum(geometric_result.grid_returns) / len(geometric_result.grid_returns)
        if geometric_result.grid_returns
        else 0.0
    )

    # 如果有分组，在表格中插入分组汇总
    if num_groups is not None:
        geometric_group_stats = calculate_group_stats(geometric_result, num_groups)
        grids_per_group = len(geometric_result.buy_prices) // num_groups
        group_idx = 0

        for i in range(len(geometric_result.buy_prices)):
            price = geometric_result.buy_prices[i]
            quote = geometric_result.quote_amounts[i]
            base = geometric_result.base_amounts[i]
            return_pct = geometric_result.grid_returns[i]
            total_quote_check += quote
            lines.append(f"| {i+1} | {price:,.4f} | {quote:,.4f} | {base:,.8f} | {return_pct:,.2f} |")

            # 如果是组的最后一个网格，插入分组汇总行
            if (i + 1) % grids_per_group == 0:
                group_stat = geometric_group_stats[group_idx]
                lines.append(
                    f"| **第 {group_stat.group_number} 组合计** | | **{group_stat.quote_amount:,.4f}** | **{group_stat.base_amount:,.8f}** | |"
                )
                group_idx += 1
                # 如果不是最后一组，添加分隔行
                if group_idx < num_groups:
                    lines.append("| | | | | |")
    else:
        # 没有分组时，正常输出所有网格
        for i in range(len(geometric_result.buy_prices)):
            price = geometric_result.buy_prices[i]
            quote = geometric_result.quote_amounts[i]
            base = geometric_result.base_amounts[i]
            return_pct = geometric_result.grid_returns[i]
            total_quote_check += quote
            lines.append(f"| {i+1} | {price:,.4f} | {quote:,.4f} | {base:,.8f} | {return_pct:,.2f} |")

    # 合计行
    lines.append(
        f"| **合计** | | **{total_quote_check:,.4f}** | **{geometric_result.total_base_amount:,.8f}** | **{geometric_avg_return:,.2f}** |"
    )
    lines.append("")

    # 汇总统计
    lines.append("### 汇总统计")
    lines.append("")
    lines.append(f"- **总购买量**: {geometric_result.total_base_amount:,.8f} {base_asset}")
    lines.append(f"- **总投入资金**: {total_quote_check:,.2f} {quote_asset}")
    lines.append(f"- **平均价格**: {geometric_result.average_price:,.4f} {quote_asset}/{base_asset}")
    lines.append(f"- **平均单网格收益率**: {geometric_avg_return:,.2f}%")
    lines.append("")

    # 输出等差数列网格结果
    lines.append("## 等差数列网格")
    lines.append("")

    # 价格分布点
    lines.append(f"### 价格分布点（共 {len(arithmetic_result.price_points)} 个）")
    lines.append("")
    price_table_rows = []
    for i, price in enumerate(arithmetic_result.price_points):
        marker = "（最高价，不含买单）" if i == len(arithmetic_result.price_points) - 1 else ""
        price_table_rows.append(f"| {i+1} | {price:,.4f} {quote_asset} | {marker} |")
    lines.append("| 序号 | 价格 | 备注 |")
    lines.append("|------|------|------|")
    lines.extend(price_table_rows)
    lines.append("")

    # 买入网格详情
    lines.append(f"### 买入网格详情（共 {len(arithmetic_result.buy_prices)} 个）")
    lines.append("")
    lines.append(f"| 层级 | 价格 ({quote_asset}) | 投入资金 ({quote_asset}) | 购买量 ({base_asset}) | 收益率 (%) |")
    lines.append("|------|------|------|------|------|")

    total_quote_check = 0
    arithmetic_avg_return = (
        sum(arithmetic_result.grid_returns) / len(arithmetic_result.grid_returns)
        if arithmetic_result.grid_returns
        else 0.0
    )

    # 如果有分组，在表格中插入分组汇总
    if num_groups is not None:
        arithmetic_group_stats = calculate_group_stats(arithmetic_result, num_groups)
        grids_per_group = len(arithmetic_result.buy_prices) // num_groups
        group_idx = 0

        for i in range(len(arithmetic_result.buy_prices)):
            price = arithmetic_result.buy_prices[i]
            quote = arithmetic_result.quote_amounts[i]
            base = arithmetic_result.base_amounts[i]
            return_pct = arithmetic_result.grid_returns[i]
            total_quote_check += quote
            lines.append(f"| {i+1} | {price:,.4f} | {quote:,.4f} | {base:,.8f} | {return_pct:,.2f} |")

            # 如果是组的最后一个网格，插入分组汇总行
            if (i + 1) % grids_per_group == 0:
                group_stat = arithmetic_group_stats[group_idx]
                lines.append(
                    f"| **第 {group_stat.group_number} 组合计** | | **{group_stat.quote_amount:,.4f}** | **{group_stat.base_amount:,.8f}** | |"
                )
                group_idx += 1
                # 如果不是最后一组，添加分隔行
                if group_idx < num_groups:
                    lines.append("| | | | | |")
    else:
        # 没有分组时，正常输出所有网格
        for i in range(len(arithmetic_result.buy_prices)):
            price = arithmetic_result.buy_prices[i]
            quote = arithmetic_result.quote_amounts[i]
            base = arithmetic_result.base_amounts[i]
            return_pct = arithmetic_result.grid_returns[i]
            total_quote_check += quote
            lines.append(f"| {i+1} | {price:,.4f} | {quote:,.4f} | {base:,.8f} | {return_pct:,.2f} |")

    # 合计行
    lines.append(
        f"| **合计** | | **{total_quote_check:,.4f}** | **{arithmetic_result.total_base_amount:,.8f}** | **{arithmetic_avg_return:,.2f}** |"
    )
    lines.append("")

    # 汇总统计
    lines.append("### 汇总统计")
    lines.append("")
    lines.append(f"- **总购买量**: {arithmetic_result.total_base_amount:,.8f} {base_asset}")
    lines.append(f"- **总投入资金**: {total_quote_check:,.2f} {quote_asset}")
    lines.append(f"- **平均价格**: {arithmetic_result.average_price:,.4f} {quote_asset}/{base_asset}")
    lines.append(f"- **平均单网格收益率**: {arithmetic_avg_return:,.2f}%")
    lines.append("")

    # 对比总结
    lines.append("## 对比总结")
    lines.append("")
    advantage_pct = (
        (geometric_result.total_base_amount - arithmetic_result.total_base_amount)
        / arithmetic_result.total_base_amount
        * 100
    )

    lines.append("### 购买量对比")
    lines.append("")
    lines.append(f"- **等比数列总购买量**: {geometric_result.total_base_amount:,.8f} {base_asset}")
    lines.append(f"- **等差数列总购买量**: {arithmetic_result.total_base_amount:,.8f} {base_asset}")
    if advantage_pct > 0:
        lines.append(f"- **等比数列优势**: +{advantage_pct:.2f}%")
    else:
        lines.append(f"- **等比数列优势**: {advantage_pct:.2f}%")
    lines.append("")

    lines.append("### 平均价格对比")
    lines.append("")
    lines.append(f"- **等比数列平均价格**: {geometric_result.average_price:,.4f} {quote_asset}/{base_asset}")
    lines.append(f"- **等差数列平均价格**: {arithmetic_result.average_price:,.4f} {quote_asset}/{base_asset}")
    price_diff_pct = (
        (arithmetic_result.average_price - geometric_result.average_price) / arithmetic_result.average_price * 100
    )
    if price_diff_pct > 0:
        lines.append(f"- **等比数列平均价格优势**: -{price_diff_pct:.2f}%（更低的价格意味着更好的买入成本）")
    else:
        lines.append(f"- **等比数列平均价格差异**: {price_diff_pct:.2f}%")
    lines.append("")

    # 平均收益率对比
    lines.append("### 平均收益率对比")
    lines.append("")
    lines.append(f"- **等比数列平均单网格收益率**: {geometric_avg_return:,.2f}%")
    lines.append(f"- **等差数列平均单网格收益率**: {arithmetic_avg_return:,.2f}%")
    return_diff = geometric_avg_return - arithmetic_avg_return
    if return_diff > 0:
        lines.append(f"- **等比数列收益率优势**: +{return_diff:.2f}%")
    elif return_diff < 0:
        lines.append(f"- **等比数列收益率差异**: {return_diff:.2f}%")
    else:
        lines.append("- **两种网格的平均收益率相同**")
    lines.append("")

    # 返回 Markdown 字符串
    return "\n".join(lines)


def main():
    """
    主函数

    解析命令行参数，计算并输出网格交易参数。
    """
    parser = argparse.ArgumentParser(
        description="计算网格交易的价格分布、资金分配和购买量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
----------

示例 1：计算 BTC-USDT 网格参数（使用短选项）
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 10
  
  这将计算：
  - 交易对：BTC-USDT
  - 资金总额：10000 USDT
  - 价格区间：1000-2000 USDT
  - 网格数量：10 个
  - 输出：等差数列和等比数列两种网格的参数

示例 2：计算 BTC-USDT 网格参数（带分组）
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 12 -G 4
  
  这将计算：
  - 交易对：BTC-USDT
  - 资金总额：10000 USDT
  - 价格区间：1000-2000 USDT
  - 网格数量：12 个
  - 分组数量：4 组（每组 3 个网格）
  - 输出：在买入网格详情表格中，每组网格后会显示该组的汇总信息

示例 3：计算 ETH-USDT 网格参数（使用长选项）
  python3 grid_calculator.py --trading-pair ETH-USDT --capital 5000 --min-price 2000 --max-price 3000 --grids 5
  
  这将计算：
  - 交易对：ETH-USDT
  - 资金总额：5000 USDT
  - 价格区间：2000-3000 USDT
  - 网格数量：5 个

示例 4：将结果保存到文件
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 10 -o result.md
  
  这将计算网格参数并将 Markdown 格式的结果保存到 result.md 文件

输出说明:
----------
脚本以 Markdown 格式输出以下内容：
1. 输入参数摘要
2. 等差数列网格：
   - 价格分布点（n+1 个）
   - 买入网格详情（n 个网格的价格、投入资金、购买量）
   - 如果指定了分组，每组网格后会显示该组的汇总信息
   - 总购买量和总投入资金
3. 等比数列网格：
   - 价格分布点（n+1 个）
   - 买入网格详情（n 个网格的价格、投入资金、购买量）
   - 如果指定了分组，每组网格后会显示该组的汇总信息
   - 总购买量和总投入资金
4. 对比总结：两种网格类型的购买量对比

输出格式：
- 所有输出均为 Markdown 格式，可直接保存为 .md 文件
- 使用 --output/-o 参数可将结果保存到指定文件
- 如果未指定 --output 参数，将根据命令行参数自动生成默认文件名（全小写+下划线格式）并保存

注意事项:
----------
- 最高价不包含买单，仅作为卖出参考点
- 价格分布点数量 = 网格数量 + 1
- 买入网格数量 = 网格数量
- 所有买入网格的资金总和等于输入的资金总额
        """,
    )

    parser.add_argument(
        "--trading-pair",
        "-p",
        type=str,
        required=True,
        help="交易对，格式：基础资产-报价资产（例如：BTC-USDT、ETH-USDT）",
    )
    parser.add_argument(
        "--capital",
        "-c",
        type=float,
        required=True,
        help="资金总额，以报价资产计价（例如：10000 表示 10000 USDT）",
    )
    parser.add_argument(
        "--min-price",
        "-m",
        type=float,
        required=True,
        help="最低价，网格交易的价格区间下限（必须大于 0）",
    )
    parser.add_argument(
        "--max-price",
        "-M",
        type=float,
        required=True,
        help="最高价，网格交易的价格区间上限（必须大于最低价）",
    )
    parser.add_argument(
        "--grids",
        "-g",
        type=int,
        required=True,
        help="网格数量 n，即买入订单的层级数量（必须大于 0）",
    )
    parser.add_argument(
        "--groups",
        "-G",
        type=int,
        default=None,
        help="分组数量，将网格按顺序分成指定数量的分组（必须是网格数量的因数）",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="输出文件路径（可选），如果未指定则根据命令行参数自动生成默认文件名（全小写+下划线格式）",
    )

    args = parser.parse_args()

    # 参数验证
    if args.capital <= 0:
        print("错误: 资金总额必须大于 0")
        return

    if args.min_price <= 0 or args.max_price <= 0:
        print("错误: 价格必须大于 0")
        return

    if args.min_price >= args.max_price:
        print("错误: 最低价必须小于最高价")
        return

    if args.grids <= 0:
        print("错误: 网格数量必须大于 0")
        return

    if "-" not in args.trading_pair:
        print("错误: 交易对格式不正确，应为：基础资产-报价资产（例如：BTC-USDT）")
        return

    # 验证分组数量
    if args.groups is not None:
        if args.groups <= 0:
            print("错误: 分组数量必须大于 0")
            return
        if args.grids % args.groups != 0:
            print(f"错误: 分组数量 {args.groups} 必须是网格数量 {args.grids} 的因数")
            return

    # 计算两种网格
    arithmetic_result = calculate_arithmetic_grid(args.capital, args.min_price, args.max_price, args.grids)

    geometric_result = calculate_geometric_grid(args.capital, args.min_price, args.max_price, args.grids)

    # 生成 Markdown 输出
    markdown_output = format_output(
        args.trading_pair,
        args.capital,
        args.min_price,
        args.max_price,
        args.grids,
        arithmetic_result,
        geometric_result,
        args.groups,
    )

    # 输出结果
    if args.output:
        # 使用指定的文件名
        output_file = args.output
    else:
        # 使用默认文件名
        output_file = generate_default_filename(
            args.trading_pair,
            args.capital,
            args.min_price,
            args.max_price,
            args.grids,
            args.groups,
        )

    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_output)
    print(f"结果已保存到文件: {output_file}")


if __name__ == "__main__":
    main()
