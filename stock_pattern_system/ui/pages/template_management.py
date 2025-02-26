"""
模板管理页面

提供形态模板的管理功能，包括查看、创建、编辑、删除和导入导出模板。
"""
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

# 模拟数据 - 实际应用中应从数据库或API获取
SAMPLE_TEMPLATES = [
    {
        "id": 1,
        "name": "头肩顶",
        "description": "经典头肩顶形态，表示可能的趋势反转",
        "category": "反转形态",
        "created_at": "2023-01-15",
        "data": np.sin(np.linspace(0, 2*np.pi, 100)) + 0.5*np.sin(np.linspace(0, 6*np.pi, 100))
    },
    {
        "id": 2,
        "name": "双底",
        "description": "W形双底形态，表示可能的趋势反转",
        "category": "反转形态",
        "created_at": "2023-02-20",
        "data": np.sin(np.linspace(0, 2*np.pi, 100)) * -1
    },
    {
        "id": 3,
        "name": "上升三角形",
        "description": "上升三角形形态，表示可能的趋势延续",
        "category": "持续形态",
        "created_at": "2023-03-10",
        "data": np.linspace(0, 1, 100) + 0.2*np.sin(np.linspace(0, 8*np.pi, 100))
    },
]

def create_template_card(template):
    """创建模板卡片"""
    # 创建形态图表
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=template["data"],
        mode='lines',
        name=template["name"],
        line=dict(color='royalblue', width=2)
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=150,
        showlegend=False,
        xaxis=dict(showticklabels=False, showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False),
        plot_bgcolor='white'
    )
    
    # 创建卡片
    card = dbc.Card(
        [
            dbc.CardHeader(html.H5(template["name"], className="card-title")),
            dbc.CardBody(
                [
                    dcc.Graph(
                        figure=fig,
                        config={'displayModeBar': False},
                        className="mb-3"
                    ),
                    html.P(template["description"], className="card-text"),
                    html.P(f"分类: {template['category']}", className="card-text text-muted"),
                    html.P(f"创建时间: {template['created_at']}", className="card-text text-muted small"),
                ]
            ),
            dbc.CardFooter(
                [
                    dbc.ButtonGroup(
                        [
                            dbc.Button("编辑", color="primary", outline=True, size="sm", id=f"edit-btn-{template['id']}"),
                            dbc.Button("删除", color="danger", outline=True, size="sm", id=f"delete-btn-{template['id']}"),
                            dbc.Button("使用", color="success", outline=True, size="sm", id=f"use-btn-{template['id']}"),
                        ],
                        className="w-100"
                    )
                ]
            )
        ],
        className="h-100 shadow-sm"
    )
    
    return card

