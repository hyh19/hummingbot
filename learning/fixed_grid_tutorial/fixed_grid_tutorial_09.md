# 第 9 章：故障排查

## 本章导航

- [返回索引](fixed_grid_tutorial_index.md)
- [上一章：最佳实践与注意事项](fixed_grid_tutorial_08.md)
- [下一章：参考资源](fixed_grid_tutorial_10.md)

## 9.1 常见错误信息

### 9.1.1 资金不足错误

**错误信息**：

```text
WARNING: Insufficient ENJ balance for grid bot. Will attempt to rebalance.
```

**原因分析**：

- 基础资产（如 ENJ）数量不足以支持当前网格层级的卖单
- 可能是初始资金不足
- 可能是手动提取了部分资产

**解决方案**：

**方案 1：增加资金**

```bash
# 1. 暂停策略
stop

# 2. 向账户充值所需资产

# 3. 确认余额充足
balance

# 4. 重新启动策略
start --script fixed_grid.py
```

**方案 2：调整参数**

```python
# 编辑 fixed_grid.py

# 减少订单数量
order_amount = Decimal(15.0)  # 原来 18.0

# 或减少网格层数
n_levels = 6  # 原来 8

# 或缩小价格区间
grid_price_ceiling = Decimal(0.32)  # 原来 0.33
```

**方案 3：等待自动再平衡**

如果总资产充足，策略会自动尝试再平衡：

- 检查日志，确认再平衡订单是否成功挂出
- 观察再平衡订单是否成交
- 成交后策略会自动恢复正常

**预防措施**：

```text
1. 启动前仔细计算资金需求
2. 留 20% 安全缓冲
3. 不要在策略运行时手动提取资产
4. 定期检查账户余额
```

### 9.1.2 价格超出网格范围

**错误信息**：

```text
WARNING: Current price is above grid ceiling
```

或

```text
WARNING: Current price is below grid floor
```

**原因分析**：

- 市场价格突破了网格上限或下限
- 网格参数设置不合理
- 市场出现意外的大幅波动

**影响**：

```text
价格高于上限：
- 所有卖单已成交或将成交
- 持有大量报价资产（USDT）
- 错过后续上涨收益
- 策略暂停放置新订单

价格低于下限：
- 所有买单已成交或将成交
- 持有大量基础资产（如 ENJ）
- 面临资产贬值风险
- 策略暂停放置新订单
```

**解决方案**：

**方案 1：等待价格回归**

如果认为价格会回到区间内：

- 保持策略运行
- 监控价格变化
- 价格回归后策略自动恢复

**方案 2：调整网格区间**

```python
# 停止策略
stop

# 编辑 fixed_grid.py，扩大区间

# 价格突破上限时：
grid_price_ceiling = Decimal(0.36)  # 提高上限
# 可选：同时提高下限，保持区间跨度
grid_price_floor = Decimal(0.33)

# 价格跌破下限时：
grid_price_floor = Decimal(0.27)  # 降低下限
# 可选：同时降低上限，保持区间跨度
grid_price_ceiling = Decimal(0.30)

# 重新启动
start --script fixed_grid.py
```

**方案 3：止损退出**

如果判断趋势已改变：

```bash
# 1. 停止策略
stop

# 2. 查看当前持仓
balance

# 3. 决定是否清仓
# - 如果持有大量基础资产且继续看跌：卖出部分
# - 如果持有大量报价资产且继续看涨：买入部分
# - 或者持有等待
```

**预防措施**：

```text
1. 设置价格提醒（上下限附近）
2. 网格区间设置要合理，留足缓冲
3. 定期根据市场调整区间
4. 避免在强趋势市场使用网格策略
```

### 9.1.3 订单成交失败

**错误信息**：

```text
Error: Order rejected by exchange
```

**常见原因**：

**原因 1：订单金额低于最小限制**

```text
交易所最小订单要求：10 USDT
实际订单价值：order_amount × price = 5 USDT

解决方案：
增加 order_amount
```

**原因 2：价格精度不符合要求**

```text
错误价格：0.123456789（精度过高）
交易所要求：最多 4 位小数

解决方案：
调整价格计算，使用 quantize 方法
```

```python
from decimal import Decimal, ROUND_DOWN

# 调整价格精度
price = price.quantize(Decimal('0.0001'), rounding=ROUND_DOWN)
```

**原因 3：余额不足**

```text
挂卖单时基础资产不足
挂买单时报价资产不足

解决方案：
检查可用余额，补充资金或调整订单数量
```

