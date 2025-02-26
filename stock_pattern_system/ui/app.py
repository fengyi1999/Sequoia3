"""
形态选股系统Web应用

提供形态匹配、参数调优和结果展示的Web界面。
"""
import os
import sys
from pathlib import Path

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from flask import Flask

# 检查是否使用模拟服务
USE_MOCK_SERVICES = os.environ.get("USE_MOCK_SERVICES", "0") == "1"
print(f"使用模拟服务: {'是' if USE_MOCK_SERVICES else '否'}")

# 尝试使用相对导入
try:
    # 导入页面和组件
    from components.navbar import create_navbar
    from components.footer import create_footer
    from components.sidebar import create_sidebar

    # 导入页面
    from pages.home import create_home_layout
    from pages.pattern_matching import create_pattern_matching_layout
    from pages.param_tuning import create_param_tuning_layout
    from pages.template_management import create_template_management_layout
except ImportError:
    # 如果相对导入失败，尝试使用绝对导入
    try:
        # 将项目根目录添加到Python路径
        project_root = str(Path(__file__).parent.parent.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # 导入页面和组件
        from stock_pattern_system.ui.components.navbar import create_navbar
        from stock_pattern_system.ui.components.footer import create_footer
        from stock_pattern_system.ui.components.sidebar import create_sidebar

        # 导入页面
        from stock_pattern_system.ui.pages.home import create_home_layout
        from stock_pattern_system.ui.pages.pattern_matching import create_pattern_matching_layout
        from stock_pattern_system.ui.pages.param_tuning import create_param_tuning_layout
        from stock_pattern_system.ui.pages.template_management import create_template_management_layout
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保您在正确的目录中运行此脚本")
        sys.exit(1)

# 应用样式
BOOTSTRAP_THEME = dbc.themes.BOOTSTRAP
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.15.4/css/all.css"

def create_app():
    """创建并配置Dash应用"""
    # 创建Flask server
    server = Flask(__name__)
    
    # 创建Dash应用
    app = dash.Dash(
        __name__,
        server=server,
        external_stylesheets=[BOOTSTRAP_THEME, FONT_AWESOME],
        suppress_callback_exceptions=True,
        title="FengStockSelecting"
    )
    
    # 设置应用布局
    app.layout = html.Div([
        # URL路由
        dcc.Location(id='url', refresh=False),
        
        # 存储当前页面
        dcc.Store(id='current-page', data='home'),
        
        # 存储侧边栏状态
        dcc.Store(id='sidebar-state', data={'collapsed': False}),
        
        # 导航栏
        create_navbar(),
        
        # 主内容区域
        dbc.Container(
            [
                dbc.Row(
                    [
                        # 侧边栏
                        dbc.Col(create_sidebar(), id="sidebar-container", width=3, className="sidebar-col"),
                        
                        # 内容区域
                        dbc.Col(html.Div(id='page-content'), id="content-container", width=9, className="content-area"),
                    ],
                    className="mt-4"
                )
            ],
            fluid=True,
            className="mt-4"
        ),
        
        # 页脚
        create_footer()
    ])
    
    # 页面路由回调
    @app.callback(
        Output('page-content', 'children'),
        Input('url', 'pathname')
    )
    def display_page(pathname):
        """根据URL路径切换页面"""
        if pathname == '/pattern-matching':
            return create_pattern_matching_layout()
        elif pathname == '/param-tuning':
            return create_param_tuning_layout()
        elif pathname == '/template-management':
            return create_template_management_layout()
        else:  # 默认显示主页
            return create_home_layout()
    
    # 侧边栏折叠/展开回调
    @app.callback(
        [
            Output('sidebar', 'className'),
            Output('sidebar-container', 'width'),
            Output('content-container', 'width'),
            Output('sidebar-state', 'data'),
        ],
        [Input('sidebar-toggle-button', 'n_clicks')],
        [State('sidebar-state', 'data')]
    )
    def toggle_sidebar(n_clicks, sidebar_state):
        """切换侧边栏折叠状态"""
        if n_clicks is None:
            return "sidebar p-3 bg-light", 3, 9, sidebar_state
        
        # 获取当前状态
        is_collapsed = sidebar_state.get('collapsed', False)
        
        # 切换状态
        new_state = not is_collapsed
        
        if new_state:  # 折叠
            return "sidebar p-3 bg-light collapsed", 1, 11, {'collapsed': True}
        else:  # 展开
            return "sidebar p-3 bg-light", 3, 9, {'collapsed': False}
    
    # 侧边栏导航回调
    @app.callback(
        Output('url', 'pathname'),
        Input('sidebar-nav', 'active_tab')
    )
    def navigate_from_sidebar(active_tab):
        """通过侧边栏导航到对应页面"""
        if active_tab == 'home':
            return '/'
        elif active_tab == 'pattern-matching':
            return '/pattern-matching'
        elif active_tab == 'param-tuning':
            return '/param-tuning'
        elif active_tab == 'template-management':
            return '/template-management'
        return '/'
    
    # 注册各页面的回调函数
    try:
        # 尝试使用相对导入
        from pages.pattern_matching import register_callbacks as register_pattern_matching_callbacks
        from pages.param_tuning import register_callbacks as register_param_tuning_callbacks
        from pages.template_management import register_callbacks as register_template_management_callbacks
    except ImportError:
        # 如果相对导入失败，尝试使用绝对导入
        from stock_pattern_system.ui.pages.pattern_matching import register_callbacks as register_pattern_matching_callbacks
        from stock_pattern_system.ui.pages.param_tuning import register_callbacks as register_param_tuning_callbacks
        from stock_pattern_system.ui.pages.template_management import register_callbacks as register_template_management_callbacks
    
    register_pattern_matching_callbacks(app)
    register_param_tuning_callbacks(app)
    register_template_management_callbacks(app)
    
    return app

# 如果直接运行此文件，则启动应用
if __name__ == '__main__':
    app = create_app()
    app.run_server(debug=True) 