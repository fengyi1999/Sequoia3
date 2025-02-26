"""
页脚组件
"""
import dash_bootstrap_components as dbc
from dash import html

def create_footer():
    """创建页脚"""
    footer = html.Footer(
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.P("形态选股系统 © 2023", className="text-center text-muted"),
                                html.P("基于DTW算法和技术形态识别", className="text-center text-muted small"),
                            ],
                            width=12,
                        ),
                    ]
                ),
            ],
            fluid=True,
        ),
        className="footer mt-5 py-3 bg-light"
    )
    
    return footer 