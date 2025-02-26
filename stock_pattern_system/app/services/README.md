# 形态匹配服务

本目录包含形态选股系统的核心服务模块，提供基于DTW算法的时间序列相似度计算和形态匹配功能。

## DTW匹配器 (dtw_matcher.py)

DTW匹配器是一个高效的动态时间规整(Dynamic Time Warping)实现，用于计算时间序列之间的相似度。它具有以下特点：

- 支持时间序列归一化
- 提供DTW距离和相似度计算
- 支持批量处理和并行计算
- 内置LRU缓存机制，提高重复计算效率
- 提供提前终止优化，加速计算过程
- 支持可视化DTW对齐路径和序列比较

### 主要功能

- **序列归一化**：将时间序列归一化到[0,1]范围，便于比较不同尺度的数据
- **距离计算**：计算两个时间序列之间的DTW距离
- **相似度评估**：将DTW距离转换为相似度分数(0-1范围)
- **最佳匹配查找**：在候选序列中找到与模式最匹配的序列
- **对齐路径获取**：获取两个序列的DTW对齐路径
- **可视化**：提供多种可视化方法，帮助理解DTW匹配结果

### 使用示例

```python
from app.services.dtw_matcher import DTWMatcher

# 创建DTW匹配器
dtw_matcher = DTWMatcher(window=10, use_fast_dtw=True)

# 计算两个序列的相似度
similarity = dtw_matcher.compute_similarity(series1, series2)

# 在候选序列中查找最佳匹配
matches = dtw_matcher.find_best_matches(
    pattern=pattern_series,
    candidates=candidates,
    top_n=10,
    threshold=0.7
)

# 可视化比较
fig = dtw_matcher.plot_series_comparison(series1, series2)
```

## 形态匹配服务 (pattern_matcher.py)

形态匹配服务是对DTW匹配器的高级封装，提供了更加便捷的股票形态匹配功能，包括：

- 形态模板管理（保存、查询、删除）
- 股票数据获取和预处理
- 形态匹配和结果保存
- 匹配报告生成和可视化

### 主要功能

- **形态匹配**：查找与给定模式相似的股票形态
- **模板管理**：保存和管理形态模板
- **报告生成**：生成包含多种可视化图表的匹配报告
- **批量处理**：支持大规模数据的批量处理

### 使用示例

```python
from app.services.pattern_matcher import PatternMatcherService

# 创建形态匹配服务
matcher_service = PatternMatcherService()

# 查找匹配
matches = matcher_service.match_pattern(
    pattern_data={'series': pattern_series},
    top_n=10,
    threshold=0.7
)

# 保存形态模板
pattern_id = matcher_service.save_pattern_template(
    name="头肩顶形态",
    series=pattern_series,
    description="经典的头肩顶反转形态"
)

# 生成匹配报告
report = matcher_service.generate_match_report(pattern_id=pattern_id)
```

## 性能优化

DTW匹配器和形态匹配服务采用了多种优化技术，提高计算效率：

1. **LRU缓存**：缓存计算结果，避免重复计算
2. **提前终止**：在计算过程中检测距离是否已超过阈值，提前终止不必要的计算
3. **并行计算**：使用ProcessPoolExecutor进行并行计算
4. **批量处理**：支持大数据集的分批处理，避免内存溢出
5. **快速DTW算法**：使用优化的DTW算法实现，提高计算速度

## 可视化功能

DTW匹配器提供了丰富的可视化功能，帮助理解DTW算法和匹配结果：

1. **序列比较图**：直观展示两个序列的对比和对齐情况
2. **对齐路径可视化**：显示DTW对齐路径和距离矩阵
3. **多匹配比较**：同时展示多个匹配结果与模式的对比
4. **相似度分布**：显示匹配结果的相似度分布情况
5. **综合报告**：生成包含多个图表的综合匹配报告

## 示例代码

完整的使用示例可以参考 `examples/dtw_matcher_example.py`，该示例展示了DTW匹配器和形态匹配服务的主要功能和使用方法。 