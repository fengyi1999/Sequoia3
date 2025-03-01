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

# 根据环境变量决定使用真实服务还是模拟服务
USE_MOCK_SERVICES = os.environ.get("USE_MOCK_SERVICES", "0") == "1"

if USE_MOCK_SERVICES:
    # 使用模拟服务
    from stock_pattern_system.ui.pages.mock_services import MockTemplateManager
    template_manager = MockTemplateManager()
    print("模板管理页面：使用模拟服务")
    
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
            "created_at": "2023-01-20",
            "data": 1 - np.sin(np.linspace(0, 2*np.pi, 100)) + 0.3*np.sin(np.linspace(0, 8*np.pi, 100))
        },
        {
            "id": 3,
            "name": "上升三角形",
            "description": "上升三角形整理形态，表示可能的上涨延续",
            "category": "整理形态",
            "created_at": "2023-02-05",
            "data": np.linspace(0.3, 0.7, 100) + 0.2*np.sin(np.linspace(0, 6*np.pi, 100))
        }
    ]
else:
    # 使用真实服务
    from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService
    from stock_pattern_system.app.services.pattern_templates import PatternTemplateManager
    
    # 初始化真实服务
    template_manager = PatternTemplateManager()
    pattern_service = PatternMatcherService()
    print("模板管理页面：使用真实服务")
    
    # 从真实服务获取模板
    templates = pattern_service.get_pattern_templates()
    SAMPLE_TEMPLATES = []
    for i, template in enumerate(templates):
        SAMPLE_TEMPLATES.append({
            "id": i + 1,
            "name": template.get("name", f"模板{i+1}"),
            "description": template.get("description", ""),
            "category": template.get("pattern_type", "自定义形态"),
            "created_at": template.get("created_at", datetime.now().strftime("%Y-%m-%d")),
            "data": template.get("data", [])
        })

def create_template_card(template):
    """创建模板卡片"""
    # 创建模板预览图
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=template["data"],
        mode='lines',
        name=template["name"],
        line=dict(color='royalblue', width=2)
    ))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
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
                dbc.ButtonGroup(
                    [
                        dbc.Button("编辑", color="primary", outline=True, size="sm", id=f"edit-btn-{template['id']}"),
                        dbc.Button("删除", color="danger", outline=True, size="sm", id=f"delete-btn-{template['id']}"),
                        dbc.Button("使用", color="success", outline=True, size="sm", id=f"use-btn-{template['id']}"),
                    ],
                    className="w-100"
                )
            )
        ],
        className="h-100 shadow-sm"
    )
    
    return card

def create_template_management_layout():
    """创建模板管理页面布局"""
    # 模板列表
    template_cards = dbc.Row([
        dbc.Col(create_template_card(template), width=4, className="mb-4")
        for template in SAMPLE_TEMPLATES
    ])
    
    # 创建页面布局
    layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H2("形态模板管理", className="mb-4"),
                html.P("在这里管理和创建股票形态模板，用于形态匹配和分析。", className="text-muted mb-4"),
                
                # 操作按钮
                dbc.Row([
                    dbc.Col([
                        dbc.Button("创建新模板", id="create-template-btn", color="primary", className="me-2"),
                        dbc.Button("导入预定义模板", id="import-predefined-btn", color="secondary", className="me-2"),
                        dbc.Button("从股票创建", id="create-from-stock-btn", color="success"),
                    ], width=12, className="mb-4"),
                ]),
                
                # 保存状态显示
                html.Div([
                    html.P("", id="save-template-status")
                ], style={"display": "none"}, id="save-template-status-container", className="mb-3"),
                
                # 模板列表
                html.Div(template_cards, id="template-list", className="mb-4"),
                
                # 创建模板模态框
                create_template_modal(),
                
                # 从股票创建模态框
                create_from_stock_modal(),
                
                # 存储组件
                dcc.Store(id="template-data"),
                dcc.Store(id="stock-data"),
            ], width=12)
        ])
    ], fluid=True, className="py-4")

