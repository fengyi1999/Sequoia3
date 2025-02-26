#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票形态模板库示例脚本

演示如何使用股票形态模板库和自定义形态功能。
包括预定义形态的导入和使用，以及创建和管理自定义形态的功能。
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stock_pattern_system.app.services.pattern_templates import (
    PatternTemplateManager, 
    normalize_pattern,
    create_pattern_template_from_stock,
    PATTERN_GENERATORS
)
from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService


def plot_pattern(pattern_data, title=None, ax=None):
    """绘制形态图"""
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 4))
    else:
        fig = ax.figure
        
    x = np.arange(len(pattern_data))
    ax.plot(x, pattern_data, 'b-', linewidth=2)
    ax.fill_between(x, 0, pattern_data, alpha=0.2, color='blue')
    ax.set_xlim(0, len(pattern_data) - 1)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    
    if title:
        ax.set_title(title)
        
    return fig, ax


def show_predefined_patterns():
    """展示预定义的股票形态"""
    print("\n==== 预定义股票形态展示 ====")
    
    # 创建图形
    fig, axes = plt.subplots(4, 3, figsize=(15, 12))
    axes = axes.flatten()
    
    # 生成并展示每种形态
    for i, (pattern_id, pattern_info) in enumerate(PATTERN_GENERATORS.items()):
        if i >= len(axes):
            break
            
        # 生成形态数据
        pattern_data = pattern_info['function'](length=100, noise_level=0.05)
        
        # 绘制形态
        plot_pattern(
            pattern_data, 
            title=f"{pattern_info['name']} ({pattern_info['trend_indication']})", 
            ax=axes[i]
        )
    
    # 隐藏多余的子图
    for i in range(len(PATTERN_GENERATORS), len(axes)):
        axes[i].set_visible(False)
    
    plt.tight_layout()
    
    # 保存图形
    output_dir = os.path.join(project_root, "data", "examples")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "predefined_patterns.png")
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"预定义形态图已保存到: {output_file}")
    
    plt.show()


def import_predefined_templates():
    """导入预定义形态模板"""
    print("\n==== 导入预定义形态模板 ====")
    
    # 创建模板管理器
    manager = PatternTemplateManager()
    
    # 导入预定义形态
    imported_ids = manager.import_predefined_templates(length=100, noise_level=0.05)
    
    print(f"成功导入 {len(imported_ids)} 个预定义形态模板")
    
    # 显示模板列表
    templates = manager.get_templates()
    print(f"\n当前共有 {len(templates)} 个形态模板:")
    
    for template in templates:
        pattern_id = template.get('pattern_id', 'unknown')
        name = template.get('name', 'unnamed')
        pattern_type = template.get('pattern_type', 'unknown')
        tags = ", ".join(template.get('tags', []))
        
        print(f"  - ID: {pattern_id}, 名称: {name}, 类型: {pattern_type}, 标签: {tags}")
    
    return manager


def create_custom_pattern(manager):
    """创建自定义形态模板"""
    print("\n==== 创建自定义形态模板 ====")
    
    # 创建一个自定义的W形态（双底变种）
    x = np.linspace(0, 1, 100)
    pattern = np.zeros(100)
    
    # 生成W形态
    pattern[:20] = 0.8 - 0.6 * np.sin(np.linspace(0, np.pi, 20))
    pattern[20:40] = 0.2 + 0.6 * np.sin(np.linspace(0, np.pi, 20))
    pattern[40:60] = 0.8 - 0.6 * np.sin(np.linspace(0, np.pi, 20))
    pattern[60:80] = 0.2 + 0.6 * np.sin(np.linspace(0, np.pi, 20))
    pattern[80:] = 0.2 + 0.8 * np.sin(np.linspace(0, np.pi/2, 20))
    
    # 添加噪声
    pattern += np.random.normal(0, 0.03, 100)
    
    # 归一化
    pattern = normalize_pattern(pattern)
    
    # 绘制形态
    fig, ax = plot_pattern(pattern, title="自定义W形态")
    plt.show()
    
    # 保存为自定义模板
    custom_id = manager.create_custom_template(
        name="W形态",
        data=pattern.tolist(),
        description="W形态是一种强劲的反转形态，通常出现在下降趋势底部，由两个低点组成后上升，预示着趋势反转为上升趋势。",
        tags=["看涨", "高可靠", "自定义"]
    )
    
    print(f"已创建自定义形态模板，ID: {custom_id}")
    
    # 显示自定义模板
    custom_templates = manager.get_custom_templates()
    print(f"\n当前共有 {len(custom_templates)} 个自定义形态模板:")
    
    for template in custom_templates:
        pattern_id = template.get('pattern_id', 'unknown')
        name = template.get('name', 'unnamed')
        tags = ", ".join(template.get('tags', []))
        
        print(f"  - ID: {pattern_id}, 名称: {name}, 标签: {tags}")
    
    return custom_id


