"""
数据库表结构定义
"""

# 股票表 - 存储基本股票信息
CREATE_STOCKS_TABLE = """
CREATE TABLE IF NOT EXISTS stocks (
    stock_code TEXT PRIMARY KEY,
    stock_name TEXT NOT NULL,
    listing_date TEXT,
    is_active INTEGER DEFAULT 1,
    market_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# 日线数据表 - 存储股票日线数据
CREATE_DAILY_DATA_TABLE = """
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
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code),
    UNIQUE (stock_code, trade_date)
);
"""

# 创建股票日线数据索引
CREATE_DAILY_DATA_INDEX = """
CREATE INDEX IF NOT EXISTS idx_daily_data_stock_date 
ON daily_data (stock_code, trade_date);
"""

# 形态模板表 - 存储用户保存的形态模板
CREATE_PATTERN_TEMPLATES_TABLE = """
CREATE TABLE IF NOT EXISTS pattern_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    data TEXT NOT NULL,  -- JSON格式存储形态数据
    indicator TEXT DEFAULT 'close',  -- 使用的指标类型：close, ma5, ma10, ma20
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# 匹配结果表 - 存储形态匹配结果
CREATE_MATCH_RESULTS_TABLE = """
CREATE TABLE IF NOT EXISTS match_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    stock_code TEXT NOT NULL,
    similarity REAL NOT NULL,  -- 相似度分数(0-1)
    start_date TEXT,  -- 匹配形态的开始日期
    end_date TEXT,    -- 匹配形态的结束日期
    match_data TEXT,  -- JSON格式存储匹配详情
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES pattern_templates(id),
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
);
"""

# 创建匹配结果索引
CREATE_MATCH_RESULTS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_match_results_pattern_stock 
ON match_results (pattern_id, stock_code);
"""

# 所有创建表语句列表，用于初始化数据库
ALL_CREATE_TABLES = [
    CREATE_STOCKS_TABLE,
    CREATE_DAILY_DATA_TABLE,
    CREATE_DAILY_DATA_INDEX,
    CREATE_PATTERN_TEMPLATES_TABLE,
    CREATE_MATCH_RESULTS_TABLE,
    CREATE_MATCH_RESULTS_INDEX
] 