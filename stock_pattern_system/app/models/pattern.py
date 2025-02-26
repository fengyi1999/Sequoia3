"""
形态模型类，提供对形态模板的操作
"""
import json
from datetime import datetime
from .database import Database

class PatternModel:
    """形态模型，提供对形态模板的操作"""
    
    def __init__(self, db=None):
        """
        初始化形态模型
        
        Args:
            db (Database, optional): 数据库连接实例
        """
        self.db = db if db else Database()
    
    def get_patterns(self, limit=None, offset=None):
        """
        获取形态模板列表
        
        Args:
            limit (int, optional): 限制返回数量
            offset (int, optional): 结果偏移量
            
        Returns:
            list: 形态模板列表
        """
        query = "SELECT * FROM pattern_templates ORDER BY created_at DESC"
        params = []
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
            if offset:
                query += " OFFSET ?"
                params.append(offset)
                
        return [dict(row) for row in self.db.execute(query, tuple(params) if params else None)]
    
    def get_pattern(self, pattern_id):
        """
        获取形态模板详情
        
        Args:
            pattern_id (int): 形态模板ID
            
        Returns:
            dict: 形态模板详情，如果不存在返回None
        """
        query = "SELECT * FROM pattern_templates WHERE id = ?"
        result = self.db.execute(query, (pattern_id,))
        
        if not result:
            return None
            
        pattern = dict(result[0])
        # 解析JSON数据
        if 'data' in pattern and pattern['data']:
            try:
                pattern['data'] = json.loads(pattern['data'])
            except:
                pass  # 保持原样
                
        return pattern
    
    def add_pattern(self, name, data, description=None, indicator="close"):
        """
        添加形态模板
        
        Args:
            name (str): 形态名称
            data (dict or str): 形态数据，如果是字典会转为JSON字符串
            description (str, optional): 形态描述
            indicator (str, optional): 使用的指标
            
        Returns:
            int: 新添加的形态模板ID，如果失败返回None
        """
        try:
            # 如果data是字典，转换为JSON字符串
            if isinstance(data, dict):
                data = json.dumps(data)
                
            query = """
            INSERT INTO pattern_templates (name, description, data, indicator, created_at, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            with self.db.get_cursor() as cursor:
                cursor.execute(query, (name, description, data, indicator))
                return cursor.lastrowid
        except Exception as e:
            print(f"添加形态模板失败: {e}")
            return None
    
    def update_pattern(self, pattern_id, **kwargs):
        """
        更新形态模板
        
        Args:
            pattern_id (int): 形态模板ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        if not kwargs:
            return False
            
        try:
            # 如果更新data字段且是字典，转换为JSON字符串
            if 'data' in kwargs and isinstance(kwargs['data'], dict):
                kwargs['data'] = json.dumps(kwargs['data'])
                
            # 构建更新语句
            fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            query = f"UPDATE pattern_templates SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            
            # 构建参数
            params = list(kwargs.values())
            params.append(pattern_id)
            
            self.db.execute(query, tuple(params))
            return True
        except Exception as e:
            print(f"更新形态模板失败: {e}")
            return False
    
    def delete_pattern(self, pattern_id):
        """
        删除形态模板
        
        Args:
            pattern_id (int): 形态模板ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 先删除关联的匹配结果
            self.db.execute("DELETE FROM match_results WHERE pattern_id = ?", (pattern_id,))
            
            # 删除形态模板
            query = "DELETE FROM pattern_templates WHERE id = ?"
            self.db.execute(query, (pattern_id,))
            return True
        except Exception as e:
            print(f"删除形态模板失败: {e}")
            return False
    
    def save_match_results(self, pattern_id, matches):
        """
        保存匹配结果
        
        Args:
            pattern_id (int): 形态模板ID
            matches (list): 匹配结果列表，每项包含stock_code, similarity, start_date, end_date, match_data
            
        Returns:
            int: 保存的匹配结果数量
        """
        try:
            # 删除此模式的旧结果
            self.db.execute("DELETE FROM match_results WHERE pattern_id = ?", (pattern_id,))
            
            # 插入新结果
            query = """
            INSERT INTO match_results (pattern_id, stock_code, similarity, start_date, end_date, match_data)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            params_list = []
            for match in matches:
                # 如果match_data是字典，转换为JSON
                match_data = match.get('match_data')
                if isinstance(match_data, dict):
                    match_data = json.dumps(match_data)
                    
                params_list.append((
                    pattern_id, 
                    match['stock_code'], 
                    match['similarity'], 
                    match.get('start_date'), 
                    match.get('end_date'), 
                    match_data
                ))
                
            if params_list:
                return self.db.execute_many(query, params_list)
            return 0
        except Exception as e:
            print(f"保存匹配结果失败: {e}")
            return 0
    
    def get_match_results(self, pattern_id, limit=None, min_similarity=None):
        """
        获取匹配结果
        
        Args:
            pattern_id (int): 形态模板ID
            limit (int, optional): 限制返回数量
            min_similarity (float, optional): 最小相似度
            
        Returns:
            list: 匹配结果列表
        """
        query = """
        SELECT mr.*, s.stock_name
        FROM match_results mr
        JOIN stocks s ON mr.stock_code = s.stock_code
        WHERE mr.pattern_id = ?
        """
        params = [pattern_id]
        
        if min_similarity:
            query += " AND mr.similarity >= ?"
            params.append(min_similarity)
            
        query += " ORDER BY mr.similarity DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        results = self.db.execute(query, tuple(params))
        
        processed_results = []
        for row in results:
            result = dict(row)
            # 解析JSON数据
            if 'match_data' in result and result['match_data']:
                try:
                    result['match_data'] = json.loads(result['match_data'])
                except:
                    pass  # 保持原样
            processed_results.append(result)
            
        return processed_results 