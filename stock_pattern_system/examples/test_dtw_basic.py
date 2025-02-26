"""
DTW匹配器基本功能测试脚本

测试DTW匹配器的基本功能，包括距离计算、相似度评估和可视化
"""
import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.dtw_matcher import DTWMatcher

def create_test_series():
    """创建测试用的时间序列"""
    # 创建一个正弦波
    x1 = np.linspace(0, 2*np.pi, 100)
    series1 = np.sin(x1)
    
    # 创建一个相似但有偏移和噪声的正弦波
    x2 = np.linspace(0.5, 2.5*np.pi, 120)
    series2 = np.sin(x2) + np.random.normal(0, 0.1, len(x2))
    
    # 创建一个完全不同的序列（余弦波）
    x3 = np.linspace(0, 2*np.pi, 100)
    series3 = np.cos(x3)
    
    return series1, series2, series3

def test_distance_and_similarity():
    """测试DTW距离和相似度计算"""
    print("=== 测试DTW距离和相似度计算 ===")
    
    # 创建DTW匹配器
    dtw_matcher = DTWMatcher(window=10, use_fast_dtw=True)
    
    # 获取测试序列
    series1, series2, series3 = create_test_series()
    
    # 计算相似序列的距离和相似度
    distance12 = dtw_matcher.compute_distance(series1, series2)
    similarity12 = dtw_matcher.compute_similarity(series1, series2)
    
    # 计算不同序列的距离和相似度
    distance13 = dtw_matcher.compute_distance(series1, series3)
    similarity13 = dtw_matcher.compute_similarity(series1, series3)
    
    print(f"相似序列 - DTW距离: {distance12:.4f}, 相似度: {similarity12:.4f}")
    print(f"不同序列 - DTW距离: {distance13:.4f}, 相似度: {similarity13:.4f}")

def test_warping_path():
    """测试DTW对齐路径"""
    print("\n=== 测试DTW对齐路径 ===")
    
    # 创建DTW匹配器
    dtw_matcher = DTWMatcher(window=10, use_fast_dtw=True)
    
    # 获取测试序列
    series1, series2, _ = create_test_series()
    
    # 获取对齐路径
    path = dtw_matcher.get_warping_path(series1, series2)
    
    print(f"对齐路径长度: {len(path)}")
    print(f"序列1长度: {len(series1)}, 序列2长度: {len(series2)}")
    print(f"对齐路径前5个点: {path[:5]}")
    
    # 可视化对齐路径
    fig = dtw_matcher.plot_warping_path_visualization(series1, series2, path)
    plt.show()

def test_series_comparison():
    """测试序列比较可视化"""
    print("\n=== 测试序列比较可视化 ===")
    
    # 创建DTW匹配器
    dtw_matcher = DTWMatcher(window=10, use_fast_dtw=True)
    
    # 获取测试序列
    series1, series2, _ = create_test_series()
    
    # 可视化序列比较
    fig = dtw_matcher.plot_series_comparison(
        series1, series2, 
        labels=('原始正弦波', '带噪声的正弦波')
    )
    plt.show()

def test_caching():
    """测试缓存功能"""
    print("\n=== 测试缓存功能 ===")
    
    # 创建DTW匹配器
    dtw_matcher = DTWMatcher(window=10, use_fast_dtw=True, cache_size=100)
    
    # 获取测试序列
    series1, series2, _ = create_test_series()
    
    # 首次计算（无缓存）
    start_time = time.time()
    distance1 = dtw_matcher.compute_distance(series1, series2)
    first_time = time.time() - start_time
    
    # 再次计算（使用缓存）
    start_time = time.time()
    distance2 = dtw_matcher.compute_distance(series1, series2)
    second_time = time.time() - start_time
    
    print(f"首次计算时间: {first_time:.6f}秒")
    print(f"缓存后计算时间: {second_time:.6f}秒")
    print(f"加速比: {first_time/second_time:.2f}倍")
    
    # 检查计算统计信息
    stats = dtw_matcher.get_computation_stats()
    print("\n计算统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

def test_early_stopping():
    """测试提前终止功能"""
    print("\n=== 测试提前终止功能 ===")
    
    # 创建两个DTW匹配器，一个启用提前终止，一个禁用
    dtw_matcher_with_es = DTWMatcher(
        window=10, 
        use_fast_dtw=True, 
        early_stopping=True, 
        early_stopping_threshold=0.5
    )
    
    dtw_matcher_without_es = DTWMatcher(
        window=10, 
        use_fast_dtw=True, 
        early_stopping=False
    )
    
    # 创建两个非常不同的序列
    x1 = np.linspace(0, 2*np.pi, 200)
    series1 = np.sin(x1)
    
    x2 = np.linspace(0, 2*np.pi, 200)
    series2 = -np.sin(x2) + 2  # 完全相反的序列
    
    # 使用提前终止计算
    start_time = time.time()
    distance_with_es = dtw_matcher_with_es.compute_distance(series1, series2)
    time_with_es = time.time() - start_time
    
    # 不使用提前终止计算
    start_time = time.time()
    distance_without_es = dtw_matcher_without_es.compute_distance(series1, series2)
    time_without_es = time.time() - start_time
    
    print(f"启用提前终止 - 距离: {distance_with_es:.4f}, 计算时间: {time_with_es:.6f}秒")
    print(f"禁用提前终止 - 距离: {distance_without_es:.4f}, 计算时间: {time_without_es:.6f}秒")
    print(f"加速比: {time_without_es/time_with_es:.2f}倍")
    
    # 检查提前终止统计信息
    stats = dtw_matcher_with_es.get_computation_stats()
    print(f"提前终止次数: {stats['early_stops']}")

def test_batch_compute():
    """测试批量计算功能"""
    print("\n=== 测试批量计算功能 ===")
    
    # 创建DTW匹配器
    dtw_matcher = DTWMatcher(window=10, use_fast_dtw=True)
    
    # 创建参考序列
    x = np.linspace(0, 2*np.pi, 100)
    reference = np.sin(x)
    
    # 创建多个测试序列
    series_list = []
    for i in range(10):
        # 添加不同程度的偏移和噪声
        offset = i * 0.1
        noise_level = i * 0.02
        x_test = np.linspace(offset, 2*np.pi + offset, 100)
        series = np.sin(x_test) + np.random.normal(0, noise_level, len(x_test))
        series_list.append(series)
    
    # 批量计算相似度
    start_time = time.time()
    similarities = dtw_matcher.batch_compute_similarity(reference, series_list)
    total_time = time.time() - start_time
    
    print(f"批量计算 {len(series_list)} 个序列的相似度，耗时: {total_time:.6f}秒")
    print(f"平均每个序列耗时: {total_time/len(series_list):.6f}秒")
    print("\n相似度结果:")
    for i, similarity in enumerate(similarities):
        print(f"  序列 {i+1}: {similarity:.4f}")

if __name__ == "__main__":
    # 测试DTW距离和相似度计算
    test_distance_and_similarity()
    
    # 测试DTW对齐路径
    test_warping_path()
    
    # 测试序列比较可视化
    test_series_comparison()
    
    # 测试缓存功能
    test_caching()
    
    # 测试提前终止功能
    test_early_stopping()
    
    # 测试批量计算功能
    test_batch_compute() 