# 第 8 章：参考资源与工具

## 本章导航

- [返回索引](geometric_grid_tutorial_index.md)
- [上一章：动态调整与风险控制](geometric_grid_tutorial_07.md)

## 8.1 等比数列计算工具

### 8.1.1 在线计算器

**推荐搜索**：

- "等比数列计算器"
- "Geometric progression calculator"

### 8.1.2 Excel 公式

**计算第 n 层价格**：

```
=A2 * POWER(比率, ROW()-2)
```

**计算层数**：

```
=LOG(上限/下限)/LOG(比率)+1
```

### 8.1.3 Python 工具

```python
import math

def geometric_levels(lower, upper, ratio):
    """计算等比网格层级"""
    n = math.ceil(math.log(upper/lower) / math.log(ratio)) + 1
    levels = [lower * (ratio ** i) for i in range(n)]
    return levels

# 使用示例
levels = geometric_levels(50000, 60000, 1.02)
print(levels)
```

## 8.2 对数坐标图表

**TradingView**：

- 切换到对数坐标模式
- 查看价格在对数尺度上的分布
- 绘制对数趋势线

## 8.3 技术指标资源

参考等差网格教程第 8 章的相关资源。

## 8.4 进阶学习

**对数思维**：

- 理解对数尺度在金融中的应用
- 学习指数增长模型
- 研究百分比波动

## 8.5 本章小结

可用资源：

- 在线计算器和 Excel
- TradingView 对数坐标
- 编程工具（Python）

**持续学习**：

- 理解对数尺度
- 掌握百分比思维
- 实践和总结

## 8.6 结语

恭喜完成等比网格教程！

掌握了：

- 等比网格的数学原理
- 对数坐标下的技术分析
- 比率和区间的确定方法
- 资金管理策略
- 动态调整方法

**重要提醒**：

- 等比网格适合高价格币种
- 注意高价区资金需求
- 持续监控和调整
- 做好风险管理

祝交易顺利！

---

[返回索引](geometric_grid_tutorial_index.md) | [上一章：动态调整与风险控制](geometric_grid_tutorial_07.md)
