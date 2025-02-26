"""
形态选股系统启动脚本（修复版）

用于启动Web应用服务器，使用延迟导入避免循环导入问题。
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
    """主函数，延迟导入应用创建函数"""
    print("正在启动形态选股系统...")
    print("正在检查模块依赖...")
    
    # 初始化进度显示
    progress = 0
    sys.stdout.write(f"\r准备中 [{'#' * progress}{' ' * (10-progress)}] {progress*10}%")
    sys.stdout.flush()
    
    # 逐步导入模块，避免循环导入
    try:
        progress = 1
        sys.stdout.write(f"\r准备中 [{'#' * progress}{' ' * (10-progress)}] {progress*10}%")
        sys.stdout.flush()
        time.sleep(0.2)  # 显示进度的延迟
        
        # 先导入基础模块
        import dash
        import dash_bootstrap_components as dbc
        
        progress = 3
        sys.stdout.write(f"\r准备中 [{'#' * progress}{' ' * (10-progress)}] {progress*10}%")
        sys.stdout.flush()
        time.sleep(0.2)
        
        # 导入UI组件
        from stock_pattern_system.ui.components.navbar import create_navbar
        from stock_pattern_system.ui.components.footer import create_footer
        from stock_pattern_system.ui.components.sidebar import create_sidebar
        
        progress = 5
        sys.stdout.write(f"\r准备中 [{'#' * progress}{' ' * (10-progress)}] {progress*10}%")
        sys.stdout.flush()
        time.sleep(0.2)
        
        # 导入页面布局
        from stock_pattern_system.ui.pages.home import create_home_layout
        
        progress = 7
        sys.stdout.write(f"\r准备中 [{'#' * progress}{' ' * (10-progress)}] {progress*10}%")
        sys.stdout.flush()
        time.sleep(0.2)
        
        # 最后导入应用创建函数
        from stock_pattern_system.ui.app import create_app
        
        progress = 10
        sys.stdout.write(f"\r准备中 [{'#' * progress}{' ' * (10-progress)}] {progress*10}%")
        sys.stdout.flush()
        print("\n模块导入成功！")
        
        # 创建并启动应用
        print("正在创建应用...")
        app = create_app()
        print("应用创建成功！正在启动服务器...")
        print("请访问 http://localhost:8050 使用系统")
        app.run_server(debug=True, host='0.0.0.0', port=8050)
        
    except ImportError as e:
        print(f"\n导入错误: {e}")
        print("请确保所有依赖已正确安装")
        return 1
    except Exception as e:
        print(f"\n启动应用程序时出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 