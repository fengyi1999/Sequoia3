"""
形态匹配服务

提供股票形态匹配功能，使用DTW算法进行相似度计算，
并集成形态模板库，支持预定义和自定义形态。
"""
import os
import json
import numpy as np
import pandas as pd
import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from concurrent.futures import ProcessPoolExecutor

# 修改导入路径为绝对路径
from stock_pattern_system.app.models.stock import StockModel
from stock_pattern_system.app.models.pattern import PatternModel
from stock_pattern_system.app.services.dtw_matcher import DTWMatcher
# 导入normalize_pattern函数
from stock_pattern_system.app.services.pattern_templates import PatternTemplateManager, normalize_pattern

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
        self.template_manager = PatternTemplateManager(templates_file)
        
        # 初始化数据库连接
        # 使用原有连接方式，不引入新的依赖
        import sqlite3
        from pathlib import Path
        
        # 获取数据库文件路径
        db_path = os.path.join(Path(__file__).parent.parent.parent, 'data', 'stock_data.db')
        print(f"连接数据库: {db_path}")
        
        # 创建连接
        try:
            # 启用线程安全检查
            self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
            print("数据库连接成功")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            self.db_conn = None
        
    def get_pattern_templates(self):
        """获取所有形态模板"""
        return self.template_manager.get_all_templates()
        
    def match_pattern(self, pattern_id, market_types=None, indicators=None, start_date=None, end_date=None, top_n=20, min_similarity=0.7):
        """执行形态匹配
        
        Args:
            pattern_id: 形态模板ID
            market_types: 市场类型列表
            indicators: 匹配指标列表
            start_date: 开始日期
            end_date: 结束日期
            top_n: 返回前N个结果
            min_similarity: 最小相似度阈值
            
        Returns:
            list: 匹配结果列表
        """
        try:
            # 获取形态模板
            pattern_template = self.get_pattern_template(pattern_id)
            if not pattern_template:
                print(f"未找到形态模板: {pattern_id}")
                return []
            
            pattern_data = pattern_template.get("data", [])
            if not pattern_data:
                print(f"形态模板数据为空: {pattern_id}")
                return []
            
            # 准备数据
            print(f"正在准备匹配数据，应用市场类型过滤: {', '.join(market_types) if market_types else '全部'}")
            
            # 获取符合条件的股票数据
            stocks_data = self._get_stocks_data(market_types, indicators, start_date, end_date)
            
            # 统计满足条件的股票数量
            available_stocks = len(stocks_data)
            print(f"开始形态匹配，使用符合条件的 {available_stocks} 只股票进行匹配...")
            
            if market_types:
                print(f"仅匹配选定的市场类型: {', '.join(market_types)}")
            
            if available_stocks == 0:
                print("没有找到符合条件的股票数据")
                return []
            
            # 初始化相似度列表
            similarities = []
            
            # 对每只股票进行匹配
            # 分批处理，每批100只股票，显示处理进度
            batch_size = 100
            total_batches = (available_stocks + batch_size - 1) // batch_size
            
            # 获取股票代码列表
            stock_code_list = list(stocks_data.keys())
            
            processed_count = 0
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min((batch_idx + 1) * batch_size, available_stocks)
                batch_stock_codes = stock_code_list[start_idx:end_idx]
                
                for stock_code in batch_stock_codes:
                    # 获取股票信息
                    stock_info = stocks_data[stock_code]
                    
                    # 获取需要匹配的指标数据
                    for indicator in indicators:
                        if indicator not in stock_info['data']:
                            continue
                            
                        indicator_data = stock_info['data'][indicator]
                        
                        # 使用normalize_pattern函数归一化数据
                        normalized_data = normalize_pattern(indicator_data)
                        
                        # 计算相似度
                        try:
                            similarity = self.dtw_matcher.compute_similarity(pattern_data, normalized_data)
                            
                            # 计算最佳匹配位置
                            position = 0
                            match_length = len(pattern_data)
                            
                            if len(normalized_data) > len(pattern_data):
                                # 寻找最佳匹配窗口
                                max_similarity = 0
                                for i in range(len(normalized_data) - len(pattern_data) + 1):
                                    window = normalized_data[i:i+len(pattern_data)]
                                    window_similarity = self.dtw_matcher.compute_similarity(pattern_data, window)
                                    if window_similarity > max_similarity:
                                        max_similarity = window_similarity
                                        position = i
                                similarity = max_similarity
                        except Exception as e:
                            print(f"计算股票 {stock_code} 的相似度时出错: {e}")
                            continue
                            
                        if similarity >= min_similarity:
                            # 构建匹配详情
                            match_info = {
                                'code': stock_code,
                                'name': stock_info['name'],
                                'similarity': similarity,
                                'match_details': {
                                    'position': position,
                                    'length': match_length,
                                    'data': indicator_data[position:position + match_length] if position + match_length <= len(indicator_data) else indicator_data[position:]
                                }
                            }
                            similarities.append(match_info)
                    
                    processed_count += 1
                
                # 显示批次进度
                if batch_idx % 5 == 0 or batch_idx == total_batches - 1:
                    print(f"形态匹配进度: {processed_count}/{available_stocks} 只股票 (批次 {batch_idx+1}/{total_batches})")
            
            # 按相似度排序并取前N个
            sorted_results = sorted(similarities, key=lambda x: x['similarity'], reverse=True)
            top_results = sorted_results[:top_n]
            
            print(f"形态匹配完成，找到 {len(top_results)} 个匹配度较高的结果")
            
            return top_results
            
        except Exception as e:
            print(f"形态匹配过程中出错: {e}")
            import traceback
            print(traceback.format_exc())
            return []
    
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
        
        # 获取股票列表并应用市场类型过滤
        stocks = []
        for market_type in market_types:
            market_stocks = self.stock_model.get_stock_list(market_type=market_type)
            stocks.extend(market_stocks)
        
        if market_types:
            market_str = "、".join(market_types)
            print(f"正在准备匹配数据，应用市场类型过滤: {market_str}，共 {len(stocks)} 只股票")
        
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
    
    def check_data_completeness(self, market_types=None, start_date=None, end_date=None, required_stocks=None):
        """检查数据完整性
        
        Args:
            market_types: 市场类型列表
            start_date: 开始日期
            end_date: 结束日期
            required_stocks: 需要检查的股票代码列表
            
        Returns:
            tuple: (是否完整, 总数, 有数据数量, 缺失股票列表)
        """
        try:
            # 获取本地已有数据的股票列表
            local_stocks = self.get_all_local_stocks(start_date, end_date)
            
            if required_stocks:
                print(f"使用指定的股票列表进行检查，共 {len(required_stocks)} 只股票")
                all_stocks = required_stocks
            else:
                print(f"没有指定股票列表，使用全部本地股票进行检查")
                all_stocks = local_stocks
                
            # 计算有数据和缺失的股票
            with_data = []
            missing = []
            
            for stock_code in all_stocks:
                if stock_code in local_stocks:
                    with_data.append(stock_code)
                else:
                    missing.append(stock_code)
            
            is_complete = len(missing) == 0
            
            print(f"数据完整性检查结果: 需要股票 {len(all_stocks)} 只, 本地有数据 {len(with_data)} 只, 缺失 {len(missing)} 只")
            print(f"数据是否完整: {'是' if is_complete else '否'}")
            
            return is_complete, len(all_stocks), len(with_data), missing
            
        except Exception as e:
            print(f"检查数据完整性出错: {e}")
            import traceback
            print(traceback.format_exc())
            # 出错时假定数据不完整
            return False, 0, 0, required_stocks or []
    
    def _find_stock_info(self, stocks_list, stock_code):
        """
        在股票列表中查找特定股票代码的信息
        
        Args:
            stocks_list (list): 股票信息列表
            stock_code (str): 要查找的股票代码
            
        Returns:
            dict: 股票信息字典，如果找不到返回None
        """
        for stock in stocks_list:
            if stock['stock_code'] == stock_code:
                return stock
        return None
    
    def fetch_missing_data(self, missing_stocks, start_date=None, end_date=None, callback=None, batch_size=20):
        """
        获取缺失的股票数据并保存到数据库
        
        Args:
            missing_stocks (list): 缺失数据的股票列表
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期
            callback (callable, optional): 进度回调函数，接受参数(当前进度, 总数)
            batch_size (int): 批处理大小，避免请求过于频繁
            
        Returns:
            tuple: (成功获取的股票数, 失败的股票数)
        """
        # 导入data_fetcher模块
        from stock_pattern_system.app.data_fetcher import get_stock_history, init_single_stock_data
        import time
        
        total_stocks = len(missing_stocks)
        success_count = 0
        failure_count = 0
        
        # 确保至少下载部分数据，即使被中断也能使用部分结果
        if total_stocks == 0:
            print("没有缺失的股票数据需要获取")
            return (0, 0)
        
        print(f"开始获取全市场股票历史数据，共 {total_stocks} 只股票...")
        print("正在下载所有缺失的A股市场股票数据，不受市场类型过滤限制")
        print("此过程将较为耗时，请耐心等待...")
        
        # 处理所有缺失的股票数据
        for i, stock in enumerate(missing_stocks):
            stock_code = stock['code']
            stock_name = stock.get('name', stock_code)
            
            try:
                # 初始化单只股票数据
                progress = f"{i+1}/{total_stocks}"
                percent = round((i+1) / total_stocks * 100, 1)
                print(f"正在下载第 {progress} 只股票 ({percent}%) - {stock_code} {stock_name}...")
                
                if callback:
                    callback(i+1, total_stocks)
                
                result = init_single_stock_data(
                    stock_code=stock_code,
                    days=365,  # 获取一年数据
                    retry_times=3  # 增加重试次数
                )
                
                if result:
                    success_count += 1
                    print(f"成功获取股票 {stock_code} 数据")
                else:
                    failure_count += 1
                    print(f"获取股票 {stock_code} 数据失败")
                
                # 避免请求太频繁，批量处理
                if (i + 1) % batch_size == 0:
                    print(f"已处理 {i+1}/{total_stocks} 只股票，暂停一下...")
                    time.sleep(2)  # 暂停一下，避免请求太频繁
            except Exception as e:
                failure_count += 1
                print(f"获取股票 {stock_code} 时发生错误: {e}")
        
        print(f"数据获取完成：成功 {success_count} 只，失败 {failure_count} 只")
        return (success_count, failure_count)
    
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
        from stock_pattern_system.app.services.pattern_templates import create_pattern_template_from_stock
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
        try:
            # 检查股票代码是否有效
            if not stock_code or not isinstance(stock_code, str):
                print(f"无效的股票代码: {stock_code}")
                return {'dates': [], 'values': []}
            
            # 标准化股票代码(去除可能的前缀)
            stock_code = stock_code.strip()
            if len(stock_code) > 6:
                stock_code = stock_code[-6:]
            
            # 检查输入指标是否有效
            valid_indicators = ["open", "high", "low", "close", "volume", "amount", "ma5", "ma10", "ma20"]
            if indicator not in valid_indicators:
                print(f"警告: 无效的指标 {indicator}，使用默认指标 close")
                indicator = "close"
                
            # 获取股票历史数据
            needed_indicators = ['trade_date', indicator]
            print(f"正在获取股票 {stock_code} 的历史数据，指标: {needed_indicators}")
            
            df = self.stock_model.get_stock_history(
                stock_code, 
                start_date=start_date, 
                end_date=end_date,
                indicators=needed_indicators
            )
            
            if df.empty:
                print(f"股票 {stock_code} 在日期范围 {start_date} 到 {end_date} 内没有数据")
                return {'dates': [], 'values': []}
                
            # 检查必要列是否存在
            if 'trade_date' not in df.columns or indicator not in df.columns:
                missing_cols = []
                if 'trade_date' not in df.columns:
                    missing_cols.append('trade_date')
                if indicator not in df.columns:
                    missing_cols.append(indicator)
                print(f"警告: 数据中缺少必要列: {', '.join(missing_cols)}")
                return {'dates': [], 'values': []}
                
            # 处理缺失值
            df = df.dropna(subset=[indicator])
            
            # 如果数据量太少，返回空结果
            if len(df) < 5:
                print(f"警告: 股票 {stock_code} 的有效数据点太少: {len(df)}")
                return {'dates': [], 'values': []}
            
            # 返回数据
            print(f"成功获取到 {len(df)} 条股票数据记录")
            return {
                'dates': df['trade_date'].tolist(),
                'values': df[indicator].tolist(),
                'stock_code': stock_code,
                'indicator': indicator
            }
            
        except Exception as e:
            # 捕获并记录所有异常
            import traceback
            error_trace = traceback.format_exc()
            print(f"获取股票数据时出错: {type(e).__name__} - {str(e)}")
            print(f"错误详情: {error_trace}")
            
            # 返回空数据而不是抛出异常
            return {'dates': [], 'values': [], 'error': str(e)}
    
    def get_all_local_stocks(self, start_date=None, end_date=None):
        """获取本地数据库中有数据的所有股票代码
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            list: 有数据的股票代码列表
        """
        try:
            if not self.db_conn:
                print("数据库连接不存在，无法获取本地股票列表")
                return []
                
            # 为避免线程问题，每次使用时创建新的游标对象
            cursor = self.db_conn.cursor()
            
            # 构建SQL查询
            sql = "SELECT DISTINCT stock_code FROM daily_data"
            params = []
            
            # 如果提供了日期范围，筛选有该日期范围数据的股票
            if start_date and end_date:
                sql = """
                SELECT DISTINCT stock_code 
                FROM daily_data
                WHERE trade_date >= ? AND trade_date <= ?
                """
                params = [start_date, end_date]
                
            # 执行查询
            print(f"执行SQL查询获取所有本地股票: {sql}")
            print(f"查询参数: {params}")
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
                
            # 获取结果
            results = cursor.fetchall()
            stock_codes = [row[0] for row in results]
            
            print(f"本地数据库中共有 {len(stock_codes)} 只股票有数据")
            return stock_codes
            
        except Exception as e:
            print(f"获取本地股票列表出错: {e}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def get_latest_trading_day(self, target_date=None):
        """获取指定日期最近的交易日
        
        如果指定日期不是交易日，则返回该日期之前的最近交易日
        
        Args:
            target_date: 目标日期，格式为YYYY-MM-DD，默认为当前日期
            
        Returns:
            str: 最近的交易日，格式为YYYY-MM-DD
        """
        try:
            if not self.db_conn:
                print("数据库连接不存在，无法查询交易日")
                return None
                
            # 如果未指定日期，使用当前日期
            if not target_date:
                target_date = datetime.datetime.now().strftime("%Y-%m-%d")
                
            cursor = self.db_conn.cursor()
            
            # 查询小于等于指定日期的最近交易日
            # 使用GROUP BY确保只返回存在数据的日期
            sql = """
            SELECT MAX(trade_date) 
            FROM daily_data 
            WHERE trade_date <= ?
            """
            
            print(f"执行SQL查询最近交易日: {sql}")
            print(f"查询参数: [{target_date}]")
            
            cursor.execute(sql, [target_date])
            result = cursor.fetchone()
            
            if result and result[0]:
                latest_trading_day = result[0]
                print(f"查询到的最近交易日为: {latest_trading_day}")
                return latest_trading_day
            else:
                print(f"未查询到小于等于 {target_date} 的交易日")
                return None
                
        except Exception as e:
            print(f"查询最近交易日出错: {e}")
            import traceback
            print(traceback.format_exc())
            return None 
    
    def query_database_statistics(self):
        """查询数据库统计信息
        
        Returns:
            dict: 包含数据库统计信息的字典
        """
        try:
            if not self.db_conn:
                print("数据库连接不存在，无法查询统计信息")
                return {"error": "数据库连接不存在"}
                
            cursor = self.db_conn.cursor()
            stats = {}
            
            # 查询股票总数
            cursor.execute("SELECT COUNT(DISTINCT stock_code) FROM daily_data")
            stats["stock_count"] = cursor.fetchone()[0]
            
            # 查询数据总条数
            cursor.execute("SELECT COUNT(*) FROM daily_data")
            stats["record_count"] = cursor.fetchone()[0]
            
            # 查询最早和最晚的交易日期
            cursor.execute("SELECT MIN(trade_date), MAX(trade_date) FROM daily_data")
            min_date, max_date = cursor.fetchone()
            stats["earliest_date"] = min_date
            stats["latest_date"] = max_date
            
            # 查询每只股票的数据条数统计
            cursor.execute("""
                SELECT 
                    stock_code, 
                    COUNT(*) as record_count,
                    MIN(trade_date) as earliest_date,
                    MAX(trade_date) as latest_date
                FROM daily_data
                GROUP BY stock_code
                ORDER BY record_count DESC
                LIMIT 10
            """)
            
            stats["top_stocks"] = [
                {
                    "stock_code": row[0],
                    "record_count": row[1],
                    "earliest_date": row[2],
                    "latest_date": row[3]
                }
                for row in cursor.fetchall()
            ]
            
            # 查询交易日期覆盖情况
            cursor.execute("""
                SELECT 
                    trade_date, 
                    COUNT(DISTINCT stock_code) as stock_count
                FROM daily_data
                GROUP BY trade_date
                ORDER BY trade_date DESC
                LIMIT 30
            """)
            
            stats["recent_dates"] = [
                {
                    "trade_date": row[0],
                    "stock_count": row[1]
                }
                for row in cursor.fetchall()
            ]
            
            print(f"数据库统计: 股票数 {stats['stock_count']}, 记录数 {stats['record_count']}")
            print(f"数据日期范围: {stats['earliest_date']} 至 {stats['latest_date']}")
            
            return stats
            
        except Exception as e:
            print(f"查询数据库统计信息出错: {e}")
            import traceback
            print(traceback.format_exc())
            return {"error": str(e)}
    
    def query_stock_data(self, stock_codes=None, start_date=None, end_date=None, 
                       indicators=None, limit=1000, output_format="dict"):
        """查询指定股票的数据
        
        Args:
            stock_codes: 股票代码列表或单个股票代码，为None则查询全部
            start_date: 开始日期，格式为YYYY-MM-DD
            end_date: 结束日期，格式为YYYY-MM-DD
            indicators: 需要的指标列表，默认为全部
            limit: 限制返回的记录数，默认1000条
            output_format: 输出格式，可选 "dict", "dataframe", "json"
            
        Returns:
            根据output_format返回相应格式的数据
        """
        try:
            if not self.db_conn:
                print("数据库连接不存在，无法查询股票数据")
                return None
                
            cursor = self.db_conn.cursor()
            
            # 构建SQL查询
            if indicators and isinstance(indicators, list):
                # 确保包含stock_code和trade_date
                if "stock_code" not in indicators:
                    indicators.append("stock_code")
                if "trade_date" not in indicators:
                    indicators.append("trade_date")
                    
                # 构建SELECT字段
                fields = ", ".join(indicators)
            else:
                fields = "*"
            
            sql = f"SELECT {fields} FROM daily_data WHERE 1=1"
            params = []
            
            # 添加股票代码条件
            if stock_codes:
                if isinstance(stock_codes, list):
                    # 多只股票
                    placeholders = ", ".join(["?" for _ in stock_codes])
                    sql += f" AND stock_code IN ({placeholders})"
                    params.extend(stock_codes)
                else:
                    # 单只股票
                    sql += " AND stock_code = ?"
                    params.append(stock_codes)
            
            # 添加日期范围条件
            if start_date:
                sql += " AND trade_date >= ?"
                params.append(start_date)
            if end_date:
                sql += " AND trade_date <= ?"
                params.append(end_date)
            
            # 添加排序和限制
            sql += " ORDER BY stock_code, trade_date"
            if limit:
                sql += f" LIMIT {limit}"
            
            # 执行查询
            print(f"执行SQL查询股票数据: {sql}")
            print(f"查询参数: {params}")
            
            # 获取结果
            cursor.execute(sql, params)
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            
            print(f"查询到 {len(results)} 条记录")
            
            # 根据输出格式返回结果
            if output_format == "dataframe":
                import pandas as pd
                df = pd.DataFrame(results, columns=columns)
                return df
            elif output_format == "json":
                import json
                json_data = []
                for row in results:
                    json_data.append(dict(zip(columns, row)))
                return json.dumps(json_data, ensure_ascii=False, indent=2)
            else:
                # 默认返回字典列表
                dict_data = []
                for row in results:
                    dict_data.append(dict(zip(columns, row)))
                return dict_data
                
        except Exception as e:
            print(f"查询股票数据出错: {e}")
            import traceback
            print(traceback.format_exc())
            return None 
    
    def _get_stocks_data(self, market_types=None, indicators=None, start_date=None, end_date=None, required_stocks=None):
        """
        获取指定市场类型、指标和日期范围的股票数据
        
        Args:
            market_types (list): 市场类型列表
            indicators (list): 技术指标列表
            start_date (str): 开始日期
            end_date (str): 结束日期
            required_stocks (list): 指定需要获取的股票代码列表
            
        Returns:
            dict: 股票代码到数据的映射
        """
        try:
            # 确保数据库连接有效
            if not self.db_conn:
                print("数据库连接不存在，无法获取股票数据")
                return {}
                
            # 参数预处理
            if indicators is None:
                indicators = ["close"]
                
            # 获取股票列表
            stock_codes = []
            if required_stocks and len(required_stocks) > 0:
                # 使用指定的股票列表
                stock_codes = required_stocks
                print(f"使用指定的股票列表: {len(stock_codes)} 只")
            elif market_types and len(market_types) > 0:
                # 根据市场类型筛选股票
                # 修改：直接从数据库查询，避免调用不存在的方法
                from stock_pattern_system.app.data_fetcher import get_stock_list
                
                # 获取所有股票
                all_stocks_df = get_stock_list()
                if all_stocks_df.empty:
                    print("获取股票列表失败")
                    return {}
                    
                # 根据市场类型过滤
                filtered_stocks = all_stocks_df[all_stocks_df['market_type'].isin(market_types)]
                stock_codes = filtered_stocks['code'].tolist()
                print(f"根据市场类型 {market_types} 筛选出 {len(stock_codes)} 只股票")
            else:
                # 修改：直接从本地数据库获取所有股票代码
                stock_codes = self.get_all_local_stocks(start_date, end_date)
                print(f"使用本地数据库中所有 {len(stock_codes)} 只股票")
                
            # 构建SQL查询获取多只股票的多个指标数据
            print(f"开始查询 {len(stock_codes)} 只股票的历史数据")
            
            # 准备查询字段
            fields = ["stock_code", "trade_date"] + indicators
            fields_str = ", ".join(fields)
            
            # 处理大量股票代码的情况，避免SQLite参数限制
            max_params = 500  # SQLite参数限制通常为999，设置小一点以确保安全
            stocks_data = {}
            
            # 分批查询处理
            for i in range(0, len(stock_codes), max_params):
                batch_codes = stock_codes[i:i+max_params]
                
                # 构建SQL查询
                sql = f"""
                SELECT {fields_str} 
                FROM daily_data 
                WHERE stock_code IN ({','.join(['?'] * len(batch_codes))})
                """
                
                # 添加日期范围条件
                params = batch_codes.copy()
                if start_date:
                    sql += " AND trade_date >= ?"
                    params.append(start_date)
                if end_date:
                    sql += " AND trade_date <= ?"
                    params.append(end_date)
                    
                # 添加排序
                sql += " ORDER BY stock_code, trade_date"
                
                # 执行查询
                batch_num = i // max_params + 1
                batch_total = (len(stock_codes) + max_params - 1) // max_params
                print(f"执行批次 {batch_num}/{batch_total} SQL查询获取股票数据，本批次 {len(batch_codes)} 只股票")
                
                # 创建新的游标
                cursor = self.db_conn.cursor()
                cursor.execute(sql, params)
                
                # 处理结果
                results = cursor.fetchall()
                print(f"批次 {batch_num} 查询结果: {len(results)} 条记录")
                
                # 将结果整理为字典格式
                columns = [col[0] for col in cursor.description]
                
                for row in results:
                    row_dict = dict(zip(columns, row))
                    stock_code = row_dict["stock_code"]
                    
                    if stock_code not in stocks_data:
                        stocks_data[stock_code] = {indicator: [] for indicator in indicators}
                        stocks_data[stock_code]["trade_date"] = []
                        # 添加名称字段，用于显示
                        stocks_data[stock_code]["name"] = ""
                        
                    # 添加交易日期
                    stocks_data[stock_code]["trade_date"].append(row_dict["trade_date"])
                    
                    # 添加各个指标的值
                    for indicator in indicators:
                        if indicator in row_dict:
                            stocks_data[stock_code][indicator].append(row_dict[indicator])
            
            # 获取股票名称
            print("正在获取股票名称...")
            # 使用现有的数据获取名称
            from stock_pattern_system.app.data_fetcher import get_stock_list
            try:
                # 获取所有股票名称的映射
                stock_list_df = get_stock_list()
                if not stock_list_df.empty:
                    # 创建代码->名称映射
                    name_map = dict(zip(stock_list_df['code'], stock_list_df['name']))
                    
                    # 添加名称到结果
                    for stock_code in stocks_data:
                        if stock_code in name_map:
                            stocks_data[stock_code]["name"] = name_map[stock_code]
                        else:
                            stocks_data[stock_code]["name"] = stock_code
            except Exception as e:
                print(f"获取股票名称出错: {e}")
                # 如果无法获取名称，使用代码作为名称
                for stock_code in stocks_data:
                    if not stocks_data[stock_code]["name"]:
                        stocks_data[stock_code]["name"] = stock_code
            
            # 计算获取到的股票数量
            actual_stock_count = len(stocks_data)
            if len(stock_codes) > 0:
                coverage = actual_stock_count / len(stock_codes) * 100
            else:
                coverage = 0
            print(f"成功获取 {actual_stock_count} 只股票的数据 (占请求股票的 {coverage:.1f}%)")
            
            # 在返回前，为了匹配逻辑，将数据组织为需要的格式
            formatted_data = {}
            for stock_code, data in stocks_data.items():
                # 确保有足够的数据点
                if not data[indicators[0]] or len(data[indicators[0]]) < 10:
                    continue
                
                formatted_data[stock_code] = {
                    'name': data['name'],
                    'data': {
                        'trade_date': data['trade_date']
                    }
                }
                
                # 添加各个指标
                for indicator in indicators:
                    formatted_data[stock_code]['data'][indicator] = data[indicator]
            
            return formatted_data
            
        except Exception as e:
            print(f"获取股票数据出错: {e}")
            import traceback
            print(traceback.format_exc())
            return {} 