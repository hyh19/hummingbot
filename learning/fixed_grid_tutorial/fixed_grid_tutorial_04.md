# 第 4 章：快速开始使用指南

## 本章导航

- [返回索引](fixed_grid_tutorial_index.md)
- [上一章：参数配置完全指南](fixed_grid_tutorial_03.md)
- [下一章：使用示例](fixed_grid_tutorial_05.md)

## 4.1 环境准备

### 4.1.1 系统要求

**操作系统**：

- Linux（推荐 Ubuntu 20.04+）
- macOS 10.12+
- Windows 10+（通过 WSL2）

**硬件要求**：

- CPU：双核及以上
- 内存：至少 4GB RAM
- 硬盘：至少 5GB 可用空间
- 网络：稳定的互联网连接

### 4.1.2 安装 Hummingbot

如果您还未安装 Hummingbot，请根据您的系统选择安装方式：

**Docker 安装（推荐）**：

```bash
# 拉取最新镜像
docker pull hummingbot/hummingbot:latest

# 创建配置和日志目录
mkdir hummingbot_files
cd hummingbot_files
mkdir hummingbot_conf hummingbot_logs

# 启动 Hummingbot
docker run -it \
  --name hummingbot-instance \
  -v $(pwd)/hummingbot_conf:/conf \
  -v $(pwd)/hummingbot_logs:/logs \
  hummingbot/hummingbot:latest
```

**源码安装**：

```bash
# 克隆仓库
git clone https://github.com/hummingbot/hummingbot.git
cd hummingbot

# 安装依赖
./install

# 编译
./compile

# 启动
./start
```

### 4.1.3 交易所 API 配置

在使用策略前，需要配置交易所 API 密钥。

**步骤 1：在交易所创建 API 密钥**

以 Binance 为例：

1. 登录 Binance 账户
2. 进入"用户中心" → "API 管理"
3. 创建新的 API 密钥
4. 设置权限：启用"现货交易"，禁用"提现"
5. 记录 API Key 和 Secret Key

**步骤 2：在 Hummingbot 中配置**

启动 Hummingbot 后，执行：

```bash
connect binance
```

按提示输入：

- API Key
- Secret Key
- （可选）密码备注

成功后显示：

```text
You are now connected to binance.
```

### 4.1.4 检查账户余额

确保账户有足够的资金：

```bash
balance
```

输出示例：

```text
Exchange: binance
  Asset    Total     Available  Allocated
  ENJ      500.00    500.00     0.00
  USDT     1000.00   1000.00    0.00
```

**资金检查清单**：

- [ ] 基础资产（如 ENJ）数量充足
- [ ] 报价资产（如 USDT）数量充足
- [ ] 总资金满足策略需求（参考第 3 章资金计算）

## 4.2 配置策略文件

### 4.2.1 定位策略文件

Fixed Grid 策略文件位于：

```text
hummingbot/scripts/community/fixed_grid.py
```

### 4.2.2 编辑配置参数

使用文本编辑器打开 `fixed_grid.py`，找到参数配置部分（第 17-32 行）：

```17:32:scripts/community/fixed_grid.py
# Parameters to modify -----------------------------------------
trading_pair = "ENJ-USDT"
exchange = "ascend_ex"
n_levels = 8
grid_price_ceiling = Decimal(0.33)
grid_price_floor = Decimal(0.3)
order_amount = Decimal(18.0)
# Optional ----------------------
spread_scale_factor = Decimal(1.0)
amount_scale_factor = Decimal(1.0)
rebalance_order_type = "limit"
rebalance_order_spread = Decimal(0.02)
rebalance_order_refresh_time = 60.0
grid_orders_refresh_time = 3600000.0
price_source = PriceType.MidPrice
# ----------------------------------------------------------------
```

### 4.2.3 配置示例：简单配置

假设您要交易 BTC-USDT，当前价格 42000 USDT，预期震荡区间 40000-44000：

```python
# 基础配置
trading_pair = "BTC-USDT"
exchange = "binance"
n_levels = 10
grid_price_ceiling = Decimal(44000)
grid_price_floor = Decimal(40000)
order_amount = Decimal(0.01)  # 每层 0.01 BTC

# 可选参数保持默认
spread_scale_factor = Decimal(1.0)
amount_scale_factor = Decimal(1.0)
rebalance_order_type = "limit"
rebalance_order_spread = Decimal(0.02)
rebalance_order_refresh_time = 60.0
grid_orders_refresh_time = 3600000.0
price_source = PriceType.MidPrice
```

**资金需求估算**：

```text
平均价格 = (44000 + 40000) / 2 = 42000
单边资金 = 0.01 × 5 × 42000 = 2100 USDT
总资金需求 = 2100 × 2 × 1.2 = 5040 USDT

建议准备：0.05 BTC + 2500 USDT（或等值资金）
```

### 4.2.4 保存配置

修改完成后：

1. 保存文件
2. 确认无语法错误
3. 记录您的配置参数（便于后续分析）

## 4.3 启动策略

### 4.3.1 加载脚本策略

