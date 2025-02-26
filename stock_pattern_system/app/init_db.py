"""
数据库初始化脚本
"""
import os
import sys
import sqlite3
from pathlib import Path

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from app.models.database import Database
from app.models.schema import ALL_CREATE_TABLES

def init_database(db_path=None):
    """
    初始化数据库，创建所有表
    
    Args:
        db_path (str, optional): 数据库文件路径
        
    Returns:
        bool: 是否初始化成功
    """
    try:
        # 如果没有指定路径，使用默认路径
        if db_path is None:
            db_path = os.path.join(project_root, 'data', 'stock_data.db')
            
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 创建数据库连接
        db = Database(db_path)
        
        # 创建所有表
        for create_table_sql in ALL_CREATE_TABLES:
            db.create_table(create_table_sql)
            
        print(f"数据库初始化成功: {db_path}")
        return True
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

if __name__ == "__main__":
    # 从命令行参数获取数据库路径（可选）
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        
    # 初始化数据库
    success = init_database(db_path)
    
    # 设置退出码
    sys.exit(0 if success else 1) 