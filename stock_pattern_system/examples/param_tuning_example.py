#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DTW参数调优示例脚本
这个脚本演示如何使用DTWParamTuner来优化DTW匹配器的参数配置。
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stock_pattern_system.app.services.dtw_param_tuner import DTWParamTuner, generate_test_data


def main():
    """
    主函数 - 展示DTW参数调优功能
    """
    print("=" * 80)
    print("DTW参数调优示例")
    print("=" * 80)
    
    # 创建输出目录
    output_dir = os.path.join(project_root, "data", "examples")
    os.makedirs(output_dir, exist_ok=True)
    
    # 步骤1: 准备测试数据
    print("\n1. 生成测试数据...")
    
    # 创建一个无噪声的正弦波作为参考模式
    reference_data = generate_test_data(pattern_type='sine', length=100, noise_level=0.0)
    
    # 创建一系列不同噪声水平的测试序列
    test_sequences = []
    noise_levels = [0.05, 0.1, 0.2, 0.3, 0.4]
    
    for noise in noise_levels:
        # 创建带噪声的正弦波
        noisy_sine = generate_test_data(pattern_type='sine', length=100, noise_level=noise)
        test_sequences.append(noisy_sine)
    
    # 添加一个余弦波作为不同类型的序列
    cosine_data = generate_test_data(pattern_type='cosine', length=100, noise_level=0.1)
    test_sequences.append(cosine_data)
    
    # 添加一个三角波
    triangle_data = generate_test_data(pattern_type='triangle', length=100, noise_level=0.1)
    test_sequences.append(triangle_data)
    
    # 添加一个方波
    square_data = generate_test_data(pattern_type='square', length=100, noise_level=0.1)
    test_sequences.append(square_data)
    
    print(f"  - 已创建1个参考序列和{len(test_sequences)}个测试序列")
    
    # 步骤2: 初始化参数调优器
    print("\n2. 初始化参数调优器...")
    tuner = DTWParamTuner(
        reference_data=reference_data,
        test_data=test_sequences,
        max_workers=4  # 使用4个工作线程进行并行处理
    )
    
    # 步骤3: 定义参数网格
    print("\n3. 配置参数网格...")
    param_grid = {
        'window': [None, 5, 10, 20],  # None表示不使用窗口约束
        'use_fast_dtw': [True, False],  # 是否使用FastDTW算法
        'early_stopping': [True, False],  # 是否启用提前停止
        'early_stopping_threshold': [0.2, 0.5, 0.8],  # 提前停止阈值
        'cache_size': [100, 1000]  # 缓存大小
    }
    
    # 输出参数组合数量
    total_combinations = 1
    for param_values in param_grid.values():
        total_combinations *= len(param_values)
    
    print(f"  - 参数网格包含{total_combinations}种组合")
    
    # 步骤4: 执行网格搜索
    print("\n4. 执行网格搜索优化参数...")
    results = tuner.grid_search(
        param_grid=param_grid,
        similarity_threshold=0.7  # 认为相似度大于0.7的匹配是成功的
    )
    
    # 步骤5: 分析结果
    print("\n5. 分析优化结果...")
    
    # 输出前5个最佳结果
    top_results = results[:5]
    print("\n  前5个最佳参数组合:")
    for i, result in enumerate(top_results):
        params = result['params']
        accuracy = result['accuracy']
        avg_time = result['avg_time'] * 1000  # 转换为毫秒
        
        print(f"  #{i+1}: 准确率={accuracy:.2f}, 平均时间={avg_time:.2f}ms")
        print(f"      参数: window={params.get('window')}, fast_dtw={params.get('use_fast_dtw')}, "
              f"early_stopping={params.get('early_stopping')}, "
              f"threshold={params.get('early_stopping_threshold')}, "
              f"cache_size={params.get('cache_size')}")
    
    # 步骤6: 推荐最佳参数
    print("\n6. 推荐最佳参数组合...")
    
    # 默认权重 - 准确度优先
    best_params_accuracy = tuner.recommend_best_params(
        results, accuracy_weight=0.8, time_weight=0.2
    )
    print("\n  准确度优先的推荐参数:")
    for param, value in best_params_accuracy.items():
        print(f"  - {param}: {value}")
    
    # 时间优先
    best_params_time = tuner.recommend_best_params(
        results, accuracy_weight=0.2, time_weight=0.8
    )
    print("\n  速度优先的推荐参数:")
    for param, value in best_params_time.items():
        print(f"  - {param}: {value}")
    
    # 平衡权重
    best_params_balanced = tuner.recommend_best_params(
        results, accuracy_weight=0.5, time_weight=0.5
    )
    print("\n  平衡优化的推荐参数:")
    for param, value in best_params_balanced.items():
        print(f"  - {param}: {value}")
    
    # 步骤7: 可视化结果
    print("\n7. 生成结果可视化...")
    
    # 绘制整体性能比较图
    fig1 = tuner.plot_results(results)
    output_file1 = os.path.join(output_dir, "dtw_param_tuning_results.png")
    fig1.savefig(output_file1, dpi=300, bbox_inches='tight')
    print(f"  - 已保存性能比较图: {output_file1}")
    
    # 绘制窗口大小参数比较
    fig2 = tuner.plot_param_comparison(results, param_name='window')
    output_file2 = os.path.join(output_dir, "dtw_window_comparison.png")
    fig2.savefig(output_file2, dpi=300, bbox_inches='tight')
    print(f"  - 已保存窗口参数比较图: {output_file2}")
    
    # 绘制快速DTW参数比较
    fig3 = tuner.plot_param_comparison(results, param_name='use_fast_dtw')
    output_file3 = os.path.join(output_dir, "dtw_fast_dtw_comparison.png")
    fig3.savefig(output_file3, dpi=300, bbox_inches='tight')
    print(f"  - 已保存快速DTW参数比较图: {output_file3}")
    
    # 绘制提前停止参数比较
    fig4 = tuner.plot_param_comparison(results, param_name='early_stopping')
    output_file4 = os.path.join(output_dir, "dtw_early_stopping_comparison.png")
    fig4.savefig(output_file4, dpi=300, bbox_inches='tight')
    print(f"  - 已保存提前停止参数比较图: {output_file4}")
    
    print("\n" + "=" * 80)
    print("参数调优完成！现在您可以使用推荐的参数配置DTWMatcher以获得最佳性能。")
    print("=" * 80)


if __name__ == "__main__":
    main() 