def create_pattern_from_stock_data():
    """从股票数据创建形态模板"""
    print("\n==== 从股票数据创建形态模板 ====")
    
    # 创建模拟股票数据
    dates = pd.date_range(start='2023-01-01', periods=100)
    
    # 创建一个头肩顶形态的股票数据
    pattern_data = PATTERN_GENERATORS['head_and_shoulders_top']['function'](length=100, noise_level=0.1)
    
    # 缩放到合理的价格范围
    price_data = 50 + pattern_data * 20
    
    # 创建DataFrame
    stock_data = pd.DataFrame({
        'date': dates,
        'code': '000001',
        'name': '平安银行',
        'open': price_data * 0.99,
        'high': price_data * 1.02,
        'low': price_data * 0.98,
        'close': price_data,
        'volume': np.random.randint(1000000, 5000000, size=100)
    })
    
    # 创建形态模板
    template = create_pattern_template_from_stock(
        stock_data=stock_data,
        start_date='2023-01-10',
        end_date='2023-02-28',
        name="平安银行头肩顶形态",
        description="从平安银行2023年1-2月的实际数据中提取的头肩顶形态",
        tags=["看跌", "银行股", "实际案例"],
        column='close'
    )
    
    # 绘制形态
    fig, ax = plot_pattern(
        template['data'], 
        title=f"{template['name']} ({template['source']['start_date']} 至 {template['source']['end_date']})"
    )
    plt.show()
    
    # 保存为自定义模板
    manager = PatternTemplateManager()
    template_id = manager.create_custom_template(
        name=template['name'],
        data=template['data'],
        description=template['description'],
        tags=template['tags']
    )
    
    print(f"已从股票数据创建形态模板，ID: {template_id}")
    
    return template_id


