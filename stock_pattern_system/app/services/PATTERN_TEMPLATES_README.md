# 股票形态模板库与自定义形态

本模块提供了股票形态模板库和自定义形态功能，用于增强形态选股系统的功能，支持预定义的经典形态和用户自定义形态。

## 功能特点

### 预定义形态模板
- 包含11种常见技术分析形态，如头肩顶、头肩底、双顶、双底、三角形等
- 支持形态参数调整（长度、噪声水平）
- 形态分类和标签（看涨/看跌、可靠性高/中/低）
- 详细的形态描述和市场应用场景

### 自定义形态功能
- 从实际股票数据中提取形态
- 手动定义形态曲线
- 保存、加载和管理自定义形态
- 形态标记和分类管理

### 形态管理功能
- 形态模板的增删改查
- 形态分类和过滤
- 模板导入和导出
- 形态可视化展示

### 集成形态匹配
- 与DTW匹配器无缝集成
- 使用形态模板进行全市场匹配
- 相似度阈值和排序
- 匹配结果可视化和导出

## 预定义形态

形态模板库包含以下预定义形态：

1. **头肩顶（Head and Shoulders Top）**
   - 反转形态，出现在上升趋势顶部
   - 预示着趋势即将反转为下降趋势
   - 看跌信号，可靠性高

2. **头肩底（Head and Shoulders Bottom）**
   - 反转形态，出现在下降趋势底部
   - 预示着趋势即将反转为上升趋势
   - 看涨信号，可靠性高

3. **双顶（Double Top）**
   - 反转形态，出现在上升趋势顶部
   - 由两个相近高点组成
   - 看跌信号，可靠性高

4. **双底（Double Bottom）**
   - 反转形态，出现在下降趋势底部
   - 由两个相近低点组成
   - 看涨信号，可靠性高

5. **上升三角形（Ascending Triangle）**
   - 延续形态，通常出现在上升趋势中
   - 表示短暂整理后趋势将继续上升
   - 看涨信号，可靠性中等

6. **下降三角形（Descending Triangle）**
   - 延续形态，通常出现在下降趋势中
   - 表示短暂整理后趋势将继续下降
   - 看跌信号，可靠性中等

7. **牛旗形（Bull Flag）**
   - 延续形态，出现在上升趋势中
   - 表示短暂回调后趋势将继续上升
   - 看涨信号，可靠性中等

8. **熊旗形（Bear Flag）**
   - 延续形态，出现在下降趋势中
   - 表示短暂反弹后趋势将继续下降
   - 看跌信号，可靠性中等

9. **杯柄形态（Cup and Handle）**
   - 延续形态，通常出现在上升趋势中
   - 表示长期看涨趋势中的暂时回调
   - 看涨信号，可靠性高

10. **上升楔形（Rising Wedge）**
    - 反转形态，通常出现在上升趋势末期
    - 预示着趋势即将反转为下降趋势
    - 看跌信号，可靠性中等

11. **下降楔形（Falling Wedge）**
    - 反转形态，通常出现在下降趋势末期
    - 预示着趋势即将反转为上升趋势
    - 看涨信号，可靠性中等

## 使用示例

### 导入预定义形态模板

```python
from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService

# 创建模式匹配服务
matcher_service = PatternMatcherService()

# 导入预定义形态模板
imported_ids = matcher_service.import_predefined_templates(length=100, noise_level=0.05)

# 获取所有形态模板
templates = matcher_service.get_pattern_templates()
for template in templates:
    print(f"模板: {template['name']}, 标签: {template['tags']}")
```

### 创建自定义形态

