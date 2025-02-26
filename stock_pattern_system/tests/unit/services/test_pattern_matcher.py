#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单元测试文件 - 模式匹配服务
这个测试文件包含对PatternMatcherService类的单元测试，验证其核心功能的正确性。
"""

import os
import sys
import json
import unittest
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService


class TestPatternMatcherService(unittest.TestCase):
    """测试模式匹配服务的功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 使用测试配置创建服务实例
        self.matcher = PatternMatcherService(
            window_size=3,
            use_fast_dtw=False,
            max_workers=2
        )
        
        # 创建模拟数据
        self.pattern_data = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=10),
            'close': [10, 11, 12, 13, 14, 13, 12, 11, 10, 11]
        })
        
        self.stock_data = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=20),
            'code': '000001',
            'name': '平安银行',
            'close': [10, 11, 12, 13, 14, 13, 12, 11, 10, 11,
                     12, 13, 14, 15, 14, 13, 12, 11, 10, 9]
        })
        
        # 创建模拟模板数据
        self.pattern_template = {
            "pattern_id": "test_pattern",
            "name": "测试形态",
            "description": "这是一个用于测试的形态模板",
            "data": [10, 11, 12, 13, 14, 13, 12, 11, 10, 11],
            "created_at": "2023-01-01T00:00:00",
            "tags": ["测试", "上升", "下降"]
        }
        
        # 模拟数据文件路径
        self.test_data_dir = os.path.join(project_root, "data", "test")
        os.makedirs(self.test_data_dir, exist_ok=True)
        self.test_templates_file = os.path.join(self.test_data_dir, "test_templates.json")
        
        # 创建测试模板文件
        with open(self.test_templates_file, 'w', encoding='utf-8') as f:
            json.dump([self.pattern_template], f, ensure_ascii=False)
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试文件
        if os.path.exists(self.test_templates_file):
            os.remove(self.test_templates_file)
    
    @patch('stock_pattern_system.app.services.pattern_matcher.PatternMatcherService._get_pattern_data')
    @patch('stock_pattern_system.app.services.pattern_matcher.PatternMatcherService._get_candidates')
    def test_match_pattern(self, mock_get_candidates, mock_get_pattern_data):
        """测试模式匹配功能"""
        # 设置模拟函数返回值
        mock_get_pattern_data.return_value = self.pattern_data['close'].values
        mock_get_candidates.return_value = [
            {'code': '000001', 'name': '平安银行', 'data': self.stock_data['close'].values},
            {'code': '000002', 'name': '万科A', 'data': self.stock_data['close'].values + 5}
        ]
        
        # 调用匹配函数
        result = self.matcher.match_pattern(
            pattern_id="test_pattern",
            market_types=["沪深A股"],
            indicators=["close"],
            start_date="2023-01-01",
            end_date="2023-01-20",
            top_n=5,
            min_similarity=0.7
        )
        
        # 验证结果
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)  # 应当返回两个匹配结果
        
        # 验证第一个匹配结果的结构
        first_match = result[0]
        self.assertIn('code', first_match)
        self.assertIn('name', first_match)
        self.assertIn('similarity', first_match)
        self.assertIn('match_details', first_match)
        
        # 验证模拟函数被正确调用
        mock_get_pattern_data.assert_called_once_with("test_pattern")
        mock_get_candidates.assert_called_once()
    
    def test_get_pattern_data_from_template(self):
        """测试从模板获取模式数据"""
        # 模拟模板数据路径
        self.matcher.templates_file = self.test_templates_file
        
        # 调用函数
        pattern_data = self.matcher._get_pattern_data("test_pattern")
        
        # 验证结果
        self.assertIsInstance(pattern_data, np.ndarray)
        np.testing.assert_array_equal(pattern_data, np.array(self.pattern_template["data"]))
    
    def test_get_pattern_data_from_provided_data(self):
        """测试从提供的数据获取模式数据"""
        # 调用函数，提供pattern_data参数
        pattern_data = self.matcher._get_pattern_data(
            pattern_id=None, 
            pattern_data=self.pattern_data['close'].values
        )
        
        # 验证结果
        self.assertIsInstance(pattern_data, np.ndarray)
        np.testing.assert_array_equal(pattern_data, self.pattern_data['close'].values)
    
    def test_get_pattern_data_invalid(self):
        """测试无效的模式数据情况"""
        # 不存在的模式ID且没有提供数据
        with self.assertRaises(ValueError):
            self.matcher._get_pattern_data("non_existent_pattern")
        
        # 空数据
        with self.assertRaises(ValueError):
            self.matcher._get_pattern_data(pattern_id=None, pattern_data=[])
    
    @patch('stock_pattern_system.app.services.pattern_matcher.get_stock_data')
    def test_get_candidates(self, mock_get_stock_data):
        """测试获取候选股票数据"""
        # 设置模拟函数返回值
        mock_get_stock_data.return_value = {
            '000001': {
                'code': '000001',
                'name': '平安银行',
                'data': self.stock_data
            },
            '000002': {
                'code': '000002',
                'name': '万科A',
                'data': self.stock_data.copy()
            }
        }
        
        # 调用函数
        candidates = self.matcher._get_candidates(
            market_types=["沪深A股"],
            indicators=["close"],
            start_date="2023-01-01",
            end_date="2023-01-20"
        )
        
        # 验证结果
        self.assertIsInstance(candidates, list)
        self.assertEqual(len(candidates), 2)
        
        # 验证第一个候选的结构
        first_candidate = candidates[0]
        self.assertIn('code', first_candidate)
        self.assertIn('name', first_candidate)
        self.assertIn('data', first_candidate)
        
        # 验证模拟函数被正确调用
        mock_get_stock_data.assert_called_once()
    
    def test_save_match_results(self):
        """测试保存匹配结果"""
        # 创建测试结果
        test_results = [
            {
                'code': '000001',
                'name': '平安银行',
                'similarity': 0.95,
                'match_details': {'position': 5, 'length': 10}
            },
            {
                'code': '000002',
                'name': '万科A',
                'similarity': 0.85,
                'match_details': {'position': 3, 'length': 10}
            }
        ]
        
        # 设置测试输出文件
        test_output_file = os.path.join(self.test_data_dir, "test_match_results.json")
        
        # 调用函数
        self.matcher.save_match_results(test_results, test_output_file)
        
        # 验证文件已创建
        self.assertTrue(os.path.exists(test_output_file))
        
        # 读取文件并验证内容
        with open(test_output_file, 'r', encoding='utf-8') as f:
            saved_results = json.load(f)
        
        self.assertEqual(len(saved_results), 2)
        self.assertEqual(saved_results[0]['code'], '000001')
        self.assertEqual(saved_results[1]['code'], '000002')
        
        # 清理测试文件
        os.remove(test_output_file)
    
    @patch('stock_pattern_system.app.services.pattern_matcher.PatternMatcherService.match_pattern')
    @patch('stock_pattern_system.app.services.pattern_matcher.os.makedirs')
    @patch('stock_pattern_system.app.services.pattern_matcher.plt')
    @patch('stock_pattern_system.app.services.pattern_matcher.pd.DataFrame.to_csv')
    def test_generate_match_report(self, mock_to_csv, mock_plt, mock_makedirs, mock_match_pattern):
        """测试生成匹配报告"""
        # 设置模拟函数返回值
        mock_match_pattern.return_value = [
            {
                'code': '000001',
                'name': '平安银行',
                'similarity': 0.95,
                'match_details': {'position': 5, 'length': 10, 'data': self.stock_data['close'].values}
            },
            {
                'code': '000002',
                'name': '万科A',
                'similarity': 0.85,
                'match_details': {'position': 3, 'length': 10, 'data': self.stock_data['close'].values}
            }
        ]
        
        # 设置测试报告目录
        test_report_dir = os.path.join(self.test_data_dir, "test_report")
        
        # 调用函数
        report = self.matcher.generate_match_report(
            pattern_id="test_pattern",
            pattern_data=self.pattern_data['close'].values,
            market_types=["沪深A股"],
            indicators=["close"],
            start_date="2023-01-01",
            end_date="2023-01-20",
            output_dir=test_report_dir
        )
        
        # 验证结果
        self.assertIsInstance(report, dict)
        self.assertIn('pattern_info', report)
        self.assertIn('matches', report)
        self.assertIn('statistics', report)
        
        # 验证模拟函数被正确调用
        mock_match_pattern.assert_called_once()
        mock_makedirs.assert_called_once()
        # plt.savefig应该被调用至少一次
        mock_plt.savefig.assert_called()
        # to_csv应该被调用一次
        mock_to_csv.assert_called_once()
    
    def test_save_pattern_template(self):
        """测试保存模式模板"""
        # 设置测试模板文件
        self.matcher.templates_file = self.test_templates_file
        
        # 创建新的测试模板
        new_template = {
            "pattern_id": "new_test_pattern",
            "name": "新测试形态",
            "description": "这是一个新的测试形态模板",
            "data": [1, 2, 3, 4, 5, 4, 3, 2, 1],
            "tags": ["测试", "波动"]
        }
        
        # 调用函数
        self.matcher.save_pattern_template(**new_template)
        
        # 读取模板文件并验证内容
        with open(self.test_templates_file, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        # 应有两个模板：原始的和新添加的
        self.assertEqual(len(templates), 2)
        
        # 验证新添加的模板
        new_template_saved = next((t for t in templates if t["pattern_id"] == "new_test_pattern"), None)
        self.assertIsNotNone(new_template_saved)
        self.assertEqual(new_template_saved["name"], "新测试形态")
        self.assertEqual(new_template_saved["description"], "这是一个新的测试形态模板")
        self.assertListEqual(new_template_saved["data"], [1, 2, 3, 4, 5, 4, 3, 2, 1])
    
    def test_get_pattern_templates(self):
        """测试获取模式模板列表"""
        # 设置测试模板文件
        self.matcher.templates_file = self.test_templates_file
        
        # 调用函数
        templates = self.matcher.get_pattern_templates()
        
        # 验证结果
        self.assertIsInstance(templates, list)
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]["pattern_id"], "test_pattern")
    
    def test_delete_pattern_template(self):
        """测试删除模式模板"""
        # 设置测试模板文件
        self.matcher.templates_file = self.test_templates_file
        
        # 调用函数
        result = self.matcher.delete_pattern_template("test_pattern")
        
        # 验证结果
        self.assertTrue(result)
        
        # 读取模板文件并验证内容
        with open(self.test_templates_file, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        # 应为空列表
        self.assertEqual(len(templates), 0)
        
        # 测试删除不存在的模板
        result = self.matcher.delete_pattern_template("non_existent_pattern")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main() 