**原因 4：交易对已下架或暂停交易**

```text
解决方案：
更换交易对或等待交易恢复
```

### 9.1.4 API 连接问题

**错误信息**：

```text
Error: Unable to connect to binance
Error: API key invalid
Error: Request timeout
```

**原因及解决方案**：

**API Key 错误**：

```bash
# 重新配置 API
connect binance

# 按提示输入正确的 API Key 和 Secret
```

**网络连接问题**：

```bash
# 测试网络连接
ping api.binance.com

# 如果无法连接，检查：
# 1. 防火墙设置
# 2. VPN 或代理配置
# 3. DNS 设置
```

**API 限流**：

```text
错误：429 Too Many Requests

原因：请求过于频繁

解决方案：
1. 增加 grid_orders_refresh_time（减少刷新频率）
2. 降低交易频率
3. 升级 VIP 等级获得更高限流
```

**IP 白名单限制**：

```text
错误：IP not in whitelist

解决方案：
1. 登录交易所
2. 找到 API 管理
3. 添加当前服务器 IP 到白名单
```

### 9.1.5 策略无响应

**症状**：

```text
- 运行 status 命令无输出或卡住
- 策略不创建新订单
- 订单成交后不更新级别
```

**原因分析**：

**原因 1：策略死锁或崩溃**

```bash
# 查看日志
log

# 查看最后的错误信息
tail -100 logs/logs_strategy.log | grep ERROR
```

**原因 2：时间戳问题**

```text
create_timestamp 设置过大，导致长时间不执行

检查代码中的时间戳设置
```

**原因 3：条件判断错误**

```text
inv_correct 永远为 False
current_level 异常值

解决方案：
重启策略，检查参数配置
```

**解决方案**：

```bash
# 1. 停止策略
stop

# 2. 检查日志文件
cat logs/logs_strategy.log | tail -50

# 3. 如果发现异常，记录错误信息

# 4. 重启 Hummingbot
exit
./start

# 5. 重新加载策略
start --script fixed_grid.py
```

## 9.2 日志分析

### 9.2.1 日志文件位置

```text
主日志文件：
hummingbot/logs/hummingbot_logs.log

策略日志文件：
hummingbot/logs/logs_strategy.log

交易日志文件：
hummingbot/logs/logs_trades.log
```

### 9.2.2 日志级别

```text
DEBUG：调试信息（最详细）
INFO：一般信息
WARNING：警告信息
ERROR：错误信息
CRITICAL：严重错误
```

### 9.2.3 关键日志信息

**正常启动日志**：

```text
2025-10-24 10:00:00 - INFO - Running script strategy fixed_grid...
2025-10-24 10:00:01 - INFO - Current price 0.31, Initial level 4
2025-10-24 10:00:02 - INFO - Strategy started.
```

**订单创建日志**：

```text
2025-10-24 10:00:03 - INFO - Created BUY order: 10 ENJ @ 0.30
2025-10-24 10:00:03 - INFO - Created SELL order: 10 ENJ @ 0.32
```

**订单成交日志**：

```text
2025-10-24 10:15:23 - INFO - BUY 10.0 ENJ-USDT binance at 0.30
2025-10-24 10:15:24 - INFO - Order filled: buy 10.0 at 0.30
```

**警告日志**：

```text
2025-10-24 11:00:00 - WARNING - Insufficient ENJ balance for grid bot. Will attempt to rebalance
2025-10-24 11:00:01 - INFO - Placing buy order to rebalance; amount: 5.0, price: 0.305
```

**错误日志**：

```text
2025-10-24 12:00:00 - ERROR - Failed to create order: Insufficient balance
2025-10-24 12:00:01 - ERROR - API request failed: Connection timeout
```

### 9.2.4 日志分析技巧

**查找特定时间的日志**：

```bash
# 查找 10:00 到 11:00 之间的日志
grep "2025-10-24 10:" logs/logs_strategy.log

# 查找最近 1 小时的错误
tail -1000 logs/logs_strategy.log | grep ERROR
```

**统计交易次数**：

```bash
# 统计买单成交次数
grep "BUY.*ENJ-USDT" logs/logs_strategy.log | wc -l

# 统计卖单成交次数
grep "SELL.*ENJ-USDT" logs/logs_strategy.log | wc -l
```

**查找再平衡事件**：

```bash
grep "rebalance" logs/logs_strategy.log -i
```

**导出特定日期的日志**：

```bash
grep "2025-10-24" logs/logs_strategy.log > 2025-10-24_log.txt
```

