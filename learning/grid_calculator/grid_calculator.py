#!/usr/bin/env python3
"""
网格交易计算脚本

概述
----
本脚本用于计算等差数列与等比数列两种网格交易策略的价格分布、资金分配与买入数量，并将结果导出为 Markdown 文件。计算过程支持分组资金权重与买卖手续费评估，可用于快速比较两种网格策略的表现。

支持的功能：
- 等差数列网格：价格按固定价差划分。
- 等比数列网格：价格按固定比例划分。
- 资金分组：将网格平均划分为若干组，并按资金公比分配报价资产。
- 手续费评估：买入按基础资产计费，卖出按报价资产计费，统一手续费率。

输入参数
----
- trading_pair：交易对，格式为「基础资产-报价资产」（例如：BTC-USDT）。
- total_capital：投入策略的报价资产总额（例如：10000 USDT）。
- min_price：网格价格区间下限。
- max_price：网格价格区间上限。
- num_grids：网格数量（买入层级数）。
- num_groups：分组数量，必须整除网格数量，默认为 1。
- group_ratio：相邻分组的资金公比，默认为 1。
- fee_rate：买入与卖出共用的手续费率（小数表示），默认为 0.001。
- output_dir：输出目录，可选；未指定时默认为脚本所在目录下的 output 子目录。

输出内容
----
脚本会以 Markdown 格式生成以下信息：
1. 输入参数摘要。
2. 等比数列网格：
   - n + 1 个价格分布点（包含最高价）。
   - n 个买入网格的价格、投入资金、手续费、购买量、收益率与净收益。
   - 分组汇总（在启用分组时）。
   - 汇总统计与最低价全仓对比。
3. 等差数列网格：同上。
4. 等比与等差策略之间的购买量、平均价格与平均收益率对比。

使用方法
----
通过命令行参数运行脚本，例如：

  python3 grid_calculator.py --trading-pair BTC-USDT --capital 10000 --min-price 1000 --max-price 2000 --grids 10

常用操作：
- 指定分组并设置资金公比：
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 12 -G 4 -R 1.2
- 修改手续费率：
  python3 grid_calculator.py -p ETH-USDT -c 5000 -m 2000 -M 3000 -g 8 -f 0.0005
- 指定输出目录：
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 10 --output-dir ./results

脚本会根据输入自动生成文件名（例如：btc_usdt_capital_10000_min_price_1000_max_price_2000_grids_10.md），并将其写入输出目录。若未指定 --output-dir，则默认为脚本所在目录下的 output 子目录。

注意事项
----
- 最高价价格点仅用于卖出参考，不产生买单。
- 所有买单的报价资产投入总和等于 total_capital。
- 分组数量必须为正且为网格数量的因数。
- 手续费率必须非负，资金公比必须为正。

参考文档
----
- grid_purchase_quantity_comparison.md
- geometric_sequence_spacing_proof.md
- arithmetic_grid_tutorial/
- geometric_grid_tutorial/
"""

import argparse
import os
from dataclasses import dataclass
from typing import List


@dataclass
class GroupStats:
    """
    分组统计信息。

    Attributes:
        group_number (int): 组别编号，从 1 开始。
        quote_amount (float): 当前分组的报价资产资金总额。
        base_amount (float): 当前分组购买的基础资产数量。
    """

    group_number: int
    quote_amount: float
    base_amount: float


@dataclass
class GridResult:
    """
    网格计算结果。

    Attributes:
        grid_type (str): 结果类型，可为 "arithmetic" 或 "geometric"。
        price_points (List[float]): 全部价格分布点列表，长度为 n + 1。
        buy_prices (List[float]): 买入价格列表，长度为 n。
        quote_amounts (List[float]): 各网格投入的报价资产金额列表。
        base_amounts (List[float]): 各网格建仓后的基础资产数量列表。
        total_base_amount (float): 所有网格合计的基础资产数量。
        total_quote_amount (float): 所有网格合计的报价资产投入金额。
        average_price (float): 加权平均买入价格，单位为报价资产除以基础资产。
        grid_returns (List[float]): 各网格的收益率（百分比）。
        net_profit_amounts (List[float]): 各网格的净收益金额，单位为报价资产。
        buy_fee_base_amounts (List[float]): 各网格买入手续费金额，单位为基础资产。
        sell_fee_quote_amounts (List[float]): 各网格卖出手续费金额，单位为报价资产。
        group_quote_totals (List[float]): 各资金分组的报价资产总额列表。
        group_base_amounts_per_grid (List[float]): 各资金分组内单个网格的基础资产数量。
        fee_rate (float): 买入与卖出的统一手续费率。
    """

    grid_type: str
    price_points: List[float]
    buy_prices: List[float]
    quote_amounts: List[float]
    base_amounts: List[float]
    total_base_amount: float
    total_quote_amount: float
    average_price: float
    grid_returns: List[float]
    net_profit_amounts: List[float]
    buy_fee_base_amounts: List[float]
    sell_fee_quote_amounts: List[float]
    group_quote_totals: List[float]
    group_base_amounts_per_grid: List[float]
    fee_rate: float


def compute_group_quote_shares(
    total_capital: float,
    num_groups: int,
    fund_ratio: float,
) -> List[float]:
    """
    根据资金公比计算各分组的报价资产配额。

    Args:
        total_capital (float): 投入网格策略的报价资产总额，单位与报价资产一致。
        num_groups (int): 资金划分的组数，决定报价资产在分层网格中的分配数量。
        fund_ratio (float): 相邻组之间的资金公比，需大于 0；大于 1 时高价组获得更多资金，介于 0 与 1 之间时低价组获得更多资金。

    Returns:
        List[float]: 从低价组到高价组顺序排列的报价资产配额列表，总和等于 total_capital。

    Raises:
        ValueError: 当 num_groups 小于等于 0 时抛出。
    """
    # 验证分组数量是否为正数，若不满足条件则直接抛出错误以阻止后续计算。
    if num_groups <= 0:
        raise ValueError("分组数量必须大于 0")

    # 当只有一个分组时，直接返回包含全部资金的单元素列表。
    if num_groups == 1:
        return [total_capital]

    # 对资金公比进行下限截断，避免出现零或负值导致指数权重计算异常。
    normalized_ratio = max(fund_ratio, 1e-12)

    # 判断资金公比是否等于 1，若近似相等则采用等额分配方案。
    if abs(normalized_ratio - 1.0) < 1e-12:
        # 创建长度为分组数量的列表，为每组分配相同份额。
        shares = [total_capital / num_groups] * num_groups
    else:
        # 构造指数权重序列，当 normalized_ratio 大于 1 时权重递增，介于 0 与 1 之间时递减。
        weights = [normalized_ratio**i for i in range(num_groups)]
        # 计算权重总和，用于归一化各组的资金份额。
        weight_sum = sum(weights)
        # 根据权重占比为每组分配对应的资金份额。
        shares = [total_capital * weight / weight_sum for weight in weights]

    # 汇总当前的资金份额，准备执行浮点误差修正。
    current_total = sum(shares)
    # 将误差集中到最后一组，确保份额之和严格等于总资金。
    shares[-1] += total_capital - current_total
    # 返回最终的资金配额列表，供后续网格计算使用。
    return shares


