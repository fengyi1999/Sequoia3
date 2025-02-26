"""
股票数据模型类
"""
import json
from datetime import datetime, timedelta
from .database import Database

class StockModel:
    """股票数据模型，提供对股票数据的操作"""
    
    def __init__(self, db=None):
        """
        初始化股票数据模型
        
        Args:
            db (Database, optional): 数据库连接实例
        """
        self.db = db if db else Database()
    
    def get_stock_list(self, market_type=None, is_active=1, limit=None, offset=None):
        """
        获取股票列表
        
        Args:
            market_type (str, optional): 市场类型过滤 ('主板', '创业板', '科创板')
            is_active (int, optional): 是否活跃(1:活跃, 0:非活跃)
            limit (int, optional): 限制返回数量
            offset (int, optional): 结果偏移量
            
        Returns:
            list: 股票信息列表
        """
        query = "SELECT * FROM stocks WHERE 1=1"
        params = []
        
        if market_type:
            query += " AND market_type = ?"
            params.append(market_type)
            
        if is_active is not None:
            query += " AND is_active = ?"
            params.append(is_active)
            
        query += " ORDER BY stock_code"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
            if offset:
                query += " OFFSET ?"
                params.append(offset)
                
        return self.db.execute(query, tuple(params) if params else None)
    
    def get_stock_info(self, stock_code):
        """
        获取股票信息
        
        Args:
            stock_code (str): 股票代码
            
        Returns:
            dict: 股票信息，如果不存在返回None
        """
        query = "SELECT * FROM stocks WHERE stock_code = ?"
        result = self.db.execute(query, (stock_code,))
        return dict(result[0]) if result else None
    
    def add_stock(self, stock_code, stock_name, listing_date=None, market_type=None, is_active=1):
        """
        添加股票
        
        Args:
            stock_code (str): 股票代码
            stock_name (str): 股票名称
            listing_date (str, optional): 上市日期
            market_type (str, optional): 市场类型
            is_active (int, optional): 是否活跃
            
        Returns:
            bool: 是否添加成功
        """
        try:
            query = """
            INSERT INTO stocks (stock_code, stock_name, listing_date, market_type, is_active)
            VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute(query, (stock_code, stock_name, listing_date, market_type, is_active))
            return True
        except Exception as e:
            print(f"添加股票失败: {e}")
            return False
    
    def update_stock(self, stock_code, **kwargs):
        """
        更新股票信息
        
        Args:
            stock_code (str): 股票代码
            **kwargs: 要更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        if not kwargs:
            return False
            
        try:
            # 构建更新语句
            fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            query = f"UPDATE stocks SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE stock_code = ?"
            
            # 构建参数
            params = list(kwargs.values())
            params.append(stock_code)
            
            self.db.execute(query, tuple(params))
            return True
        except Exception as e:
            print(f"更新股票失败: {e}")
            return False
    
    def get_stock_history(self, stock_code, start_date=None, end_date=None, indicators=None):
        """
        获取股票历史数据
        
        Args:
            stock_code (str): 股票代码
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期
            indicators (list, optional): 要返回的指标列表
            
        Returns:
            pandas.DataFrame: 股票历史数据
        """
        # 确定要查询的字段
        if indicators:
            fields = ", ".join(["stock_code", "trade_date"] + indicators)
        else:
            fields = "*"
            
        query = f"SELECT {fields} FROM daily_data WHERE stock_code = ?"
        params = [stock_code]
        
        if start_date:
            query += " AND trade_date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND trade_date <= ?"
            params.append(end_date)
            
        query += " ORDER BY trade_date"
        
        return self.db.query_to_dataframe(query, tuple(params))
    
    def add_daily_data(self, stock_code, trade_date, open_price, high, low, close, volume, amount=None, ma5=None, ma10=None, ma20=None):
        """
        添加日线数据
        
        Args:
            stock_code (str): 股票代码
            trade_date (str): 交易日期
            open_price (float): 开盘价
            high (float): 最高价
            low (float): 最低价
            close (float): 收盘价
            volume (float): 成交量
            amount (float, optional): 成交额
            ma5 (float, optional): 5日均线
            ma10 (float, optional): 10日均线
            ma20 (float, optional): 20日均线
            
        Returns:
            bool: 是否添加成功
        """
        try:
            query = """
            INSERT OR REPLACE INTO daily_data 
            (stock_code, trade_date, open, high, low, close, volume, amount, ma5, ma10, ma20)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute(query, (
                stock_code, trade_date, open_price, high, low, close, 
                volume, amount, ma5, ma10, ma20
            ))
            return True
        except Exception as e:
            print(f"添加日线数据失败: {e}")
            return False
    
    def batch_add_daily_data(self, data_list):
        """
        批量添加日线数据
        
        Args:
            data_list (list): 日线数据列表，每项为包含所有必需字段的字典
            
        Returns:
            int: 添加的数据条数
        """
        try:
            query = """
            INSERT OR REPLACE INTO daily_data 
            (stock_code, trade_date, open, high, low, close, volume, amount, ma5, ma10, ma20)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params_list = [
                (
                    item['stock_code'], item['trade_date'], item['open'], 
                    item['high'], item['low'], item['close'], item['volume'],
                    item.get('amount'), item.get('ma5'), item.get('ma10'), item.get('ma20')
                )
                for item in data_list
            ]
            return self.db.execute_many(query, params_list)
        except Exception as e:
            print(f"批量添加日线数据失败: {e}")
            return 0
    
    def calculate_ma(self, stock_code, window_sizes=[5, 10, 20]):
        """
        计算均线并更新数据库
        
        Args:
            stock_code (str): 股票代码
            window_sizes (list, optional): 均线窗口大小列表
            
        Returns:
            bool: 是否计算成功
        """
        try:
            # 获取股票数据
            df = self.get_stock_history(stock_code, indicators=['trade_date', 'close'])
            if df.empty:
                return False
                
            # 计算各均线
            updates = []
            for window in window_sizes:
                ma_col = f'ma{window}'
                df[ma_col] = df['close'].rolling(window=window).mean()
                
                # 构建更新数据
                for _, row in df.iterrows():
                    if pd.notna(row[ma_col]):
                        updates.append({
                            'stock_code': stock_code,
                            'trade_date': row['trade_date'],
                            'ma_type': ma_col,
                            'value': row[ma_col]
                        })
            
            # 批量更新数据库
            if updates:
                with self.db.get_cursor() as cursor:
                    for update in updates:
                        query = f"UPDATE daily_data SET {update['ma_type']} = ? WHERE stock_code = ? AND trade_date = ?"
                        cursor.execute(query, (update['value'], update['stock_code'], update['trade_date']))
                
            return True
        except Exception as e:
            print(f"计算均线失败: {e}")
            return False 