## 9.3 调试技巧

### 9.3.1 修改日志级别

**临时修改**（在 Hummingbot 命令行）：

```bash
config log_level debug
```

**永久修改**（编辑配置文件）：

```bash
# 编辑 conf/conf_global.yml
log_level: DEBUG
```

**在策略代码中添加调试日志**：

```python
class FixedGridDebug(FixedGrid):
    def on_tick(self):
        # 添加调试信息
        self.logger().debug(f"Current level: {self.current_level}")
        self.logger().debug(f"Inventory correct: {self.inv_correct}")
        
        # 调用父类方法
        super().on_tick()
    
    def create_grid_proposal(self):
        proposal = super().create_grid_proposal()
        
        # 输出订单详情
        self.logger().debug(f"Created {len(proposal)} orders")
        for order in proposal:
            self.logger().debug(
                f"{order.order_side.name} {order.amount} @ {order.price}"
            )
        
        return proposal
```

### 9.3.2 使用断点调试

**安装 pdb（Python Debugger）**：

```python
# 在关键位置添加断点
import pdb

class FixedGridDebug(FixedGrid):
    def on_tick(self):
        # 在此处暂停执行
        pdb.set_trace()
        
        # 可以交互式查看变量
        # p self.current_level
        # p self.inv_correct
        # c（继续执行）
        
        super().on_tick()
```

**注意**：断点调试会暂停策略执行，仅用于开发测试环境。

### 9.3.3 模拟模式测试

**使用纸面交易**：

Hummingbot 支持纸面交易模式，使用模拟资金测试策略：

```bash
# 配置纸面交易
config paper_trade_enabled true

# 设置初始资金
config paper_trade_account_balance
```

**优点**：

- 无实际资金风险
- 可以快速测试参数
- 验证策略逻辑

**限制**：

- 不考虑滑点和流动性
- 订单 100% 成交
- 无法模拟极端市场情况

### 9.3.4 单元测试

**编写测试用例**：

```python
import unittest
from decimal import Decimal
from fixed_grid import FixedGrid

class TestFixedGrid(unittest.TestCase):
    def test_price_levels_calculation(self):
        """测试价格层级计算"""
        # 模拟连接器
        mock_connectors = {}
        
        # 创建策略实例
        strategy = FixedGrid(mock_connectors)
        strategy.n_levels = 8
        strategy.grid_price_floor = Decimal(0.30)
        strategy.grid_price_ceiling = Decimal(0.33)
        strategy.spread_scale_factor = Decimal(1.0)
        
        # 执行初始化
        strategy.__init__(mock_connectors)
        
        # 验证价格层级数量
        self.assertEqual(len(strategy.price_levels), 8)
        
        # 验证第一层和最后一层
        self.assertEqual(strategy.price_levels[0], Decimal(0.30))
        self.assertEqual(strategy.price_levels[7], Decimal(0.33))
        
        # 验证间距一致性（等距模式）
        spacing = strategy.price_levels[1] - strategy.price_levels[0]
        for i in range(1, 7):
            actual_spacing = strategy.price_levels[i+1] - strategy.price_levels[i]
            self.assertAlmostEqual(float(spacing), float(actual_spacing), places=4)
    
    def test_inventory_calculation(self):
        """测试库存需求计算"""
        # ... 测试代码
    
    def run_all_tests(self):
        unittest.main()

# 运行测试
# python -m unittest test_fixed_grid.py
```

## 9.4 紧急情况处理

### 9.4.1 快速停止策略

**方法 1：命令行停止**

```bash
# 在 Hummingbot 中
stop
```

**方法 2：强制退出**

```bash
# 如果命令行无响应
# 按 Ctrl+C（可能需要多次）

# 如果还是无法退出
# 按 Ctrl+Z 暂停进程
# 然后执行：
kill -9 <hummingbot_pid>
```

**方法 3：交易所手动操作**

```text
1. 登录交易所网页或 App
2. 进入"当前委托"或"开放订单"
3. 全部取消（Cancel All）
4. 确认所有订单已取消
```

### 9.4.2 账户异常处理

**资金突然减少**：

```bash
# 1. 立即停止策略
stop

# 2. 检查账户历史
# 登录交易所查看：
# - 资金流水
# - 交易历史
# - 提现记录

# 3. 确认是否有异常操作
# 如果发现异常：
# - 立即修改密码
# - 冻结 API Key
# - 联系交易所客服

# 4. 如果正常，分析资金变化原因
# - 是否是正常亏损
# - 是否有手动操作
# - 检查策略日志
```

