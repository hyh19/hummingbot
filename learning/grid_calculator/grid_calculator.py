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
- num_groups: 分组数量（默认 1），将网格按顺序分成指定数量的分组（必须是网格数量的因数）
- group_ratio: 分组资金分配公比（默认 1 表示各组均分资金，group_ratio > 1 时倾向于给高价组更多资金，0 < group_ratio < 1 时倾向于给低价组更多资金）

输出内容：
----------
对于每种网格类型，输出以下信息：
1. 价格分布点：n+1 个价格点（从最低价到最高价）
   - 注意：最高价不包含买单，仅作为卖出参考点
2. 买入网格详情：n 个网格的详细信息
   - 每个网格的价格
   - 每个网格投入的报价资产数量
   - 每组内每个网格购买的基础资产数量
   - 如果指定了分组数量，会在每组网格后显示该组的汇总信息（资金总额、购买量）
3. 汇总统计：
   - 总购买的基础资产数量
   - 总投入的报价资产数量
   - 平均价格（总投入资金 / 总购买的基础资产数量）
4. 对比分析：等比数列与等差数列的购买量、平均价格与收益率对比

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
  --groups, -G: 分组数量（默认 1），必须是网格数量的因数
  --group-ratio, -R: 资金分配公比（可选，> 0，默认 1 表示分组等额分配，group_ratio > 1 时高价组获得更多资金，0 < group_ratio < 1 时低价组获得更多资金）
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
2. 等比数列网格计算结果（价格分布、买入详情、汇总）
3. 等差数列网格计算结果（价格分布、买入详情、汇总）
4. 两种网格类型的对比总结（购买量、平均价格与收益率）

输出格式说明：
- 所有输出均为 Markdown 格式，可直接保存为 .md 文件
- 使用 --output/-o 参数可将结果保存到指定文件

注意事项：
----------
1. 价格分布点数量 = 网格数量 + 1（包括最低价和最高价）
2. 买入网格数量 = 网格数量（最高价不包含买单）
3. 所有买入网格的资金总和等于输入的资金总额
4. 每组内的网格购买的基础资产数量相同，不同组之间因资金分配比例而异
5. 等比数列通常在相同资金下能购买更多的基础资产

参考文档：
----------
- grid_purchase_quantity_comparison.md：等差数列与等比数列购买量比较
- geometric_sequence_spacing_proof.md：等比数列间距性质验证
- arithmetic_grid_tutorial/：等差数列网格教程
- geometric_grid_tutorial/：等比数列网格教程
"""

import argparse
from typing import List
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
    group_quote_totals: List[float]  # 每组的资金总额（报价资产）
    group_base_amounts_per_grid: List[float]  # 每组中单个网格的基础资产购买量


def compute_group_quote_shares(
    total_capital: float,
    num_groups: int,
    fund_ratio: float,
) -> List[float]:
    """
    根据资金分配公比计算分组资金权重，并返回每组的资金配额。

    参数：
        total_capital: 总资金
        num_groups: 分组数量
        fund_ratio: 资金分配公比（> 0，fund_ratio > 1 时高价组资金更多，0 < fund_ratio < 1 时低价组资金更多）

    返回：
        长度为 num_groups 的列表，顺序与分组索引一致（从低价组到高价组）。
        fund_ratio > 1 时列表随索引递增，0 < fund_ratio < 1 时列表随索引递减。
        最后一项会进行浮点修正以确保份额之和等于 total_capital。
    """
    if num_groups <= 0:
        raise ValueError("分组数量必须大于 0")

    if num_groups == 1:
        return [total_capital]

    normalized_ratio = max(fund_ratio, 1e-12)

    if abs(normalized_ratio - 1.0) < 1e-12:
        shares = [total_capital / num_groups] * num_groups
    else:
        # fund_ratio > 1 时份额按索引递增，0 < fund_ratio < 1 时份额按索引递减
        weights = [normalized_ratio**i for i in range(num_groups)]
        weight_sum = sum(weights)
        shares = [total_capital * weight / weight_sum for weight in weights]

    current_total = sum(shares)
    shares[-1] += total_capital - current_total
    return shares


def calculate_arithmetic_grid(
    total_capital: float,
    min_price: float,
    max_price: float,
    num_grids: int,
    num_groups: int,
    group_quote_shares: List[float],
) -> GridResult:
    """
    计算等差数列网格

    参数：
        total_capital: 资金总额（报价资产数量）
        min_price: 最低价
        max_price: 最高价
        num_grids: 网格数量 n
        num_groups: 分组数量
        group_quote_shares: 分组资金份额列表（长度为分组数量，顺序对应从低价组到高价组）

    返回：
        GridResult 对象

    说明：
        - 生成 n+1 个价格点（从最低价到最高价）
        - 只在前 n 个层级买入（不包括最高价）
        - 将总资金按分组资金份额进行分配，每组共享统一的价格分布点
        - 在每组内，根据该组买入价格的总和计算单个网格的基础资产购买量
        - 每组内的网格购买量一致，不同组之间的购买量根据资金份额不同而变化
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

    if len(group_quote_shares) != num_groups:
        raise ValueError("group_quote_shares 的长度必须等于分组数量")

    if abs(sum(group_quote_shares) - total_capital) > 1e-6:
        raise ValueError("group_quote_shares 的总和必须等于总资金")

    grids_per_group = num_grids // num_groups

    quote_amounts: List[float] = []
    base_amounts: List[float] = []
    group_quote_totals: List[float] = []
    group_base_amounts_per_grid: List[float] = []

    for group_idx in range(num_groups):
        start_idx = group_idx * grids_per_group
        end_idx = start_idx + grids_per_group
        group_prices = buy_prices[start_idx:end_idx]

        group_quote_share = group_quote_shares[group_idx]

        # 每组的价格分布点与大网格一致，按组内价格总和分配基础资产
        price_sum_group = sum(group_prices)
        base_amount_per_grid_group = group_quote_share / price_sum_group if price_sum_group > 0 else 0.0

        for price in group_prices:
            base_amounts.append(base_amount_per_grid_group)
            quote_amounts.append(base_amount_per_grid_group * price)

        group_quote_totals.append(group_quote_share)
        group_base_amounts_per_grid.append(base_amount_per_grid_group)

    # 计算平均价格
    total_quote_amount = sum(quote_amounts)
    total_base_amount = sum(base_amounts)
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
        group_quote_totals=group_quote_totals,
        group_base_amounts_per_grid=group_base_amounts_per_grid,
    )


