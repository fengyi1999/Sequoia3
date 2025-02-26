"""
形态选股系统本地启动脚本

直接运行应用程序，避免模块导入问题
"""
import os
import sys
from pathlib import Path
import site
import subprocess

# 确保当前目录在路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 同时添加上层目录到路径中
parent_dir = os.path.dirname(current_dir)
parent_parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, parent_parent_dir)

# 添加site-packages目录
site_packages = site.getsitepackages()
for sp in site_packages:
    if sp not in sys.path:
        sys.path.append(sp)

# 添加用户site-packages目录
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)

print(f"当前工作目录: {os.getcwd()}")
print(f"Python路径: {sys.path[:3]}")
print(f"Site-packages路径: {site_packages}")
print(f"用户Site-packages路径: {user_site}")

# 直接运行应用，不检查依赖
try:
    # 尝试导入简化版app
    print("正在使用简化版应用...")
    from simple_app import create_app
    
    if __name__ == '__main__':
        print("正在启动形态选股系统...")
        print("请访问 http://localhost:8050 使用系统")
        app = create_app()
        app.run_server(debug=True, host='0.0.0.0', port=8050)
except Exception as e:
    print(f"启动应用程序时出错: {e}")
    print(f"错误类型: {type(e).__name__}")
    print("请确保所有必要的文件都存在，并且依赖已正确安装")
    import traceback
    traceback.print_exc()
    
    # 尝试查找已安装的包
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                               capture_output=True, text=True, check=True)
        print("\n已安装的包:")
        print(result.stdout)
    except Exception:
        pass
    
    sys.exit(1) 