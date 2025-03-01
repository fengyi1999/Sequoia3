import os
import sqlite3
from contextlib import contextmanager
import pandas as pd
from pathlib import Path

class Database:
    """数据库连接管理类，提供SQLite数据库操作功能"""
    
    def __init__(self, db_path=None):
        """
        初始化数据库连接
        
        Args:
            db_path (str, optional): 数据库文件路径，默认使用项目data目录下的stock_data.db
        """
        if db_path is None:
            # 获取项目根目录
            project_root = Path(__file__).parent.parent.parent
            db_path = os.path.join(project_root, 'data', 'stock_data.db')
            
            # 确保数据目录存在
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
        self.db_path = db_path
        
        # 初始化数据库表
        self.init_database()
        
    def init_database(self):
        """
        初始化数据库表结构
        """
        try:
            # 股票基本信息表
            create_stocks_table_sql = """
            CREATE TABLE IF NOT EXISTS stocks (
                stock_code TEXT PRIMARY KEY,
                stock_name TEXT NOT NULL,
                listing_date TEXT,
                market_type TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            # 股票日线数据表
            create_daily_data_table_sql = """
            CREATE TABLE IF NOT EXISTS daily_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                amount REAL,
                ma5 REAL,
                ma10 REAL,
                ma20 REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(stock_code, trade_date)
            )
            """
            
            # 形态模板表
            create_patterns_table_sql = """
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                data TEXT NOT NULL,
                pattern_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            # 创建表
            with self.get_cursor() as cursor:
                cursor.execute(create_stocks_table_sql)
                cursor.execute(create_daily_data_table_sql)
                cursor.execute(create_patterns_table_sql)
                
            print("数据库表初始化成功")
            return True
        except Exception as e:
            import traceback
            print(f"初始化数据库表失败: {e}")
            print(traceback.format_exc())
            return False
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Yields:
            sqlite3.Connection: 数据库连接对象
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # 启用外键约束
            conn.execute('PRAGMA foreign_keys = ON')
            # 配置连接返回行为字典行
            conn.row_factory = sqlite3.Row
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self):
        """
        获取数据库游标的上下文管理器
        
        Yields:
            sqlite3.Cursor: 数据库游标对象
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
                
    def execute(self, query, params=None):
        """
        执行SQL查询
        
        Args:
            query (str): SQL查询语句
            params (tuple, optional): 查询参数
            
        Returns:
            list: 查询结果列表
        """
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
            
    def execute_many(self, query, params_list):
        """
        批量执行SQL查询
        
        Args:
            query (str): SQL查询语句
            params_list (list): 查询参数列表
            
        Returns:
            int: 受影响的行数
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def create_table(self, create_table_sql):
        """
        创建表
        
        Args:
            create_table_sql (str): 创建表的SQL语句
        """
        with self.get_cursor() as cursor:
            cursor.execute(create_table_sql)
    
    def insert_dataframe(self, df, table_name, if_exists='append'):
        """
        将DataFrame插入数据库表
        
        Args:
            df (pandas.DataFrame): 要插入的数据
            table_name (str): 表名
            if_exists (str, optional): 如果表存在，采取的操作. 默认为'append'
                可选值: 'fail', 'replace', 'append'
        """
        with self.get_connection() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    
    def query_to_dataframe(self, query, params=None):
        """
        执行查询并返回DataFrame
        
        Args:
            query (str): SQL查询语句
            params (tuple, optional): 查询参数
            
        Returns:
            pandas.DataFrame: 查询结果DataFrame
        """
        try:
            with self.get_connection() as conn:
                if params:
                    return pd.read_sql_query(query, conn, params=params)
                else:
                    return pd.read_sql_query(query, conn)
        except Exception as e:
            # 记录详细错误
            import traceback
            print(f"SQL查询失败: {str(e)}")
            print(f"SQL语句: {query}")
            print(f"参数: {params}")
            print(f"错误详情: {traceback.format_exc()}")
            
            # 返回空的DataFrame
            return pd.DataFrame()
    
    def table_exists(self, table_name):
        """
        检查表是否存在
        
        Args:
            table_name (str): 表名
            
        Returns:
            bool: 表是否存在
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute(query, (table_name,))
        return len(result) > 0 