def create_template_modal():
    """创建模板模态框"""
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("创建新模板")),
            dbc.ModalBody(
                [
                    # 保存状态显示
                    html.Div(
                        html.P("", id="save-template-status", style={"display": "none"}),
                        id="save-template-status-container", 
                        style={"display": "none"},
                        className="mb-3 p-2 border rounded"
                    ),
                    
                    # 模板表单
                    dbc.Form(
                        [
                            # ... 表单内容 ...
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
    )

def create_from_stock_modal():
    """创建从股票创建模板的模态框"""
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("从股票数据创建模板")),
            dbc.ModalBody(
                [
                    dbc.Form(
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
                            
                            # 数据预览
                            html.Div(
                                [
                                    html.H5("数据预览"),
                                    dcc.Graph(
                                        id="stock-data-preview",
                                        config={'displayModeBar': False}
                                    ),
                                ],
                                id="stock-data-preview-container",
                                style={"display": "none"}
                            ),
                        ]
                    )
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("取消", id="cancel-from-stock-btn", className="ms-auto", color="secondary"),
                    dbc.Button("创建模板", id="create-from-stock-template-btn", color="primary"),
                ]
            ),
        ],
        id="from-stock-modal",
        size="lg",
        is_open=False,
    )

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
    
    # 获取股票数据并更新预览
    @app.callback(
        [
            Output("template-preview", "figure"),
            Output("template-data", "data"),
        ],
        [Input("fetch-stock-data-btn", "n_clicks")],
        [
            State("stock-code-input", "value"),
            State("stock-indicator-input", "value"),
            State("start-date-input", "value"),
            State("end-date-input", "value"),
        ],
        prevent_initial_call=True
    )
    def fetch_stock_data(n_clicks, stock_code, indicator, start_date, end_date):
        """获取股票数据并更新预览"""
        if not n_clicks or not stock_code:
            # 返回空图表
            empty_fig = go.Figure().update_layout(
                title="请输入股票代码并获取数据",
                height=200,
                margin={"l": 40, "r": 40, "t": 40, "b": 40},
                showlegend=False,
            )
            return empty_fig, None
        
        # 格式化日期
        if start_date:
            start_date = start_date.replace("-", "")
        if end_date:
            end_date = end_date.replace("-", "")
        
        # 尝试获取股票数据
        try:
            # 首先尝试通过数据库获取
            if not USE_MOCK_SERVICES:
                # 导入相关模块
                from stock_pattern_system.app.data_fetcher import init_single_stock_data, get_stock_history
                
                print(f"检查并初始化股票 {stock_code} 数据...")
                
                # 尝试初始化数据库中的股票数据
                init_result = init_single_stock_data(stock_code, days=365)
                print(f"股票数据初始化结果: {init_result}")
                
                # 获取股票数据（从数据库）
                stock_data = pattern_service.get_stock_data_for_pattern(
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    indicator=indicator
                )
                
                # 如果数据库中没有数据，尝试直接从AKShare获取
                if not stock_data or not stock_data.get('values'):
                    print(f"数据库中未找到股票 {stock_code} 数据，尝试直接从AKShare获取...")
                    
                    # 直接从AKShare获取数据
                    df = get_stock_history(
                        stock_code=stock_code,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if not df.empty:
                        print(f"成功从AKShare获取到 {len(df)} 条股票数据")
                        
                        # 提取数据
                        dates = df['trade_date'].tolist()
                        values = df[indicator].tolist() if indicator in df.columns else df['close'].tolist()
                        
                        # 使用获取的数据
                        stock_data = {
                            'dates': dates,
                            'values': values,
                            'stock_code': stock_code,
                            'indicator': indicator if indicator in df.columns else 'close'
                        }
                    else:
                        print(f"无法从AKShare获取到股票 {stock_code} 数据")
            else:
                # 模拟环境下，使用模拟服务获取数据
                stock_data = pattern_service.get_stock_data_for_pattern(
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    indicator=indicator
                )
            
            # 检查是否有有效数据
            if not stock_data or not stock_data.get('values'):
                # 如果没有获取到数据，返回错误信息
                error_fig = go.Figure().update_layout(
                    title=f"未能获取到股票 {stock_code} 的数据，请检查股票代码和日期范围",
                    height=200,
                    margin={"l": 40, "r": 40, "t": 40, "b": 40},
                    showlegend=False,
                )
                error_fig.add_annotation(
                    text="无法获取数据，请确认股票代码正确且在指定日期范围内有交易",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(color="red", size=12),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="red",
                    borderwidth=1
                )
                return error_fig, None
            
            # 提取数据
            dates = stock_data.get('dates', [])
            values = stock_data.get('values', [])
            
            # 创建预览图
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates if dates else list(range(len(values))),  # 使用实际日期作为X轴，如果没有则使用序号
                y=values,
                mode="lines",
                name=f"{stock_code} {indicator}"
            ))
            
            # 更新布局
            fig.update_layout(
                title=f"{stock_code} {indicator} 数据预览（{len(values)}个数据点）",
                height=200,
                margin={"l": 40, "r": 40, "t": 40, "b": 40},
                showlegend=False,
                xaxis={
                    "title": "日期",
                    "tickangle": 45,
                    "tickmode": "array",
                    "tickvals": dates[::max(1, len(dates)//10)] if dates else None,  # 仅显示部分日期标签
                },
                yaxis={"title": indicator}
            )
            
            # 归一化数据用于模板
            if values:
                min_val = min(values)
                max_val = max(values)
                if max_val > min_val:
                    normalized_data = [(v - min_val) / (max_val - min_val) for v in values]
                else:
                    normalized_data = [0.5 for _ in values]
            else:
                normalized_data = []
            
            # 创建模板数据
            template_data = {
                "stock_code": stock_code,
                "indicator": indicator,
                "start_date": start_date,
                "end_date": end_date,
                "data": normalized_data,
                "dates": dates,
                "values": values,
                "is_mock": False
            }
            
            return fig, template_data
                
        except Exception as e:
            # 捕获错误，记录详细错误信息
            error_msg = str(e)
            error_type = type(e).__name__
            import traceback
            error_trace = traceback.format_exc()
            
            print(f"获取股票数据错误: {error_type} - {error_msg}")
            print(f"错误详情: {error_trace}")
            
            # 创建错误图表
            error_fig = go.Figure().update_layout(
                title=f"数据获取失败: {error_type}",
                height=200,
                margin={"l": 40, "r": 40, "t": 40, "b": 40},
                showlegend=False,
            )
            
            # 添加错误信息文本到图表
            error_fig.add_annotation(
                text=f"错误: {error_msg[:100]}..." if len(error_msg) > 100 else f"错误: {error_msg}",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(color="red", size=10),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="red",
                borderwidth=1
            )
            
            return error_fig, None
    
    # 保存状态样式回调
    @app.callback(
        Output("save-template-status", "style"),
        [Input("save-template-status", "children")]
    )
    def update_save_status_style(status):
        """根据保存状态更新样式"""
        if not status:
            return {"display": "none"}
            
        if "成功" in status:
            return {"color": "green", "fontWeight": "bold"}
        else:
            return {"color": "red", "fontWeight": "bold"}
    
    # 保存模板回调
    @app.callback(
        [
            Output("template-modal", "is_open", allow_duplicate=True),
            Output("template-list", "children", allow_duplicate=True),
            Output("save-template-status", "children", allow_duplicate=True),
            Output("save-template-status-container", "style", allow_duplicate=True)
        ],
        [Input("save-template-btn", "n_clicks")],
        [
            State("template-name-input", "value"),
            State("template-description-input", "value"),
            State("template-category-input", "value"),
            State("template-data-source", "value"),
            State("template-data", "data"),
        ],
        prevent_initial_call=True
    )
    def save_template(n_clicks, name, description, category, data_source, template_data):
        """保存模板"""
        # 声明全局变量在函数开始处
        global SAMPLE_TEMPLATES
        
        # 检查点击次数
        if not n_clicks:
            print("保存按钮未点击")
            return dash.no_update, dash.no_update, "", {"display": "none"}
        
        # 检查必要的输入
        if not name:
            print("模板名称为空")
            return False, dash.no_update, "保存失败: 请输入模板名称", {"display": "block"}
            
        if not template_data:
            print("模板数据为空")
            return False, dash.no_update, "保存失败: 没有可用的形态数据", {"display": "block"}
        
        try:
            print(f"正在保存模板: {name}, 分类: {category}, 数据来源: {data_source}")
            print(f"模板数据类型: {type(template_data)}, 内容: {template_data}")
            
            # 获取模板数据
            stock_code = template_data.get("stock_code", "")
            indicator = template_data.get("indicator", "close")
            start_date = template_data.get("start_date", "")
            end_date = template_data.get("end_date", "")
            pattern_data = template_data.get("data", [])
            
            # 详细检查数据有效性
            if not pattern_data:
                print("模板数据中没有pattern_data字段")
                return False, dash.no_update, "保存失败: 形态数据不存在", {"display": "block"}
                
            if len(pattern_data) < 5:
                print(f"模板数据点数量不足: {len(pattern_data)}")
                return False, dash.no_update, f"保存失败: 形态数据点数量不足 (至少需要5个点, 当前: {len(pattern_data)})", {"display": "block"}
            
            # 标签设置
            tags = []
            if category:
                tags.append(category)
            if data_source == "stock" and stock_code:
                tags.append(f"股票:{stock_code}")
                tags.append(f"指标:{indicator}")
            
            # 自动生成描述（如果用户未提供）
            if not description:
                if data_source == "stock" and stock_code:
                    description = f"从股票 {stock_code} {start_date}至{end_date}的{indicator}数据创建"
                else:
                    description = f"创建于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 保存模板到服务
            template_id = None
            if not USE_MOCK_SERVICES:
                try:
                    print("尝试保存模板到真实服务...")
                    # 直接使用已获取的数据保存模板
                    template_id = pattern_service.save_pattern_template(
                        name=name,
                        data=pattern_data,
                        description=description,
                        tags=tags,
                        pattern_type="custom"
                    )
                    print(f"模板保存成功, ID: {template_id}")
                    
                    # 确保模板管理器重新加载模板
                    print("重新加载模板...")
                    template_manager.load_templates()
                except Exception as e:
                    error_msg = f"保存模板到服务失败: {str(e)}"
                    print(error_msg)
                    import traceback
                    print(traceback.format_exc())
                    return False, dash.no_update, error_msg, {"display": "block"}
            else:
                # 模拟服务下，简单打印信息
                print("模拟服务环境，模拟保存模板")
            
            # 重新获取模板列表
            templates = []
            if USE_MOCK_SERVICES:
                # 在模拟环境中模拟添加模板
                new_template = {
                    "id": len(SAMPLE_TEMPLATES) + 1,
                    "name": name,
                    "description": description,
                    "category": category or "自定义形态",
                    "created_at": datetime.now().strftime("%Y-%m-%d"),
                    "data": pattern_data,
                    "pattern_id": f"custom_{int(datetime.now().timestamp())}"  # 添加pattern_id
                }
                SAMPLE_TEMPLATES.append(new_template)
                templates = SAMPLE_TEMPLATES
                
                # 更新模拟服务的模板列表
                if hasattr(template_manager, "templates"):
                    print("更新模拟服务的模板列表")
                    template_manager.templates.append({
                        "pattern_id": new_template["pattern_id"],
                        "name": name,
                        "description": description,
                        "data": pattern_data,
                        "tags": tags,
                        "pattern_type": "custom",
                        "created_at": datetime.now().isoformat()
                    })
            else:
                # 从真实服务获取最新模板列表
                # 重新加载模板以确保获取最新数据
                try:
                    print("从真实服务获取最新模板列表")
                    template_manager.load_templates()
                    templates = pattern_service.get_pattern_templates()
                    templates_list = []
                    for i, template in enumerate(templates):
                        templates_list.append({
                            "id": i + 1,
                            "name": template.get("name", f"模板{i+1}"),
                            "description": template.get("description", ""),
                            "category": template.get("pattern_type", "自定义形态"),
                            "created_at": template.get("created_at", datetime.now().strftime("%Y-%m-%d")),
                            "data": template.get("data", []),
                            "pattern_id": template.get("pattern_id", "")  # 保留pattern_id
                        })
                    templates = templates_list
                except Exception as e:
                    error_msg = f"重新加载模板失败: {str(e)}"
                    print(error_msg)
                    import traceback
                    print(traceback.format_exc())
                    
                    # 如果重新加载失败，至少添加新保存的模板
                    if template_id:
                        print("添加新保存的模板到本地列表")
                        new_template = {
                            "id": len(SAMPLE_TEMPLATES) + 1,
                            "name": name,
                            "description": description,
                            "category": "自定义形态",
                            "created_at": datetime.now().strftime("%Y-%m-%d"),
                            "data": pattern_data,
                            "pattern_id": template_id
                        }
                        SAMPLE_TEMPLATES.append(new_template)
                        templates = SAMPLE_TEMPLATES
            
            # 重新设置全局模板列表
            SAMPLE_TEMPLATES = templates
            
            # 重新生成模板卡片
            template_cards = dbc.Row([
                dbc.Col(create_template_card(template), width=4, className="mb-4")
                for template in templates
            ])
            
            # 返回更新后的状态
            return False, template_cards, "模板保存成功！", {"display": "block"}
            
        except Exception as e:
            # 记录错误
            error_msg = f"保存模板错误: {str(e)}"
            print(error_msg)
            import traceback
            print(traceback.format_exc())
            return False, dash.no_update, error_msg, {"display": "block"}
    
    # 这里可以添加更多回调函数，如删除模板、过滤模板等
    
    return app 