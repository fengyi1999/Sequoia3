"""
首页布局
"""
import dash_bootstrap_components as dbc
from dash import html, dcc

def create_home_layout():
    """创建首页布局"""
    layout = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1("形态选股系统", className="display-4"),
                            html.P(
                                "基于DTW算法的股票技术形态识别与匹配系统，支持预定义形态和自定义形态。",
                                className="lead",
                            ),
                            html.Hr(className="my-4"),
                        ],
                        width=12,
                    )
                ]
            ),
            
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H4("形态匹配", className="card-title")),
                                dbc.CardBody(
                                    [
                                        html.P("使用预定义或自定义形态模板进行全市场匹配，找出形态相似的股票。"),
                                        dbc.Button("开始匹配", color="primary", href="/pattern-matching"),
                                    ]
                                ),
                            ],
                            className="h-100 shadow",
                        ),
                        width=4,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H4("参数调优", className="card-title")),
                                dbc.CardBody(
                                    [
                                        html.P("调整DTW算法参数，测试不同参数组合的性能，优化匹配效果。"),
                                        dbc.Button("开始调优", color="primary", href="/param-tuning"),
                                    ]
                                ),
                            ],
                            className="h-100 shadow",
                        ),
                        width=4,
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H4("模板管理", className="card-title")),
                                dbc.CardBody(
                                    [
                                        html.P("管理预定义和自定义形态模板，导入导出模板，创建自定义形态。"),
                                        dbc.Button("管理模板", color="primary", href="/template-management"),
                                    ]
                                ),
                            ],
                            className="h-100 shadow",
                        ),
                        width=4,
                    ),
                ],
                className="mt-4",
            ),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Hr(className="my-4"),
                            html.H3("系统特点", className="mb-3"),
                            dbc.ListGroup(
                                [
                                    dbc.ListGroupItem("基于DTW算法的形态匹配，支持不同长度序列匹配"),
                                    dbc.ListGroupItem("11种预定义经典技术形态，包括头肩顶/底、双顶/底、三角形等"),
                                    dbc.ListGroupItem("支持从实际股票数据创建自定义形态"),
                                    dbc.ListGroupItem("交互式参数调优，可视化展示参数效果"),
                                    dbc.ListGroupItem("全市场形态扫描，快速发现相似形态股票"),
                                ],
                                className="mb-4",
                            ),
                        ],
                        width=12,
                    )
                ],
                className="mt-4",
            ),
        ]
    )
    
    return layout 