def calculate_geometric_grid(
    total_capital: float,
    min_price: float,
    max_price: float,
    num_grids: int,
    num_groups: int,
    group_quote_shares: List[float],
) -> GridResult:
    """
    计算等比数列网格

    参数：
        total_capital: 资金总额（报价资产数量）
        min_price: 最低价
        max_price: 最高价
        num_grids: 网格数量 n
        num_groups: 分组数量
        group_quote_shares: 分组资金份额列表（长度为分组数量，顺序对应从低价组到高价组）

    返回：
        GridResult 对象

    说明：
        - 生成 n+1 个价格点（从最低价到最高价）
        - 只在前 n 个层级买入（不包括最高价）
        - 将总资金按分组资金份额进行分配，列表顺序对应从低价组到高价组
        - 在每组内，根据该组买入价格的总和计算单个网格的基础资产购买量
        - 每组内的网格购买量一致，不同组之间的购买量根据资金份额不同而变化
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

    if len(group_quote_shares) != num_groups:
        raise ValueError("group_quote_shares 的长度必须等于分组数量")

    if abs(sum(group_quote_shares) - total_capital) > 1e-6:
        raise ValueError("group_quote_shares 的总和必须等于总资金")

    grids_per_group = num_grids // num_groups

    quote_amounts: List[float] = []
    base_amounts: List[float] = []
    group_quote_totals: List[float] = []
    group_base_amounts_per_grid: List[float] = []

    for group_idx in range(num_groups):
        start_idx = group_idx * grids_per_group
        end_idx = start_idx + grids_per_group
        group_prices = buy_prices[start_idx:end_idx]

        group_quote_share = group_quote_shares[group_idx]

        # 每组沿用原有价格点，根据组内价格总和分配基础资产
        price_sum_group = sum(group_prices)
        base_amount_per_grid_group = group_quote_share / price_sum_group if price_sum_group > 0 else 0.0

        for price in group_prices:
            base_amounts.append(base_amount_per_grid_group)
            quote_amounts.append(base_amount_per_grid_group * price)

        group_quote_totals.append(group_quote_share)
        group_base_amounts_per_grid.append(base_amount_per_grid_group)

    # 计算平均价格
    total_quote_amount = sum(quote_amounts)
    total_base_amount = sum(base_amounts)
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
        group_quote_totals=group_quote_totals,
        group_base_amounts_per_grid=group_base_amounts_per_grid,
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
        group_quote_amount = grid_result.group_quote_totals[group_idx]
        group_base_amount = grid_result.group_base_amounts_per_grid[group_idx] * grids_per_group

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
    num_groups: int = 1,
    fund_ratio: float = 1.0,
) -> str:
    """
    根据命令行参数生成默认文件名

    参数：
        trading_pair: 交易对
        total_capital: 资金总额
        min_price: 最低价
        max_price: 最高价
        num_grids: 网格数量
        num_groups: 分组数量
        fund_ratio: 资金分配公比

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

    # 如果分组数量大于 1，添加分组信息
    if num_groups > 1:
        parts.append(f"groups_{num_groups}")
    if abs(fund_ratio - 1.0) > 1e-12:
        parts.append(f"group_ratio_{fund_ratio:.4f}".replace(".", "_"))

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
    num_groups: int = 1,
    fund_ratio: float = 1.0,
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
        num_groups: 分组数量
        fund_ratio: 资金分配公比

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
    if num_groups > 1:
        lines.append(f"- **分组数量**: {num_groups}（每组 {num_grids // num_groups} 个网格）")
        lines.append(f"- **资金分配公比**: {fund_ratio:.4f}")
    lines.append("")

    # 输出等比数列网格结果
    lines.append("## 等比数列网格")
    lines.append("")

    # 价格分布点
    lines.append(f"### 价格分布点（共 {len(geometric_result.price_points)} 个，等比）")
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
    lines.append(f"### 买入网格详情（共 {len(geometric_result.buy_prices)} 个，等比）")
    lines.append("")
    lines.append(
        f"| 层级 | 价格 ({quote_asset}) | 投入资金 ({quote_asset}) | 购买量 ({base_asset}) | 收益率 (%) | 收益额 ({quote_asset}) |"
    )
    lines.append("|------|------|------|------|------|------|")

    total_quote_check = 0
    geometric_avg_return = (
        sum(geometric_result.grid_returns) / len(geometric_result.grid_returns)
        if geometric_result.grid_returns
        else 0.0
    )

    # 如果有分组，在表格中插入分组汇总
    if num_groups > 1:
        geometric_group_stats = calculate_group_stats(geometric_result, num_groups)
        grids_per_group = len(geometric_result.buy_prices) // num_groups
        group_idx = 0

        for i in range(len(geometric_result.buy_prices)):
            price = geometric_result.buy_prices[i]
            quote = geometric_result.quote_amounts[i]
            base = geometric_result.base_amounts[i]
            return_pct = geometric_result.grid_returns[i]
            sell_price = geometric_result.price_points[i + 1]
            profit_amount = base * (sell_price - price)
            total_quote_check += quote
            lines.append(
                f"| {i+1} | {price:,.4f} | {quote:,.4f} | {base:,.8f} | {return_pct:,.2f} | {profit_amount:,.4f} |"
            )

            # 如果是组的最后一个网格，插入分组汇总行
            if (i + 1) % grids_per_group == 0:
                group_stat = geometric_group_stats[group_idx]
                group_start = group_idx * grids_per_group
                group_end = group_start + grids_per_group
                group_profit = sum(
                    geometric_result.base_amounts[j]
                    * (geometric_result.price_points[j + 1] - geometric_result.buy_prices[j])
                    for j in range(group_start, group_end)
                )
                lines.append(
                    f"| **第 {group_stat.group_number} 组合计** | | **{group_stat.quote_amount:,.4f}** | **{group_stat.base_amount:,.8f}** | | **{group_profit:,.4f}** |"
                )
                group_idx += 1
                # 如果不是最后一组，添加分隔行
                if group_idx < num_groups:
                    lines.append("| | | | | | |")
    else:
        # 没有分组时，正常输出所有网格
        for i in range(len(geometric_result.buy_prices)):
            price = geometric_result.buy_prices[i]
            quote = geometric_result.quote_amounts[i]
            base = geometric_result.base_amounts[i]
            return_pct = geometric_result.grid_returns[i]
            sell_price = geometric_result.price_points[i + 1]
            profit_amount = base * (sell_price - price)
            total_quote_check += quote
            lines.append(
                f"| {i+1} | {price:,.4f} | {quote:,.4f} | {base:,.8f} | {return_pct:,.2f} | {profit_amount:,.4f} |"
            )

    # 合计行
    total_profit = sum(
        geometric_result.base_amounts[i]
        * (geometric_result.price_points[i + 1] - geometric_result.buy_prices[i])
        for i in range(len(geometric_result.buy_prices))
    )
    lines.append(
        f"| **合计** | | **{total_quote_check:,.4f}** | **{geometric_result.total_base_amount:,.8f}** | | |"
    )
    lines.append("")

    # 汇总统计
    lines.append("### 汇总统计（等比）")
    lines.append("")
    lowest_geometric_price = (
        geometric_result.buy_prices[0] if geometric_result.buy_prices else geometric_result.price_points[0]
    )
    potential_base_at_lowest_geometric = (
        geometric_result.total_quote_amount / lowest_geometric_price if lowest_geometric_price > 0 else 0.0
    )
    geometric_base_diff = geometric_result.total_base_amount - potential_base_at_lowest_geometric
    geometric_base_ratio = (
        geometric_result.total_base_amount / potential_base_at_lowest_geometric * 100
        if potential_base_at_lowest_geometric > 0
        else 0.0
    )
    lines.append(f"- **总购买量**: {geometric_result.total_base_amount:,.8f} {base_asset}")
    lines.append(f"- **总投入资金**: {geometric_result.total_quote_amount:,.2f} {quote_asset}")
    lines.append(f"- **平均价格**: {geometric_result.average_price:,.4f} {quote_asset}/{base_asset}")
    lines.append(f"- **最低价全仓购买量**: {potential_base_at_lowest_geometric:,.8f} {base_asset}")
    lines.append(
        f"- **与最低价全仓比较**: {geometric_base_diff:+,.8f} {base_asset}（实际为最低价全仓的 {geometric_base_ratio:,.2f}%）"
    )
    lines.append(f"- **平均单网格收益率**: {geometric_avg_return:,.2f}%")
    lines.append("")

    # 输出等差数列网格结果
    lines.append("## 等差数列网格")
    lines.append("")

    # 价格分布点
    lines.append(f"### 价格分布点（共 {len(arithmetic_result.price_points)} 个，等差）")
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
    lines.append(f"### 买入网格详情（共 {len(arithmetic_result.buy_prices)} 个，等差）")
    lines.append("")
    lines.append(
        f"| 层级 | 价格 ({quote_asset}) | 投入资金 ({quote_asset}) | 购买量 ({base_asset}) | 收益率 (%) | 收益额 ({quote_asset}) |"
    )
    lines.append("|------|------|------|------|------|------|")

    total_quote_check = 0
    arithmetic_avg_return = (
        sum(arithmetic_result.grid_returns) / len(arithmetic_result.grid_returns)
        if arithmetic_result.grid_returns
        else 0.0
    )

    # 如果有分组，在表格中插入分组汇总
    if num_groups > 1:
        arithmetic_group_stats = calculate_group_stats(arithmetic_result, num_groups)
        grids_per_group = len(arithmetic_result.buy_prices) // num_groups
        group_idx = 0

        for i in range(len(arithmetic_result.buy_prices)):
            price = arithmetic_result.buy_prices[i]
            quote = arithmetic_result.quote_amounts[i]
            base = arithmetic_result.base_amounts[i]
            return_pct = arithmetic_result.grid_returns[i]
            sell_price = arithmetic_result.price_points[i + 1]
            profit_amount = base * (sell_price - price)
            total_quote_check += quote
            lines.append(
                f"| {i+1} | {price:,.4f} | {quote:,.4f} | {base:,.8f} | {return_pct:,.2f} | {profit_amount:,.4f} |"
            )

            # 如果是组的最后一个网格，插入分组汇总行
            if (i + 1) % grids_per_group == 0:
                group_stat = arithmetic_group_stats[group_idx]
                group_start = group_idx * grids_per_group
                group_end = group_start + grids_per_group
                group_profit = sum(
                    arithmetic_result.base_amounts[j]
                    * (arithmetic_result.price_points[j + 1] - arithmetic_result.buy_prices[j])
                    for j in range(group_start, group_end)
                )
                lines.append(
                    f"| **第 {group_stat.group_number} 组合计** | | **{group_stat.quote_amount:,.4f}** | **{group_stat.base_amount:,.8f}** | | **{group_profit:,.4f}** |"
                )
                group_idx += 1
                # 如果不是最后一组，添加分隔行
                if group_idx < num_groups:
                    lines.append("| | | | | | |")
    else:
        # 没有分组时，正常输出所有网格
        for i in range(len(arithmetic_result.buy_prices)):
            price = arithmetic_result.buy_prices[i]
            quote = arithmetic_result.quote_amounts[i]
            base = arithmetic_result.base_amounts[i]
            return_pct = arithmetic_result.grid_returns[i]
            sell_price = arithmetic_result.price_points[i + 1]
            profit_amount = base * (sell_price - price)
            total_quote_check += quote
            lines.append(
                f"| {i+1} | {price:,.4f} | {quote:,.4f} | {base:,.8f} | {return_pct:,.2f} | {profit_amount:,.4f} |"
            )

    # 合计行
    total_profit = sum(
        arithmetic_result.base_amounts[i]
        * (arithmetic_result.price_points[i + 1] - arithmetic_result.buy_prices[i])
        for i in range(len(arithmetic_result.buy_prices))
    )
    lines.append(
        f"| **合计** | | **{total_quote_check:,.4f}** | **{arithmetic_result.total_base_amount:,.8f}** | | |"
    )
    lines.append("")

    # 汇总统计
    lines.append("### 汇总统计（等差）")
    lines.append("")
    lowest_arithmetic_price = (
        arithmetic_result.buy_prices[0] if arithmetic_result.buy_prices else arithmetic_result.price_points[0]
    )
    potential_base_at_lowest_arithmetic = (
        arithmetic_result.total_quote_amount / lowest_arithmetic_price if lowest_arithmetic_price > 0 else 0.0
    )
    arithmetic_base_diff = arithmetic_result.total_base_amount - potential_base_at_lowest_arithmetic
    arithmetic_base_ratio = (
        arithmetic_result.total_base_amount / potential_base_at_lowest_arithmetic * 100
        if potential_base_at_lowest_arithmetic > 0
        else 0.0
    )
    lines.append(f"- **总购买量**: {arithmetic_result.total_base_amount:,.8f} {base_asset}")
    lines.append(f"- **总投入资金**: {arithmetic_result.total_quote_amount:,.2f} {quote_asset}")
    lines.append(f"- **平均价格**: {arithmetic_result.average_price:,.4f} {quote_asset}/{base_asset}")
    lines.append(f"- **最低价全仓购买量**: {potential_base_at_lowest_arithmetic:,.8f} {base_asset}")
    lines.append(
        f"- **与最低价全仓比较**: {arithmetic_base_diff:+,.8f} {base_asset}（实际为最低价全仓的 {arithmetic_base_ratio:,.2f}%）"
    )
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
  - 输出：包含等比数列与等差数列的网格明细以及对比总结

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
2. 等比数列网格：
   - 价格分布点（n+1 个）
   - 买入网格详情（n 个网格的价格、投入资金、购买量与收益率）
   - 如果指定了分组，每组网格后会显示该组的汇总信息
   - 汇总统计（总购买量、总投入资金、平均价格、最低价全仓对比、平均单网格收益率）
