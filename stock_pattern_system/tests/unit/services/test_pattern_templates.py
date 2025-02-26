#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单元测试文件 - 股票形态模板库
这个测试文件包含对形态模板库和模式匹配服务的集成功能测试，验证形态库和匹配功能。
"""

import os
import sys
import json
import unittest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import tempfile
import shutil

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stock_pattern_system.app.services.pattern_templates import (
    PatternTemplateManager, 
    normalize_pattern,
    create_pattern_template_from_stock,
    PATTERN_GENERATORS
)
from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService


class TestPatternTemplates(unittest.TestCase):
    """测试形态模板库功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        self.templates_file = os.path.join(self.test_dir, "test_templates.json")
        
        # 创建模板管理器
        self.manager = PatternTemplateManager(self.templates_file)
        
        # 关闭matplotlib图形显示
        plt.ioff()
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时目录
        shutil.rmtree(self.test_dir)
        
        # 关闭所有图形
        plt.close('all')
    
    def test_pattern_generators(self):
        """测试预定义形态生成器"""
        # 测试所有形态生成器
        for pattern_id, pattern_info in PATTERN_GENERATORS.items():
            # 生成形态
            pattern_data = pattern_info['function'](length=50, noise_level=0.05)
            
            # 验证形态数据
            self.assertIsInstance(pattern_data, np.ndarray)
            self.assertEqual(len(pattern_data), 50)
            
            # 验证形态属性
            self.assertTrue(np.all(pattern_data >= 0))
            self.assertTrue(np.all(pattern_data <= 1))
    
    def test_normalize_pattern(self):
        """测试形态归一化"""
        # 测试正常数据
        data = [10, 20, 30, 40, 50]
        normalized = normalize_pattern(data)
        self.assertAlmostEqual(np.min(normalized), 0)
        self.assertAlmostEqual(np.max(normalized), 1)
        
        # 测试常量数据
        const_data = [5, 5, 5, 5, 5]
        const_normalized = normalize_pattern(const_data)
        np.testing.assert_array_equal(const_normalized, np.zeros_like(const_normalized))
    
    def test_add_template(self):
        """测试添加形态模板"""
        # 添加测试模板
        pattern_id = self.manager.add_template(
            name="测试形态",
            data=[0.1, 0.2, 0.3, 0.4, 0.5],
            description="这是一个测试形态",
            tags=["测试", "上升"],
            pattern_type="test"
        )
        
        # 验证返回的ID
        self.assertIsNotNone(pattern_id)
        
        # 验证模板已被添加
        templates = self.manager.get_templates()
        self.assertEqual(len(templates), 1)
        
        # 验证模板内容
        template = templates[0]
        self.assertEqual(template['name'], "测试形态")
        self.assertEqual(template['description'], "这是一个测试形态")
        self.assertListEqual(template['tags'], ["测试", "上升"])
        self.assertEqual(template['pattern_type'], "test")
        self.assertListEqual(template['data'], [0.1, 0.2, 0.3, 0.4, 0.5])
    
    def test_import_predefined_templates(self):
        """测试导入预定义形态模板"""
        # 导入预定义形态
        imported_ids = self.manager.import_predefined_templates(length=30, noise_level=0.05)
        
        # 验证导入结果
        self.assertEqual(len(imported_ids), len(PATTERN_GENERATORS))
        
        # 验证模板内容
        templates = self.manager.get_templates()
        self.assertEqual(len(templates), len(PATTERN_GENERATORS))
        
        # 验证模板类型
        for template in templates:
            self.assertEqual(template['pattern_type'], "predefined")
            
        # 验证模板数据长度
        for template in templates:
            self.assertEqual(len(template['data']), 30)
    
    def test_update_template(self):
        """测试更新形态模板"""
        # 添加测试模板
        pattern_id = self.manager.add_template(
            name="测试形态",
            data=[0.1, 0.2, 0.3, 0.4, 0.5],
            description="这是一个测试形态",
            tags=["测试"],
            pattern_type="test"
        )
        
        # 更新模板
        result = self.manager.update_template(
            pattern_id,
            name="更新的形态",
            description="这是更新后的形态",
            tags=["测试", "已更新"]
        )
        
        # 验证更新结果
        self.assertTrue(result)
        
        # 验证模板内容
        template = self.manager.get_template(pattern_id)
        self.assertEqual(template['name'], "更新的形态")
        self.assertEqual(template['description'], "这是更新后的形态")
        self.assertListEqual(template['tags'], ["测试", "已更新"])
        
        # 测试更新不存在的模板
        result = self.manager.update_template(
            "non_existent_id",
            name="不存在的形态"
        )
        self.assertFalse(result)
    
    def test_delete_template(self):
        """测试删除形态模板"""
        # 添加测试模板
        pattern_id = self.manager.add_template(
            name="测试形态",
            data=[0.1, 0.2, 0.3, 0.4, 0.5],
            description="这是一个测试形态",
            tags=["测试"],
            pattern_type="test"
        )
        
        # 删除模板
        result = self.manager.delete_template(pattern_id)
        
        # 验证删除结果
        self.assertTrue(result)
        
        # 验证模板已被删除
        templates = self.manager.get_templates()
        self.assertEqual(len(templates), 0)
        
        # 测试删除不存在的模板
        result = self.manager.delete_template("non_existent_id")
        self.assertFalse(result)
    
    def test_create_pattern_from_stock(self):
        """测试从股票数据创建形态模板"""
        # 创建模拟股票数据
        dates = pd.date_range(start='2023-01-01', periods=100)
        
        # 使用头肩顶形态数据
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
        
        # 创建模板
        template = create_pattern_template_from_stock(
            stock_data=stock_data,
            start_date='2023-01-10',
            end_date='2023-02-28',
            name="测试形态",
            description="测试描述",
            tags=["测试"],
            column='close'
        )
        
        # 验证模板内容
        self.assertEqual(template['name'], "测试形态")
        self.assertEqual(template['description'], "测试描述")
        self.assertListEqual(template['tags'], ["测试"])
        self.assertIn('data', template)
        self.assertIsInstance(template['data'], list)
        
        # 验证源信息
        self.assertIn('source', template)
        self.assertEqual(template['source']['stock_code'], '000001')
        self.assertEqual(template['source']['stock_name'], '平安银行')


