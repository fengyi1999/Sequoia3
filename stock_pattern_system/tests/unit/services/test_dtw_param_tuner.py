#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单元测试文件 - DTW参数调优器
这个测试文件包含对DTWParamTuner类的单元测试，验证其核心功能的正确性。
"""

import os
import sys
import unittest
import pytest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stock_pattern_system.app.services.dtw_param_tuner import DTWParamTuner, generate_test_data


class TestDTWParamTuner(unittest.TestCase):
    """测试DTW参数调优器的功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 生成测试数据
        self.ref_data = generate_test_data(pattern_type='sine', length=50, noise_level=0.0)
        
        # 生成一些测试序列：不同噪声水平的正弦波
        self.test_sequences = [
            generate_test_data(pattern_type='sine', length=50, noise_level=0.05),
            generate_test_data(pattern_type='sine', length=50, noise_level=0.1),
            generate_test_data(pattern_type='sine', length=50, noise_level=0.2),
            generate_test_data(pattern_type='cosine', length=50, noise_level=0.05)
        ]
        
        # 创建调优器实例
        self.tuner = DTWParamTuner(reference_data=self.ref_data, max_workers=2)
        
        # 定义参数网格
        self.param_grid = {
            'window': [None, 3, 5],
            'use_fast_dtw': [True, False],
            'early_stopping': [True, False],
            'early_stopping_threshold': [0.2, 0.5]
        }
        
        # 创建测试目录
        self.test_output_dir = os.path.join(project_root, "data", "test", "param_tuning")
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def tearDown(self):
        """测试后的清理工作"""
        # 关闭所有图形
        plt.close('all')
    
    def test_initialization(self):
        """测试初始化参数"""
        # 测试默认参数
        tuner = DTWParamTuner(reference_data=self.ref_data)
        self.assertIsNotNone(tuner.reference_data)
        self.assertEqual(tuner.max_workers, 1)
        self.assertEqual(len(tuner.test_data), 0)
        
        # 测试自定义参数
        tuner = DTWParamTuner(
            reference_data=self.ref_data,
            test_data=self.test_sequences,
            max_workers=4
        )
        self.assertEqual(len(tuner.test_data), len(self.test_sequences))
        self.assertEqual(tuner.max_workers, 4)
        
        # 测试无效参数
        with self.assertRaises(ValueError):
            DTWParamTuner(reference_data=None)
        
        with self.assertRaises(ValueError):
            DTWParamTuner(reference_data=np.array([]))
        
        with self.assertRaises(ValueError):
            DTWParamTuner(reference_data=self.ref_data, max_workers=0)
    
    def test_set_test_data(self):
        """测试设置测试数据"""
        tuner = DTWParamTuner(reference_data=self.ref_data)
        
        # 测试设置有效数据
        tuner.set_test_data(self.test_sequences)
        self.assertEqual(len(tuner.test_data), len(self.test_sequences))
        
        # 测试设置无效数据
        with self.assertRaises(ValueError):
            tuner.set_test_data([])
        
        with self.assertRaises(ValueError):
            tuner.set_test_data([None])
    
    def test_evaluate_params(self):
        """测试评估单个参数组合"""
        self.tuner.set_test_data(self.test_sequences)
        
        # 测试评估一个参数组合
        params = {
            'window': 3,
            'use_fast_dtw': True,
            'early_stopping': False,
            'early_stopping_threshold': None
        }
        
        results = self.tuner._evaluate_params(params)
        
        # 验证结果
        self.assertIsInstance(results, dict)
        self.assertIn('params', results)
        self.assertIn('accuracy', results)
        self.assertIn('avg_time', results)
        self.assertIn('similarities', results)
        
        # 验证准确度和时间是有效值
        self.assertGreaterEqual(results['accuracy'], 0)
        self.assertGreaterEqual(results['avg_time'], 0)
    
    def test_grid_search(self):
        """测试网格搜索功能"""
        self.tuner.set_test_data(self.test_sequences[:2])  # 只使用前两个序列加速测试
        
        # 执行网格搜索
        results = self.tuner.grid_search(
            param_grid=self.param_grid,
            similarity_threshold=0.7
        )
        
        # 验证结果
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        
        # 验证每个结果项的结构
        first_result = results[0]
        self.assertIn('params', first_result)
        self.assertIn('accuracy', first_result)
        self.assertIn('avg_time', first_result)
        
        # 验证结果按准确度排序
        for i in range(len(results) - 1):
            self.assertGreaterEqual(results[i]['accuracy'], results[i+1]['accuracy'])
    
    def test_recommend_best_params(self):
        """测试推荐最佳参数功能"""
        # 创建模拟结果
        mock_results = [
            {
                'params': {'window': 3, 'use_fast_dtw': True},
                'accuracy': 0.9,
                'avg_time': 0.01
            },
            {
                'params': {'window': 5, 'use_fast_dtw': True},
                'accuracy': 0.95,
                'avg_time': 0.02
            },
            {
                'params': {'window': None, 'use_fast_dtw': False},
                'accuracy': 0.98,
                'avg_time': 0.1
            }
        ]
        
        # 测试默认权重（准确度优先）
        best_params = self.tuner.recommend_best_params(mock_results)
        self.assertEqual(best_params, mock_results[0]['params'])
        
        # 测试自定义权重（时间优先）
        best_params = self.tuner.recommend_best_params(
            mock_results, 
            accuracy_weight=0.3,
            time_weight=0.7
        )
        self.assertEqual(best_params, mock_results[0]['params'])
        
        # 测试自定义权重（平衡）
        best_params = self.tuner.recommend_best_params(
            mock_results, 
            accuracy_weight=0.5,
            time_weight=0.5
        )
        self.assertEqual(best_params, mock_results[0]['params'])
    
    def test_plot_results(self):
        """测试结果可视化功能"""
        # 创建模拟结果
        mock_results = [
            {
                'params': {'window': 3, 'use_fast_dtw': True, 'early_stopping': True, 'early_stopping_threshold': 0.2},
                'accuracy': 0.9,
                'avg_time': 0.01,
                'similarities': [0.9, 0.85, 0.8, 0.7]
            },
            {
                'params': {'window': 5, 'use_fast_dtw': True, 'early_stopping': True, 'early_stopping_threshold': 0.5},
                'accuracy': 0.95,
                'avg_time': 0.02,
                'similarities': [0.95, 0.9, 0.85, 0.75]
            },
            {
                'params': {'window': None, 'use_fast_dtw': False, 'early_stopping': False, 'early_stopping_threshold': None},
                'accuracy': 0.98,
                'avg_time': 0.1,
                'similarities': [0.98, 0.95, 0.9, 0.8]
            }
        ]
        
        # 测试绘制结果
        fig = self.tuner.plot_results(mock_results)
        self.assertIsInstance(fig, plt.Figure)
        
        # 测试保存图表
        output_file = os.path.join(self.test_output_dir, "test_results_plot.png")
        fig.savefig(output_file)
        self.assertTrue(os.path.exists(output_file))
        
        # 清理测试文件
        if os.path.exists(output_file):
            os.remove(output_file)
    
    def test_plot_param_comparison(self):
        """测试参数比较可视化功能"""
        # 创建模拟结果
        mock_results = [
            {
                'params': {'window': 3, 'use_fast_dtw': True, 'early_stopping': True, 'early_stopping_threshold': 0.2},
                'accuracy': 0.9,
                'avg_time': 0.01,
                'similarities': [0.9, 0.85, 0.8, 0.7]
            },
            {
                'params': {'window': 5, 'use_fast_dtw': True, 'early_stopping': True, 'early_stopping_threshold': 0.5},
                'accuracy': 0.95,
                'avg_time': 0.02,
                'similarities': [0.95, 0.9, 0.85, 0.75]
            },
            {
                'params': {'window': None, 'use_fast_dtw': False, 'early_stopping': False, 'early_stopping_threshold': None},
                'accuracy': 0.98,
                'avg_time': 0.1,
                'similarities': [0.98, 0.95, 0.9, 0.8]
            }
        ]
        
        # 测试绘制参数比较
        fig = self.tuner.plot_param_comparison(mock_results, param_name='window')
        self.assertIsInstance(fig, plt.Figure)
        
        # 测试保存图表
        output_file = os.path.join(self.test_output_dir, "test_param_comparison.png")
        fig.savefig(output_file)
        self.assertTrue(os.path.exists(output_file))
        
        # 清理测试文件
        if os.path.exists(output_file):
            os.remove(output_file)
    
    def test_generate_test_data(self):
        """测试生成测试数据的功能"""
        # 测试生成正弦波
        sine_data = generate_test_data(pattern_type='sine', length=100, noise_level=0.1)
        self.assertEqual(len(sine_data), 100)
        
        # 测试生成余弦波
        cosine_data = generate_test_data(pattern_type='cosine', length=100, noise_level=0.1)
        self.assertEqual(len(cosine_data), 100)
        
        # 测试生成三角波
        triangle_data = generate_test_data(pattern_type='triangle', length=100, noise_level=0.1)
        self.assertEqual(len(triangle_data), 100)
        
        # 测试生成方波
        square_data = generate_test_data(pattern_type='square', length=100, noise_level=0.1)
        self.assertEqual(len(square_data), 100)
        
        # 测试无效的模式类型
        with self.assertRaises(ValueError):
            generate_test_data(pattern_type='invalid', length=100, noise_level=0.1)


if __name__ == "__main__":
    unittest.main() 