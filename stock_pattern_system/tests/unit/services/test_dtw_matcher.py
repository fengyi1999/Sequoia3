#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单元测试文件 - DTW匹配器服务
这个测试文件包含对DTWMatcher类的单元测试，验证其核心功能的正确性。
"""

import os
import sys
import unittest
import pytest
import numpy as np
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from stock_pattern_system.app.services.dtw_matcher import DTWMatcher, LRUCache


class TestLRUCache(unittest.TestCase):
    """测试LRU缓存的功能"""
    
    def test_initialization(self):
        """测试LRU缓存初始化"""
        cache = LRUCache(capacity=5)
        self.assertEqual(cache.capacity, 5)
        self.assertEqual(len(cache.cache), 0)
        self.assertEqual(len(cache.use_order), 0)
        
        # 测试无效的容量参数
        with self.assertRaises(ValueError):
            LRUCache(capacity=0)
        
        with self.assertRaises(ValueError):
            LRUCache(capacity=-1)

    def test_put_and_get(self):
        """测试缓存的存取功能"""
        cache = LRUCache(capacity=3)
        
        # 添加缓存项
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # 验证获取缓存项
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")
        self.assertIsNone(cache.get("key4"))  # 不存在的键
        
        # 验证LRU逻辑 - 添加第四项后，最早的key1应被淘汰
        cache.put("key4", "value4")
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")
        self.assertEqual(cache.get("key4"), "value4")
        
        # 验证访问会更新使用顺序
        cache.get("key2")  # 访问key2，使其变为最近使用
        cache.put("key5", "value5")  # 添加key5，应淘汰key3
        self.assertIsNone(cache.get("key3"))
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key4"), "value4")
        self.assertEqual(cache.get("key5"), "value5")


class TestDTWMatcher(unittest.TestCase):
    """测试DTW匹配器的功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.matcher = DTWMatcher(window=3, use_fast_dtw=False)
        
        # 创建一些测试序列
        self.seq1 = np.array([1, 2, 3, 4, 5])
        self.seq2 = np.array([1, 2, 3, 4, 5])  # 相同序列
        self.seq3 = np.array([5, 4, 3, 2, 1])  # 反转序列
        self.seq4 = np.array([1, 2, 3, 4])     # 长度不同的序列
        self.seq5 = np.array([1.1, 2.1, 3.1, 4.1, 5.1])  # 略有不同的序列
        
        # 创建包含NaN的序列
        self.seq_with_nan = np.array([1, 2, np.nan, 4, 5])
        
        # 创建包含无限值的序列
        self.seq_with_inf = np.array([1, 2, np.inf, 4, 5])
        
        # 创建更复杂的序列
        t = np.linspace(0, 2*np.pi, 100)
        self.sine_wave = np.sin(t)
        self.cosine_wave = np.cos(t)
        self.noisy_sine = np.sin(t) + np.random.normal(0, 0.1, 100)
    
    def test_initialization(self):
        """测试DTWMatcher初始化参数"""
        # 测试默认参数
        matcher = DTWMatcher()
        self.assertIsNone(matcher.window)
        self.assertFalse(matcher.use_fast_dtw)
        self.assertTrue(matcher.use_caching)
        self.assertEqual(matcher.cache.capacity, 1000)
        
        # 测试自定义参数
        matcher = DTWMatcher(window=5, use_fast_dtw=True, 
                            use_caching=False, cache_size=500,
                            early_stopping=True, early_stopping_threshold=0.5,
                            max_workers=4)
        self.assertEqual(matcher.window, 5)
        self.assertTrue(matcher.use_fast_dtw)
        self.assertFalse(matcher.use_caching)
        self.assertEqual(matcher.cache.capacity, 500)
        self.assertTrue(matcher.early_stopping)
        self.assertEqual(matcher.early_stopping_threshold, 0.5)
        self.assertEqual(matcher.max_workers, 4)
        
        # 测试无效参数
        with self.assertRaises(ValueError):
            DTWMatcher(window=0)
        
        with self.assertRaises(ValueError):
            DTWMatcher(window=-1)
        
        with self.assertRaises(ValueError):
            DTWMatcher(cache_size=0)
        
        with self.assertRaises(ValueError):
            DTWMatcher(early_stopping_threshold=-0.1)
        
        with self.assertRaises(ValueError):
            DTWMatcher(early_stopping_threshold=1.1)
            
        with self.assertRaises(ValueError):
            DTWMatcher(max_workers=0)
    
    def test_normalize_series(self):
        """测试序列归一化功能"""
        matcher = DTWMatcher()
        
        # 测试标准序列的归一化
        norm_seq = matcher.normalize_series(self.seq1)
        self.assertEqual(norm_seq.shape, self.seq1.shape)
        self.assertAlmostEqual(np.min(norm_seq), 0)
        self.assertAlmostEqual(np.max(norm_seq), 1)
        
        # 测试常量序列的归一化
        const_seq = np.array([5, 5, 5, 5, 5])
        norm_const = matcher.normalize_series(const_seq)
        np.testing.assert_array_equal(norm_const, np.zeros_like(const_seq))
        
        # 测试无效输入
        with self.assertRaises(ValueError):
            matcher.normalize_series(None)
        
        with self.assertRaises(ValueError):
            matcher.normalize_series(np.array([]))
        
        with self.assertRaises(ValueError):
            matcher.normalize_series(self.seq_with_nan)
        
        with self.assertRaises(ValueError):
            matcher.normalize_series(self.seq_with_inf)
    
    def test_compute_distance(self):
        """测试DTW距离计算"""
        matcher = DTWMatcher()
        
        # 测试相同序列，距离应为0
        dist1 = matcher.compute_distance(self.seq1, self.seq2)
        self.assertEqual(dist1, 0)
        
        # 测试不同序列
        dist2 = matcher.compute_distance(self.seq1, self.seq3)
        self.assertGreater(dist2, 0)
        
        # 测试长度不同的序列
        dist3 = matcher.compute_distance(self.seq1, self.seq4)
        self.assertGreater(dist3, 0)
        
        # 测试略有不同的序列
        dist4 = matcher.compute_distance(self.seq1, self.seq5)
        self.assertGreater(dist4, 0)
        self.assertLess(dist4, dist2)  # 应小于反转序列的距离
        
        # 测试更复杂的序列
        dist5 = matcher.compute_distance(self.sine_wave, self.cosine_wave)
        dist6 = matcher.compute_distance(self.sine_wave, self.noisy_sine)
        self.assertGreater(dist5, dist6)  # 与噪声sine的距离应小于与cosine的距离
        
        # 测试无效输入
        with self.assertRaises(ValueError):
            matcher.compute_distance(None, self.seq1)
        
        with self.assertRaises(ValueError):
            matcher.compute_distance(self.seq1, None)
        
        with self.assertRaises(ValueError):
            matcher.compute_distance(np.array([]), self.seq1)
        
        with self.assertRaises(ValueError):
            matcher.compute_distance(self.seq1, np.array([]))
    
    def test_compute_similarity(self):
        """测试相似度计算"""
        matcher = DTWMatcher()
        
        # 测试相同序列，相似度应为1
        sim1 = matcher.compute_similarity(self.seq1, self.seq2)
        self.assertAlmostEqual(sim1, 1.0)
        
        # 测试不同序列，相似度应在0到1之间
        sim2 = matcher.compute_similarity(self.seq1, self.seq3)
        self.assertGreater(sim2, 0)
        self.assertLess(sim2, 1)
        
        # 测试复杂序列
        sim3 = matcher.compute_similarity(self.sine_wave, self.noisy_sine)
        sim4 = matcher.compute_similarity(self.sine_wave, self.cosine_wave)
        self.assertGreater(sim3, sim4)  # 与噪声sine的相似度应大于与cosine的相似度
    
    def test_caching(self):
        """测试缓存功能"""
        # 使用带缓存的匹配器
        matcher_with_cache = DTWMatcher(use_caching=True, cache_size=10)
        
        # 第一次计算应该没有缓存命中
        matcher_with_cache.compute_distance(self.seq1, self.seq3)
        self.assertEqual(matcher_with_cache.cache_hits, 0)
        self.assertEqual(matcher_with_cache.cache_misses, 1)
        
        # 第二次计算应该有缓存命中
        matcher_with_cache.compute_distance(self.seq1, self.seq3)
        self.assertEqual(matcher_with_cache.cache_hits, 1)
        self.assertEqual(matcher_with_cache.cache_misses, 1)
        
        # 测试不使用缓存
        matcher_no_cache = DTWMatcher(use_caching=False)
        matcher_no_cache.compute_distance(self.seq1, self.seq3)
        matcher_no_cache.compute_distance(self.seq1, self.seq3)
        self.assertEqual(matcher_no_cache.cache_hits, 0)
        self.assertEqual(matcher_no_cache.cache_misses, 0)  # 不使用缓存时不统计缓存未命中
    
    def test_warping_path(self):
        """测试时间弯曲路径的计算"""
        matcher = DTWMatcher()
        
        # 对于相同序列，弯曲路径应该是对角线
        _, path1 = matcher.compute_distance_with_path(self.seq1, self.seq2)
        for i, (x, y) in enumerate(path1):
            self.assertEqual(x, i)
            self.assertEqual(y, i)
        
        # 对于不同序列，弯曲路径应返回有效值
        _, path2 = matcher.compute_distance_with_path(self.seq1, self.seq3)
        self.assertEqual(len(path2), max(len(self.seq1), len(self.seq3)))
        
        # 验证路径的起点和终点
        self.assertEqual(path2[0], (0, 0))
        self.assertEqual(path2[-1], (len(self.seq1)-1, len(self.seq3)-1))
    
    def test_batch_compute(self):
        """测试批量计算距离功能"""
        matcher = DTWMatcher(max_workers=2)
        
        # 创建多个序列
        sequences = [self.seq1, self.seq3, self.seq5, self.sine_wave, self.cosine_wave]
        
        # 批量计算与seq1的距离
        distances = matcher.batch_compute_distance(self.seq1, sequences)
        
        # 验证结果
        self.assertEqual(len(distances), len(sequences))
        self.assertEqual(distances[0], 0)  # 与自身的距离为0
        self.assertGreater(distances[1], 0)  # 与其他序列的距离应大于0
        
        # 测试无效输入
        with self.assertRaises(ValueError):
            matcher.batch_compute_distance(None, sequences)
        
        with self.assertRaises(ValueError):
            matcher.batch_compute_distance(self.seq1, [])
    
    def test_find_best_matches(self):
        """测试查找最佳匹配功能"""
        matcher = DTWMatcher()
        
        # 创建多个候选序列
        candidates = [
            self.seq1,  # 完全相同
            self.seq3,  # 反转序列
            self.seq5,  # 略有不同
            self.noisy_sine,  # 噪声正弦
            self.cosine_wave  # 余弦
        ]
        
        # 使用seq1作为模式查找最佳匹配
        matches = matcher.find_best_matches(self.seq1, candidates, top_n=3)
        
        # 验证结果
        self.assertEqual(len(matches), 3)
        # 验证返回的是(index, similarity)对的列表
        self.assertIsInstance(matches[0], tuple)
        self.assertEqual(len(matches[0]), 2)
        
        # 第一个匹配应该是自身
        self.assertEqual(matches[0][0], 0)
        self.assertAlmostEqual(matches[0][1], 1.0)
        
        # 验证相似度排序
        for i in range(len(matches) - 1):
            self.assertGreaterEqual(matches[i][1], matches[i+1][1])
    
    def test_early_stopping(self):
        """测试提前停止功能"""
        # 创建启用提前停止的匹配器
        matcher_with_es = DTWMatcher(early_stopping=True, early_stopping_threshold=0.5)
        
        # 计算距离但应该提前停止
        dist = matcher_with_es.compute_distance(self.seq1, self.seq3)
        self.assertGreater(dist, 0)
        
        # 由于提前停止，实际计算的距离应该不是真实的DTW距离
        matcher_without_es = DTWMatcher(early_stopping=False)
        true_dist = matcher_without_es.compute_distance(self.seq1, self.seq3)
        
        # 根据提前停止的实现方式，这个断言可能需要调整
        self.assertNotEqual(dist, true_dist)


if __name__ == "__main__":
    unittest.main() 