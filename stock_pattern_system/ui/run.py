"""
形态选股系统启动脚本

用于启动Web应用服务器。
"""
import os
import sys
import time
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """主函数，启动应用"""
    print("="*60)
    print(" "*20 + "形态选股系统" + " "*20)
    print("="*60)
    print("正在启动系统...")
    
    # 设置环境变量，确保用模拟服务
    os.environ["USE_MOCK_SERVICES"] = "1"
    
    # 初始化进度显示
    for i in range(11):
        progress = i
        sys.stdout.write(f"\r准备中 [{'#' * progress}{' ' * (10-progress)}] {progress*10}%")
        sys.stdout.flush()
        time.sleep(0.1)  # 显示进度的延迟
    
    print("\n系统初始化完成！")
    
    try:
        # 延迟导入应用创建函数，避免可能的导入问题
        from stock_pattern_system.ui.app import create_app
        
        print("正在创建应用...")
        app = create_app()
        print("应用创建成功！正在启动服务器...")
        print("请访问 http://localhost:8050 使用系统")
        app.run_server(debug=True, host='0.0.0.0', port=8050)
    except Exception as e:
        print(f"\n启动应用程序时出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 