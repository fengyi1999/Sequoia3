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
        with self.get_connection() as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            else:
                return pd.read_sql_query(query, conn)
    
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