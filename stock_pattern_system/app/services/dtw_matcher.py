"""
基于DTW的形态匹配模块

使用动态时间规整(DTW)算法计算时间序列相似度，支持高效的形态匹配和相似度计算。
该模块提供了归一化、距离计算、相似度评估、最佳匹配查找和可视化等功能。
"""
import numpy as np
from dtaidistance import dtw
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import time
from collections import OrderedDict
import warnings
import matplotlib.pyplot as plt

class LRUCache:
    """简单的LRU缓存实现，用于存储计算结果"""
    
    def __init__(self, capacity=100):
        """
        初始化LRU缓存
        
        Args:
            capacity (int): 缓存容量
        """
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("缓存容量必须是正整数")
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key):
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的值，如果不存在返回None
        """
        if key not in self.cache:
            return None
        # 将访问的项移到末尾（最近使用）
        value = self.cache.pop(key)
        self.cache[key] = value
        return value
    
    def put(self, key, value):
        """
        添加或更新缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            
        Returns:
            None
        """
        if key in self.cache:
            # 键已存在，先移除
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            # 缓存已满，移除最久未使用的项（第一个）
            self.cache.popitem(last=False)
        # 添加新项
        self.cache[key] = value

class DTWMatcher:
    """DTW匹配器，使用动态时间规整算法计算时间序列相似度"""
    
    def __init__(self, window=None, use_fast_dtw=True, max_workers=None, 
                 cache_size=1000, early_stopping=True, early_stopping_threshold=2.0):
        """
        初始化DTW匹配器
        
        Args:
            window (int, optional): DTW计算的窗口大小，限制对齐路径的偏移量
            use_fast_dtw (bool): 是否使用快速DTW算法，默认True
            max_workers (int, optional): 并行计算的最大工作进程数
            cache_size (int): 缓存大小，存储计算结果以提高性能
            early_stopping (bool): 是否启用提前终止优化
            early_stopping_threshold (float): 提前终止阈值，距离超过此值时终止计算
            
        Raises:
            ValueError: 参数无效时抛出
        """
        if window is not None and (not isinstance(window, int) or window <= 0):
            raise ValueError("window必须是正整数或None")
        if not isinstance(cache_size, int) or cache_size < 0:
            raise ValueError("cache_size必须是非负整数")
        if not isinstance(early_stopping_threshold, (int, float)) or early_stopping_threshold <= 0:
            raise ValueError("early_stopping_threshold必须是正数")
            
        self.window = window
        self.use_fast_dtw = use_fast_dtw
        self.max_workers = max_workers
        self.early_stopping = early_stopping
        self.early_stopping_threshold = early_stopping_threshold
        
        # 初始化缓存
        self.cache = LRUCache(capacity=cache_size)
        
        # 初始化计算统计
        self.stats = {
            'computations': 0,
            'cache_hits': 0,
            'early_stops': 0,
            'total_time': 0
        }
    
    def normalize_series(self, series):
        """
        将时间序列归一化到[0,1]范围
        
        Args:
            series (array-like): 输入时间序列
            
        Returns:
            numpy.ndarray: 归一化后的时间序列
            
        Raises:
            ValueError: 输入序列无效时抛出
        """
        if series is None:
            raise ValueError("输入序列不能为None")
            
        # 转换为numpy数组
        try:
            series = np.asarray(series, dtype=np.float64)
        except (ValueError, TypeError) as e:
            raise ValueError(f"无法将输入转换为数值数组: {e}")
            
        if series.size == 0:
            raise ValueError("输入序列不能为空")
            
        if np.isnan(series).any():
            raise ValueError("输入序列包含NaN值")
            
        # 处理常数序列的情况
        min_val = np.min(series)
        max_val = np.max(series)
        
        if np.isclose(min_val, max_val):
            # 如果是常数序列，返回全0数组
            warnings.warn("输入是常数序列，将归一化为全0数组")
            return np.zeros_like(series)
            
        # 归一化到[0,1]范围
        normalized = (series - min_val) / (max_val - min_val)
        return normalized
    
    def _generate_cache_key(self, series1, series2):
        """
        为两个序列生成缓存键
        
        Args:
            series1 (numpy.ndarray): 第一个序列
            series2 (numpy.ndarray): 第二个序列
            
        Returns:
            tuple: 缓存键
        """
        # 使用序列的哈希作为键
        # 注意: 由于浮点数精度问题，这种方法不是100%可靠
        # 但对于实际应用已足够好
        hash1 = hash(series1.tobytes())
        hash2 = hash(series2.tobytes())
        
        # 确保键的顺序一致（距离是对称的）
        if hash1 > hash2:
            return (hash2, hash1)
        return (hash1, hash2)
    
    def compute_distance(self, series1, series2):
        """
        计算两个时间序列之间的DTW距离
        
        Args:
            series1 (array-like): 第一个时间序列
            series2 (array-like): 第二个时间序列
            
        Returns:
            float: DTW距离
            
        Raises:
            ValueError: 输入序列无效时抛出
        """
        if series1 is None or series2 is None:
            raise ValueError("输入序列不能为None")
            
        # 记录计算开始时间
        start_time = time.time()
        
        try:
            # 转换为numpy数组并归一化
            norm_series1 = self.normalize_series(series1)
            norm_series2 = self.normalize_series(series2)
            
            # 检查缓存
            cache_key = self._generate_cache_key(norm_series1, norm_series2)
            cached_result = self.cache.get(cache_key)
            
            if cached_result is not None:
                # 缓存命中
                self.stats['cache_hits'] += 1
                return cached_result
                
            # 计算DTW距离
            self.stats['computations'] += 1
            
            if self.early_stopping:
                # 使用支持提前终止的DTW计算
                distance = self._compute_dtw_with_early_stopping(norm_series1, norm_series2)
            else:
                # 使用标准DTW计算
                if self.use_fast_dtw:
                    distance = dtw.distance_fast(
                        norm_series1, 
                        norm_series2,
                        window=self.window
                    )
                else:
                    distance = dtw.distance(
                        norm_series1, 
                        norm_series2,
                        window=self.window
                    )
                
            # 添加到缓存
            self.cache.put(cache_key, distance)
            
            return distance
        finally:
            # 更新总计算时间
            self.stats['total_time'] += time.time() - start_time
    
    def _compute_dtw_with_early_stopping(self, series1, series2):
        """
        使用提前终止优化计算DTW距离
        
        Args:
            series1 (numpy.ndarray): 归一化的第一个时间序列
            series2 (numpy.ndarray): 归一化的第二个时间序列
            
        Returns:
            float: DTW距离
        """
        # 由于dtaidistance库不直接支持提前终止，我们使用一个简单的启发式方法:
        # 如果欧几里得距离已经超过阈值，则序列可能差异很大，可以提前终止
        
        # 计算欧几里得距离
        if len(series1) > 10 and len(series2) > 10:
            # 仅使用序列的一部分计算初步距离
            sample_size = min(10, min(len(series1), len(series2)))
            euclidean_dist = np.sqrt(np.sum((series1[:sample_size] - series2[:sample_size])**2))
            
            if euclidean_dist > self.early_stopping_threshold:
                # 序列差异很大，提前终止
                self.stats['early_stops'] += 1
                # 返回一个较大的距离值
                return euclidean_dist * 2
        
        # 正常计算DTW距离
        if self.use_fast_dtw:
            return dtw.distance_fast(
                series1, 
                series2,
                window=self.window
            )
        else:
            return dtw.distance(
                series1, 
                series2,
                window=self.window
            )
    
    def compute_similarity(self, series1, series2):
        """
        计算两个时间序列之间的相似度
        
        Args:
            series1 (array-like): 第一个时间序列
            series2 (array-like): 第二个时间序列
            
        Returns:
            float: 相似度(0-1)，1表示完全相似，0表示完全不同
            
        Raises:
            ValueError: 输入序列无效时抛出
        """
        if series1 is None or series2 is None:
            raise ValueError("输入序列不能为None")
        
        # 计算DTW距离
        distance = self.compute_distance(series1, series2)
        
        # 转换为相似度(0-1)
        # 使用指数衰减函数: similarity = exp(-distance)
        similarity = np.exp(-distance)
        
        return similarity
    
    def find_best_matches(self, pattern, candidates, top_n=10, threshold=0.7, batch_size=None):
        """
        在候选序列列表中查找与模式最匹配的前N个序列
        
        Args:
            pattern (array-like): 要匹配的模式序列
            candidates (list): 候选序列列表，每个元素是(序列, 标识符)元组
            top_n (int): 返回的最佳匹配数量
            threshold (float): 相似度阈值(0-1)，低于此值的匹配会被忽略
            batch_size (int, optional): 批量处理大小，用于大数据集
            
        Returns:
            list: 最佳匹配列表，每个元素是包含标识符和相似度的字典
            
        Raises:
            ValueError: 参数无效时抛出
        """
        if pattern is None:
            raise ValueError("模式序列不能为None")
        if not candidates:
            return []
        if not isinstance(top_n, int) or top_n <= 0:
            raise ValueError("top_n必须是正整数")
        if not 0 <= threshold <= 1:
            raise ValueError("threshold必须在0-1范围内")
            
        # 规范化模式
        try:
            pattern = self.normalize_series(pattern)
        except ValueError as e:
            raise ValueError(f"无法规范化模式序列: {e}")
            
        # 如果启用批量处理
        if batch_size is not None and batch_size > 0 and len(candidates) > batch_size:
            matches = []
            # 分批处理候选序列
            for i in range(0, len(candidates), batch_size):
                batch = candidates[i:i+batch_size]
                batch_matches = self._process_candidates_batch(pattern, batch, top_n, threshold)
                matches.extend(batch_matches)
                
            # 保留全局前N个匹配
            matches.sort(key=lambda x: x['similarity'], reverse=True)
            return matches[:top_n]
        else:
            # 直接处理所有候选序列
            return self._process_candidates_batch(pattern, candidates, top_n, threshold)
    
    def _process_candidates_batch(self, pattern, candidates, top_n, threshold):
        """
        处理一批候选序列，找出最佳匹配
        
        Args:
            pattern (numpy.ndarray): 归一化的模式序列
            candidates (list): 候选序列列表
            top_n (int): 返回的最佳匹配数量
            threshold (float): 相似度阈值
            
        Returns:
            list: 最佳匹配列表
        """
        matches = []
        
        # 使用并行处理计算相似度
        if self.max_workers is not None and self.max_workers > 1:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                # 准备任务
                futures = []
                for i, (candidate_series, code) in enumerate(candidates):
                    future = executor.submit(
                        self._compute_similarity_task, 
                        pattern, 
                        candidate_series,
                        code
                    )
                    futures.append(future)
                
                # 收集结果
                for future in futures:
                    try:
                        result = future.result()
                        if result and result['similarity'] >= threshold:
                            matches.append(result)
                    except Exception as e:
                        warnings.warn(f"计算相似度时发生错误: {e}")
        else:
            # 串行处理
            for candidate_series, code in candidates:
                try:
                    result = self._compute_similarity_task(pattern, candidate_series, code)
                    if result and result['similarity'] >= threshold:
                        matches.append(result)
                except Exception as e:
                    warnings.warn(f"计算相似度时发生错误: {e}")
        
        # 按相似度排序
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches[:top_n]
    
    def _compute_similarity_task(self, pattern, candidate_series, code):
        """
        计算单个候选序列与模式的相似度
        
        Args:
            pattern (numpy.ndarray): 归一化的模式序列
            candidate_series (array-like): 候选序列
            code: 候选序列标识符
            
        Returns:
            dict: 包含标识符和相似度的结果字典
        """
        try:
            # 计算相似度
            similarity = self.compute_similarity(pattern, candidate_series)
            
            return {
                'code': code,
                'similarity': similarity
            }
        except Exception as e:
            warnings.warn(f"计算序列 {code} 的相似度时发生错误: {e}")
            return None
    
    def get_warping_path(self, series1, series2):
        """
        获取两个时间序列的DTW对齐路径
        
        Args:
            series1 (array-like): 第一个时间序列
            series2 (array-like): 第二个时间序列
            
        Returns:
            list: 对齐路径，元素为(series1索引, series2索引)的元组
            
        Raises:
            ValueError: 输入序列无效时抛出
        """
        if series1 is None or series2 is None:
            raise ValueError("输入序列不能为None")
            
        try:
            # 转换为numpy数组并归一化
            norm_series1 = self.normalize_series(series1)
            norm_series2 = self.normalize_series(series2)
            
            # 计算路径
            path = dtw.warping_path(
                norm_series1, 
                norm_series2,
                window=self.window
            )
            
            return path
        except Exception as e:
            raise ValueError(f"计算对齐路径时发生错误: {e}")
    
    def batch_compute_similarity(self, reference_series, series_list):
        """
        批量计算一个参考序列与多个序列的相似度
        
        Args:
            reference_series (array-like): 参考序列
            series_list (list): 要比较的序列列表
            
        Returns:
            list: 相似度列表，顺序与输入序列相同
            
        Raises:
            ValueError: 输入无效时抛出
        """
        if reference_series is None:
            raise ValueError("参考序列不能为None")
        if not series_list:
            return []
            
        similarities = []
        for series in series_list:
            try:
                similarity = self.compute_similarity(reference_series, series)
                similarities.append(similarity)
            except Exception as e:
                warnings.warn(f"计算相似度时发生错误: {e}")
                similarities.append(0.0)  # 错误情况下设为零相似度
                
        return similarities
    
    def get_computation_stats(self):
        """
        获取计算统计信息
        
        Returns:
            dict: 包含计算次数、缓存命中次数、提前终止次数等的字典
        """
        # 计算缓存命中率
        total = self.stats['computations'] + self.stats['cache_hits']
        cache_hit_rate = self.stats['cache_hits'] / total if total > 0 else 0
        
        # 计算提前终止率
        early_stop_rate = self.stats['early_stops'] / self.stats['computations'] if self.stats['computations'] > 0 else 0
        
        return {
            **self.stats,
            'cache_hit_rate': cache_hit_rate,
            'early_stop_rate': early_stop_rate
        }
    
    def reset_stats(self):
        """
        重置计算统计信息
        
        Returns:
            None
        """
        self.stats = {
            'computations': 0,
            'cache_hits': 0,
            'early_stops': 0,
            'total_time': 0
        }
    
    def clear_cache(self):
        """清空计算缓存"""
        self.cache = LRUCache(capacity=self.cache.capacity)
    
    def plot_warping_path_visualization(self, series1, series2, path=None):
        """
        可视化两个时间序列的DTW对齐路径
        
        Args:
            series1 (array-like): 第一个时间序列
            series2 (array-like): 第二个时间序列
            path (list, optional): 预先计算的对齐路径，如果为None则计算
            
        Returns:
            matplotlib.figure.Figure: 图形对象
            
        Raises:
            ValueError: 输入序列无效时抛出
        """
        if series1 is None or series2 is None:
            raise ValueError("输入序列不能为None")
            
        try:
            # 转换为numpy数组并归一化
            norm_series1 = self.normalize_series(series1)
            norm_series2 = self.normalize_series(series2)
            
            # 获取对齐路径
            if path is None:
                path = self.get_warping_path(norm_series1, norm_series2)
                
            # 创建图形
            fig = plt.figure(figsize=(12, 8))
            
            # 1. 序列对比图 (上方)
            ax1 = fig.add_subplot(211)
            ax1.plot(norm_series1, label='Series 1')
            ax1.plot(norm_series2, label='Series 2')
            ax1.set_title('时间序列比较')
            ax1.legend()
            ax1.grid(True)
            
            # 2. 距离矩阵和对齐路径 (下方)
            ax2 = fig.add_subplot(212)
            
            # 计算距离矩阵
            n, m = len(norm_series1), len(norm_series2)
            distance_matrix = np.zeros((n, m))
            for i in range(n):
                for j in range(m):
                    distance_matrix[i, j] = (norm_series1[i] - norm_series2[j])**2
                    
            # 绘制距离矩阵
            im = ax2.imshow(distance_matrix, cmap='viridis', origin='lower')
            fig.colorbar(im, ax=ax2, label='距离')
            
            # 绘制对齐路径
            path_x, path_y = zip(*path)
            ax2.plot(path_y, path_x, 'r-', linewidth=2)
            ax2.plot(path_y, path_x, 'r.', markersize=6)
            
            ax2.set_xlabel('Series 2')
            ax2.set_ylabel('Series 1')
            ax2.set_title('DTW对齐路径')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            raise ValueError(f"可视化对齐路径时发生错误: {e}")
    
    def plot_series_comparison(self, series1, series2, labels=None):
        """
        可视化比较两个时间序列
        
        Args:
            series1 (array-like): 第一个时间序列
            series2 (array-like): 第二个时间序列
            labels (tuple, optional): 序列标签(label1, label2)
            
        Returns:
            matplotlib.figure.Figure: 图形对象
            
        Raises:
            ValueError: 输入序列无效时抛出
        """
        if series1 is None or series2 is None:
            raise ValueError("输入序列不能为None")
            
        # 设置默认标签
        if labels is None:
            labels = ('Series 1', 'Series 2')
            
        try:
            # 转换为numpy数组
            s1 = np.asarray(series1)
            s2 = np.asarray(series2)
            
            # 计算DTW距离和相似度
            distance = self.compute_distance(s1, s2)
            similarity = self.compute_similarity(s1, s2)
            
            # 获取对齐路径
            path = self.get_warping_path(s1, s2)
            
            # 创建图形
            fig = plt.figure(figsize=(12, 10))
            
            # 1. 原始序列对比 (上方)
            ax1 = fig.add_subplot(311)
            ax1.plot(s1, label=labels[0])
            ax1.plot(s2, label=labels[1])
            ax1.set_title('原始时间序列比较')
            ax1.legend()
            ax1.grid(True)
            
            # 添加距离和相似度信息
            ax1.annotate(
                f'DTW距离: {distance:.4f}\n相似度: {similarity:.4f}',
                xy=(0.02, 0.85),
                xycoords='axes fraction',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
            )
            
            # 2. 归一化序列对比 (中间)
            ax2 = fig.add_subplot(312)
            norm_s1 = self.normalize_series(s1)
            norm_s2 = self.normalize_series(s2)
            ax2.plot(norm_s1, label=f'{labels[0]} (归一化)')
            ax2.plot(norm_s2, label=f'{labels[1]} (归一化)')
            ax2.set_title('归一化时间序列比较')
            ax2.legend()
            ax2.grid(True)
            
            # 3. 对齐连接线 (下方)
            ax3 = fig.add_subplot(313)
            
            # 绘制两个序列
            x1 = np.arange(len(norm_s1))
            x2 = np.arange(len(norm_s2))
            ax3.plot(x1, norm_s1, 'o-', label=labels[0])
            ax3.plot(x2, norm_s2, 'o-', label=labels[1])
            
            # 绘制对齐连接线
            for pair in path:
                i, j = pair
                ax3.plot([i, j], [norm_s1[i], norm_s2[j]], 'k-', alpha=0.2)
                
            ax3.set_title('DTW对齐连接')
            ax3.legend()
            ax3.grid(True)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            raise ValueError(f"可视化序列比较时发生错误: {e}")
    
    def plot_multiple_matches(self, pattern, matches, top_n=5):
        """
        可视化一个模式与多个匹配结果的比较
        
        Args:
            pattern (array-like): 模式序列
            matches (list): 匹配结果列表，每个元素包含 'code', 'similarity' 和 'series' 字段
            top_n (int): 显示的匹配数量
            
        Returns:
            matplotlib.figure.Figure: 图形对象
            
        Raises:
            ValueError: 输入无效时抛出
        """
        if pattern is None:
            raise ValueError("模式序列不能为None")
        if not matches:
            raise ValueError("匹配结果列表不能为空")
            
        # 限制显示数量
        top_matches = matches[:min(top_n, len(matches))]
        
        try:
            # 转换为numpy数组并归一化
            norm_pattern = self.normalize_series(pattern)
            
            # 创建图形
            n_matches = len(top_matches)
            fig = plt.figure(figsize=(12, 3 * (n_matches + 1)))
            
            # 1. 模式序列 (上方)
            ax1 = fig.add_subplot(n_matches + 1, 1, 1)
            ax1.plot(norm_pattern, 'b-', linewidth=2)
            ax1.set_title('模式序列')
            ax1.grid(True)
            
            # 2. 匹配序列 (下方)
            for i, match in enumerate(top_matches, 1):
                ax = fig.add_subplot(n_matches + 1, 1, i + 1)
                
                # 获取序列数据
                if 'series' in match:
                    series = match['series']
                else:
                    # 如果匹配中没有序列数据，跳过
                    continue
                    
                # 归一化并绘制
                norm_series = self.normalize_series(series)
                ax.plot(norm_series, 'g-', linewidth=2)
                
                # 设置标题
                code = match.get('code', f'匹配 {i}')
                similarity = match.get('similarity', 0)
                ax.set_title(f'{code} (相似度: {similarity:.4f})')
                ax.grid(True)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            raise ValueError(f"可视化多匹配比较时发生错误: {e}")
    
    def plot_similarity_distribution(self, similarities):
        """
        可视化相似度分布直方图
        
        Args:
            similarities (list): 相似度值列表
            
        Returns:
            matplotlib.figure.Figure: 图形对象
            
        Raises:
            ValueError: 输入无效时抛出
        """
        if not similarities:
            raise ValueError("相似度列表不能为空")
            
        try:
            # 创建图形
            fig = plt.figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            
            # 绘制直方图
            n, bins, patches = ax.hist(
                similarities, 
                bins=20, 
                range=(0, 1), 
                alpha=0.7, 
                color='skyblue',
                edgecolor='black'
            )
            
            # 添加统计信息
            mean = np.mean(similarities)
            median = np.median(similarities)
            std = np.std(similarities)
            
            stats_text = (
                f'样本数: {len(similarities)}\n'
                f'平均值: {mean:.4f}\n'
                f'中位数: {median:.4f}\n'
                f'标准差: {std:.4f}\n'
                f'最小值: {min(similarities):.4f}\n'
                f'最大值: {max(similarities):.4f}'
            )
            
            ax.annotate(
                stats_text,
                xy=(0.95, 0.95),
                xycoords='axes fraction',
                horizontalalignment='right',
                verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8)
            )
            
            # 绘制平均值和中位数线
            ax.axvline(mean, color='red', linestyle='dashed', linewidth=2, label=f'平均值: {mean:.4f}')
            ax.axvline(median, color='green', linestyle='dashed', linewidth=2, label=f'中位数: {median:.4f}')
            
            # 设置图形属性
            ax.set_title('相似度分布')
            ax.set_xlabel('相似度')
            ax.set_ylabel('频率')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            raise ValueError(f"可视化相似度分布时发生错误: {e}")
    
    def generate_dtw_report(self, pattern, matches, top_n=5):
        """
        生成综合DTW匹配报告
        
        Args:
            pattern (array-like): 模式序列
            matches (list): 匹配结果列表
            top_n (int): 报告中包含的匹配数量
            
        Returns:
            dict: 包含各种图形和统计信息的报告字典
            
        Raises:
            ValueError: 输入无效时抛出
        """
        if pattern is None:
            raise ValueError("模式序列不能为None")
        if not matches:
            return {'error': '没有匹配结果'}
            
        report = {}
        
        try:
            # 1. 添加统计信息
            similarities = [match['similarity'] for match in matches if 'similarity' in match]
            report['stats'] = {
                'matches_count': len(matches),
                'mean_similarity': np.mean(similarities) if similarities else 0,
                'median_similarity': np.median(similarities) if similarities else 0,
                'std_similarity': np.std(similarities) if similarities else 0,
                'min_similarity': min(similarities) if similarities else 0,
                'max_similarity': max(similarities) if similarities else 0,
                'computation_stats': self.get_computation_stats()
            }
            
            # 2. 添加相似度分布图
            if similarities:
                report['similarity_distribution'] = self.plot_similarity_distribution(similarities)
                
            # 3. 获取前N个最佳匹配
            top_matches = matches[:min(top_n, len(matches))]
            
            # 4. 添加最佳匹配的比较图
            if top_matches and len(top_matches) > 0 and 'series' in top_matches[0]:
                best_match = top_matches[0]
                report['best_match_comparison'] = self.plot_series_comparison(
                    pattern, 
                    best_match['series'],
                    labels=('模式', best_match.get('code', '最佳匹配'))
                )
                
            # 5. 添加多匹配比较图
            if all('series' in match for match in top_matches):
                report['multiple_matches'] = self.plot_multiple_matches(
                    pattern, 
                    top_matches, 
                    top_n=top_n
                )
                
            return report
            
        except Exception as e:
            return {'error': f"生成报告时发生错误: {e}"} 