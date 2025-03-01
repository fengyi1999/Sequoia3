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

def get_local_stock_data(stock_code, start_date=None, end_date=None):
    """
    从本地数据库获取股票历史数据
    
    Args:
        stock_code (str): 股票代码
        start_date (str, optional): 开始日期，格式为YYYY-MM-DD
        end_date (str, optional): 结束日期，格式为YYYY-MM-DD
        
    Returns:
        pd.DataFrame: 股票历史数据
    """
    try:
        # 初始化数据库连接
        db = Database()
        conn = db.get_connection()
        
        # 构建SQL查询
        query = "SELECT * FROM daily_data WHERE stock_code = ?"
        params = [stock_code]
        
        # 添加日期过滤条件
        if start_date:
            query += " AND trade_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND trade_date <= ?"
            params.append(end_date)
        
        query += " ORDER BY trade_date"
        
        # 执行查询
        print(f"执行SQL查询: {query}")
        print(f"查询参数: {params}")
        
        # 读取数据到DataFrame
        df = pd.read_sql_query(query, conn, params=params)
        
        # 关闭连接
        conn.close()
        
        return df
    except Exception as e:
        print(f"获取本地股票 {stock_code} 数据失败: {e}")
        return pd.DataFrame()

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

def init_single_stock_data(stock_code, days=60, retry_times=3, force_update=False):
    """初始化单个股票的历史数据
    
    Args:
        stock_code (str): 股票代码
        days (int, optional): 获取的天数. Defaults to 60.
        retry_times (int, optional): 重试次数. Defaults to 3.
        force_update (bool, optional): 是否强制更新. Defaults to False.
        
    Returns:
        bool: 是否成功
    """
    # 导入matcher_service，用于检查最近交易日
    from stock_pattern_system.ui.pages.pattern_matching import matcher_service
    
    try:
        print(f"执行SQL查询: SELECT * FROM daily_data WHERE stock_code = ? ORDER BY trade_date")
        print(f"查询参数: ['{stock_code}']")
        
        # 获取股票已有数据
        stock_data = get_local_stock_data(stock_code)
        
        # 计算需要更新的日期范围
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        
        # 检查是否需要获取数据
        if not stock_data.empty and not force_update:
            print(f"股票 {stock_code} 已有 {len(stock_data)} 条历史数据记录")
            
            # 获取最后更新日期
            last_date = stock_data['trade_date'].max()
            print(f"股票 {stock_code} 最后更新日期为 {last_date}，尝试更新到 {current_date}")
            
            # 检查最近的交易日，避免下载到不存在的未来数据
            latest_trading_day = None
            if matcher_service:
                latest_trading_day = matcher_service.get_latest_trading_day()
                if latest_trading_day:
                    # 将YYYY-MM-DD格式转换为YYYYMMDD格式
                    latest_trading_day_fmt = latest_trading_day.replace('-', '')
                    print(f"检测到最近交易日为: {latest_trading_day}")
                    
                    # 如果最后更新日期已经是最近交易日，则不需要更新
                    if last_date >= latest_trading_day:
                        print(f"股票 {stock_code} 数据已是最新，无需更新")
                        return True
                    
                    # 使用最近交易日作为结束日期
                    current_date = latest_trading_day_fmt
        
        # 获取股票历史数据
        print(f"正在从AKShare获取股票 {stock_code} 历史数据 (1/{retry_times})...")
        
        # 尝试获取历史数据，支持重试
        for i in range(retry_times):
            try:
                stock_data = get_stock_history(stock_code, days=days)
                break
            except Exception as e:
                print(f"获取股票 {stock_code} 历史数据失败 ({i+1}/{retry_times}): {e}")
                if i == retry_times - 1:
                    # 全部重试失败
                    return False
                time.sleep(1)  # 避免请求过于频繁
        
        # 保存到数据库
        if not stock_data.empty:
            save_result = save_stock_data(stock_data)
            print(f"成功保存 {len(stock_data)} 条股票 {stock_code} 历史数据记录")
            return save_result
        else:
            print(f"获取股票 {stock_code} 历史数据为空")
            return False
            
    except Exception as e:
        print(f"初始化股票 {stock_code} 数据失败: {e}")
        return False

def save_stock_data(stock_data):
    """
    将股票历史数据保存到数据库
    
    Args:
        stock_data (pd.DataFrame): 股票历史数据DataFrame
        
    Returns:
        bool: 是否成功保存
    """
    try:
        if stock_data.empty:
            print("股票数据为空，无需保存")
            return False
            
        # 初始化数据库
        db = Database()
        stock_model = StockModel(db)
        
        # 转换数据准备保存
        data_to_save = []
        for _, row in stock_data.iterrows():
            # 确保必要字段存在
            if "stock_code" not in row or "trade_date" not in row:
                continue
                
            data_item = {
                'stock_code': row['stock_code'],
                'trade_date': row['trade_date'],
            }
            
            # 添加可能存在的其他字段
            for field in ['open', 'high', 'low', 'close', 'volume', 'amount', 'ma5', 'ma10', 'ma20']:
                if field in row:
                    data_item[field] = row[field]
            
            data_to_save.append(data_item)
        
        # 批量保存到数据库
        if data_to_save:
            stock_model.batch_add_daily_data(data_to_save)
            print(f"成功保存 {len(data_to_save)} 条股票数据记录")
            return True
        else:
            print("没有有效数据需要保存")
            return False
            
    except Exception as e:
        print(f"保存股票数据失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def init_database():
    """
    初始化数据库，创建必要的表结构
    
    Returns:
        bool: 是否成功初始化
    """
    try:
        # 初始化数据库
        db = Database()
        
        # 数据库表已经在Database类初始化时自动创建，无需额外操作
        print("数据库初始化完成")
        
        # 测试创建一个示例股票
        stock_model = StockModel(db)
        
        # 检查示例股票是否存在
        sample_stock = "000001"  # 平安银行
        stock_info = stock_model.get_stock_info(sample_stock)
        
        if not stock_info:
            print(f"添加示例股票 {sample_stock}...")
            stock_model.add_stock(
                stock_code=sample_stock,
                stock_name="平安银行",
                market_type="主板"
            )
        
        return True
    except Exception as e:
        print(f"初始化数据库失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    # 从命令行参数获取天数（可选）
    days = 90
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print(f"无效的天数参数: {sys.argv[1]}，使用默认值 90")
    
    fetch_and_save_stock_data(days) 