def match_with_template(template_id):
    """使用形态模板进行匹配"""
    print("\n==== 使用形态模板进行匹配 ====")
    
    # 创建模式匹配服务
    matcher_service = PatternMatcherService(window_size=10, use_fast_dtw=True)
    
    # 创建模拟数据
    # 在实际应用中，这里会使用真实股票数据
    print("创建模拟股票数据...")
    stock_codes = [f"6{i:05d}" for i in range(1, 11)]
    stock_names = [f"测试股票{i}" for i in range(1, 11)]
    
    mock_data = []
    for i, (code, name) in enumerate(zip(stock_codes, stock_names)):
        # 创建不同的形态
        if i % 5 == 0:
            # 创建头肩顶形态
            pattern = PATTERN_GENERATORS['head_and_shoulders_top']['function'](length=100, noise_level=0.15)
        elif i % 5 == 1:
            # 创建头肩底形态
            pattern = PATTERN_GENERATORS['head_and_shoulders_bottom']['function'](length=100, noise_level=0.15)
        elif i % 5 == 2:
            # 创建双顶形态
            pattern = PATTERN_GENERATORS['double_top']['function'](length=100, noise_level=0.15)
        elif i % 5 == 3:
            # 创建双底形态
            pattern = PATTERN_GENERATORS['double_bottom']['function'](length=100, noise_level=0.15)
        else:
            # 创建杯柄形态
            pattern = PATTERN_GENERATORS['cup_and_handle']['function'](length=100, noise_level=0.15)
        
        # 缩放到合理的价格范围
        close_data = 50 + pattern * 20
        
        # 添加到模拟数据
        mock_data.append({
            'code': code,
            'name': name,
            'data': close_data
        })
    
    # 进行模式匹配
    print("使用形态模板进行匹配...")
    
    # 获取模板数据
    template_manager = PatternTemplateManager()
    template = template_manager.get_template(template_id)
    
    if not template:
        print(f"错误：找不到形态模板 {template_id}")
        return
    
    # 模拟匹配结果
    print(f"使用形态 '{template['name']}' 进行匹配...")
    
    matches = []
    for stock in mock_data:
        # 计算相似度
        similarity = matcher_service.dtw_matcher.compute_similarity(
            template['data'], 
            stock['data']
        )
        
        # 添加匹配结果
        matches.append({
            'code': stock['code'],
            'name': stock['name'],
            'similarity': similarity,
            'series': stock['data']
        })
    
    # 按相似度排序
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    
    # 显示匹配结果
    print("\n匹配结果:")
    for i, match in enumerate(matches[:5]):
        print(f"  {i+1}. 股票: {match['code']} ({match['name']}), 相似度: {match['similarity']:.4f}")
    
    # 生成匹配报告
    print("\n生成匹配报告...")
    report = matcher_service.dtw_matcher.generate_dtw_report(
        np.array(template['data']), 
        matches
    )
    
    # 显示匹配比较图
    if 'multiple_matches' in report:
        plt.figure(report['multiple_matches'].number)
        plt.suptitle(f"形态 '{template['name']}' 的匹配结果")
        plt.tight_layout()
        plt.show()


def manage_templates():
    """管理形态模板库"""
    print("\n==== 形态模板库管理 ====")
    
    manager = PatternTemplateManager()
    templates = manager.get_templates()
    
    print(f"当前共有 {len(templates)} 个形态模板")
    
    # 按类型分组
    predefined = manager.get_predefined_templates()
    custom = manager.get_custom_templates()
    
    print(f"  - 预定义形态: {len(predefined)}个")
    print(f"  - 自定义形态: {len(custom)}个")
    
    # 更新一个模板
    if custom:
        template_to_update = custom[0]
        print(f"\n更新模板: {template_to_update['name']} (ID: {template_to_update['pattern_id']})")
        
        # 更新描述和标签
        manager.update_template(
            template_to_update['pattern_id'],
            description=template_to_update.get('description', '') + " (已更新)",
            tags=template_to_update.get('tags', []) + ["已更新"]
        )
        
        # 验证更新
        updated = manager.get_template(template_to_update['pattern_id'])
        print(f"更新后的描述: {updated['description']}")
        print(f"更新后的标签: {', '.join(updated['tags'])}")
    
    # 删除一个自定义模板
    if len(custom) > 1:
        template_to_delete = custom[-1]
        print(f"\n删除模板: {template_to_delete['name']} (ID: {template_to_delete['pattern_id']})")
        
        # 删除模板
        manager.delete_template(template_to_delete['pattern_id'])
        
        # 验证删除
        remaining = manager.get_templates()
        print(f"删除后剩余模板数量: {len(remaining)}")
        
        # 确认已删除
        deleted = manager.get_template(template_to_delete['pattern_id'])
        print(f"模板是否已被删除: {deleted is None}")


def main():
    """主函数"""
    # 展示预定义形态
    show_predefined_patterns()
    
    # 导入预定义模板
    manager = import_predefined_templates()
    
    # 创建自定义形态
    custom_id = create_custom_pattern(manager)
    
    # 从股票数据创建形态
    stock_pattern_id = create_pattern_from_stock_data()
    
    # 使用形态模板进行匹配
    match_with_template(custom_id)
    
    # 管理形态模板
    manage_templates()
    
    print("\n形态模板库示例完成!")


if __name__ == "__main__":
    main() 