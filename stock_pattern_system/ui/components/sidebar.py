"""
侧边栏组件
"""
import dash_bootstrap_components as dbc
from dash import html, dcc

def create_sidebar():
    """创建侧边栏"""
    sidebar = html.Div(
        [
            # 添加折叠按钮
            html.Div(
                [
                    html.Button(
                        html.I(className="fas fa-bars"),
                        id="sidebar-toggle-button",
                        className="btn btn-light sidebar-toggle",
                    ),
                    html.H4("功能导航", className="sidebar-header ms-2"),
                ],
                className="d-flex align-items-center"
            ),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavItem(
                        dbc.NavLink(
                            [html.I(className="fas fa-home me-2"), html.Span("首页", className="nav-text")],
                            active="exact",
                            href="/",
                        )
                    ),
                    dbc.NavItem(
                        dbc.NavLink(
                            [html.I(className="fas fa-chart-line me-2"), html.Span("形态匹配", className="nav-text")],
                            href="/pattern-matching",
                            active="exact",
                        )
                    ),
                    dbc.NavItem(
                        dbc.NavLink(
                            [html.I(className="fas fa-sliders-h me-2"), html.Span("参数调优", className="nav-text")],
                            href="/param-tuning",
                            active="exact",
                        )
                    ),
                    dbc.NavItem(
                        dbc.NavLink(
                            [html.I(className="fas fa-database me-2"), html.Span("模板管理", className="nav-text")],
                            href="/template-management",
                            active="exact",
                        )
                    ),
                ],
                vertical=True,
                pills=True,
                id="sidebar-nav",
                className="my-4"
            ),
            
            html.Hr(),
            
            # 系统状态信息
            html.Div(
                [
                    html.H6("系统状态", className="sidebar-subheader"),
                    dbc.Badge("正常运行", color="success", className="mb-2", style={"width": "100%"}),
                    html.P("预定义模板: 11", className="small text-muted"),
                    html.P("自定义模板: 0", className="small text-muted", id="custom-templates-count"),
                ],
                className="mt-4 status-info"
            )
        ],
        className="sidebar p-3 bg-light",
        id="sidebar"
    )
    
    return sidebar 