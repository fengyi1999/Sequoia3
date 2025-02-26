"""
形态匹配服务

提供股票形态匹配功能，使用DTW算法进行相似度计算，
并集成形态模板库，支持预定义和自定义形态。
"""
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor

from app.models.stock import StockModel
from app.models.pattern import PatternModel
from app.services.dtw_matcher import DTWMatcher
# 移除直接导入，改为延迟导入
# from app.services.pattern_templates import PatternTemplateManager, normalize_pattern

class PatternMatcherService:
    """形态匹配服务，提供股票形态匹配功能"""
    
    def __init__(self, window_size=None, use_fast_dtw=True, max_workers=None, templates_file=None):
        """
        初始化形态匹配服务
        
        Args:
            window_size (int, optional): DTW窗口大小限制
            use_fast_dtw (bool): 是否使用快速DTW算法
            max_workers (int, optional): 并行计算的最大工作进程数
            templates_file (str, optional): 形态模板文件路径
        """
        self.stock_model = StockModel()
        self.pattern_model = PatternModel()
        self.dtw_matcher = DTWMatcher(
            window=window_size, 
            use_fast_dtw=use_fast_dtw, 
            max_workers=max_workers
        )
        
        # 延迟导入并初始化模板管理器
        from app.services.pattern_templates import PatternTemplateManager
        self.template_manager = PatternTemplateManager(templates_file)
        
    def get_pattern_templates(self):
        """获取所有形态模板"""
        return self.template_manager.get_all_templates()
        
    def match_pattern(self, pattern_id=None, pattern_data=None, market_types=None, 
                    indicators=None, start_date=None, end_date=None, 
                    top_n=20, min_similarity=0.7):
        """
        匹配形态
        
        Args:
            pattern_id (str, optional): 形态模板ID
            pattern_data (array-like, optional): 形态数据
            market_types (list, optional): 市场类型过滤
            indicators (list, optional): 使用的指标列表
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期
            top_n (int): 返回的最佳匹配数量
            min_similarity (float): 最小相似度阈值
            
        Returns:
            list: 匹配结果列表
        """
        # 获取模式数据
        pattern_series = self._get_pattern_data(pattern_id, pattern_data)
        if pattern_series is None:
            return []
            
        # 获取候选股票列表
        candidates = self._get_candidates(market_types, indicators, start_date, end_date)
        if not candidates:
            return []
            
        # 执行匹配
        candidate_series = []
        for candidate in candidates:
            candidate_series.append((candidate['data'], candidate))
            
        # 查找最佳匹配
        matches = []
        
        # 使用并行处理计算相似度
        if self.dtw_matcher.max_workers is not None and self.dtw_matcher.max_workers > 1:
            with ProcessPoolExecutor(max_workers=self.dtw_matcher.max_workers) as executor:
                # 准备任务
                futures = []
                for candidate in candidates:
                    future = executor.submit(
                        self._compute_similarity_task, 
                        pattern_series, 
                        candidate['data'],
                        candidate
                    )
                    futures.append(future)
                
                # 收集结果
                for future in futures:
                    try:
                        result = future.result()
                        if result and result['similarity'] >= min_similarity:
                            matches.append(result)
                    except Exception as e:
                        print(f"计算相似度时发生错误: {e}")
        else:
            # 串行处理
            for candidate in candidates:
                try:
                    result = self._compute_similarity_task(pattern_series, candidate['data'], candidate)
                    if result and result['similarity'] >= min_similarity:
                        matches.append(result)
                except Exception as e:
                    print(f"计算相似度时发生错误: {e}")
        
        # 按相似度排序
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 限制返回数量
        matches = matches[:top_n]
        
        return matches
    
    def _compute_similarity_task(self, pattern_series, candidate_series, candidate_info):
        """
        计算单个候选序列与模式的相似度
        
        Args:
            pattern_series (numpy.ndarray): 模式序列
            candidate_series (array-like): 候选序列
            candidate_info (dict): 候选股票信息
            
        Returns:
            dict: 匹配结果
        """
        try:
            # 计算相似度
            similarity = self.dtw_matcher.compute_similarity(pattern_series, candidate_series)
            
            # 计算最佳匹配位置
            position = 0
            if len(candidate_series) > len(pattern_series):
                # 寻找最佳匹配窗口
                max_similarity = 0
                for i in range(len(candidate_series) - len(pattern_series) + 1):
                    window = candidate_series[i:i+len(pattern_series)]
                    window_similarity = self.dtw_matcher.compute_similarity(pattern_series, window)
                    if window_similarity > max_similarity:
                        max_similarity = window_similarity
                        position = i
            
            # 构建匹配详情
            match_details = {
                'position': position,
                'length': len(pattern_series),
                'data': candidate_series
            }
            
            # 构建匹配结果
            return {
                'code': candidate_info['code'],
                'name': candidate_info['name'],
                'similarity': similarity,
                'match_details': match_details
            }
        except Exception as e:
            print(f"计算序列 {candidate_info['code']} 的相似度时发生错误: {e}")
            return None
    
    def _get_pattern_data(self, pattern_id=None, pattern_data=None):
        """
        获取模式数据
        
        Args:
            pattern_id (str, optional): 形态模板ID
            pattern_data (array-like, optional): 形态数据
            
        Returns:
            numpy.ndarray: 模式序列数据
        """
        if pattern_id:
            # 先尝试从形态模板库获取
            template = self.template_manager.get_template(pattern_id)
            if template:
                return np.array(template['data'])
                
            # 如果在模板库中找不到，尝试从数据库获取
            pattern = self.pattern_model.get_pattern(pattern_id)
            if pattern:
                # 解析pattern数据
                if isinstance(pattern['data'], str):
                    try:
                        pattern_data = json.loads(pattern['data'])
                        if 'data' in pattern_data:
                            return np.array(pattern_data['data'])
                        else:
                            return np.array(pattern_data)
                    except:
                        pass
                elif isinstance(pattern['data'], list):
                    return np.array(pattern['data'])
            
            raise ValueError(f"找不到形态模板: {pattern_id}")
            
        elif pattern_data is not None:
            # 使用提供的模式数据
            if isinstance(pattern_data, list) or isinstance(pattern_data, np.ndarray):
                if len(pattern_data) == 0:
                    raise ValueError("形态数据不能为空")
                return np.array(pattern_data)
            else:
                raise ValueError("无效的形态数据格式，应为列表或NumPy数组")
        else:
            raise ValueError("必须提供pattern_id或pattern_data")
    
    def _get_candidates(self, market_types=None, indicators=None, start_date=None, end_date=None):
        """
        获取候选股票列表
        
        Args:
            market_types (list, optional): 市场类型过滤
            indicators (list, optional): 使用的指标列表
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期
            
        Returns:
            list: 候选股票列表
        """
        # 默认值
        market_types = market_types or ["主板", "创业板", "科创板"]
        indicators = indicators or ["close"]
        indicator = indicators[0]  # 暂时只使用第一个指标
        
        # 获取股票列表
        stocks = []
        for market_type in market_types:
            market_stocks = self.stock_model.get_stock_list(market_type=market_type)
            stocks.extend(market_stocks)
        
        candidates = []
        for stock in stocks:
            stock_code = stock['stock_code']
            
            # 获取股票历史数据
            df = self.stock_model.get_stock_history(
                stock_code, 
                start_date=start_date, 
                end_date=end_date,
                indicators=[indicator]
            )
            
            if df.empty:
                continue
                
            # 提取指标数据
            series = df[indicator].dropna().values
            if len(series) < 10:  # 忽略数据太少的股票
                continue
                
            candidates.append({
                'code': stock_code,
                'name': stock['stock_name'],
                'data': series
            })
            
        return candidates
    
    def save_match_results(self, matches, output_file=None):
        """
        保存匹配结果到文件
        
        Args:
            matches (list): 匹配结果列表
            output_file (str, optional): 输出文件路径
            
        Returns:
            str: 保存的文件路径
        """
        if not matches:
            return None
            
        # 默认输出路径
        if output_file is None:
            output_dir = os.path.join(Path(__file__).parent.parent.parent, 'data', 'results')
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"matches_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json")
            
        # 准备数据
        output_data = []
        for match in matches:
            # 复制必要字段，移除大型数据
            match_dict = {
                'code': match['code'],
                'name': match['name'],
                'similarity': match['similarity']
            }
            
            # 复制匹配详情，但移除大型数据
            if 'match_details' in match:
                match_details = match['match_details'].copy() if isinstance(match['match_details'], dict) else {}
                if 'data' in match_details:
                    del match_details['data']
                match_dict['match_details'] = match_details
                
            output_data.append(match_dict)
            
        # 保存到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        return output_file
    
    def generate_match_report(self, pattern_id=None, pattern_data=None, market_types=None, 
                           indicators=None, start_date=None, end_date=None, output_dir=None):
        """
        生成匹配报告
        
        Args:
            pattern_id (str, optional): 形态模板ID
            pattern_data (array-like, optional): 形态数据
            market_types (list, optional): 市场类型过滤
            indicators (list, optional): 使用的指标列表
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期
            output_dir (str, optional): 输出目录
            
        Returns:
            dict: 报告数据
        """
        # 获取模式数据
        pattern_series = self._get_pattern_data(pattern_id, pattern_data)
        if pattern_series is None:
            return {'error': '无效的形态数据'}
            
        # 进行匹配
        matches = self.match_pattern(
            pattern_id=pattern_id,
            pattern_data=pattern_data,
            market_types=market_types,
            indicators=indicators,
            start_date=start_date,
            end_date=end_date,
            top_n=20,
            min_similarity=0.5  # 使用较低的阈值以获取更多结果
        )
        
        if not matches:
            return {'error': '未找到匹配结果'}
            
        # 创建输出目录
        if output_dir is None:
            output_dir = os.path.join(Path(__file__).parent.parent.parent, 'data', 'reports')
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取形态名称和描述
        pattern_name = "自定义形态"
        pattern_description = None
        
        if pattern_id:
            # 尝试从形态模板库获取
            template = self.template_manager.get_template(pattern_id)
            if template:
                pattern_name = template.get('name', pattern_name)
                pattern_description = template.get('description')
        
        # 创建报告数据
        report = {
            'pattern_info': {
                'id': pattern_id,
                'name': pattern_name,
                'description': pattern_description,
                'length': len(pattern_series)
            },
            'matches': matches,
            'statistics': {
                'match_count': len(matches),
                'avg_similarity': np.mean([m['similarity'] for m in matches]),
                'max_similarity': max([m['similarity'] for m in matches]),
                'min_similarity': min([m['similarity'] for m in matches])
            }
        }
        
        # 保存匹配结果
        results_file = os.path.join(output_dir, 'match_results.json')
        self.save_match_results(matches, results_file)
        
        # 创建匹配结果表格
        results_df = pd.DataFrame([
            {
                'rank': i+1,
                'code': m['code'],
                'name': m['name'],
                'similarity': m['similarity']
            }
            for i, m in enumerate(matches)
        ])
        
        # 保存为CSV
        csv_file = os.path.join(output_dir, 'match_results.csv')
        results_df.to_csv(csv_file, index=False)
        
        # 生成图表
        chart_data = self.dtw_matcher.generate_dtw_report(pattern_series, matches[:10])
        
        # 添加图表到报告
        report['charts'] = {}
        
        # 保存图表
        for chart_name, fig in chart_data.items():
            if isinstance(fig, plt.Figure):
                file_path = os.path.join(output_dir, f"{chart_name}.png")
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                report['charts'][chart_name] = file_path
                
        return report
    
    # 形态模板管理功能
    def get_predefined_templates(self):
        """
        获取预定义形态模板
        
        Returns:
            list: 预定义形态模板列表
        """
        return self.template_manager.get_predefined_templates()
    
    def get_custom_templates(self):
        """
        获取自定义形态模板
        
        Returns:
            list: 自定义形态模板列表
        """
        return self.template_manager.get_custom_templates()
    
    def get_pattern_template(self, pattern_id):
        """
        获取指定ID的形态模板
        
        Args:
            pattern_id (str): 形态ID
            
        Returns:
            dict: 形态模板，如果不存在返回None
        """
        return self.template_manager.get_template(pattern_id)
    
    def save_pattern_template(self, name, data, description=None, tags=None, pattern_type="custom"):
        """
        保存形态模板
        
        Args:
            name (str): 形态名称
            data (list): 形态数据
            description (str, optional): 形态描述
            tags (list, optional): 标签列表
            pattern_type (str): 形态类型，默认为"custom"
            
        Returns:
            str: 新保存的形态模板ID
        """
        # 归一化数据
        normalized_data = normalize_pattern(data).tolist()
        
        # 添加到模板库
        return self.template_manager.add_template(
            name=name,
            data=normalized_data,
            description=description,
            tags=tags,
            pattern_type=pattern_type
        )
    
    def update_pattern_template(self, pattern_id, **kwargs):
        """
        更新形态模板
        
        Args:
            pattern_id (str): 形态ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        # 如果更新数据，需要归一化
        if 'data' in kwargs and kwargs['data'] is not None:
            kwargs['data'] = normalize_pattern(kwargs['data']).tolist()
            
        return self.template_manager.update_template(pattern_id, **kwargs)
    
    def delete_pattern_template(self, pattern_id):
        """
        删除形态模板
        
        Args:
            pattern_id (str): 形态ID
            
        Returns:
            bool: 是否删除成功
        """
        return self.template_manager.delete_template(pattern_id)
    
    def import_predefined_templates(self, length=50, noise_level=0.05):
        """
        导入预定义形态模板
        
        Args:
            length (int): 形态长度
            noise_level (float): 噪声水平
            
        Returns:
            list: 导入的形态模板ID列表
        """
        return self.template_manager.import_predefined_templates(length, noise_level)
    
    def create_pattern_from_stock(self, stock_code, start_date, end_date, name, 
                               description=None, tags=None, indicator="close"):
        """
        从股票数据创建形态模板
        
        Args:
            stock_code (str): 股票代码
            start_date (str): 开始日期
            end_date (str): 结束日期
            name (str): 形态名称
            description (str, optional): 形态描述
            tags (list, optional): 标签列表
            indicator (str): 使用的指标
            
        Returns:
            str: 新创建的形态模板ID
        """
        # 获取股票数据
        df = self.stock_model.get_stock_history(
            stock_code, 
            start_date=start_date, 
            end_date=end_date,
            indicators=[indicator]
        )
        
        if df.empty:
            raise ValueError(f"股票 {stock_code} 在日期范围 {start_date} 到 {end_date} 内没有数据")
            
        # 获取股票信息
        stock_info = self.stock_model.get_stock_info(stock_code)
        stock_name = stock_info['stock_name'] if stock_info else None
        
        # 添加股票信息到DataFrame
        df['code'] = stock_code
        df['name'] = stock_name
        
        # 创建模板
        from app.services.pattern_templates import create_pattern_template_from_stock
        template = create_pattern_template_from_stock(
            stock_data=df,
            start_date=start_date,
            end_date=end_date,
            name=name,
            description=description,
            tags=tags,
            column=indicator
        )
        
        # 保存为自定义模板
        return self.save_pattern_template(
            name=template['name'],
            data=template['data'],
            description=template['description'],
            tags=template['tags']
        )
    
    def get_stock_data_for_pattern(self, stock_code, start_date=None, end_date=None, indicator="close"):
        """
        获取用于形态匹配的股票数据
        
        Args:
            stock_code (str): 股票代码
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期
            indicator (str, optional): 使用的指标
            
        Returns:
            dict: 股票数据，包含日期和值
        """
        # 获取股票历史数据
        df = self.stock_model.get_stock_history(
            stock_code, 
            start_date=start_date, 
            end_date=end_date,
            indicators=['trade_date', indicator]
        )
        
        if df.empty:
            return {'dates': [], 'values': []}
            
        # 处理缺失值
        df = df.dropna(subset=[indicator])
        
        return {
            'dates': df['trade_date'].tolist(),
            'values': df[indicator].tolist(),
            'stock_code': stock_code,
            'indicator': indicator
        } 