在 Hummingbot 命令行中执行：

```bash
start --script fixed_grid.py
```

### 4.3.2 启动过程输出

策略启动时会显示初始化信息：

```text
Running script strategy fixed_grid...

Current price 42150.5, Initial level 6

Strategy started.
Enter "status" to see strategy status.
```

**关键信息解读**：

- **Current price**：当前市场价格
- **Initial level**：初始网格级别（价格所在层级）

**可能的警告信息**：

```text
WARNING: Current price is above grid ceiling
```

说明当前价格超出网格上限，需要调整参数。

```text
WARNING: Current price is below grid floor
```

说明当前价格低于网格下限，需要调整参数。

```text
WARNING: Insufficient ENJ balance for grid bot. Will attempt to rebalance
```

说明基础资产不足，策略会尝试再平衡。

### 4.3.3 验证策略运行

检查策略是否正常运行：

```bash
status
```

正常情况下会显示详细的策略状态（见下一节）。

## 4.4 监控策略状态

### 4.4.1 查看状态命令

在 Hummingbot 命令行执行：

```bash
status
```

### 4.4.2 状态输出解读

**完整输出示例**：

```text
  Balances:
    Exchange    Asset    Total     Available  Allocated
    binance     BTC      0.2500    0.1000     0.1500
    binance     USDT     5000.00   2500.00    2500.00

  Grid:
    Parameter                      Value
    Grid spread                    400.0
    Current grid level             6
    BTC required                   0.05
    USDT required in BTC          0.05952
    BTC balance                    0.2500
    USDT balance in BTC           0.05952
    Correct inventory balance      True

  Assets:
                        BTC        USDT
    Total Balance       0.2500     5000.00
    Available Balance   0.1000     2500.00
    Current Value (USDT) 10537.50  5000.00
    Current %           67.8%      32.2%

  Orders:
    Market    Symbol      Type    Price       Amount     Age
    binance   BTC-USDT    buy     40400.0     0.01       00:01:23
    binance   BTC-USDT    buy     40800.0     0.01       00:01:23
    binance   BTC-USDT    buy     41200.0     0.01       00:01:23
    binance   BTC-USDT    buy     41600.0     0.01       00:01:23
    binance   BTC-USDT    buy     42000.0     0.01       00:01:23
    binance   BTC-USDT    sell    42800.0     0.01       00:01:23
    binance   BTC-USDT    sell    43200.0     0.01       00:01:23
    binance   BTC-USDT    sell    43600.0     0.01       00:01:23
    binance   BTC-USDT    sell    44000.0     0.01       00:01:23
```

### 4.4.3 关键指标说明

**1. Balances（账户余额）**

- **Total**：总余额
- **Available**：可用余额
- **Allocated**：已分配余额（挂单占用）

**2. Grid（网格信息）**

- **Grid spread**：网格间距
- **Current grid level**：当前所在层级
- **Asset required**：策略需要的资产数量
- **Asset balance**：实际持有的资产数量
- **Correct inventory balance**：库存是否正确
  - `True`：库存充足，策略正常运行
  - `False`：库存不足，正在再平衡

**3. Assets（资产配比）**

- **Total Balance**：各资产总量
- **Current Value**：当前价值（折算为报价资产）
- **Current %**：资产占比

理想情况：两种资产占比接近 50:50

**4. Orders（活跃订单）**

显示所有挂单信息：

- **Type**：buy（买单）或 sell（卖单）
- **Price**：订单价格
- **Amount**：订单数量
- **Age**：订单存在时间

### 4.4.4 实时日志查看

查看策略实时日志：

```bash
log
```

或在日志文件中查看：

```bash
tail -f logs/logs_strategy.log
```

**日志示例**：

```text
2025-10-24 10:15:32,123 - INFO - BUY 0.01 BTC-USDT binance at 41600.0
2025-10-24 10:15:33,456 - INFO - Order filled: buy 0.01 BTC at 41600.0
2025-10-24 10:15:34,789 - INFO - Placing sell order: 0.01 BTC at 42000.0
```

## 4.5 策略运行中的操作

### 4.5.1 查看历史交易

```bash
history
```

输出示例：

```text
  Recent Trades:
    Timestamp             Market       Type  Price       Amount    Trade PnL
    2025-10-24 10:15:33   BTC-USDT     buy   41600.0     0.01      -
    2025-10-24 10:18:45   BTC-USDT     sell  42000.0     0.01      4.00 USDT
    2025-10-24 10:25:12   BTC-USDT     buy   41200.0     0.01      -
    2025-10-24 10:30:28   BTC-USDT     sell  41600.0     0.01      4.00 USDT
```

**Trade PnL**：单次交易的盈亏（不包括手续费）

### 4.5.2 查看盈亏统计

```bash
pnl
```

输出示例：

```text
  PnL:
    Market        Trading Pair  Total Trades  Total PnL (USDT)  Return %
    binance       BTC-USDT      24            96.50             1.92%
```

**注意**：PnL 计算可能不包括未实现盈亏和手续费。

