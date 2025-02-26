"""
DTW参数调优模块

提供自动化参数调优功能，测试不同参数组合的效果，并记录比较性能表现。
支持网格搜索和基于性能的参数推荐。
"""
import time
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor
from .dtw_matcher import DTWMatcher

class DTWParamTuner:
    """DTW参数调优器，用于测试和评估不同参数组合的效果"""
    
    def __init__(self, test_data=None, reference_data=None, n_workers=None):
        """
        初始化参数调优器
        
        Args:
            test_data (list): 测试数据集，用于评估不同参数的效果
            reference_data (list): 参考数据集，用于计算相似度
            n_workers (int): 并行工作进程数，默认为None（由系统决定）
        """
        self.test_data = test_data
        self.reference_data = reference_data
        self.n_workers = n_workers
        self.results = None
        
    def set_test_data(self, test_data, reference_data=None):
        """
        设置测试数据集
        
        Args:
            test_data (list): 测试数据集
            reference_data (list, optional): 参考数据集，如不提供则使用test_data中的第一个序列
        """
        self.test_data = test_data
        if reference_data is not None:
            self.reference_data = reference_data
        elif test_data and len(test_data) > 0:
            self.reference_data = test_data[0]
            
    def grid_search(self, param_grid, metric='accuracy', timeout=None):
        """
        网格搜索最佳参数组合
        
        Args:
            param_grid (dict): 参数网格，如 {'window': [None, 5, 10], 'use_fast_dtw': [True, False]}
            metric (str): 评估指标，可选 'accuracy', 'time', 'memory', 'combined'
            timeout (float): 每个参数组合的最大执行时间（秒），超时则中断
            
        Returns:
            pd.DataFrame: 包含所有参数组合评估结果的DataFrame
        """
        if not self.test_data:
            raise ValueError("请先设置测试数据集")
            
        # 生成所有参数组合
        param_keys = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(itertools.product(*param_values))
        
        results = []
        
        # 使用并行处理评估参数组合
        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            futures = []
            for params in param_combinations:
                param_dict = dict(zip(param_keys, params))
                future = executor.submit(
                    self._evaluate_params, 
                    param_dict, 
                    metric, 
                    timeout
                )
                futures.append((future, param_dict))
            
            # 收集结果
            for future, param_dict in futures:
                try:
                    result = future.result()
                    results.append({**param_dict, **result})
                except Exception as e:
                    print(f"参数组合 {param_dict} 评估失败: {e}")
                    results.append({**param_dict, 'error': str(e)})
        
        # 转换为DataFrame并排序
        self.results = pd.DataFrame(results)
        if 'error' not in self.results.columns:
            self.results['error'] = None
            
        # 根据指标排序
        if metric == 'accuracy':
            self.results.sort_values('accuracy', ascending=False, inplace=True)
        elif metric == 'time':
            self.results.sort_values('time', ascending=True, inplace=True)
        elif metric == 'combined':
            # 组合指标 = 准确率 / 时间
            self.results['combined_score'] = self.results['accuracy'] / self.results['time']
            self.results.sort_values('combined_score', ascending=False, inplace=True)
            
        return self.results
    
    def _evaluate_params(self, params, metric, timeout):
        """
        评估单个参数组合的性能
        
        Args:
            params (dict): 参数字典
            metric (str): 评估指标
            timeout (float): 超时时间
            
        Returns:
            dict: 评估结果
        """
        # 创建DTW匹配器
        dtw_matcher = DTWMatcher(**params)
        
        # 初始化结果
        result = {
            'time': 0,
            'memory': 0,
            'accuracy': 0,
            'early_stops': 0,
            'cache_hits': 0
        }
        
        # 测量时间性能
        start_time = time.time()
        
        # 根据选择的指标执行不同的测试
        if metric in ['accuracy', 'combined']:
            # 执行相似度计算和评估准确性
            similarities = []
            for i, test_seq in enumerate(self.test_data):
                try:
                    # 计算相似度
                    similarity = dtw_matcher.compute_similarity(
                        self.reference_data, test_seq
                    )
                    similarities.append(similarity)
                except Exception as e:
                    print(f"相似度计算失败 ({i}): {e}")
            
            # 计算准确性 (这里可以根据实际需求定义准确性)
            # 例如：高相似度序列的平均相似度
            if similarities:
                result['accuracy'] = np.mean(similarities)
        
        # 测量执行时间
        result['time'] = time.time() - start_time
        
        # 获取计算统计信息
        stats = dtw_matcher.get_computation_stats()
        result['early_stops'] = stats.get('early_stops', 0)
        result['cache_hits'] = stats.get('cache_hits', 0)
        result['computations'] = stats.get('computations', 0)
        
        return result
    
    def recommend_params(self, importance=None):
        """
        根据评估结果推荐最佳参数组合
        
        Args:
            importance (dict, optional): 各指标的重要性权重，如 {'accuracy': 0.7, 'time': 0.3}
            
        Returns:
            dict: 推荐的参数组合
        """
        if self.results is None or len(self.results) == 0:
            raise ValueError("请先使用grid_search方法评估参数")
            
        # 默认权重
        if importance is None:
            importance = {'accuracy': 0.7, 'time': 0.3}
            
        # 数据规范化
        normalized = self.results.copy()
        for col in ['accuracy', 'time']:
            if col in normalized.columns:
                # 对于时间，越小越好
                if col == 'time':
                    max_val = normalized[col].max()
                    normalized[col] = (max_val - normalized[col]) / max_val
                # 对于准确率，越大越好
                else:
                    min_val = normalized[col].min()
                    max_val = normalized[col].max()
                    normalized[col] = (normalized[col] - min_val) / (max_val - min_val)
        
        # 计算综合得分
        score = 0
        for metric, weight in importance.items():
            if metric in normalized.columns:
                score += normalized[metric] * weight
        
        normalized['score'] = score
        
        # 返回得分最高的参数组合
        best_idx = normalized['score'].idxmax()
        param_columns = [col for col in self.results.columns 
                         if col not in ['accuracy', 'time', 'memory', 'early_stops', 
                                        'cache_hits', 'computations', 'error', 'combined_score']]
        
        return self.results.loc[best_idx, param_columns].to_dict()
    
    def plot_results(self, x_param=None, y_param=None, metric='accuracy'):
        """
        可视化参数评估结果
        
        Args:
            x_param (str, optional): X轴参数名称，如果为None则自动选择
            y_param (str, optional): Y轴参数名称，如果为None则自动选择
            metric (str): 颜色编码的指标，如 'accuracy', 'time'
            
        Returns:
            matplotlib.figure.Figure: 图形对象
        """
        if self.results is None or len(self.results) == 0:
            raise ValueError("请先使用grid_search方法评估参数")
            
        # 获取参数列名（非结果指标）
        param_columns = [col for col in self.results.columns 
                         if col not in ['accuracy', 'time', 'memory', 'early_stops', 
                                        'cache_hits', 'computations', 'error', 'combined_score']]
        
        # 如果未指定参数，自动选择
        if x_param is None and len(param_columns) > 0:
            x_param = param_columns[0]
        if y_param is None and len(param_columns) > 1:
            y_param = param_columns[1]
            
        # 创建图形
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if x_param and y_param and metric in self.results.columns:
            # 二维参数热力图
            pivot = self.results.pivot_table(
                index=y_param, 
                columns=x_param, 
                values=metric,
                aggfunc='mean'
            )
            
            im = ax.imshow(pivot.values, cmap='viridis')
            
            # 设置坐标轴
            ax.set_xticks(np.arange(len(pivot.columns)))
            ax.set_yticks(np.arange(len(pivot.index)))
            ax.set_xticklabels(pivot.columns)
            ax.set_yticklabels(pivot.index)
            
            # 添加颜色条
            cbar = fig.colorbar(im, ax=ax)
            cbar.set_label(metric)
            
            # 设置标题和标签
            ax.set_title(f'{metric.capitalize()} vs {x_param} 和 {y_param}')
            ax.set_xlabel(x_param)
            ax.set_ylabel(y_param)
            
        elif x_param and metric in self.results.columns:
            # 单参数条形图
            grouped = self.results.groupby(x_param)[metric].mean().reset_index()
            ax.bar(grouped[x_param].astype(str), grouped[metric])
            
            # 设置标题和标签
            ax.set_title(f'{metric.capitalize()} vs {x_param}')
            ax.set_xlabel(x_param)
            ax.set_ylabel(metric)
            
        else:
            # 绘制所有参数的相关性热力图
            if len(param_columns) > 0 and metric in self.results.columns:
                corr = self.results[param_columns + [metric]].corr()
                im = ax.imshow(corr.values, cmap='coolwarm')
                
                # 设置坐标轴
                ax.set_xticks(np.arange(len(corr.columns)))
                ax.set_yticks(np.arange(len(corr.index)))
                ax.set_xticklabels(corr.columns)
                ax.set_yticklabels(corr.index)
                
                # 添加相关系数
                for i in range(len(corr.index)):
                    for j in range(len(corr.columns)):
                        ax.text(j, i, f"{corr.iloc[i, j]:.2f}",
                                ha="center", va="center", color="white")
                
                # 设置标题
                ax.set_title('参数相关性矩阵')
            
        plt.tight_layout()
        return fig
    
    def compare_performance(self, top_n=5, metric='combined_score'):
        """
        比较表现最好的几个参数组合
        
        Args:
            top_n (int): 比较的参数组合数量
            metric (str): 排序指标
            
        Returns:
            tuple: (pd.DataFrame, matplotlib.figure.Figure) 比较表格和图表
        """
        if self.results is None or len(self.results) == 0:
            raise ValueError("请先使用grid_search方法评估参数")
            
        # 确保指标存在
        if metric not in self.results.columns and metric == 'combined_score':
            # 计算组合得分
            self.results['combined_score'] = (
                self.results['accuracy'] / self.results['time'].clip(lower=0.001)
            )
            
        # 按指标排序
        sorted_results = self.results.sort_values(metric, ascending=(metric == 'time'))
        top_results = sorted_results.head(top_n)
        
        # 创建比较图表
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # 准确率比较
        if 'accuracy' in top_results.columns:
            axes[0].bar(range(len(top_results)), top_results['accuracy'])
            axes[0].set_title('准确率比较')
            axes[0].set_xticks(range(len(top_results)))
            axes[0].set_xticklabels([f"组合{i+1}" for i in range(len(top_results))])
            axes[0].set_ylabel('准确率')
            
            # 添加参数标签
            for i, (_, row) in enumerate(top_results.iterrows()):
                param_text = ", ".join([f"{k}={v}" for k, v in row.items() 
                                        if k not in ['accuracy', 'time', 'memory', 
                                                     'early_stops', 'cache_hits', 
                                                     'computations', 'error', 
                                                     'combined_score']])
                axes[0].text(i, 0.02, param_text, ha='center', 
                             va='bottom', rotation=90, fontsize=8)
        
        # 时间比较
        if 'time' in top_results.columns:
            axes[1].bar(range(len(top_results)), top_results['time'])
            axes[1].set_title('计算时间比较')
            axes[1].set_xticks(range(len(top_results)))
            axes[1].set_xticklabels([f"组合{i+1}" for i in range(len(top_results))])
            axes[1].set_ylabel('时间(秒)')
        
        plt.tight_layout()
        
        return top_results, fig


