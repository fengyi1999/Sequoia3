# 形态选股系统

基于Python的A股形态选股系统，使用DTW和K-Shape算法进行股票形态匹配。

## 功能特点

- 使用AKShare获取中国A股数据（主板、创业板、科创板）
- 支持动态时间规整(DTW)和K-Shape算法进行股票形态匹配
- 通过Plotly Dash构建交互式用户界面
- 支持均线技术指标分析
- 用户可选择标准形态，匹配全市场约5000只股票
- 按匹配度输出结果，并支持交互式K线图显示
- 支持自定义算法参数和形态

## 系统要求

- Python 3.8+
- Windows系统
- 至少32GB内存和100GB磁盘空间

## 安装方法

1. 克隆项目代码
```
git clone https://github.com/yourusername/stock_pattern_system.git
cd stock_pattern_system
```

2. 安装依赖
```
pip install -r requirements.txt
```

3. 初始化数据库
```
python stock_pattern_system/app/init_db.py
```

4. 获取股票数据
```
python stock_pattern_system/app/data_fetcher.py
```

## 使用方法

1. 启动应用
```
python stock_pattern_system/run.py
```

2. 打开浏览器，访问 http://localhost:8050

## 项目结构

```
stock_pattern_system/
├── app/                  # 应用主目录
│   ├── api/              # API接口
│   ├── models/           # 数据模型
│   ├── services/         # 业务逻辑
│   └── utils/            # 工具函数
├── data/                 # 数据存储
├── ui/                   # 用户界面
│   ├── assets/           # 静态资源
│   ├── components/       # UI组件
│   ├── pages/            # 页面布局
│   └── templates/        # 模板文件
├── run.py                # 主运行脚本
└── README.md             # 项目说明
```

## 数据更新

系统默认获取最近90个交易日的历史数据，可以运行以下命令更新数据：

```
python stock_pattern_system/app/data_fetcher.py
```

## 许可证

MIT 