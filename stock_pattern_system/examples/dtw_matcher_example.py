"""
DTW匹配器示例脚本

展示如何使用DTW匹配器和模式匹配服务进行股票形态匹配
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.services.dtw_matcher import DTWMatcher
from app.services.pattern_matcher import PatternMatcherService
from app.models.stock import StockModel

def test_dtw_basic():
    """测试DTW匹配器的基本功能"""
    print("=== 测试DTW匹配器的基本功能 ===")
    
    # 创建DTW匹配器
    dtw_matcher = DTWMatcher(window=10, use_fast_dtw=True)
    
    # 创建两个测试序列
    series1 = np.sin(np.linspace(0, 2*np.pi, 100))
    series2 = np.sin(np.linspace(0.5, 2.5*np.pi, 120))
    
    # 计算DTW距离和相似度
    distance = dtw_matcher.compute_distance(series1, series2)
    similarity = dtw_matcher.compute_similarity(series1, series2)
    
    print(f"DTW距离: {distance:.4f}")
    print(f"相似度: {similarity:.4f}")
    
    # 获取对齐路径
    path = dtw_matcher.get_warping_path(series1, series2)
    print(f"对齐路径长度: {len(path)}")
    
    # 可视化
    fig = dtw_matcher.plot_series_comparison(series1, series2, labels=('序列1', '序列2'))
    plt.show()
    
    # 可视化对齐路径
    fig = dtw_matcher.plot_warping_path_visualization(series1, series2)
    plt.show()
    
    # 测试缓存功能
    start_time = time.time()
    dtw_matcher.compute_distance(series1, series2)
    first_time = time.time() - start_time
    
    start_time = time.time()
    dtw_matcher.compute_distance(series1, series2)
    second_time = time.time() - start_time
    
    print(f"首次计算时间: {first_time:.6f}秒")
    print(f"缓存后计算时间: {second_time:.6f}秒")
    print(f"加速比: {first_time/second_time:.2f}倍")
    
    # 显示计算统计信息
    stats = dtw_matcher.get_computation_stats()
    print("计算统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

def test_stock_pattern_matching():
    """测试股票形态匹配"""
    print("\n=== 测试股票形态匹配 ===")
    
    # 创建模式匹配服务
    matcher_service = PatternMatcherService(window=10, use_fast_dtw=True)
    
    # 获取一只股票的数据作为模式
    stock_model = StockModel()
    pattern_stock = "000001"  # 平安银行
    
    print(f"获取股票 {pattern_stock} 的数据作为模式...")
    df = stock_model.get_stock_history(pattern_stock, indicators=['close'])
    
    if df.empty:
        print("无法获取股票数据，请先运行数据获取脚本")
        return
    
    # 使用最近30天的收盘价作为模式
    pattern_series = df['close'].tail(30).tolist()
    
    # 创建模式数据
    pattern_data = {
        'series': pattern_series,
        'indicator': 'close'
    }
    
    # 查找匹配
    print("查找匹配的股票形态...")
    matches = matcher_service.match_pattern(
        pattern_data=pattern_data,
        top_n=10,
        threshold=0.7,
        market_types=['主板'],
        batch_size=50
    )
    
    # 显示匹配结果
    print(f"找到 {len(matches)} 个匹配结果:")
    for i, match in enumerate(matches):
        print(f"{i+1}. 股票代码: {match['code']}, 相似度: {match['similarity']:.4f}")
    
    # 生成报告
    print("\n生成匹配报告...")
    report = matcher_service.generate_match_report(pattern_data=pattern_data, matches=matches)
    
    # 显示统计信息
    if 'stats' in report:
        print("匹配统计信息:")
        for key, value in report['stats'].items():
            if key != 'computation_stats':
                print(f"  {key}: {value}")
    
    # 保存报告图表
    output_dir = os.path.join(project_root, 'data', 'examples')
    saved_files = matcher_service.save_report_charts(report, output_dir)
    
    print(f"报告图表已保存到 {output_dir} 目录")
    for name, path in saved_files.items():
        print(f"  {name}: {os.path.basename(path)}")
    
    # 显示最佳匹配的比较图
    if 'best_match_comparison' in report:
        plt.figure(report['best_match_comparison'].number)
        plt.show()

def test_pattern_template():
    """测试形态模板保存和匹配"""
    print("\n=== 测试形态模板保存和匹配 ===")
    
    # 创建模式匹配服务
    matcher_service = PatternMatcherService()
    
    # 创建一个合成的形态模式
    x = np.linspace(0, 4*np.pi, 60)
    pattern_series = np.sin(x) + 0.5 * np.sin(2*x) + np.random.normal(0, 0.1, len(x))
    pattern_series = pattern_series.tolist()
    
    # 保存形态模板
    pattern_name = "测试形态-正弦波"
    pattern_desc = "一个合成的正弦波形态，用于测试"
    
    pattern_id = matcher_service.save_pattern_template(
        name=pattern_name,
        series=pattern_series,
        description=pattern_desc
    )
    
    if not pattern_id:
        print("保存形态模板失败")
        return
    
    print(f"形态模板已保存，ID: {pattern_id}")
    
    # 查找匹配
    print("查找匹配的股票形态...")
    matches = matcher_service.match_pattern(
        pattern_id=pattern_id,
        top_n=5,
        threshold=0.6
    )
    
    # 显示匹配结果
    print(f"找到 {len(matches)} 个匹配结果:")
    for i, match in enumerate(matches):
        print(f"{i+1}. 股票代码: {match['code']}, 相似度: {match['similarity']:.4f}")
    
    # 获取所有形态模板
    templates = matcher_service.get_pattern_templates()
    print(f"\n系统中共有 {len(templates)} 个形态模板:")
    for template in templates:
        print(f"  ID: {template['id']}, 名称: {template['name']}")
    
    # 删除测试形态模板
    if matcher_service.delete_pattern_template(pattern_id):
        print(f"已删除测试形态模板 (ID: {pattern_id})")

if __name__ == "__main__":
    import time
    
    # 测试DTW基本功能
    test_dtw_basic()
    
    # 测试股票形态匹配
    test_stock_pattern_matching()
    
    # 测试形态模板
    test_pattern_template() 