### 4.5.3 手动刷新订单

如果需要手动取消并重新创建所有订单：

```bash
# 停止策略
stop

# 重新启动
start --script fixed_grid.py
```

### 4.5.4 修改配置参数

如果需要调整参数：

1. 停止策略：`stop`
2. 编辑 `fixed_grid.py` 文件
3. 保存修改
4. 重新启动：`start --script fixed_grid.py`

**注意**：运行中修改参数需要重启策略才能生效。

## 4.6 停止策略

### 4.6.1 正常停止

在 Hummingbot 命令行执行：

```bash
stop
```

策略会：

1. 取消所有活跃订单
2. 停止执行新订单
3. 保存运行数据

输出：

```text
Stopping strategy...
All orders cancelled.
Strategy stopped.
```

### 4.6.2 紧急停止

如果遇到异常情况需要立即停止：

**方法 1：使用 exit 命令**

```bash
exit
```

这会退出 Hummingbot，但订单可能仍在交易所挂单。

**方法 2：直接在交易所取消订单**

登录交易所网页或 App，手动取消所有订单。

### 4.6.3 停止后的检查

停止策略后，建议检查：

1. **交易所订单**：确认所有订单已取消

```bash
balance
```

2. **账户资产**：记录当前持仓

3. **交易历史**：分析策略表现

```bash
history
pnl
```

## 4.7 常见启动问题

### 4.7.1 API 连接失败

**问题**：

```text
Error: Unable to connect to binance. Please check your API keys.
```

**解决方案**：

1. 检查 API Key 和 Secret 是否正确
2. 确认 API 权限包含"现货交易"
3. 检查 IP 白名单设置（如果启用）
4. 确认网络连接正常

### 4.7.2 资金不足

**问题**：

```text
WARNING: Insufficient BTC balance for grid bot. Unable to rebalance.
```

**解决方案**：

1. 增加账户资金
2. 减少 `order_amount` 参数
3. 减少 `n_levels` 参数
4. 调整网格价格区间

### 4.7.3 价格超出网格

**问题**：

```text
WARNING: Current price is above grid ceiling
```

**解决方案**：

1. 调高 `grid_price_ceiling`
2. 调低 `grid_price_floor`
3. 等待价格回落到区间内

### 4.7.4 最小订单限制

**问题**：

```text
Error: Order amount below minimum requirement
```

**解决方案**：

增加 `order_amount`，确保：

```text
order_amount × grid_price_floor ≥ 交易所最小订单金额
```

### 4.7.5 脚本加载失败

**问题**：

```text
Error: Cannot load script fixed_grid.py
```

**解决方案**：

1. 确认文件路径正确
2. 检查文件权限
3. 验证 Python 语法无误：

```bash
python3 -m py_compile scripts/community/fixed_grid.py
```

## 4.8 性能监控建议

### 4.8.1 关键监控指标

**每天检查**：

- 策略运行状态（是否正常）
- 订单执行情况（成交次数）
- 账户余额变化
- 盈亏统计

**每周分析**：

- 总收益率
- 交易频率
- 手续费占比
- 资产配比变化

### 4.8.2 监控工具

**内置命令**：

```bash
status    # 实时状态
history   # 交易历史
pnl       # 盈亏统计
balance   # 账户余额
```

**日志文件**：

```bash
# 查看策略日志
tail -f logs/logs_strategy.log

# 查看所有日志
tail -f logs/hummingbot_logs.log
```

**交易所 Web 界面**：

- 登录交易所查看订单历史
- 导出交易记录进行详细分析
- 查看费率折扣和返佣

### 4.8.3 建立记录表格

建议使用表格记录策略运行数据：

| 日期 | 初始资金 | 当前资金 | 日收益 | 交易次数 | 手续费 | 备注 |
|------|---------|---------|--------|---------|--------|------|
| 10-24 | 5000 | 5019.5 | +19.5 | 4 | -8.4 | 正常运行 |
| 10-25 | 5019.5 | 5048.2 | +28.7 | 6 | -12.6 | 波动增加 |

## 4.9 本章小结

本章详细介绍了 Fixed Grid 策略的快速启动流程：

**关键步骤**：

1. **环境准备**：安装 Hummingbot，配置 API
2. **配置策略**：编辑参数，计算资金需求
3. **启动策略**：加载脚本，验证运行
4. **监控状态**：查看状态输出，理解关键指标
5. **日常维护**：检查日志，分析表现
6. **正常停止**：安全退出，保存数据

**重要提示**：

- 首次运行建议使用小额资金测试
- 密切关注初期运行状态
- 遇到问题及时停止并排查
- 定期检查和记录策略表现

**下一步**：

现在您已经掌握了基本的启动和监控方法，下一章我们将学习 [使用示例](fixed_grid_tutorial_05.md)，通过 3 个实际案例深入理解不同场景下的参数配置。

---

[返回索引](fixed_grid_tutorial_index.md) | [上一章：参数配置完全指南](fixed_grid_tutorial_03.md) | [下一章：使用示例](fixed_grid_tutorial_05.md)

