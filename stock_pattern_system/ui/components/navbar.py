"""
导航栏组件
"""
import dash
import dash_bootstrap_components as dbc
from dash import html

def create_navbar():
    """创建导航栏"""
    
    # 使用FontAwesome图标代替SVG - 使用两个图标并添加圆形背景
    taurus_icon = html.Div([
        html.I(className="fas fa-chart-line fa-lg"),
    ], style={
        "background": "#80d8ff", 
        "width": "35px", 
        "height": "35px", 
        "borderRadius": "50%",
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center",
        "color": "#00579d"
    })
    
    navbar = dbc.Navbar(
        dbc.Container(
            [
                # 应用Logo和名称
                dbc.Row(
                    [
                        dbc.Col(
                            taurus_icon, 
                            width="auto",
                            className="d-flex align-items-center me-2"
                        ),
                        dbc.Col(
                            dbc.NavbarBrand("FengStockSelecting", className="ms-1 fw-bold"),
                            width="auto"
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                
                # 导航链接
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.NavItem(dbc.NavLink("首页", href="/")),
                            dbc.NavItem(dbc.NavLink("形态匹配", href="/pattern-matching")),
                            dbc.NavItem(dbc.NavLink("参数调优", href="/param-tuning")),
                            dbc.NavItem(dbc.NavLink("模板管理", href="/template-management")),
                        ],
                        className="ms-auto",
                        navbar=True
                    ),
                    id="navbar-collapse",
                    navbar=True,
                ),
            ],
            fluid=True,
        ),
        color="primary",
        dark=True,
        className="mb-4",
    )
    
    return navbar 