import os
import sys
from pathlib import Path

# 设置使用模拟服务的环境变量
os.environ["USE_MOCK_SERVICES"] = "1"

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入应用
from ui.app import create_app

# 默认配置
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8050
DEFAULT_DEBUG = False  # 更改为False以避免重复输出

def main():
    """主函数，启动应用"""
    # 获取环境变量配置或使用默认值
    host = os.getenv("HOST", DEFAULT_HOST)
    port = int(os.getenv("PORT", DEFAULT_PORT))
    debug = os.getenv("DEBUG", str(DEFAULT_DEBUG)).lower() == "true"
    
    # 打印启动信息
    print("=" * 60)
    print(" " * 20 + "FengStockSelecting" + " " * 20)
    print("=" * 60)
    print("正在启动系统...")
    print("使用模拟服务进行演示")
    
    # 创建并启动应用
    app = create_app()
    print(f"启动形态选股系统服务，访问地址：http://{host}:{port}")
    try:
        app.run_server(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\n程序已停止运行")
    except Exception as e:
        print(f"\n运行时出错: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 