def generate_test_data(n_series=10, length=100, noise_levels=None):
    """
    生成测试数据集
    
    Args:
        n_series (int): 生成的序列数量
        length (int): 每个序列的长度
        noise_levels (list, optional): 噪声级别，如果为None则随机生成
        
    Returns:
        list: 生成的时间序列列表
    """
    if noise_levels is None:
        noise_levels = np.linspace(0, 0.5, n_series)
        
    # 创建基础序列 (正弦波)
    x = np.linspace(0, 4 * np.pi, length)
    base_series = np.sin(x)
    
    # 生成带噪声的变种
    series_list = []
    for i in range(n_series):
        # 添加随机噪声
        noise = np.random.normal(0, noise_levels[i], length)
        # 添加随机相位偏移
        phase_shift = np.random.uniform(-np.pi/4, np.pi/4)
        # 随机伸缩序列长度 (80%-120%)
        stretch = np.random.uniform(0.8, 1.2)
        stretched_length = int(length * stretch)
        
        # 创建新的x轴
        new_x = np.linspace(0 + phase_shift, 4 * np.pi + phase_shift, stretched_length)
        # 生成序列
        new_series = np.sin(new_x) + noise[:stretched_length] if stretched_length <= length else np.sin(new_x) + np.append(noise, np.zeros(stretched_length - length))
        
        series_list.append(new_series)
        
    return series_list 