class TestPatternMatcher(unittest.TestCase):
    """测试形态匹配服务与形态模板库的集成"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        self.templates_file = os.path.join(self.test_dir, "test_templates.json")
        
        # 创建模式匹配服务
        self.matcher = PatternMatcherService(
            window_size=3,
            use_fast_dtw=True,
            max_workers=2,
            templates_file=self.templates_file
        )
        
        # 创建测试形态
        self.test_pattern_data = PATTERN_GENERATORS['head_and_shoulders_top']['function'](length=50, noise_level=0.1)
        
        # 关闭matplotlib图形显示
        plt.ioff()
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时目录
        shutil.rmtree(self.test_dir)
        
        # 关闭所有图形
        plt.close('all')
    
    def test_save_and_get_templates(self):
        """测试保存和获取形态模板"""
        # 保存测试形态
        pattern_id = self.matcher.save_pattern_template(
            name="测试形态",
            data=self.test_pattern_data,
            description="这是一个测试形态",
            tags=["测试", "头肩顶"]
        )
        
        # 验证返回的ID
        self.assertIsNotNone(pattern_id)
        
        # 验证模板已被添加
        templates = self.matcher.get_pattern_templates()
        self.assertEqual(len(templates), 1)
        
        # 获取单个模板
        template = self.matcher.get_pattern_template(pattern_id)
        self.assertIsNotNone(template)
        self.assertEqual(template['name'], "测试形态")
        
        # 测试获取不存在的模板
        template = self.matcher.get_pattern_template("non_existent_id")
        self.assertIsNone(template)
        
        # 测试删除模板
        result = self.matcher.delete_pattern_template(pattern_id)
        self.assertTrue(result)
        templates = self.matcher.get_pattern_templates()
        self.assertEqual(len(templates), 0)
    
    def test_import_predefined_templates(self):
        """测试导入预定义形态模板"""
        # 导入预定义形态
        imported_ids = self.matcher.import_predefined_templates(length=30, noise_level=0.05)
        
        # 验证导入结果
        self.assertEqual(len(imported_ids), len(PATTERN_GENERATORS))
        
        # 验证模板分类
        predefined = self.matcher.get_predefined_templates()
        custom = self.matcher.get_custom_templates()
        self.assertEqual(len(predefined), len(PATTERN_GENERATORS))
        self.assertEqual(len(custom), 0)
    
    def test_pattern_matching_with_template(self):
        """测试使用形态模板进行匹配"""
        # 导入预定义形态
        self.matcher.import_predefined_templates(length=30, noise_level=0.05)
        
        # 创建自定义形态
        pattern_id = self.matcher.save_pattern_template(
            name="测试形态",
            data=self.test_pattern_data,
            description="这是一个测试形态",
            tags=["测试", "头肩顶"]
        )
        
        # 创建模拟数据
        candidates = []
        
        # 添加几个相似度不同的候选
        for i in range(5):
            # 在原形态基础上添加不同程度的噪声
            noise_level = 0.05 + i * 0.05
            pattern = self.test_pattern_data + np.random.normal(0, noise_level, len(self.test_pattern_data))
            pattern = normalize_pattern(pattern)
            
            candidates.append({
                'code': f'00000{i}',
                'name': f'测试股票{i}',
                'data': pattern
            })
        
        # 添加一个完全不同的形态
        different_pattern = PATTERN_GENERATORS['double_bottom']['function'](length=50, noise_level=0.1)
        candidates.append({
            'code': '000005',
            'name': '测试股票5',
            'data': different_pattern
        })
        
        # 模拟匹配
        with unittest.mock.patch.object(self.matcher, '_get_candidates', return_value=candidates):
            matches = self.matcher.match_pattern(
                pattern_id=pattern_id,
                top_n=3,
                min_similarity=0.5
            )
        
        # 验证匹配结果
        self.assertEqual(len(matches), 3)  # 限制了返回前3个
        
        # 验证相似度排序
        for i in range(len(matches) - 1):
            self.assertGreaterEqual(matches[i]['similarity'], matches[i+1]['similarity'])
        
        # 验证第一个匹配应该是最相似的
        self.assertEqual(matches[0]['code'], '000000')


if __name__ == "__main__":
    unittest.main() 