def calculate_arithmetic_grid(
    total_capital: float,
    min_price: float,
    max_price: float,
    num_grids: int,
    num_groups: int,
    group_quote_shares: List[float],
    fee_rate: float,
) -> GridResult:
    """
    计算等差数列网格的资金与收益指标。

    Args:
        total_capital (float): 用于构建网格的报价资产总资金。
        min_price (float): 网格价格区间的下限。
        max_price (float): 网格价格区间的上限。
        num_grids (int): 买入网格的数量。
        num_groups (int): 资金分组数量，需为 num_grids 的因数。
        group_quote_shares (List[float]): 各分组的报价资产份额列表，按价格从低到高排列。
        fee_rate (float): 单次交易手续费率，十进制表示。

    Returns:
        GridResult: 等差网格的完整计算结果。

    Raises:
        ValueError: 当 group_quote_shares 的长度与 num_groups 不一致时抛出。
        ValueError: 当 group_quote_shares 之和与 total_capital 不符时抛出。
    """
    # 计算等差价格间隔
    price_diff = (max_price - min_price) / num_grids

    # 生成包含最高价的等差价格点列表
    price_points = [min_price + i * price_diff for i in range(num_grids + 1)]

    # 将末尾价格修正为最大值，消除浮点误差
    price_points[-1] = max_price

    # 截取买入使用的价格序列
    buy_prices = price_points[:num_grids]

    # 验证分组资金列表长度是否匹配
    if len(group_quote_shares) != num_groups:
        raise ValueError("group_quote_shares 的长度必须等于分组数量")

    # 验证分组资金总和是否等于总资金
    if abs(sum(group_quote_shares) - total_capital) > 1e-6:
        raise ValueError("group_quote_shares 的总和必须等于总资金")

    # 计算每组应包含的网格数量
    grids_per_group = num_grids // num_groups

    # 初始化单个网格的报价资产成本列表
    quote_amounts: List[float] = []

    # 初始化单个网格的基础资产数量列表
    base_amounts: List[float] = []

    # 初始化各分组的报价资产总额列表
    group_quote_totals: List[float] = []

    # 初始化各分组单网格基础资产数量列表
    group_base_amounts_per_grid: List[float] = []

    # 初始化单个网格买入手续费列表
    buy_fee_base_amounts: List[float] = []

    # 遍历每个分组
    for group_idx in range(num_groups):
        # 计算当前分组的起始索引位置
        start_idx = group_idx * grids_per_group

        # 计算当前分组的结束索引位置
        end_idx = start_idx + grids_per_group

        # 截取当前分组负责的买入价格序列
        group_prices = buy_prices[start_idx:end_idx]

        # 提取当前分组的报价资产份额
        group_quote_share = group_quote_shares[group_idx]

        # 计算当前分组价格之和
        price_sum_group = sum(group_prices)

        # 计算每个网格的建仓基础资产数量（未扣手续费）
        base_amount_before_fee_per_grid = group_quote_share / price_sum_group if price_sum_group > 0 else 0.0

        # 计算每个网格买入手续费（以基础资产计）
        buy_fee_base_per_grid = base_amount_before_fee_per_grid * fee_rate

        # 计算每个网格扣除手续费后的实际基础资产数量
        base_amount_after_fee_per_grid = base_amount_before_fee_per_grid - buy_fee_base_per_grid

        # 遍历分组内的每个价格
        for price in group_prices:
            # 记录当前网格的实际基础资产数量
            base_amounts.append(base_amount_after_fee_per_grid)

            # 记录当前网格的买入手续费
            buy_fee_base_amounts.append(buy_fee_base_per_grid)

            # 计算当前网格的报价资产成本
            gross_buy_quote = base_amount_before_fee_per_grid * price

            # 记录当前网格的报价资产成本
            quote_amounts.append(gross_buy_quote)

        # 记录当前分组的报价资产总额
        group_quote_totals.append(group_quote_share)

        # 记录当前分组单网格的基础资产数量
        group_base_amounts_per_grid.append(base_amount_after_fee_per_grid)

    # 统计所有网格的报价资产总额
    total_quote_amount = sum(quote_amounts)

    # 统计所有网格的基础资产总量
    total_base_amount = sum(base_amounts)

    # 计算整体加权平均买入价格
    average_price = total_quote_amount / total_base_amount if total_base_amount > 0 else 0.0

    # 初始化网格收益率列表
    grid_returns: List[float] = []

    # 初始化网格净收益列表
    net_profit_amounts: List[float] = []

    # 初始化网格卖出手续费列表
    sell_fee_quote_amounts: List[float] = []

    # 遍历每个买入网格
    for i in range(len(buy_prices)):
        # 取出对应的卖出价格
        sell_price = price_points[i + 1]

        # 取出该网格的基础资产持仓
        base_amount = base_amounts[i]

        # 取出该网格的买入总成本
        total_buy_cost = quote_amounts[i]

        # 计算该网格卖出时获得的报价资产金额
        sell_quote = base_amount * sell_price

        # 计算该网格卖出时的手续费
        sell_fee = sell_quote * fee_rate

        # 记录该网格的卖出手续费
        sell_fee_quote_amounts.append(sell_fee)

        # 计算该网格的净收益
        net_profit = sell_quote - sell_fee - total_buy_cost

        # 记录该网格的净收益
        net_profit_amounts.append(net_profit)

        # 计算该网格的收益率百分比
        return_pct = net_profit / total_buy_cost * 100.0 if total_buy_cost > 0 else 0.0

        # 记录该网格的收益率百分比
        grid_returns.append(return_pct)

    # 返回等差网格的完整结果
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
        net_profit_amounts=net_profit_amounts,
        buy_fee_base_amounts=buy_fee_base_amounts,
        sell_fee_quote_amounts=sell_fee_quote_amounts,
        group_quote_totals=group_quote_totals,
        group_base_amounts_per_grid=group_base_amounts_per_grid,
        fee_rate=fee_rate,
    )


