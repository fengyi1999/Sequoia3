"""
形态选股系统简化版运行脚本

这个脚本创建一个独立的Dash应用，避免循环导入问题
"""
import os
import sys
from pathlib import Path
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

# 确保当前目录在路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def create_app():
    """创建一个简化版的Dash应用"""
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        title="形态选股系统 (简化版)"
    )
    
    # 创建简化版布局
    app.layout = html.Div([
        # 导航栏
        dbc.NavbarSimple(
            brand="形态选股系统 (简化版)",
            brand_href="#",
            color="primary",
            dark=True,
        ),
        
        # 主内容
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H2("欢迎使用形态选股系统", className="mt-4"),
                    html.Hr(),
                    html.P("这是一个基于DTW算法的股票技术形态识别与匹配系统。"),
                    html.P("当前显示的是简化版界面，用于测试系统是否可以正常启动。"),
                    
                    dbc.Card([
                        dbc.CardHeader("系统状态"),
                        dbc.CardBody([
                            html.P("✅ 应用服务器运行正常"),
                            html.P("✅ UI界面加载成功"),
                            html.P("⚠️ 后端功能暂不可用（简化版）"),
                            html.P("⚠️ 需要解决循环导入问题")
                        ])
                    ], className="mt-4"),
                    
                    html.Div([
                        html.H4("问题诊断", className="mt-4"),
                        html.P("检测到循环导入问题:"),
                        dbc.Alert([
                            html.Code("from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService"),
                            html.Br(),
                            html.Code("from app.services.pattern_templates import PatternTemplateManager")
                        ], color="warning"),
                        html.P("建议解决方法:"),
                        dbc.Alert([
                            html.P("1. 使用延迟导入策略"),
                            html.P("2. 重构代码，消除循环依赖"),
                            html.P("3. 创建中间模块，打破循环")
                        ], color="info")
                    ])
                ])
            ])
        ], className="my-4"),
        
        # 页脚
        html.Footer(
            dbc.Container([
                html.Hr(),
                html.P("形态选股系统 © 2023", className="text-center text-muted")
            ]),
            className="mt-5"
        )
    ])
    
    return app

if __name__ == "__main__":
    print("正在启动简化版形态选股系统...")
    print("-------------------------------------")
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"脚本路径: {__file__}")
    print("-------------------------------------")
    
    try:
        app = create_app()
        print("应用创建成功！正在启动服务器...")
        print("请访问 http://localhost:8050 查看测试页面")
        app.run_server(debug=True, host='0.0.0.0', port=8050)
    except Exception as e:
        print(f"启动应用程序时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 