```python
import numpy as np
from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService
from stock_pattern_system.app.services.pattern_templates import normalize_pattern

# 创建模式匹配服务
matcher_service = PatternMatcherService()

# 创建自定义W形态
x = np.linspace(0, 1, 100)
pattern = np.zeros(100)

# 生成W形态数据
pattern[:20] = 0.8 - 0.6 * np.sin(np.linspace(0, np.pi, 20))
pattern[20:40] = 0.2 + 0.6 * np.sin(np.linspace(0, np.pi, 20))
pattern[40:60] = 0.8 - 0.6 * np.sin(np.linspace(0, np.pi, 20))
pattern[60:80] = 0.2 + 0.6 * np.sin(np.linspace(0, np.pi, 20))
pattern[80:] = 0.2 + 0.8 * np.sin(np.linspace(0, np.pi/2, 20))

# 添加噪声并归一化
pattern += np.random.normal(0, 0.03, 100)
pattern = normalize_pattern(pattern)

# 保存自定义形态
pattern_id = matcher_service.save_pattern_template(
    name="W形态",
    data=pattern,
    description="W形态是一种强劲的反转形态，通常出现在下降趋势底部，预示着趋势反转为上升趋势。",
    tags=["看涨", "高可靠", "自定义"]
)
```

### 从实际股票数据创建形态

```python
from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService

# 创建模式匹配服务
matcher_service = PatternMatcherService()

# 从股票数据创建形态
pattern_id = matcher_service.create_pattern_from_stock(
    stock_code="000001",  # 平安银行
    start_date="2023-01-01",
    end_date="2023-01-31",
    name="平安银行头肩顶形态",
    description="从平安银行2023年1月的实际数据中提取的头肩顶形态",
    tags=["看跌", "银行股", "实际案例"],
    indicator="close"
)
```

### 使用形态模板进行匹配

```python
from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService

# 创建模式匹配服务
matcher_service = PatternMatcherService()

# 使用形态模板进行匹配
matches = matcher_service.match_pattern(
    pattern_id="pattern_1_1635423456",  # 形态模板ID
    market_types=["主板", "创业板", "科创板"],
    indicators=["close"],
    start_date="2023-01-01",
    end_date="2023-12-31",
    top_n=20,
    min_similarity=0.7
)

# 显示匹配结果
for i, match in enumerate(matches):
    print(f"{i+1}. 股票: {match['code']} ({match['name']}), 相似度: {match['similarity']:.4f}")

# 生成匹配报告
report = matcher_service.generate_match_report(
    pattern_id="pattern_1_1635423456",
    market_types=["主板"],
    indicators=["close"],
    start_date="2023-01-01",
    end_date="2023-12-31",
    output_dir="./reports"
)
```

### 管理形态模板

```python
from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService

# 创建模式匹配服务
matcher_service = PatternMatcherService()

# 获取预定义形态和自定义形态
predefined = matcher_service.get_predefined_templates()
custom = matcher_service.get_custom_templates()

print(f"预定义形态数量: {len(predefined)}")
print(f"自定义形态数量: {len(custom)}")

# 更新形态模板
matcher_service.update_pattern_template(
    pattern_id="pattern_1_1635423456",
    name="更新的形态名称",
    description="更新的形态描述",
    tags=["新标签1", "新标签2"]
)

# 删除形态模板
matcher_service.delete_pattern_template("pattern_1_1635423456")
```

## 技术实现

形态模板库的实现主要包括以下组件：

1. **形态生成器**：使用数学函数和随机噪声生成各种技术形态
2. **模板管理器**：提供形态模板的保存、加载和管理功能
3. **形态提取工具**：从实际股票数据中提取和归一化形态
4. **集成匹配**：与DTW匹配器集成，进行形态匹配

形态数据存储为JSON格式，包含形态数据、描述、标签等信息，支持可持续扩展和自定义。

## 扩展功能

1. **添加新的技术形态**：可以通过实现新的形态生成函数来扩展预定义形态库
2. **形态模板分享**：导出和导入形态模板，支持模板分享和交流
3. **形态组合**：支持多个形态组合使用，提高匹配精度
4. **形态演变**：跟踪形态随时间的演变，预测未来趋势

## 注意事项

- 形态匹配只是技术分析的一种方法，应结合其他因素综合分析
- 预定义形态是理想化的，实际市场中的形态可能存在变形和噪声
- 形态的可靠性取决于多种因素，包括市场环境、交易量和趋势强度等
- 自定义形态需要一定的技术分析经验，建议初学者先使用预定义形态 