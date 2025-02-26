"""
股票数据获取模块

使用AKShare获取A股数据并保存到数据库
"""
import os
import sys
import time
import datetime
import traceback
import pandas as pd
import numpy as np
import akshare as ak
from tqdm import tqdm

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from app.models.database import Database
from app.models.stock import StockModel

# 市场类型映射
MARKET_TYPES = {
    "600": "主板",  # 上证主板
    "601": "主板",
    "603": "主板",
    "605": "主板",
    "688": "科创板",  # 科创板
    "000": "主板",  # 深证主板
    "001": "主板",
    "002": "中小板",  # 中小板
    "003": "中小板",
    "300": "创业板",  # 创业板
}

def get_market_type(stock_code):
    """
    根据股票代码判断市场类型
    
    Args:
        stock_code (str): 股票代码
        
    Returns:
        str: 市场类型
    """
    prefix = stock_code[:3]
    return MARKET_TYPES.get(prefix, "其他")

def get_stock_list():
    """
    获取A股股票列表
    
    Returns:
        pd.DataFrame: 股票列表DataFrame
    """
    # 获取A股股票代码和名称
    print("获取A股股票列表...")
    try:
        # 使用AKShare获取股票列表
        stock_info_a_code_name_df = ak.stock_info_a_code_name()
        
        # 添加市场类型
        stock_info_a_code_name_df['market_type'] = stock_info_a_code_name_df['code'].apply(get_market_type)
        
        # 筛选市场类型
        valid_market_types = ["主板", "创业板", "科创板"]
        stock_info_a_code_name_df = stock_info_a_code_name_df[
            stock_info_a_code_name_df['market_type'].isin(valid_market_types)
        ]
        
        print(f"共获取 {len(stock_info_a_code_name_df)} 只股票")
        return stock_info_a_code_name_df
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return pd.DataFrame()

def get_stock_history(stock_code, start_date=None, end_date=None, adjust="qfq"):
    """
    获取单只股票的历史数据
    
    Args:
        stock_code (str): 股票代码 (6位数字)
        start_date (str, optional): 开始日期 (YYYYMMDD)
        end_date (str, optional): 结束日期 (YYYYMMDD)
        adjust (str, optional): 复权类型，默认前复权 (qfq)
        
    Returns:
        pd.DataFrame: 股票历史数据
    """
    try:
        # 使用AKShare获取股票历史数据
        stock_history_df = ak.stock_zh_a_hist(
            symbol=stock_code, 
            period="daily", 
            start_date=start_date, 
            end_date=end_date, 
            adjust=adjust
        )
        
        # 重命名列
        column_map = {
            "日期": "trade_date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount"
        }
        stock_history_df.rename(columns=column_map, inplace=True)
        
        # 添加股票代码列
        stock_history_df["stock_code"] = stock_code
        
        # 计算均线
        stock_history_df["ma5"] = stock_history_df["close"].rolling(window=5).mean()
        stock_history_df["ma10"] = stock_history_df["close"].rolling(window=10).mean()
        stock_history_df["ma20"] = stock_history_df["close"].rolling(window=20).mean()
        
        return stock_history_df
    except Exception as e:
        print(f"获取股票 {stock_code} 历史数据失败: {e}")
        return pd.DataFrame()

def save_stock_list_to_db(stock_list_df, stock_model):
    """
    保存股票列表到数据库
    
    Args:
        stock_list_df (pd.DataFrame): 股票列表DataFrame
        stock_model (StockModel): 股票模型实例
        
    Returns:
        int: 添加或更新的股票数量
    """
    count = 0
    for _, row in stock_list_df.iterrows():
        try:
            stock_code = row['code']
            stock_name = row['name']
            market_type = row['market_type']
            
            # 检查股票是否已存在
            stock_info = stock_model.get_stock_info(stock_code)
            if stock_info:
                # 更新股票信息
                stock_model.update_stock(
                    stock_code, 
                    stock_name=stock_name,
                    market_type=market_type
                )
            else:
                # 添加新股票
                stock_model.add_stock(
                    stock_code, 
                    stock_name, 
                    market_type=market_type
                )
            count += 1
        except Exception as e:
            print(f"保存股票 {row['code']} 信息失败: {e}")
    
    return count

def fetch_and_save_stock_data(days=90, retry_times=3, sleep_time=1):
    """
    获取并保存股票数据
    
    Args:
        days (int): 获取最近多少天的数据，默认90天
        retry_times (int): 重试次数
        sleep_time (float): 重试间隔时间(秒)
        
    Returns:
        tuple: (成功数量, 失败数量)
    """
    try:
        # 初始化数据库和模型
        db = Database()
        stock_model = StockModel(db)
        
        # 获取股票列表
        stock_list_df = get_stock_list()
        if stock_list_df.empty:
            print("获取股票列表失败")
            return (0, 0)
        
        # 保存股票列表到数据库
        save_count = save_stock_list_to_db(stock_list_df, stock_model)
        print(f"保存股票列表完成，共 {save_count} 只股票")
        
        # 计算日期范围
        today = datetime.datetime.now()
        end_date = today.strftime("%Y%m%d")
        start_date = (today - datetime.timedelta(days=days)).strftime("%Y%m%d")
        
        print(f"开始获取股票历史数据，时间范围: {start_date} - {end_date}")
        
        success_count = 0
        fail_count = 0
        
        # 获取每只股票的历史数据
        for _, row in tqdm(stock_list_df.iterrows(), total=len(stock_list_df), desc="获取股票数据"):
            stock_code = row['code']
            
            # 多次重试
            for attempt in range(retry_times):
                try:
                    # 获取历史数据
                    stock_history_df = get_stock_history(
                        stock_code,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if not stock_history_df.empty:
                        # 转换数据准备保存
                        data_to_save = []
                        for _, hist_row in stock_history_df.iterrows():
                            data_to_save.append({
                                'stock_code': stock_code,
                                'trade_date': hist_row['trade_date'],
                                'open': hist_row['open'],
                                'high': hist_row['high'],
                                'low': hist_row['low'],
                                'close': hist_row['close'],
                                'volume': hist_row['volume'],
                                'amount': hist_row.get('amount'),
                                'ma5': hist_row.get('ma5'),
                                'ma10': hist_row.get('ma10'),
                                'ma20': hist_row.get('ma20')
                            })
                        
                        # 批量保存到数据库
                        if data_to_save:
                            stock_model.batch_add_daily_data(data_to_save)
                            success_count += 1
                        break  # 成功获取数据，跳出重试循环
                    else:
                        # 空数据，可能是新股或停牌
                        print(f"股票 {stock_code} 无历史数据")
                        break
                except Exception as e:
                    if attempt < retry_times - 1:
                        print(f"获取股票 {stock_code} 数据失败，重试 ({attempt+1}/{retry_times}): {e}")
                        time.sleep(sleep_time)
                    else:
                        print(f"获取股票 {stock_code} 数据失败: {e}")
                        fail_count += 1
        
        print(f"股票数据获取完成：成功 {success_count} 只，失败 {fail_count} 只")
        return (success_count, fail_count)
    except Exception as e:
        print(f"获取股票数据过程发生错误: {e}")
        traceback.print_exc()
        return (0, 0)

if __name__ == "__main__":
    # 从命令行参数获取天数（可选）
    days = 90
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print(f"无效的天数参数: {sys.argv[1]}，使用默认值 90")
    
    fetch_and_save_stock_data(days) 