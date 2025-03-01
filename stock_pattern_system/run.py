"""
股票形态选股系统主程序入口
"""
import os
import sys
from pathlib import Path

# 设置环境变量
# 0: 使用真实服务, 1: 使用模拟服务
os.environ["USE_MOCK_SERVICES"] = "0"

# 将当前目录加入Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

# 导入应用模块
import stock_pattern_system
from stock_pattern_system.ui.app import create_app

# 初始化数据库
def initialize_database():
    """初始化数据库和必要的表结构"""
    try:
        from stock_pattern_system.app.data_fetcher import init_database
        
        print("正在初始化数据库...")
        result = init_database()
        
        if result:
            print("数据库初始化成功")
        else:
            print("数据库初始化失败，但将继续尝试启动应用")
    except Exception as e:
        print(f"数据库初始化过程中出现异常: {e}")
        import traceback
        print(traceback.format_exc())

def run_app():
    """运行股票形态选股系统"""
    print("使用模拟服务: " + ("是" if os.environ.get("USE_MOCK_SERVICES") == "1" else "否"))
    
    # 创建并运行应用
    app = create_app()
    
    # 打印系统信息
    print("=" * 60)
    print(" " * 20 + "FengStockSelecting")
    print("=" * 60)
    print("正在启动系统...")
    print("使用" + ("模拟" if os.environ.get("USE_MOCK_SERVICES") == "1" else "真实") + "数据进行选股")
    
    # 启动Web应用
    print("启动形态选股系统服务，访问地址：http://127.0.0.1:8050")
    app.run_server(debug=False, host='127.0.0.1', port=8050)

if __name__ == "__main__":
    # 首先初始化数据库
    initialize_database()
    
    # 然后运行应用
    run_app() 