def calculate_geometric_grid(
    total_capital: float,
    min_price: float,
    max_price: float,
    num_grids: int,
    num_groups: int,
    group_quote_shares: List[float],
    fee_rate: float,
) -> GridResult:
    """
    计算等比数列网格的资金与收益指标。

    Args:
        total_capital (float): 用于构建网格的报价资产总资金。
        min_price (float): 网格价格区间的下限。
        max_price (float): 网格价格区间的上限。
        num_grids (int): 买入网格的数量。
        num_groups (int): 资金分组数量，需为 num_grids 的因数。
        group_quote_shares (List[float]): 各分组的报价资产份额列表，按价格从低到高排列。
        fee_rate (float): 单次交易手续费率，十进制表示。

    Returns:
        GridResult: 等比网格的完整计算结果。

    Raises:
        ValueError: 当 group_quote_shares 的长度与 num_groups 不一致时抛出。
        ValueError: 当 group_quote_shares 之和与 total_capital 不符时抛出。
    """
    # 计算等比价格公比
    ratio = (max_price / min_price) ** (1.0 / num_grids)

    # 生成包含最高价的等比价格点列表
    price_points = [min_price * (ratio**i) for i in range(num_grids + 1)]

    # 将末尾价格修正为最大值，消除浮点误差影响
    price_points[-1] = max_price

    # 截取买入使用的价格序列
    buy_prices = price_points[:num_grids]

    # 验证分组资金列表长度是否匹配
    if len(group_quote_shares) != num_groups:
        raise ValueError("group_quote_shares 的长度必须等于分组数量")

    # 验证分组资金总和是否等于总资金
    if abs(sum(group_quote_shares) - total_capital) > 1e-6:
        raise ValueError("group_quote_shares 的总和必须等于总资金")

    # 计算每组应包含的网格数量
    grids_per_group = num_grids // num_groups

    # 初始化单个网格的报价资产成本列表
    quote_amounts: List[float] = []

    # 初始化单个网格的基础资产数量列表
    base_amounts: List[float] = []

    # 初始化各分组的报价资产总额列表
    group_quote_totals: List[float] = []

    # 初始化各分组单网格基础资产数量列表
    group_base_amounts_per_grid: List[float] = []

    # 初始化单个网格买入手续费列表
    buy_fee_base_amounts: List[float] = []

    # 遍历每个分组
    for group_idx in range(num_groups):
        # 计算当前分组的起始索引位置
        start_idx = group_idx * grids_per_group

        # 计算当前分组的结束索引位置
        end_idx = start_idx + grids_per_group

        # 截取当前分组负责的买入价格序列
        group_prices = buy_prices[start_idx:end_idx]

        # 提取当前分组的报价资产份额
        group_quote_share = group_quote_shares[group_idx]

        # 计算当前分组价格之和
        price_sum_group = sum(group_prices)

        # 计算每个网格的建仓基础资产数量（未扣手续费）
        base_amount_before_fee_per_grid = group_quote_share / price_sum_group if price_sum_group > 0 else 0.0

        # 计算每个网格买入手续费（以基础资产计）
        buy_fee_base_per_grid = base_amount_before_fee_per_grid * fee_rate

        # 计算每个网格扣除手续费后的实际基础资产数量
        base_amount_after_fee_per_grid = base_amount_before_fee_per_grid - buy_fee_base_per_grid

        # 遍历分组内的每个价格
        for price in group_prices:
            # 记录当前网格的实际基础资产数量
            base_amounts.append(base_amount_after_fee_per_grid)

            # 记录当前网格的买入手续费
            buy_fee_base_amounts.append(buy_fee_base_per_grid)

            # 计算当前网格的报价资产成本
            gross_buy_quote = base_amount_before_fee_per_grid * price

            # 记录当前网格的报价资产成本
            quote_amounts.append(gross_buy_quote)

        # 记录当前分组的报价资产总额
        group_quote_totals.append(group_quote_share)

        # 记录当前分组单网格的基础资产数量
        group_base_amounts_per_grid.append(base_amount_after_fee_per_grid)

    # 统计所有网格的报价资产总额
    total_quote_amount = sum(quote_amounts)

    # 统计所有网格的基础资产总量
    total_base_amount = sum(base_amounts)

    # 计算整体加权平均买入价格
    average_price = total_quote_amount / total_base_amount if total_base_amount > 0 else 0.0

    # 初始化网格卖出手续费列表
    sell_fee_quote_amounts: List[float] = []

    # 初始化网格净收益列表
    net_profit_amounts: List[float] = []

    # 初始化网格收益率列表
    grid_returns: List[float] = []

    # 遍历每个买入网格
    for i in range(len(buy_prices)):
        # 取出对应的卖出价格
        sell_price = price_points[i + 1]

        # 取出该网格的基础资产持仓
        base_amount = base_amounts[i]

        # 取出该网格的买入总成本
        total_buy_cost = quote_amounts[i]

        # 计算该网格卖出时获得的报价资产金额
        sell_quote = base_amount * sell_price

        # 计算该网格卖出时的手续费
        sell_fee = sell_quote * fee_rate

        # 记录该网格的卖出手续费
        sell_fee_quote_amounts.append(sell_fee)

        # 计算该网格的净收益
        net_profit = sell_quote - sell_fee - total_buy_cost

        # 记录该网格的净收益
        net_profit_amounts.append(net_profit)

        # 计算该网格的收益率百分比
        grid_return = net_profit / total_buy_cost * 100.0 if total_buy_cost > 0 else 0.0

        # 记录该网格的收益率百分比
        grid_returns.append(grid_return)

    # 返回等比网格的完整结果
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
        net_profit_amounts=net_profit_amounts,
        buy_fee_base_amounts=buy_fee_base_amounts,
        sell_fee_quote_amounts=sell_fee_quote_amounts,
        group_quote_totals=group_quote_totals,
        group_base_amounts_per_grid=group_base_amounts_per_grid,
        fee_rate=fee_rate,
    )


