"""
形态选股系统直接运行脚本

这个脚本直接使用顶层依赖，避免模块导入问题
"""
import os
import sys
import subprocess

# 打印Python版本和路径信息
print(f"Python版本: {sys.version}")
print(f"Python可执行文件: {sys.executable}")
print(f"当前工作目录: {os.getcwd()}")

# 尝试导入必要的包
try:
    import dash
    import dash_bootstrap_components as dbc
    from dash import html
    import plotly
    import pandas as pd
    import numpy as np
    from flask import Flask
    
    print("\n✅ 成功导入所有必要的包")
    print(f"Dash版本: {dash.__version__}")
    print(f"Plotly版本: {plotly.__version__}")
    print(f"Pandas版本: {pd.__version__}")
    print(f"NumPy版本: {np.__version__}")
    
    # 创建一个最小化的Dash应用
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    app.layout = html.Div([
        html.H1("形态选股系统 - 测试页面"),
        html.P("如果您能看到这个页面，说明系统已经成功启动！"),
        html.Hr(),
        html.Div([
            html.H4("系统信息"),
            html.Ul([
                html.Li(f"Dash版本: {dash.__version__}"),
                html.Li(f"Plotly版本: {plotly.__version__}"),
                html.Li(f"Pandas版本: {pd.__version__}"),
                html.Li(f"NumPy版本: {np.__version__}"),
                html.Li(f"Python版本: {sys.version}"),
            ])
        ])
    ])
    
    if __name__ == '__main__':
        print("\n正在启动测试服务器...")
        print("请访问 http://localhost:8050 查看测试页面")
        app.run_server(debug=True, host='0.0.0.0', port=8050)
        
except ImportError as e:
    print(f"\n❌ 导入错误: {e}")
    print("尝试安装缺失的依赖...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                              "dash", "dash-bootstrap-components", "plotly", 
                              "pandas", "numpy", "flask"])
        print("依赖安装完成，请重新运行此脚本")
    except Exception as e:
        print(f"安装依赖失败: {e}")
        print("请手动安装必要的依赖")
    
    sys.exit(1)
except Exception as e:
    print(f"\n❌ 发生错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 