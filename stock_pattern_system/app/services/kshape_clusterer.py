"""
基于K-Shape的时间序列聚类模块

使用K-Shape算法对时间序列进行聚类，作为DTW匹配的预处理步骤
"""
import numpy as np
from tslearn.clustering import KShape
from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from sklearn.metrics import silhouette_score
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import pickle
import os
from datetime import datetime

class KShapeClusterer:
    """K-Shape聚类器，提供对时间序列的聚类功能"""
    
    def __init__(self, n_clusters=10, max_iter=100, random_state=42, max_workers=None, cache_dir=None):
        """
        初始化K-Shape聚类器
        
        Args:
            n_clusters (int): 聚类数量
            max_iter (int): 最大迭代次数
            random_state (int): 随机种子，用于结果复现
            max_workers (int, optional): 并行计算的最大工作进程数，默认使用CPU核心数-1
            cache_dir (str, optional): 缓存目录，用于保存聚类模型
        """
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.random_state = random_state
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count() - 1)
        self.cache_dir = cache_dir
        
        self.model = None
        self.scaler = TimeSeriesScalerMeanVariance()
        self.fitted = False
        self.cluster_centers_ = None
        self.labels_ = None
        self.series_codes = None  # 存储训练时的股票代码
        
    def preprocess_series(self, series):
        """
        预处理时间序列数据
        
        Args:
            series (numpy.ndarray or list): 时间序列数据
            
        Returns:
            numpy.ndarray: 预处理后的时间序列
        """
        if len(series) == 0:
            return np.array([[]])
            
        # 转换为numpy数组
        series = np.array(series, dtype=float)
        
        # 处理缺失值
        series = np.nan_to_num(series)
        
        # 转换为tslearn所需的格式: (n_samples, n_timestamps, n_features)
        if series.ndim == 1:
            series = series.reshape((1, -1, 1))
        elif series.ndim == 2:
            series = series.reshape((series.shape[0], series.shape[1], 1))
            
        return series
    
    def fit(self, series_list, codes=None):
        """
        使用K-Shape算法对时间序列集合进行聚类
        
        Args:
            series_list (list): 时间序列列表，每个元素为一个序列
            codes (list, optional): 与series_list对应的标识符（如股票代码）
            
        Returns:
            self: 训练后的聚类器
        """
        if not series_list:
            raise ValueError("输入的时间序列列表不能为空")
            
        # 预处理数据
        processed_series = []
        valid_indices = []
        
        for i, series in enumerate(series_list):
            if len(series) > 0:
                processed = self.preprocess_series(series)
                if processed.size > 1:  # 确保序列有效
                    processed_series.append(processed[0])
                    valid_indices.append(i)
        
        if not processed_series:
            raise ValueError("预处理后没有有效的时间序列")
            
        # 将列表转换为3D数组
        X = np.array(processed_series)
        
        # 保存有效序列对应的代码
        if codes:
            self.series_codes = [codes[i] for i in valid_indices]
        else:
            self.series_codes = valid_indices
        
        # 标准化数据
        X_scaled = self.scaler.fit_transform(X)
        
        # 创建并训练K-Shape模型
        self.model = KShape(
            n_clusters=min(self.n_clusters, len(X_scaled)),
            max_iter=self.max_iter,
            random_state=self.random_state
        )
        
        # 训练模型
        self.model.fit(X_scaled)
        
        # 保存训练结果
        self.fitted = True
        self.cluster_centers_ = self.model.cluster_centers_
        self.labels_ = self.model.labels_
        
        return self
    
    def predict(self, series):
        """
        预测新序列所属的聚类
        
        Args:
            series (numpy.ndarray or list): 时间序列数据
            
        Returns:
            int: 聚类标签
        """
        if not self.fitted:
            raise ValueError("模型尚未训练，请先调用fit方法")
            
        # 预处理数据
        processed = self.preprocess_series(series)
        
        # 标准化数据
        scaled = self.scaler.transform(processed)
        
        # 预测聚类
        return self.model.predict(scaled)[0]
    
    def transform(self, series_list):
        """
        将时间序列转换为到各聚类中心的距离矩阵
        
        Args:
            series_list (list): 时间序列列表
            
        Returns:
            numpy.ndarray: 距离矩阵
        """
        if not self.fitted:
            raise ValueError("模型尚未训练，请先调用fit方法")
            
        # 预处理数据
        processed_series = []
        for series in series_list:
            if len(series) > 0:
                processed = self.preprocess_series(series)
                if processed.size > 1:  # 确保序列有效
                    processed_series.append(processed[0])
        
        if not processed_series:
            raise ValueError("预处理后没有有效的时间序列")
            
        # 将列表转换为3D数组
        X = np.array(processed_series)
        
        # 标准化数据
        X_scaled = self.scaler.transform(X)
        
        # 转换为距离矩阵
        return self.model.transform(X_scaled)
    
    def get_cluster_members(self, cluster_label):
        """
        获取指定聚类的成员
        
        Args:
            cluster_label (int): 聚类标签
            
        Returns:
            list: 聚类成员的索引或代码
        """
        if not self.fitted:
            raise ValueError("模型尚未训练，请先调用fit方法")
            
        if cluster_label < 0 or cluster_label >= self.n_clusters:
            raise ValueError(f"无效的聚类标签: {cluster_label}")
            
        # 找到属于该聚类的所有成员
        member_indices = np.where(self.labels_ == cluster_label)[0]
        
        # 返回对应的代码或索引
        if self.series_codes:
            return [self.series_codes[i] for i in member_indices]
        else:
            return member_indices.tolist()
    
    def get_all_clusters(self):
        """
        获取所有聚类及其成员
        
        Returns:
            dict: 聚类标签与成员的映射
        """
        if not self.fitted:
            raise ValueError("模型尚未训练，请先调用fit方法")
            
        clusters = {}
        for label in range(self.n_clusters):
            clusters[label] = self.get_cluster_members(label)
            
        return clusters
    
    def find_optimal_clusters(self, series_list, max_clusters=20, method='silhouette'):
        """
        寻找最佳聚类数量
        
        Args:
            series_list (list): 时间序列列表
            max_clusters (int): 最大聚类数量
            method (str): 评估方法，目前支持'silhouette'
            
        Returns:
            tuple: (最佳聚类数量, 评分列表)
        """
        if method != 'silhouette':
            raise ValueError(f"不支持的评估方法: {method}")
            
        # 预处理数据
        processed_series = []
        for series in series_list:
            if len(series) > 0:
                processed = self.preprocess_series(series)
                if processed.size > 1:  # 确保序列有效
                    processed_series.append(processed[0])
        
        if not processed_series:
            raise ValueError("预处理后没有有效的时间序列")
            
        # 将列表转换为3D数组
        X = np.array(processed_series)
        
        # 标准化数据
        X_scaled = self.scaler.fit_transform(X)
        
        # 计算不同聚类数量的得分
        min_clusters = min(2, len(X_scaled) - 1)  # 至少需要2个聚类
        max_clusters = min(max_clusters, len(X_scaled) - 1)  # 最多为样本数-1
        
        scores = []
        n_clusters_range = range(min_clusters, max_clusters + 1)
        
        for n in n_clusters_range:
            # 创建并训练K-Shape模型
            model = KShape(n_clusters=n, max_iter=self.max_iter, random_state=self.random_state)
            labels = model.fit_predict(X_scaled)
            
            # 计算轮廓系数
            if len(set(labels)) > 1:  # 确保至少有2个不同的标签
                score = silhouette_score(X_scaled.reshape(X_scaled.shape[0], -1), labels)
                scores.append(score)
            else:
                scores.append(-1)  # 无效的聚类结果
        
        # 找到最佳聚类数量
        best_index = np.argmax(scores)
        best_n_clusters = n_clusters_range[best_index]
        
        return best_n_clusters, scores
    
    def save_model(self, filename=None):
        """
        保存聚类模型
        
        Args:
            filename (str, optional): 文件名，默认使用时间戳生成
            
        Returns:
            str: 保存的文件路径
        """
        if not self.fitted:
            raise ValueError("模型尚未训练，请先调用fit方法")
            
        if not self.cache_dir:
            raise ValueError("未指定缓存目录")
            
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 生成文件名
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kshape_model_{self.n_clusters}_{timestamp}.pkl"
            
        filepath = os.path.join(self.cache_dir, filename)
        
        # 保存模型
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'n_clusters': self.n_clusters,
                'max_iter': self.max_iter,
                'random_state': self.random_state,
                'cluster_centers_': self.cluster_centers_,
                'labels_': self.labels_,
                'series_codes': self.series_codes,
                'fitted': self.fitted
            }, f)
            
        return filepath
    
    def load_model(self, filepath):
        """
        加载聚类模型
        
        Args:
            filepath (str): 模型文件路径
            
        Returns:
            self: 加载了模型的聚类器
        """
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                
            self.model = data['model']
            self.scaler = data['scaler']
            self.n_clusters = data['n_clusters']
            self.max_iter = data['max_iter']
            self.random_state = data['random_state']
            self.cluster_centers_ = data['cluster_centers_']
            self.labels_ = data['labels_']
            self.series_codes = data['series_codes']
            self.fitted = data['fitted']
            
            return self
        except Exception as e:
            raise ValueError(f"加载模型失败: {e}")
    
    def batch_predict(self, series_list):
        """
        批量预测多个序列的聚类
        
        Args:
            series_list (list): 时间序列列表
            
        Returns:
            list: 聚类标签列表
        """
        if not self.fitted:
            raise ValueError("模型尚未训练，请先调用fit方法")
            
        # 使用多进程并行预测
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(self.predict, series_list))
            
        return results 