3. 等差数列网格：
   - 价格分布点（n+1 个）
   - 买入网格详情（n 个网格的价格、投入资金、购买量与收益率）
   - 如果指定了分组，每组网格后会显示该组的汇总信息
   - 汇总统计（总购买量、总投入资金、平均价格、最低价全仓对比、平均单网格收益率）
4. 对比总结：
   - 购买量对比
   - 平均价格对比
   - 平均收益率对比

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
        default=1,
        help="分组数量，将网格按顺序分成指定数量的分组（必须是网格数量的因数，默认 1）",
    )
    parser.add_argument(
        "--group-ratio",
        "-R",
        type=float,
        default=1.0,
        help="资金分配公比（> 0，默认 1 表示分组等额分配，group_ratio > 1 时高价组获得更多资金，0 < group_ratio < 1 时低价组获得更多资金）",
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
    if args.groups <= 0:
        print("错误: 分组数量必须大于 0")
        return
    if args.grids % args.groups != 0:
        print(f"错误: 分组数量 {args.groups} 必须是网格数量 {args.grids} 的因数")
        return
    if args.group_ratio is not None and args.group_ratio <= 0:
        print("错误: 资金分配公比必须大于 0")
        return

    # 计算两种网格
    group_ratio = args.group_ratio if args.group_ratio is not None else 1.0
    group_quote_shares = compute_group_quote_shares(args.capital, args.groups, group_ratio)

    arithmetic_result = calculate_arithmetic_grid(
        args.capital,
        args.min_price,
        args.max_price,
        args.grids,
        args.groups,
        group_quote_shares,
    )

    geometric_result = calculate_geometric_grid(
        args.capital,
        args.min_price,
        args.max_price,
        args.grids,
        args.groups,
        group_quote_shares,
    )

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
        args.group_ratio,
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
            group_ratio,
        )

    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_output)
    print(f"结果已保存到文件: {output_file}")


if __name__ == "__main__":
    main()