def create_template_management_layout():
    """创建模板管理页面布局"""
    layout = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("形态模板管理"),
                            html.P("管理预定义和自定义形态模板，创建、编辑、删除和导入导出模板。"),
                            html.Hr(),
                        ],
                        width=12
                    )
                ]
            ),
            
            # 操作按钮
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.ButtonGroup(
                                [
                                    dbc.Button("创建新模板", color="primary", id="create-template-btn"),
                                    dbc.Button("导入模板", color="secondary", id="import-template-btn"),
                                    dbc.Button("导出所有模板", color="secondary", id="export-all-templates-btn"),
                                ],
                                className="mb-4"
                            )
                        ],
                        width=12
                    )
                ]
            ),
            
            # 过滤器
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText("搜索"),
                                    dbc.Input(id="template-search", placeholder="输入模板名称或描述..."),
                                ],
                                className="mb-3"
                            )
                        ],
                        width=6
                    ),
                    dbc.Col(
                        [
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText("分类"),
                                    dbc.Select(
                                        id="template-category-filter",
                                        options=[
                                            {"label": "全部", "value": "all"},
                                            {"label": "反转形态", "value": "反转形态"},
                                            {"label": "持续形态", "value": "持续形态"},
                                            {"label": "自定义", "value": "自定义"},
                                        ],
                                        value="all"
                                    ),
                                ],
                                className="mb-3"
                            )
                        ],
                        width=6
                    )
                ]
            ),
            
            # 模板列表
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                id="template-list",
                                children=[
                                    dbc.Row(
                                        [
                                            dbc.Col(create_template_card(template), width=4, className="mb-4")
                                            for template in SAMPLE_TEMPLATES
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=12
                    )
                ]
            ),
            
            # 创建/编辑模板对话框
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("创建新模板")),
                    dbc.ModalBody(
                        [
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("模板名称"),
                                                    dbc.Input(id="template-name-input", placeholder="输入模板名称", type="text"),
                                                ],
                                                width=12,
                                                className="mb-3"
                                            )
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("描述"),
                                                    dbc.Textarea(id="template-description-input", placeholder="输入模板描述"),
                                                ],
                                                width=12,
                                                className="mb-3"
                                            )
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("分类"),
                                                    dbc.Select(
                                                        id="template-category-input",
                                                        options=[
                                                            {"label": "反转形态", "value": "反转形态"},
                                                            {"label": "持续形态", "value": "持续形态"},
                                                            {"label": "自定义", "value": "自定义"},
                                                        ],
                                                        value="自定义"
                                                    ),
                                                ],
                                                width=12,
                                                className="mb-3"
                                            )
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label("数据来源"),
                                                    dbc.RadioItems(
                                                        id="template-data-source",
                                                        options=[
                                                            {"label": "从股票数据创建", "value": "stock"},
                                                            {"label": "手动绘制", "value": "draw"},
                                                            {"label": "上传数据文件", "value": "upload"},
                                                        ],
                                                        value="stock",
                                                        inline=True
                                                    ),
                                                ],
                                                width=12,
                                                className="mb-3"
                                            )
                                        ]
                                    ),
                                    # 数据来源为股票时的选项
                                    html.Div(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("股票代码"),
                                                            dbc.Input(id="stock-code-input", placeholder="输入股票代码，如: 600000", type="text"),
                                                        ],
                                                        width=6
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("选择指标"),
                                                            dbc.Select(
                                                                id="stock-indicator-input",
                                                                options=[
                                                                    {"label": "收盘价", "value": "close"},
                                                                    {"label": "5日均线", "value": "ma5"},
                                                                    {"label": "10日均线", "value": "ma10"},
                                                                    {"label": "20日均线", "value": "ma20"},
                                                                ],
                                                                value="close"
                                                            ),
                                                        ],
                                                        width=6
                                                    )
                                                ],
                                                className="mb-3"
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("开始日期"),
                                                            dbc.Input(id="start-date-input", type="date"),
                                                        ],
                                                        width=6
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("结束日期"),
                                                            dbc.Input(id="end-date-input", type="date"),
                                                        ],
                                                        width=6
                                                    )
                                                ],
                                                className="mb-3"
                                            ),
                                            dbc.Button("获取股票数据", id="fetch-stock-data-btn", color="primary", className="mb-3"),
                                        ],
                                        id="stock-data-options",
                                        style={"display": "block"}
                                    ),
                                    # 数据来源为手动绘制时的选项
                                    html.Div(
                                        [
                                            dbc.Label("绘制形态"),
                                            html.P("点击并拖动鼠标在图表上绘制形态"),
                                            dcc.Graph(
                                                id="draw-pattern-graph",
                                                figure={
                                                    "data": [
                                                        {
                                                            "x": list(range(100)),
                                                            "y": [0] * 100,
                                                            "mode": "lines+markers",
                                                            "name": "形态",
                                                            "line": {"color": "royalblue"}
                                                        }
                                                    ],
                                                    "layout": {
                                                        "title": "绘制形态",
                                                        "height": 300,
                                                        "margin": {"l": 40, "r": 40, "t": 40, "b": 40},
                                                        "xaxis": {"showgrid": True},
                                                        "yaxis": {"showgrid": True},
                                                        "plot_bgcolor": "white"
                                                    }
                                                },
                                                config={"editable": True, "edits": {"shapePosition": True}}
                                            ),
                                            dbc.Button("清除", id="clear-drawing-btn", color="secondary", className="mt-2"),
                                        ],
                                        id="draw-data-options",
                                        style={"display": "none"}
                                    ),
                                    # 数据来源为上传文件时的选项
                                    html.Div(
                                        [
                                            dbc.Label("上传数据文件"),
                                            dcc.Upload(
                                                id="upload-data-file",
                                                children=html.Div([
                                                    "拖放或 ",
                                                    html.A("选择文件")
                                                ]),
                                                style={
                                                    "width": "100%",
                                                    "height": "60px",
                                                    "lineHeight": "60px",
                                                    "borderWidth": "1px",
                                                    "borderStyle": "dashed",
                                                    "borderRadius": "5px",
                                                    "textAlign": "center",
                                                    "margin": "10px 0"
                                                },
                                                multiple=False
                                            ),
                                            html.Div(id="upload-data-output"),
                                        ],
                                        id="upload-data-options",
                                        style={"display": "none"}
                                    ),
                                    # 预览
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Hr(),
                                                    html.H5("形态预览"),
                                                    dcc.Graph(
                                                        id="template-preview",
                                                        figure={
                                                            "data": [
                                                                {
                                                                    "y": np.zeros(100),
                                                                    "mode": "lines",
                                                                    "name": "预览",
                                                                    "line": {"color": "royalblue"}
                                                                }
                                                            ],
                                                            "layout": {
                                                                "height": 200,
                                                                "margin": {"l": 40, "r": 40, "t": 10, "b": 40},
                                                                "showlegend": False,
                                                                "xaxis": {"showticklabels": False, "showgrid": False},
                                                                "yaxis": {"showticklabels": False, "showgrid": False},
                                                                "plot_bgcolor": "white"
                                                            }
                                                        },
                                                        config={"displayModeBar": False}
                                                    ),
                                                ],
                                                width=12
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button("取消", id="cancel-template-btn", className="ms-auto", color="secondary"),
                            dbc.Button("保存", id="save-template-btn", color="primary"),
                        ]
                    ),
                ],
                id="template-modal",
                size="lg",
                is_open=False,
            ),
            
            # 删除确认对话框
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("确认删除")),
                    dbc.ModalBody("确定要删除这个模板吗？此操作无法撤销。"),
                    dbc.ModalFooter(
                        [
                            dbc.Button("取消", id="cancel-delete-btn", className="ms-auto", color="secondary"),
                            dbc.Button("删除", id="confirm-delete-btn", color="danger"),
                        ]
                    ),
                ],
                id="delete-confirm-modal",
                is_open=False,
            ),
            
            # 存储组件
            dcc.Store(id="current-template-id", data=None),
            dcc.Store(id="template-data", data=None),
        ]
    )
    
    return layout