def calculate_group_stats(grid_result: GridResult, num_groups: int) -> List[GroupStats]:
    """
    汇总每个资金分组的统计信息。

    Args:
        grid_result (GridResult): 网格计算结果对象。
        num_groups (int): 分组数量。

    Returns:
        List[GroupStats]: 每个分组的统计数据列表。
    """
    # 计算网格数量
    num_grids = len(grid_result.buy_prices)

    # 计算每组包含的网格数量
    grids_per_group = num_grids // num_groups

    # 初始化分组统计列表
    group_stats = []

    # 遍历每个分组索引
    for group_idx in range(num_groups):
        # 获取当前分组的报价资金总额
        group_quote_amount = grid_result.group_quote_totals[group_idx]

        # 获取当前分组的基础资产总量
        group_base_amount = grid_result.group_base_amounts_per_grid[group_idx] * grids_per_group

        # 将当前分组统计信息追加到列表
        group_stats.append(
            GroupStats(
                # 记录分组编号
                group_number=group_idx + 1,
                # 记录报价资产金额
                quote_amount=group_quote_amount,
                # 记录基础资产数量
                base_amount=group_base_amount,
            )
        )

    # 返回所有分组的统计信息
    return group_stats


def generate_output_filename(
    trading_pair: str,
    total_capital: float,
    min_price: float,
    max_price: float,
    num_grids: int,
    num_groups: int = 1,
    fund_ratio: float = 1.0,
) -> str:
    """
    根据命令行参数生成默认的 Markdown 文件名。

    Args:
        trading_pair (str): 交易对名称。
        total_capital (float): 资金总额。
        min_price (float): 最低价。
        max_price (float): 最高价。
        num_grids (int): 网格数量。
        num_groups (int): 分组数量，默认为 1。
        fund_ratio (float): 资金分配公比，默认为 1.0。

    Returns:
        str: 以小写和下划线拼接的文件名，扩展名为 `.md`。
    """
    # 将交易对转换为小写并替换连字符为下划线，生成基础交易对名称
    pair_name = trading_pair.lower().replace("-", "_")

    # 初始化文件名片段列表
    parts = []

    # 将交易对名称加入文件名片段
    parts.append(pair_name)

    # 将资金总额信息加入文件名片段
    parts.append(f"capital_{int(total_capital)}")

    # 将最低价信息加入文件名片段
    parts.append(f"min_price_{int(min_price)}")

    # 将最高价信息加入文件名片段
    parts.append(f"max_price_{int(max_price)}")

    # 将网格数量信息加入文件名片段
    parts.append(f"grids_{num_grids}")

    # 当分组数量大于 1 时，将分组信息加入文件名片段
    if num_groups > 1:
        # 将分组数量格式化后追加到文件名片段
        parts.append(f"groups_{num_groups}")

    # 当资金分配公比不为 1 时，追加公比信息
    if abs(fund_ratio - 1.0) > 1e-12:
        # 将资金分配公比格式化并替换小数点为下划线后追加
        parts.append(f"group_ratio_{fund_ratio:.4f}".replace(".", "_"))

    # 使用下划线连接各片段并追加扩展名形成文件名
    filename = "_".join(parts) + ".md"

    # 返回生成的文件名
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
    将网格计算结果格式化为 Markdown 文本。

    Args:
        trading_pair (str): 交易对名称。
        total_capital (float): 资金总额。
        min_price (float): 最低价。
        max_price (float): 最高价。
        num_grids (int): 网格数量。
        arithmetic_result (GridResult): 等差网格的计算结果。
        geometric_result (GridResult): 等比网格的计算结果。
        num_groups (int): 分组数量，默认为 1。
        fund_ratio (float): 资金分配公比，默认为 1.0。

    Returns:
        str: 适用于 Markdown 文件的完整输出内容。
    """
    # 将输入的交易对拆分为基础资产和报价资产
    base_asset, quote_asset = trading_pair.split("-")
    # 初始化用于存储 Markdown 行的列表
    lines = []

    # 添加一级标题，指明输出的整体主题
    lines.append("# 网格交易计算结果")
    # 添加空行，使标题与正文之间保留间距
    lines.append("")

    # 添加输入参数部分的标题
    lines.append("## 输入参数")
    # 添加空行，使章节结构更加清晰
    lines.append("")
    # 添加交易对信息，展示基础资产和报价资产
    lines.append(f"- **交易对**: {trading_pair}")
    # 添加资金总额信息，标明投入的报价资产规模
    lines.append(f"- **资金总额**: {total_capital:,.2f} {quote_asset}")
    # 添加价格区间信息，说明策略适用的价格范围
    lines.append(f"- **价格区间**: {min_price:,.2f} - {max_price:,.2f} {quote_asset}")
    # 添加网格数量信息，展示划分层数
    lines.append(f"- **网格数量**: {num_grids}")
    # 判断是否启用了分组模式
    if num_groups > 1:
        # 添加分组数量信息，说明每组包含的网格数
        lines.append(f"- **分组数量**: {num_groups}（每组 {num_grids // num_groups} 个网格）")
        # 添加资金分配公比，展示不同分组的资金占比
        lines.append(f"- **资金分配公比**: {fund_ratio:.4f}")
    # 计算手续费率的百分比表示形式
    fee_rate_pct = geometric_result.fee_rate * 100
    # 添加手续费率说明，明确买入与卖出的费用
    lines.append(f"- **手续费率**: {fee_rate_pct:.4f}%（买入与卖出相同，买入按基础资产计费，卖出按报价资产计费）")
    # 添加空行，结束输入参数部分
    lines.append("")

    # 添加等比网格的章节标题
    lines.append("## 等比数列网格")
    # 添加空行，使章节结构更加清晰
    lines.append("")

    # 价格分布点
    # 添加价格分布点的小节标题，说明价格点数量
    lines.append(f"### 价格分布点（共 {len(geometric_result.price_points)} 个，等比）")
    # 添加空行，使表格与标题之间留白
    lines.append("")
    # 初始化价格表格行的容器
    price_table_rows = []
    # 遍历等比价格点，构建表格行
    for i, price in enumerate(geometric_result.price_points):
        # 判定当前价格点是否为最高价
        marker = "（最高价，不含买单）" if i == len(geometric_result.price_points) - 1 else ""
        # 添加对应的表格行，包含序号、价格和备注
        price_table_rows.append(f"| {i+1} | {price:,.4f} {quote_asset} | {marker} |")
    # 添加表格的表头
    lines.append("| 序号 | 价格 | 备注 |")
    # 添加表格的分隔线
    lines.append("|------|------|------|")
    # 添加所有价格行到输出列表
    lines.extend(price_table_rows)
    # 添加空行，结束价格分布点小节
    lines.append("")

    # 添加等比买入网格详情小节标题
    lines.append(f"### 买入网格详情（共 {len(geometric_result.buy_prices)} 个，等比）")
    # 添加空行，增强可读性
    lines.append("")
    # 添加买入网格详情的表头说明
    lines.append(
        f"| 层级 | 价格 ({quote_asset}) | 投入资金 ({quote_asset}) | 买入手续费 ({base_asset}) | 卖出手续费 ({quote_asset}) | 购买量 ({base_asset}) | 收益率 (%) | 收益额 ({quote_asset}) |"
    )
    # 添加表格分隔行，保持 Markdown 标准
    lines.append(
        "|------|------------------|------------------|--------------------|--------------------|------------------|--------------|------------------|"
    )

    # 初始化报价资产总额用于校验
    total_quote_check = 0
    # 计算等比网格的平均收益率
    geometric_avg_return = (
        sum(geometric_result.grid_returns) / len(geometric_result.grid_returns)
        if geometric_result.grid_returns
        else 0.0
    )

    # 判断是否需要在表格中插入分组汇总
    if num_groups > 1:
        # 计算每个分组的统计数据
        geometric_group_stats = calculate_group_stats(geometric_result, num_groups)
        # 计算每组所包含的网格数量
        grids_per_group = len(geometric_result.buy_prices) // num_groups
        # 初始化分组索引，用于追踪当前分组
        group_idx = 0

        # 遍历等比网格的买入价格数据
        for i, price in enumerate(geometric_result.buy_prices):
            # 获取当前层级投入的报价资产
            quote = geometric_result.quote_amounts[i]
            # 获取当前层级买入的基础资产数量
            base = geometric_result.base_amounts[i]
            # 获取当前层级的收益率
            return_pct = geometric_result.grid_returns[i]
            # 获取当前层级的买入手续费（以基础资产计）
            buy_fee = geometric_result.buy_fee_base_amounts[i]
            # 获取当前层级的卖出手续费（以报价资产计）
            sell_fee = geometric_result.sell_fee_quote_amounts[i]
            # 获取当前层级的净收益额
            profit_amount = geometric_result.net_profit_amounts[i]
            # 累加投入的报价资产，用于校验总额
            total_quote_check += quote
            # 添加当前层级的详细表格行
            lines.append(
                f"| {i+1} | {price:,.4f} | {quote:,.4f} | {buy_fee:,.8f} | {sell_fee:,.4f} | {base:,.8f} | {return_pct:,.2f} | {profit_amount:,.4f} |"
            )

            # 判断当前层级是否为当前分组的最后一个网格
            if (i + 1) % grids_per_group == 0:
                # 获取相应分组的统计数据
                group_stat = geometric_group_stats[group_idx]
                # 添加分组合计行，呈现资金和数量汇总
                lines.append(
                    f"| **第 {group_stat.group_number} 组合计** | | **{group_stat.quote_amount:,.4f}** | | | **{group_stat.base_amount:,.8f}** | | |"
                )
                # 递增分组索引，转向下一组
                group_idx += 1
                # 若当前分组不是最后一组，则添加空行作为分隔
                if group_idx < num_groups:
                    # 添加空白分隔行，分隔不同分组的数据
                    lines.append("| | | | | | | | |")
    else:
        # 当未启用分组时直接输出所有网格数据
        for i, price in enumerate(geometric_result.buy_prices):
            # 获取当前层级投入的报价资产
            quote = geometric_result.quote_amounts[i]
            # 获取当前层级买入的基础资产数量
            base = geometric_result.base_amounts[i]
            # 获取当前层级的收益率
            return_pct = geometric_result.grid_returns[i]
            # 获取当前层级的买入手续费（以基础资产计）
            buy_fee = geometric_result.buy_fee_base_amounts[i]
            # 获取当前层级的卖出手续费（以报价资产计）
            sell_fee = geometric_result.sell_fee_quote_amounts[i]
            # 获取当前层级的净收益额
            profit_amount = geometric_result.net_profit_amounts[i]
            # 累加投入的报价资产，用于校验总额
            total_quote_check += quote
            # 添加当前层级的详细表格行
            lines.append(
                f"| {i+1} | {price:,.4f} | {quote:,.4f} | {buy_fee:,.8f} | {sell_fee:,.4f} | {base:,.8f} | {return_pct:,.2f} | {profit_amount:,.4f} |"
            )

    # 合计行
    # 添加等比网格的合计行，用于呈现总投入与总购买量
    lines.append(
        f"| **合计** | | **{total_quote_check:,.4f}** | | | **{geometric_result.total_base_amount:,.8f}** | | |"
    )
    # 添加空行，为后续统计小节留白
    lines.append("")

    # 添加等比汇总统计的小节标题
    lines.append("### 汇总统计（等比）")
    # 添加空行，增强排版可读性
    lines.append("")
    # 获取等比网格的最低买入价格，若无买单则取价格点
    lowest_geometric_price = (
        geometric_result.buy_prices[0] if geometric_result.buy_prices else geometric_result.price_points[0]
    )
    # 计算按最低价全仓买入时能够获取的基础资产数量
    potential_base_at_lowest_geometric = (
        (geometric_result.total_quote_amount / lowest_geometric_price) * (1.0 - geometric_result.fee_rate)
        if lowest_geometric_price > 0
        else 0.0
    )
    # 计算实际购买量与最低价全仓购买量之间的差值
    geometric_base_diff = geometric_result.total_base_amount - potential_base_at_lowest_geometric
    # 计算实际购买量相对于最低价全仓的比例
    geometric_base_ratio = (
        geometric_result.total_base_amount / potential_base_at_lowest_geometric * 100
        if potential_base_at_lowest_geometric > 0
        else 0.0
    )
    # 添加总购买量说明，突出基础资产的持有量
    lines.append(f"- **总购买量**: {geometric_result.total_base_amount:,.8f} {base_asset}")
    # 添加总投入资金说明，体现报价资产支出
    lines.append(f"- **总投入资金**: {geometric_result.total_quote_amount:,.2f} {quote_asset}")
    # 添加平均价格说明，展示整体持仓成本
    lines.append(f"- **平均价格**: {geometric_result.average_price:,.4f} {quote_asset}/{base_asset}")
    # 添加最低价全仓购买量说明，用于对比策略效果
    lines.append(f"- **最低价全仓购买量**: {potential_base_at_lowest_geometric:,.8f} {base_asset}")
    # 添加与最低价全仓比较的说明，包含绝对值与百分比
    lines.append(
        f"- **与最低价全仓比较**: {geometric_base_diff:+,.8f} {base_asset}（实际为最低价全仓的 {geometric_base_ratio:,.2f}%）"
    )
    # 添加平均单网格收益率说明，概述预期收益水平
    lines.append(f"- **平均单网格收益率**: {geometric_avg_return:,.2f}%")
    # 添加空行，结束等比汇总统计小节
    lines.append("")

    # 输出等差数列网格结果
    # 添加等差网格的章节标题
    lines.append("## 等差数列网格")
    # 添加空行，保持章节层次分明
    lines.append("")

    # 添加等差价格分布点的小节标题
    lines.append(f"### 价格分布点（共 {len(arithmetic_result.price_points)} 个，等差）")
    # 添加空行，为表格留出空白
    lines.append("")
    # 初始化等差价格表格行的容器
    price_table_rows = []
    # 遍历等差价格点，构建表格数据
    for i, price in enumerate(arithmetic_result.price_points):
        # 判定当前价格点是否为最高价
        marker = "（最高价，不含买单）" if i == len(arithmetic_result.price_points) - 1 else ""
        # 添加表格行，包含序号、价格和备注
        price_table_rows.append(f"| {i+1} | {price:,.4f} {quote_asset} | {marker} |")
    # 添加表格表头
    lines.append("| 序号 | 价格 | 备注 |")
    # 添加表格分隔线，保持 Markdown 规范
    lines.append("|------|------|------|")
    # 添加所有表格数据行
    lines.extend(price_table_rows)
    # 添加空行，结束等差价格分布点小节
    lines.append("")

    # 添加等差买入网格详情的小节标题
    lines.append(f"### 买入网格详情（共 {len(arithmetic_result.buy_prices)} 个，等差）")
    # 添加空行，增强可读性
    lines.append("")
    # 添加等差买入网格详情表头
    lines.append(
        f"| 层级 | 价格 ({quote_asset}) | 投入资金 ({quote_asset}) | 买入手续费 ({base_asset}) | 卖出手续费 ({quote_asset}) | 购买量 ({base_asset}) | 收益率 (%) | 收益额 ({quote_asset}) |"
    )
    # 添加表格分隔线，确保格式统一
    lines.append(
        "|------|------------------|------------------|--------------------|--------------------|------------------|--------------|------------------|"
    )

    # 重置报价资产总额校验变量
    total_quote_check = 0
    # 计算等差网格的平均收益率
    arithmetic_avg_return = (
        sum(arithmetic_result.grid_returns) / len(arithmetic_result.grid_returns)
        if arithmetic_result.grid_returns
        else 0.0
    )

    # 判断是否需要在等差表格中插入分组汇总
    if num_groups > 1:
        # 计算等差网格各分组的汇总数据
        arithmetic_group_stats = calculate_group_stats(arithmetic_result, num_groups)
        # 计算每个分组包含的网格数
        grids_per_group = len(arithmetic_result.buy_prices) // num_groups
        # 初始化分组索引，追踪当前分组
        group_idx = 0

        # 遍历等差网格的买入数据
        for i, price in enumerate(arithmetic_result.buy_prices):
            # 获取当前层级投入的报价资产
            quote = arithmetic_result.quote_amounts[i]
            # 获取当前层级买入的基础资产数量
            base = arithmetic_result.base_amounts[i]
            # 获取当前层级的收益率
            return_pct = arithmetic_result.grid_returns[i]
            # 获取当前层级的买入手续费（以基础资产计）
            buy_fee = arithmetic_result.buy_fee_base_amounts[i]
            # 获取当前层级的卖出手续费（以报价资产计）
            sell_fee = arithmetic_result.sell_fee_quote_amounts[i]
            # 获取当前层级的净收益额
            profit_amount = arithmetic_result.net_profit_amounts[i]
            # 累加投入的报价资产，用于校验总额
            total_quote_check += quote
            # 添加当前层级的表格行
            lines.append(
                f"| {i+1} | {price:,.4f} | {quote:,.4f} | {buy_fee:,.8f} | {sell_fee:,.4f} | {base:,.8f} | {return_pct:,.2f} | {profit_amount:,.4f} |"
            )

            # 判断是否到达当前分组的最后一个网格
            if (i + 1) % grids_per_group == 0:
                # 获取当前分组的汇总结果
                group_stat = arithmetic_group_stats[group_idx]
                # 添加分组合计行，展示投入与购买量汇总
                lines.append(
                    f"| **第 {group_stat.group_number} 组合计** | | **{group_stat.quote_amount:,.4f}** | | | **{group_stat.base_amount:,.8f}** | | |"
                )
                # 分组索引递增，指向下一组
                group_idx += 1
                # 若仍有后续分组，则添加空白分隔行
                if group_idx < num_groups:
                    # 添加空白分隔行，分隔不同分组的数据
                    lines.append("| | | | | | | | |")
    else:
        # 未启用分组时直接输出所有等差网格数据
        for i, price in enumerate(arithmetic_result.buy_prices):
            # 获取当前层级投入的报价资产
            quote = arithmetic_result.quote_amounts[i]
            # 获取当前层级买入的基础资产数量
            base = arithmetic_result.base_amounts[i]
            # 获取当前层级的收益率
            return_pct = arithmetic_result.grid_returns[i]
            # 获取当前层级的买入手续费（以基础资产计）
            buy_fee = arithmetic_result.buy_fee_base_amounts[i]
            # 获取当前层级的卖出手续费（以报价资产计）
            sell_fee = arithmetic_result.sell_fee_quote_amounts[i]
            # 获取当前层级的净收益额
            profit_amount = arithmetic_result.net_profit_amounts[i]
            # 累加投入的报价资产，用于校验总额
            total_quote_check += quote
            # 添加当前层级的表格行
            lines.append(
                f"| {i+1} | {price:,.4f} | {quote:,.4f} | {buy_fee:,.8f} | {sell_fee:,.4f} | {base:,.8f} | {return_pct:,.2f} | {profit_amount:,.4f} |"
            )

    # 合计行
    # 添加等差网格的合计行，用于呈现总投入与总购买量
    lines.append(
        f"| **合计** | | **{total_quote_check:,.4f}** | | | **{arithmetic_result.total_base_amount:,.8f}** | | |"
    )
    # 添加空行，为后续统计小节留白
    lines.append("")

    # 添加等差汇总统计的小节标题
    lines.append("### 汇总统计（等差）")
    # 添加空行，增强排版可读性
    lines.append("")
    # 获取等差网格的最低买入价格，若无买单则取价格点
    lowest_arithmetic_price = (
        arithmetic_result.buy_prices[0] if arithmetic_result.buy_prices else arithmetic_result.price_points[0]
    )
    # 计算按最低价全仓买入时能够获得的基础资产数量
    potential_base_at_lowest_arithmetic = (
        (arithmetic_result.total_quote_amount / lowest_arithmetic_price) * (1.0 - arithmetic_result.fee_rate)
        if lowest_arithmetic_price > 0
        else 0.0
    )
    # 计算实际购买量与最低价全仓购买量之间的差值
    arithmetic_base_diff = arithmetic_result.total_base_amount - potential_base_at_lowest_arithmetic
    # 计算实际购买量相对于最低价全仓的比例
    arithmetic_base_ratio = (
        arithmetic_result.total_base_amount / potential_base_at_lowest_arithmetic * 100
        if potential_base_at_lowest_arithmetic > 0
        else 0.0
    )
    # 添加总购买量说明，突出基础资产的持有量
    lines.append(f"- **总购买量**: {arithmetic_result.total_base_amount:,.8f} {base_asset}")
    # 添加总投入资金说明，体现报价资产支出
    lines.append(f"- **总投入资金**: {arithmetic_result.total_quote_amount:,.2f} {quote_asset}")
    # 添加平均价格说明，展示整体持仓成本
    lines.append(f"- **平均价格**: {arithmetic_result.average_price:,.4f} {quote_asset}/{base_asset}")
    # 添加最低价全仓购买量说明，用于对比策略效果
    lines.append(f"- **最低价全仓购买量**: {potential_base_at_lowest_arithmetic:,.8f} {base_asset}")
    # 添加与最低价全仓比较的说明，包含绝对值与百分比
    lines.append(
        f"- **与最低价全仓比较**: {arithmetic_base_diff:+,.8f} {base_asset}（实际为最低价全仓的 {arithmetic_base_ratio:,.2f}%）"
    )
    # 添加平均单网格收益率说明，概述预期收益水平
    lines.append(f"- **平均单网格收益率**: {arithmetic_avg_return:,.2f}%")
    # 添加空行，结束等差汇总统计小节
    lines.append("")

    # 添加对比总结的章节标题
    lines.append("## 对比总结")
    # 添加空行，增强章节可读性
    lines.append("")
    # 计算等比相对等差的购买量优势比例
    advantage_pct = (
        (geometric_result.total_base_amount - arithmetic_result.total_base_amount)
        / arithmetic_result.total_base_amount
        * 100
    )

    # 添加购买量对比的小节标题
    lines.append("### 购买量对比")
    # 添加空行，使段落层次分明
    lines.append("")
    # 添加等比网格的总购买量说明
    lines.append(f"- **等比数列总购买量**: {geometric_result.total_base_amount:,.8f} {base_asset}")
    # 添加等差网格的总购买量说明
    lines.append(f"- **等差数列总购买量**: {arithmetic_result.total_base_amount:,.8f} {base_asset}")
    # 判断等比购买量优势是否为正数
    if advantage_pct > 0:
        # 添加正向优势说明
        lines.append(f"- **等比数列优势**: +{advantage_pct:.2f}%")
    else:
        # 添加差异说明，用于表示非正向结果
        lines.append(f"- **等比数列优势**: {advantage_pct:.2f}%")
    # 添加空行，结束购买量对比小节
    lines.append("")

    # 添加平均价格对比的小节标题
    lines.append("### 平均价格对比")
    # 添加空行，突出结构层次
    lines.append("")
    # 添加等比网格的平均价格说明
    lines.append(f"- **等比数列平均价格**: {geometric_result.average_price:,.4f} {quote_asset}/{base_asset}")
    # 添加等差网格的平均价格说明
    lines.append(f"- **等差数列平均价格**: {arithmetic_result.average_price:,.4f} {quote_asset}/{base_asset}")
    # 计算平均价格差异百分比
    price_diff_pct = (
        (arithmetic_result.average_price - geometric_result.average_price) / arithmetic_result.average_price * 100
    )
    # 判断等比平均价格是否具有优势
    if price_diff_pct > 0:
        # 添加等比平均价格优势说明
        lines.append(f"- **等比数列平均价格优势**: -{price_diff_pct:.2f}%（更低的价格意味着更好的买入成本）")
    else:
        # 添加等比平均价格差异说明
        lines.append(f"- **等比数列平均价格差异**: {price_diff_pct:.2f}%")
    # 添加空行，结束平均价格对比小节
    lines.append("")

    # 添加平均收益率对比的小节标题
    lines.append("### 平均收益率对比")
    # 添加空行，使布局更加清晰
    lines.append("")
    # 添加等比网格的平均收益率说明
    lines.append(f"- **等比数列平均单网格收益率**: {geometric_avg_return:,.2f}%")
    # 添加等差网格的平均收益率说明
    lines.append(f"- **等差数列平均单网格收益率**: {arithmetic_avg_return:,.2f}%")
    # 计算平均收益率差异
    return_diff = geometric_avg_return - arithmetic_avg_return
    # 判断收益率差异是否为正
    if return_diff > 0:
        # 添加收益率优势说明
        lines.append(f"- **等比数列收益率优势**: +{return_diff:.2f}%")
    elif return_diff < 0:
        # 添加收益率差异说明，用于表示不利情况
        lines.append(f"- **等比数列收益率差异**: {return_diff:.2f}%")
    else:
        # 添加收益率相等的说明
        lines.append("- **两种网格的平均收益率相同**")
    # 添加空行，结束平均收益率对比小节
    lines.append("")

    # 返回拼接后的 Markdown 字符串结果
    return "\n".join(lines)


def main():
    """
    解析命令行参数并生成网格交易结果文件。
    """
    # 创建命令行解析器并附加说明示例
    parser = argparse.ArgumentParser(
        description="计算网格交易的价格分布、资金分配和购买量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例
--------

示例 1：基础网格计算
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 10
  - 生成包含 10 个买入网格的等差与等比结果。

示例 2：启用分组与资金公比
  python3 grid_calculator.py -p BTC-USDT -c 10000 -m 1000 -M 2000 -g 12 -G 4 -R 1.2
  - 网格按顺序拆分为 4 组，每组 3 个网格，并按照公比 1.2 分配资金。

示例 3：自定义手续费率与输出目录
  python3 grid_calculator.py -p ETH-USDT -c 5000 -m 2000 -M 3000 -g 8 -f 0.0005 --output-dir ./reports
  - 使用 0.05% 手续费率，并将结果保存到 ./reports 目录下（若目录不存在会自动创建）。

输出说明
--------

- 输出文件以 Markdown 形式包含输入摘要、两类网格明细、分组汇总以及整体对比。
- 运行结束后终端会打印实际写入的完整文件路径（文件名根据输入自动生成）。
        """,
    )
    # 注册交易对参数
    parser.add_argument(
        "--trading-pair",
        "-p",
        type=str,
        required=True,
        help="交易对，格式：基础资产-报价资产（例如：BTC-USDT、ETH-USDT）",
    )
    # 注册资金总额参数
    parser.add_argument(
        "--capital",
        "-c",
        type=float,
        required=True,
        help="资金总额，以报价资产计价（例如：10000 表示 10000 USDT）",
    )
    # 注册最低价参数
    parser.add_argument(
        "--min-price",
        "-m",
        type=float,
        required=True,
        help="最低价，网格交易的价格区间下限（必须大于 0）",
    )
    # 注册最高价参数
    parser.add_argument(
        "--max-price",
        "-M",
        type=float,
        required=True,
        help="最高价，网格交易的价格区间上限（必须大于最低价）",
    )
    # 注册网格数量参数
    parser.add_argument(
        "--grids",
        "-g",
        type=int,
        required=True,
        help="网格数量 n，即买入订单的层级数量（必须大于 0）",
    )
    # 注册分组数量参数
    parser.add_argument(
        "--groups",
        "-G",
        type=int,
        default=1,
        help="分组数量，将网格按顺序分成指定数量的分组（必须是网格数量的因数，默认 1）",
    )
    # 注册资金分配公比参数
    parser.add_argument(
        "--group-ratio",
        "-R",
        type=float,
        default=1.0,
        help="资金分配公比（> 0，默认 1 表示分组等额分配，group_ratio > 1 时高价组获得更多资金，0 < group_ratio < 1 时低价组获得更多资金）",
    )
    # 注册手续费率参数
    parser.add_argument(
        "--fee-rate",
        "-f",
        type=float,
        default=0.001,
        help="买入与卖出的统一手续费率（小数），默认 0.001 表示 0.1%%",
    )
    # 注册输出目录参数
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录路径（可选），未指定时默认使用脚本所在目录下的 output 子目录",
    )
    # 解析命令行参数
    args = parser.parse_args()

    # 参数验证
    # 校验资金总额需大于零
    if args.capital <= 0:
        # 输出资金总额错误信息
        print("错误: 资金总额必须大于 0")
        # 终止程序执行
        return

    # 校验价格上下限必须大于零
    if args.min_price <= 0 or args.max_price <= 0:
        # 输出价格范围错误信息
        print("错误: 价格必须大于 0")
        # 终止程序执行
        return

    # 校验最低价需小于最高价
    if args.min_price >= args.max_price:
        # 输出价格顺序错误信息
        print("错误: 最低价必须小于最高价")
        # 终止程序执行
        return

    # 校验网格数量需大于零
    if args.grids <= 0:
        # 输出网格数量错误信息
        print("错误: 网格数量必须大于 0")
        # 终止程序执行
        return

    # 校验交易对格式必须包含分隔符
    if "-" not in args.trading_pair:
        # 输出交易对格式错误信息
        print("错误: 交易对格式不正确，应为：基础资产-报价资产（例如：BTC-USDT）")
        # 终止程序执行
        return

    # 验证分组数量
    # 校验分组数量需大于零
    if args.groups <= 0:
        # 输出分组数量错误信息
        print("错误: 分组数量必须大于 0")
        # 终止程序执行
        return
    # 校验网格数量需能被分组数量整除
    if args.grids % args.groups != 0:
        # 输出分组因数错误信息
        print(f"错误: 分组数量 {args.groups} 必须是网格数量 {args.grids} 的因数")
        # 终止程序执行
        return
    # 校验资金分配公比需大于零
    if args.group_ratio is not None and args.group_ratio <= 0:
        # 输出资金公比错误信息
        print("错误: 资金分配公比必须大于 0")
        # 终止程序执行
        return
    # 校验手续费率需非负
    if args.fee_rate is not None and args.fee_rate < 0:
        # 输出手续费率错误信息
        print("错误: 手续费率不能为负")
        # 终止程序执行
        return

    # 计算两种网格
    # 在未指定时使用默认资金公比
    group_ratio = args.group_ratio if args.group_ratio is not None else 1.0
    # 计算各分组应分配的报价资产
    group_quote_shares = compute_group_quote_shares(args.capital, args.groups, group_ratio)
    # 获取脚本所在目录，供默认输出目录使用
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 计算等差网格结果
    arithmetic_result = calculate_arithmetic_grid(
        # 传入总资金参数
        args.capital,
        # 传入最低价格
        args.min_price,
        # 传入最高价格
        args.max_price,
        # 传入网格数量
        args.grids,
        # 传入分组数量
        args.groups,
        # 传入分组资金份额
        group_quote_shares,
        # 传入手续费率
        args.fee_rate,
    )

    # 计算等比网格结果
    geometric_result = calculate_geometric_grid(
        # 传入总资金参数
        args.capital,
        # 传入最低价格
        args.min_price,
        # 传入最高价格
        args.max_price,
        # 传入网格数量
        args.grids,
        # 传入分组数量
        args.groups,
        # 传入分组资金份额
        group_quote_shares,
        # 传入手续费率
        args.fee_rate,
    )

    # 生成 Markdown 输出内容
    markdown_output = format_output(
        # 交易对名称
        args.trading_pair,
        # 资金总额
        args.capital,
        # 最低价格
        args.min_price,
        # 最高价格
        args.max_price,
        # 网格数量
        args.grids,
        # 等差网格结果
        arithmetic_result,
        # 等比网格结果
        geometric_result,
        # 分组数量
        args.groups,
        # 资金公比
        args.group_ratio,
    )

    # 确定输出目录
    output_dir = os.path.abspath(args.output_dir) if args.output_dir else os.path.join(script_dir, "output")
    # 如果目录不存在则自动创建
    os.makedirs(output_dir, exist_ok=True)

    # 根据输入参数生成默认输出文件名
    output_filename = generate_output_filename(
        # 交易对
        args.trading_pair,
        # 资金总额
        args.capital,
        # 最低价格
        args.min_price,
        # 最高价格
        args.max_price,
        # 网格数量
        args.grids,
        # 分组数量
        args.groups,
        # 资金公比
        group_ratio,
    )

    # 拼接最终输出路径
    output_path = os.path.join(output_dir, output_filename)

    # 写入结果到 Markdown 文件
    with open(output_path, "w", encoding="utf-8") as f:
        # 输出格式化后的内容
        f.write(markdown_output)
    # 在控制台提示保存路径
    print(f"结果已保存到文件: {output_path}")


if __name__ == "__main__":
    main()
