"""
形态选股系统Web应用 (简化版)

提供形态匹配、参数调优和结果展示的Web界面。
"""
import os
import sys
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from flask import Flask

# 应用样式
BOOTSTRAP_THEME = dbc.themes.BOOTSTRAP

def create_app():
    """创建并配置Dash应用"""
    # 创建Flask server
    server = Flask(__name__)
    
    # 打印当前工作目录和资源目录
    print(f"Flask实例目录: {server.root_path}")
    print(f"静态文件目录: {server.static_folder}")
    print(f"模板目录: {server.template_folder}")
    
    # 创建Dash应用
    app = dash.Dash(
        __name__,
        server=server,
        external_stylesheets=[BOOTSTRAP_THEME],
        suppress_callback_exceptions=True,
        title="形态选股系统",
        assets_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
    )
    
    # 打印Dash资源目录
    print(f"Dash资源目录: {app.config.assets_folder}")
    
    # 设置应用布局 - 简化版，仅显示欢迎信息
    app.layout = html.Div([
        dbc.NavbarSimple(
            brand="形态选股系统",
            brand_href="#",
            color="primary",
            dark=True,
        ),
        
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H2("欢迎使用形态选股系统", className="mt-4"),
                                html.Hr(),
                                html.P("这是一个基于DTW算法的股票技术形态识别与匹配系统。"),
                                html.P("系统目前处于简化模式，完整功能正在开发中..."),
                                
                                dbc.Card(
                                    [
                                        dbc.CardHeader("系统状态"),
                                        dbc.CardBody(
                                            [
                                                html.P("✅ 应用服务器运行正常"),
                                                html.P("✅ 基础依赖已安装"),
                                                html.P("⚠️ 模块导入路径需要配置"),
                                                html.P("⚠️ 完整功能尚未实现"),
                                            ]
                                        )
                                    ],
                                    className="mt-4"
                                )
                            ],
                            width=12
                        )
                    ]
                )
            ],
            className="mt-4"
        ),
        
        html.Footer(
            dbc.Container(
                [
                    html.P("形态选股系统 © 2023", className="text-center text-muted")
                ]
            ),
            className="mt-5 py-3 bg-light"
        )
    ])
    
    return app

# 如果直接运行此文件，则启动应用
if __name__ == '__main__':
    app = create_app()
    app.run_server(debug=True, host='0.0.0.0', port=8050) 