def register_callbacks(app):
    """注册回调函数"""
    
    # 打开创建模板对话框
    @app.callback(
        Output("template-modal", "is_open"),
        Output("template-modal", "children", allow_duplicate=True),
        Input("create-template-btn", "n_clicks"),
        Input("cancel-template-btn", "n_clicks"),
        Input("save-template-btn", "n_clicks"),
        State("template-modal", "is_open"),
        prevent_initial_call=True
    )
    def toggle_template_modal(create_clicks, cancel_clicks, save_clicks, is_open):
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open, dash.no_update
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        if button_id == "create-template-btn" and not is_open:
            # 打开创建模板对话框
            return True, dash.no_update
        elif button_id in ["cancel-template-btn", "save-template-btn"] and is_open:
            # 关闭对话框
            return False, dash.no_update
        
        return is_open, dash.no_update
    
    # 切换数据来源选项显示
    @app.callback(
        Output("stock-data-options", "style"),
        Output("draw-data-options", "style"),
        Output("upload-data-options", "style"),
        Input("template-data-source", "value")
    )
    def toggle_data_source_options(data_source):
        stock_style = {"display": "block" if data_source == "stock" else "none"}
        draw_style = {"display": "block" if data_source == "draw" else "none"}
        upload_style = {"display": "block" if data_source == "upload" else "none"}
        
        return stock_style, draw_style, upload_style
    
    # 这里可以添加更多回调函数，如保存模板、删除模板、过滤模板等
    
    return app 