**订单异常**：

```text
症状：
- 订单价格异常（如远高于或低于市场价）
- 订单数量异常（如比预期大很多）
- 意外的订单类型

处理：
1. 立即取消所有订单
2. 停止策略
3. 检查代码是否有错误
4. 查看日志找出原因
5. 修复问题后小额测试
```

### 9.4.3 交易所故障

**API 故障**：

```text
症状：
- 无法连接 API
- 请求超时
- 返回错误

处理：
1. 确认交易所状态（官方公告/社区）
2. 如果是全网故障，等待恢复
3. 如果长时间无法恢复：
   - 停止策略
   - 考虑手动管理订单
   - 等待恢复后再启动
```

**充提暂停**：

```text
症状：
- 无法充值或提现
- 资金冻结

处理：
1. 查看官方公告
2. 如果只是临时维护，等待即可
3. 策略可继续运行（不影响交易）
4. 如果需要紧急提现，联系客服
```

### 9.4.4 极端行情应对

**闪崩**（价格暴跌）：

```text
现象：
- 价格快速跌破网格下限
- 所有买单成交
- 持有大量基础资产

应对：
1. 保持冷静，不要恐慌
2. 评估是否是短期波动
3. 如果是闪崩且有信心反弹：
   - 保持策略运行
   - 等待价格回升
4. 如果判断继续下跌：
   - 停止策略
   - 考虑止损
```

**瀑布**（持续下跌）：

```text
应对：
1. 及时止损，防止更大损失
2. 停止策略
3. 分析下跌原因
4. 等待市场稳定后重新评估
```

**暴涨**（价格暴涨）：

```text
现象：
- 价格快速突破网格上限
- 所有卖单成交
- 持有大量报价资产（USDT）

应对：
1. 如果有信心继续上涨：
   - 调整网格上限
   - 重新启动策略
2. 如果担心回调：
   - 保持现金
   - 等待价格回落
```

## 9.5 数据恢复

### 9.5.1 策略状态恢复

**场景**：Hummingbot 意外关闭，需要恢复策略状态。

**处理**：

```bash
# 1. 重新启动 Hummingbot
./start

# 2. 检查交易所订单
balance

# 3. 查看最后的日志
tail -100 logs/logs_strategy.log

# 4. 确定当前应该在的网格级别
# 根据当前价格和订单情况判断

# 5. 可能需要手动取消交易所的旧订单
# 登录交易所取消

# 6. 重新启动策略
start --script fixed_grid.py

# 策略会自动重新初始化并确定当前级别
```

### 9.5.2 交易历史导出

**导出 Hummingbot 交易记录**：

```bash
# 交易记录存储在 SQLite 数据库中
# 位置：data/hummingbot.db

# 使用 SQLite 命令行工具导出
sqlite3 data/hummingbot.db

# 在 SQLite 中执行：
.headers on
.mode csv
.output trades_export.csv
SELECT * FROM Trade WHERE timestamp > '2025-10-01';
.quit
```

**从交易所导出**：

```text
1. 登录交易所
2. 进入"订单历史"或"交易记录"
3. 选择时间范围和交易对
4. 导出为 CSV 或 Excel
```

## 9.6 本章小结

本章详细介绍了 Fixed Grid 策略的故障排查方法：

**常见错误**：

- 资金不足：增加资金或调整参数
- 价格超出网格：调整区间或等待回归
- 订单失败：检查参数设置和交易所要求
- API 问题：检查网络、密钥和限流
- 策略无响应：查看日志并重启

**日志分析**：

- 理解不同日志级别的含义
- 掌握日志文件位置和查找技巧
- 学会从日志中定位问题

**调试技巧**：

- 修改日志级别获取更多信息
- 使用纸面交易测试
- 编写单元测试验证逻辑

**紧急处理**：

- 快速停止策略的多种方法
- 账户异常的处理流程
- 极端行情的应对策略

**数据恢复**：

- 策略状态的恢复方法
- 交易历史的导出技巧

掌握这些故障排查技能，可以帮助您快速识别和解决问题，确保策略稳定运行。

下一章是本教程的最后一章：[参考资源](fixed_grid_tutorial_10.md)，我们将提供进一步学习和探索的资源链接。

---

[返回索引](fixed_grid_tutorial_index.md) | [上一章：最佳实践与注意事项](fixed_grid_tutorial_08.md) | [下一章：参考资源](fixed_grid_tutorial_10.md)

