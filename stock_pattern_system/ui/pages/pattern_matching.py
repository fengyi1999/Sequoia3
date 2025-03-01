"""
形态匹配页面

提供形态匹配功能和结果展示。
"""
import os
import json
import uuid
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from pathlib import Path
import datetime
import random

# 导入数据获取模块
from stock_pattern_system.app.data_fetcher import get_stock_list, init_single_stock_data

# 根据环境变量决定使用真实服务还是模拟服务
USE_MOCK_SERVICES = os.environ.get("USE_MOCK_SERVICES", "0") == "1"

if USE_MOCK_SERVICES:
    # 使用模拟服务
    from stock_pattern_system.ui.pages.mock_services import MockPatternMatcherService, normalize_series
    matcher_service = MockPatternMatcherService()
    print("形态匹配页面：使用模拟服务")
else:
    # 使用真实服务
    from stock_pattern_system.app.services.pattern_matcher import PatternMatcherService
    from stock_pattern_system.app.services.pattern_templates import normalize_pattern as normalize_series
    matcher_service = PatternMatcherService()
    print("形态匹配页面：使用真实服务")

def create_pattern_matching_layout():
    """创建形态匹配页面布局"""
    # 获取预定义和自定义形态模板
    templates = matcher_service.get_pattern_templates()
    predefined_templates = [t for t in templates if t.get('pattern_type') == 'predefined']
    custom_templates = [t for t in templates if t.get('pattern_type') == 'custom']
    
    # 构建模板选项
    template_options = []
    
    if predefined_templates:
        predefined_group = [{"label": f"{t['name']}", "value": t['pattern_id']} for t in predefined_templates]
        template_options.append({"label": "预定义形态", "options": predefined_group})
    
    if custom_templates:
        custom_group = [{"label": f"{t['name']}", "value": t['pattern_id']} for t in custom_templates]
        template_options.append({"label": "自定义形态", "options": custom_group})
    
    # 如果没有模板，添加导入提示
    if not template_options:
        template_options = [{"label": "请先导入或创建形态模板", "value": "none", "disabled": True}]
    
    # 将选项格式转换为简单的列表，避免使用分组格式
    simplified_options = []
    for group in template_options:
        if "options" in group:
            simplified_options.extend(group["options"])
        else:
            simplified_options.append(group)
    
    # 市场类型选项
    market_options = [
        {"label": "主板", "value": "主板"},
        {"label": "创业板", "value": "创业板"},
        {"label": "科创板", "value": "科创板"},
    ]
    
    # 指标选项
    indicator_options = [
        {"label": "收盘价", "value": "close"},
        {"label": "开盘价", "value": "open"},
        {"label": "最高价", "value": "high"},
        {"label": "最低价", "value": "low"},
    ]
    
    layout = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("形态匹配", className="mb-4"),
                            html.P("选择形态模板并设置匹配参数，进行全市场股票形态匹配。"),
                        ],
                        width=12,
                    )
                ]
            ),
            
            # 主布局区域 - 使用三列布局：匹配参数、匹配结果、形态预览
            dbc.Row(
                [
                    # 参数设置面板 - 左侧
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.H4("匹配参数", className="card-title")),
                                    dbc.CardBody(
                                        [
                                            # 形态模板选择
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("形态模板"),
                                                            dcc.Dropdown(
                                                                id="pattern-template-dropdown",
                                                                options=simplified_options,
                                                                placeholder="选择形态模板",
                                                            ),
                                                        ]
                                                    )
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 市场类型选择
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("市场类型"),
                                                            dcc.Dropdown(
                                                                id="market-type-dropdown",
                                                                options=market_options,
                                                                value=["主板", "创业板"],
                                                                multi=True,
                                                                placeholder="选择市场类型",
                                                            ),
                                                        ]
                                                    )
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 指标选择
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("匹配指标"),
                                                            dcc.Dropdown(
                                                                id="indicator-dropdown",
                                                                options=indicator_options,
                                                                value="close",
                                                                placeholder="选择匹配指标",
                                                            ),
                                                        ]
                                                    )
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 日期范围选择
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("日期范围"),
                                                            dcc.DatePickerRange(
                                                                id="date-range-picker",
                                                                start_date_placeholder_text="开始日期",
                                                                end_date_placeholder_text="结束日期",
                                                                calendar_orientation="horizontal",
                                                            ),
                                                        ]
                                                    )
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 高级参数
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("相似度阈值"),
                                                            dcc.Slider(
                                                                id="similarity-threshold-slider",
                                                                min=0.5,
                                                                max=0.95,
                                                                step=0.05,
                                                                marks={
                                                                    0.5: "0.5",
                                                                    0.6: "0.6",
                                                                    0.7: "0.7",
                                                                    0.8: "0.8",
                                                                    0.9: "0.9",
                                                                    0.95: "0.95",
                                                                },
                                                                value=0.7,
                                                            ),
                                                        ]
                                                    )
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("返回结果数量"),
                                                            dcc.Slider(
                                                                id="top-n-slider",
                                                                min=5,
                                                                max=50,
                                                                step=5,
                                                                marks={
                                                                    5: "5",
                                                                    10: "10",
                                                                    20: "20",
                                                                    30: "30",
                                                                    40: "40",
                                                                    50: "50",
                                                                },
                                                                value=20,
                                                            ),
                                                        ]
                                                    )
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 匹配按钮
                                            dbc.Button(
                                                "开始匹配",
                                                id="start-matching-button",
                                                color="primary",
                                                className="mt-3",
                                            ),
                                            
                                            # 状态和进度显示
                                            html.Div(
                                                [
                                                    html.P(id="matching-status-text", className="mt-3"),
                                                    dbc.Progress(id="matching-progress-bar", value=0, className="mb-3", style={"display": "none"}),
                                                ],
                                                id="matching-status-container",
                                                style={"display": "none"}
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow h-100",
                            ),
                        ],
                        width=3,
                    ),
                    
                    # 匹配结果面板 - 中间
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.H4("匹配结果", className="card-title")),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="matching-results-info", className="mb-3"),
                                            
                                            # 匹配结果表格
                                            dash_table.DataTable(
                                                id="matching-results-table",
                                                columns=[
                                                    {"name": "排名", "id": "rank"},
                                                    {"name": "股票代码", "id": "code"},
                                                    {"name": "股票名称", "id": "name"},
                                                    {"name": "相似度", "id": "similarity"},
                                                ],
                                                data=[],
                                                style_table={"overflowX": "auto", "height": "calc(100% - 50px)"},
                                                style_cell={
                                                    "textAlign": "left",
                                                    "padding": "8px",
                                                },
                                                style_header={
                                                    "backgroundColor": "rgb(230, 230, 230)",
                                                    "fontWeight": "bold",
                                                },
                                                style_data_conditional=[
                                                    {
                                                        "if": {"row_index": "odd"},
                                                        "backgroundColor": "rgb(248, 248, 248)",
                                                    }
                                                ],
                                                page_size=10,
                                                row_selectable="single",
                                            ),
                                        ]
                                    ),
                                ],
                                id="matching-results-container",
                                className="shadow h-100",
                                style={"display": "none"},
                            ),
                            
                            # 形态预览卡片（默认显示）
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.H4("形态预览", className="card-title")),
                                    dbc.CardBody(
                                        [
                                            # 形态信息
                                            html.Div(
                                                [
                                                    html.H5(id="pattern-name", children="未选择形态"),
                                                    html.P(id="pattern-description", className="text-muted"),
                                                    html.Div(id="pattern-tags"),
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 形态图表
                                            dcc.Graph(
                                                id="pattern-preview-graph",
                                                figure=go.Figure().update_layout(
                                                    title="选择形态模板预览",
                                                    xaxis_title="时间",
                                                    yaxis_title="价格",
                                                    height=300,
                                                ),
                                                config={"displayModeBar": False},
                                            ),
                                        ]
                                    ),
                                ],
                                id="pattern-preview-container",
                                className="shadow h-100",
                            ),
                        ],
                        width=3,
                    ),
                    
                    # 形态比较和K线图 - 右侧
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H4("股票详情", className="card-title d-inline me-2"),
                                            dbc.Tabs(
                                                [
                                                    dbc.Tab(label="形态比较", tab_id="pattern-tab", label_style={"cursor": "pointer"}),
                                                    dbc.Tab(label="K线图", tab_id="kline-tab", label_style={"cursor": "pointer"}),
                                                ],
                                                id="chart-tabs",
                                                active_tab="pattern-tab",
                                                className="card-tabs ms-3"
                                            )
                                        ],
                                        className="d-flex align-items-center"
                                    ),
                                    dbc.CardBody(
                                        [
                                            # 统一图表展示区域
                                            dcc.Graph(
                                                id="combined-chart",
                                                figure=go.Figure().update_layout(
                                                    title="请先选择形态模板进行匹配",
                                                    xaxis_title="时间/日期",
                                                    yaxis_title="价格/相似度",
                                                    height=620,
                                                ),
                                                config={"displayModeBar": True},
                                                className="h-100"
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow h-100",
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="mb-4",
            ),
            
            # 存储组件
            dcc.Store(id="matching-results-store"),
            dcc.Store(id="selected-pattern-store"),
            dcc.Store(id="selected-stock-store"),
        ]
    )
    
    return layout

# 注册回调，在实际的应用中，这些回调会在app.py中注册
def register_callbacks(app):
    """注册回调函数"""
    
    # 选择形态模板时更新预览
    @app.callback(
        [
            Output("pattern-preview-graph", "figure"),
            Output("pattern-name", "children"),
            Output("pattern-description", "children"),
            Output("pattern-tags", "children"),
            Output("selected-pattern-store", "data"),
        ],
        [Input("pattern-template-dropdown", "value")],
    )
    def update_pattern_preview(pattern_id):
        """更新形态预览"""
        if not pattern_id:
            figure = go.Figure().update_layout(
                title="选择形态模板预览",
                xaxis_title="时间",
                yaxis_title="价格",
                height=300,
            )
            return figure, "未选择形态", "", "", None
        
        # 获取形态模板
        template = matcher_service.get_pattern_template(pattern_id)
        if not template:
            figure = go.Figure().update_layout(
                title="未找到形态模板",
                xaxis_title="时间",
                yaxis_title="价格",
                height=300,
            )
            return figure, "未找到形态", "", "", None
        
        # 创建预览图
        pattern_data = template.get("data", [])
        x = list(range(len(pattern_data)))
        
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=x, y=pattern_data, mode="lines", name=template["name"]))
        figure.update_layout(
            title=f"{template['name']} 预览",
            xaxis_title="时间",
            yaxis_title="归一化价格",
            height=300,
        )
        
        # 创建标签
        tags = template.get("tags", [])
        tag_elements = []
        for tag in tags:
            color = "primary"
            if "看涨" in tag:
                color = "success"
            elif "看跌" in tag:
                color = "danger"
            elif "高" in tag:
                color = "warning"
            
            tag_elements.append(dbc.Badge(tag, color=color, className="me-1 mb-1"))
        
        # 存储选中的形态
        stored_data = {
            "pattern_id": pattern_id,
            "name": template["name"],
            "data": pattern_data,
        }
        
        return figure, template["name"], template.get("description", ""), tag_elements, stored_data
    
    # 点击开始匹配按钮时执行匹配
    @app.callback(
        [
            Output("matching-results-store", "data"),
            Output("matching-results-container", "style"),
            Output("pattern-preview-container", "style"),
            Output("matching-results-info", "children"),
            Output("matching-results-table", "data"),
            Output("combined-chart", "figure"),
            Output("selected-stock-store", "data"),
            Output("chart-tabs", "active_tab"),
            # 添加状态和进度输出
            Output("matching-status-container", "style"),
            Output("matching-status-text", "children"),
            Output("matching-progress-bar", "style"),
            Output("matching-progress-bar", "value"),
        ],
        [Input("start-matching-button", "n_clicks")],
        [
            State("pattern-template-dropdown", "value"),
            State("market-type-dropdown", "value"),
            State("indicator-dropdown", "value"),
            State("date-range-picker", "start_date"),
            State("date-range-picker", "end_date"),
            State("similarity-threshold-slider", "value"),
            State("top-n-slider", "value"),
            State("selected-pattern-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def perform_pattern_matching(n_clicks, pattern_id, market_types, indicator, start_date, end_date, threshold, top_n, pattern_data):
        """执行形态匹配"""
        # 初始空图表
        empty_chart = go.Figure().update_layout(
            title="请选择形态模板进行匹配",
            xaxis_title="时间",
            yaxis_title="价格",
            height=620,
        )
        
        if not n_clicks:
            return (None, {"display": "none"}, {"display": "block"}, "", [], empty_chart, None, "pattern-tab",
                   {"display": "none"}, "", {"display": "none"}, 0)
        
        if not pattern_id:
            return (None, {"display": "none"}, {"display": "block"}, 
                   html.Div(["请先选择形态模板"], className="alert alert-warning"), 
                   [], empty_chart, None, "pattern-tab",
                   {"display": "none"}, "", {"display": "none"}, 0)
        
        # 显示状态容器和文本
        status_container_style = {"display": "block"}
        progress_bar_style = {"display": "block"}
        progress_value = 5
        
        # 检查日期参数，如果使用未来日期修正为合理日期
        if start_date and end_date:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            if end_date > today:
                end_date = today
                print(f"结束日期调整为今天: {end_date}")
            if start_date > today:
                # 将开始日期设为一年前
                start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
                print(f"开始日期调整为一年前: {start_date}")
        
        # 使用data_fetcher获取全A股市场股票列表
        progress_value = 10
        status_text = "正在获取全A股市场股票列表..."
        try:
            stock_list_df = get_stock_list()
            
            if stock_list_df.empty:
                return (None, {"display": "none"}, {"display": "block"}, 
                       html.Div(["无法获取股票列表，请检查网络连接"], className="alert alert-danger"), 
                       [], empty_chart, None, "pattern-tab",
                       {"display": "none"}, "", {"display": "none"}, 0)
            
            # 根据市场类型过滤股票列表
            if market_types and len(market_types) > 0:
                filtered_stocks = stock_list_df[stock_list_df['market_type'].isin(market_types)]
                # 如果过滤后股票数量过少（少于10只），使用全部股票
                if len(filtered_stocks) < 10:
                    print(f"警告：市场类型 {market_types} 过滤后只有 {len(filtered_stocks)} 只股票，将使用全部股票列表")
                    filtered_stocks = stock_list_df
            else:
                filtered_stocks = stock_list_df
            
            # 获取股票代码列表
            required_stocks = filtered_stocks['code'].tolist()
            print(f"将处理 {len(required_stocks)} 只股票 (全市场共 {len(stock_list_df)} 只)")
            
            # 查询最近交易日
            latest_trading_day = matcher_service.get_latest_trading_day()
            if latest_trading_day:
                print(f"系统检测到的最近交易日为: {latest_trading_day}")
                # 如果用户选择的结束日期晚于最近交易日，则使用最近交易日
                if end_date and end_date > latest_trading_day:
                    end_date = latest_trading_day
                    print(f"用户选择的结束日期 {end_date} 晚于最近交易日，调整为 {latest_trading_day}")
            
            try:
                # 获取数据库统计信息，了解当前数据情况
                db_stats = matcher_service.query_database_statistics()
                if "error" not in db_stats:
                    print(f"数据库统计: 共有 {db_stats['stock_count']} 只股票, {db_stats['record_count']} 条记录")
                    print(f"数据日期范围: {db_stats['earliest_date']} 到 {db_stats['latest_date']}")
                
                # 检查数据库是否包含所需数据 - 确保检查所有股票
                print(f"开始检查全部 {len(required_stocks)} 只股票数据完整性...")
                
                # 直接获取本地所有股票数据
                local_stocks = matcher_service.get_all_local_stocks(start_date, end_date)
                print(f"本地已有数据的股票数量: {len(local_stocks)} 只")
                
                # 计算缺失的股票列表
                missing_stocks = [code for code in required_stocks if code not in local_stocks]
                print(f"缺失的股票数量: {len(missing_stocks)} 只")
                
                # 是否满足完整性要求
                is_complete = len(missing_stocks) == 0
                
                if not is_complete:
                    # 显示状态信息
                    status_text = f"发现 {len(missing_stocks)} 只股票数据缺失，需要下载"
                    print(status_text)
                    progress_value = 20
                    
                    # 下载所有缺失的股票数据
                    total_missing = len(missing_stocks)
                    
                    if total_missing > 1000:
                        estimated_time = total_missing / 10  # 粗略估计时间（分钟）
                        status_text = f"需要下载 {total_missing} 只股票数据，预计需要 {estimated_time:.0f} 分钟..."
                    
                    # 开始下载所有缺失股票数据
                    success_count = 0
                    failure_count = 0
                    
                    # 处理分批下载
                    batch_size = 50  # 使用更大的批次以加快下载速度
                    total_batches = (total_missing + batch_size - 1) // batch_size
                    
                    print(f"开始分 {total_batches} 批下载 {total_missing} 只缺失股票数据")
                    
                    for i, stock_code in enumerate(missing_stocks):
                        try:
                            # 使用data_fetcher的初始化单只股票数据功能
                            if init_single_stock_data(stock_code, days=180):
                                success_count += 1
                            else:
                                failure_count += 1
                            
                            # 更新进度
                            batch_progress = min(80, 20 + 60 * (i + 1) / total_missing)
                            current_batch = i // batch_size + 1
                            
                            # 更新频率降低，减少日志信息量
                            if i % 20 == 0 or i == total_missing - 1:
                                status_text = f"正在下载股票数据... {i+1}/{total_missing} (批次:{current_batch}/{total_batches}, 成功: {success_count}, 失败: {failure_count})"
                                progress_value = batch_progress
                                print(f"下载进度: {i+1}/{total_missing} - {status_text}")
                        
                        except Exception as e:
                            print(f"下载股票 {stock_code} 数据失败: {e}")
                            failure_count += 1
                    
                    # 下载完成后，再次检查完整性
                    local_stocks_after = matcher_service.get_all_local_stocks(start_date, end_date)
                    missing_after = [code for code in required_stocks if code not in local_stocks_after]
                    
                    print(f"下载完成后再次检查 - 本地已有数据股票: {len(local_stocks_after)} 只, 仍缺失: {len(missing_after)} 只")
                    
                    if len(missing_after) > 0:
                        problem_percentage = len(missing_after) / len(required_stocks) * 100
                        if problem_percentage > 50:
                            status_text = f"警告：仍有 {len(missing_after)} 只股票 ({problem_percentage:.1f}%) 数据缺失，可能影响匹配结果"
                            print(f"严重警告：数据下载不完整 - {status_text}")
                        else:
                            status_text = f"注意：仍有 {len(missing_after)} 只股票数据缺失，但已可以进行匹配"
                    else:
                        status_text = f"数据下载完成，所有 {len(required_stocks)} 只股票数据已准备就绪"
                else:
                    status_text = f"数据完整性检查通过，所有 {len(required_stocks)} 只股票数据已准备就绪"
            except Exception as e:
                # 如果数据下载或检查过程出错，使用标准的check_data_completeness作为备用
                print(f"直接数据下载处理出错，回退到标准检查方法: {str(e)}")
                is_complete, total, with_data, missing = matcher_service.check_data_completeness(
                    market_types=market_types,
                    start_date=start_date,
                    end_date=end_date,
                    required_stocks=required_stocks
                )
        except Exception as e:
            # 处理获取股票列表或数据完整性检查过程中的错误
            error_message = f"数据准备阶段发生错误: {str(e)}"
            print(error_message)
            import traceback
            print(traceback.format_exc())
            
            return (None, {"display": "none"}, {"display": "block"}, 
                   html.Div([error_message], className="alert alert-danger"), 
                   [], empty_chart, None, "pattern-tab",
                   {"display": "none"}, "", {"display": "none"}, 0)
        
        # 进度更新
        progress_value = 80
        
        # 构建指标列表
        indicators = [indicator] if indicator else ["close"]
        
        # 执行匹配
        status_text = f"正在执行匹配，这可能需要一些时间...将匹配 {len(required_stocks)} 只股票"
        matches = matcher_service.match_pattern(
            pattern_id=pattern_id,
            market_types=market_types,
            indicators=indicators,
            start_date=start_date,
            end_date=end_date,
            top_n=top_n,
            min_similarity=threshold
        )
        
        # 匹配完成，更新状态
        status_text = "匹配完成!"
        progress_value = 100
        
        if not matches:
            return (None, {"display": "block"}, {"display": "none"}, 
                   html.Div(["未找到匹配结果"], className="alert alert-info"), 
                   [], empty_chart, None, "pattern-tab",
                   status_container_style, status_text, {"display": "none"}, progress_value)
        
        # 准备表格数据
        table_data = []
        for i, match in enumerate(matches):
            table_data.append({
                "rank": i + 1,
                "code": match["code"],
                "name": match["name"],
                "similarity": f"{match['similarity']:.4f}",
                "raw_similarity": match["similarity"],
            })
        
        # 准备存储结果
        stored_results = {"matches": matches}
        
        # 创建结果信息
        info = html.Div([
            html.P(f"共找到 {len(matches)} 个相似度大于 {threshold} 的匹配结果"),
        ])
        
        # 自动显示第一个匹配结果的K线图和比较图
        if matches and pattern_data:
            first_match = matches[0]
            
            # 存储选中的股票数据
            selected_stock = {
                "code": first_match["code"],
                "name": first_match["name"],
                "similarity": first_match["similarity"],
            }
            
            # 生成比较图
            comparison_fig = generate_comparison_figure(pattern_data, first_match)
            
            return (stored_results, {"display": "block"}, {"display": "none"}, 
                   info, table_data, comparison_fig, selected_stock, "pattern-tab",
                   status_container_style, status_text, {"display": "none"}, progress_value)
        
        return (stored_results, {"display": "block"}, {"display": "none"}, 
               info, table_data, empty_chart, None, "pattern-tab",
               status_container_style, status_text, {"display": "none"}, progress_value)
    
    # 选择匹配结果行时更新股票详情
    @app.callback(
        [
            Output("combined-chart", "figure", allow_duplicate=True),
            Output("selected-stock-store", "data", allow_duplicate=True),
        ],
        [Input("matching-results-table", "selected_rows")],
        [
            State("matching-results-table", "data"),
            State("matching-results-store", "data"),
            State("selected-pattern-store", "data"),
            State("chart-tabs", "active_tab"),
        ],
        prevent_initial_call=True,
    )
    def update_stock_details(selected_rows, table_data, results_data, pattern_data, active_tab):
        """更新股票详情"""
        # 初始空图表
        empty_chart = go.Figure().update_layout(
            title="请选择股票查看详情",
            xaxis_title="时间",
            yaxis_title="价格",
            height=620,
        )
        
        if not selected_rows or not results_data or not pattern_data:
            return empty_chart, None
        
        # 获取选中的匹配结果
        selected_idx = selected_rows[0]
        selected_match = results_data["matches"][selected_idx]
        
        # 存储选中的股票数据
        selected_stock = {
            "code": selected_match["code"],
            "name": selected_match["name"],
            "similarity": selected_match["similarity"],
        }
        
        # 根据当前活动标签页生成相应图表
        if active_tab == "pattern-tab":
            # 生成比较图
            figure = generate_comparison_figure(pattern_data, selected_match)
        else:
            # 生成K线图
            figure = generate_mock_kline(selected_match["code"], selected_match["name"])
            # 调整图表高度
            figure.update_layout(height=620)
        
        return figure, selected_stock
    
    # 切换图表标签页
    @app.callback(
        Output("combined-chart", "figure", allow_duplicate=True),
        [Input("chart-tabs", "active_tab")],
        [State("selected-stock-store", "data"), 
         State("selected-pattern-store", "data"),
         State("matching-results-store", "data")],
        prevent_initial_call=True,
    )
    def switch_chart_tab(active_tab, selected_stock, pattern_data, results_data):
        """根据标签页切换显示不同图表"""
        if not selected_stock or not pattern_data or not results_data:
            # 如果没有选中的股票或形态数据，显示空图表
            return go.Figure().update_layout(
                title="请先选择形态模板进行匹配",
                xaxis_title="时间",
                yaxis_title="价格",
                height=620,
            )
        
        # 在匹配结果中查找选中的股票
        selected_match = None
        for match in results_data.get("matches", []):
            if match["code"] == selected_stock["code"]:
                selected_match = match
                break
        
        if not selected_match:
            return go.Figure().update_layout(
                title="无法找到选中的股票数据",
                xaxis_title="时间",
                yaxis_title="价格",
                height=620,
            )
        
        # 根据当前活动标签页生成相应图表
        if active_tab == "pattern-tab":
            # 生成比较图
            figure = generate_comparison_figure(pattern_data, selected_match)
        else:
            # 生成K线图
            figure = generate_mock_kline(selected_match["code"], selected_match["name"])
            # 调整图表高度
            figure.update_layout(height=620)
        
        return figure

    # 添加用于更新进度条的回调函数
    @app.callback(
        [
            Output("matching-progress-bar", "value", allow_duplicate=True),
            Output("matching-status-text", "children", allow_duplicate=True),
        ],
        [Input("matching-status-container", "id")],
        [State("matching-progress-bar", "value")],
        prevent_initial_call=True,
        interval=1000  # 每秒更新一次
    )
    def update_progress(_, current_value):
        """模拟进度条更新，实际应用中应该使用WebSocket实时更新"""
        import time
        from dash import callback_context, no_update
        from dash.exceptions import PreventUpdate
        
        if current_value >= 100:
            raise PreventUpdate
            
        # 这里只是简单模拟进度更新，实际应该从全局状态或数据库获取进度
        # 由于Dash的限制，建议在实际应用中使用WebSocket或后台任务实现更精确的进度更新
        
        return no_update, no_update

# 辅助函数

def generate_comparison_figure(pattern_data, match_data):
    """生成形态比较图"""
    pattern_series = pattern_data["data"]
    match_series = match_data.get("match_details", {}).get("data", [])
    
    if len(match_series) > len(pattern_series):
        # 找到最佳匹配窗口
        position = match_data.get("match_details", {}).get("position", 0)
        length = match_data.get("match_details", {}).get("length", len(pattern_series))
        match_series = match_series[position:position + length]
    
    # 标准化匹配序列以便比较
    match_series = normalize_series(match_series)
    
    # 创建比较图表
    x_pattern = list(range(len(pattern_series)))
    x_match = list(range(len(match_series)))
    
    figure = go.Figure()
    
    # 添加形态模板曲线
    figure.add_trace(go.Scatter(
        x=x_pattern,
        y=pattern_series,
        mode="lines",
        name=f"{pattern_data['name']} (模板)",
        line=dict(color="blue", width=2),
    ))
    
    # 添加匹配结果曲线
    figure.add_trace(go.Scatter(
        x=x_match,
        y=match_series,
        mode="lines",
        name=f"{match_data['code']} ({match_data['name']})",
        line=dict(color="red", width=2),
    ))
    
    figure.update_layout(
        title=f"形态比较 - 相似度: {match_data['similarity']:.4f}",
        xaxis_title="时间",
        yaxis_title="归一化价格",
        height=620,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
    )
    
    return figure

def generate_mock_kline(stock_code, stock_name):
    """生成模拟K线图"""
    # 生成模拟K线数据（120个交易日）
    dates = pd.date_range(end=pd.Timestamp.now(), periods=120, freq='D')
    
    # 生成随机价格数据
    np.random.seed(int(stock_code[-4:]))  # 使用股票代码后4位作为随机种子，保证同一股票显示相同数据
    
    # 初始收盘价
    initial_price = np.random.uniform(20, 100) 
    
    # 波动范围
    volatility = np.random.uniform(0.01, 0.03)
    
    # 生成日涨跌幅
    daily_returns = np.random.normal(0.0005, volatility, size=len(dates))
    
    # 计算价格序列
    prices = initial_price * (1 + np.cumsum(daily_returns))
    
    # 生成OHLC数据
    high = prices * (1 + np.random.uniform(0.01, 0.03, size=len(dates)))
    low = prices * (1 - np.random.uniform(0.01, 0.03, size=len(dates)))
    open_prices = prices * (1 + np.random.normal(0, 0.01, size=len(dates)))
    
    # 确保high > low
    high = np.maximum(high, np.maximum(open_prices, prices))
    low = np.minimum(low, np.minimum(open_prices, prices))
    
    # 生成成交量
    volume = np.random.gamma(shape=2.0, scale=1000000, size=len(dates))
    volume = volume * (1 + 0.5 * np.abs(daily_returns))  # 涨跌幅较大时成交量增加
    
    # 创建K线图
    fig = go.Figure()
    
    # 添加K线
    fig.add_trace(go.Candlestick(
        x=dates,
        open=open_prices,
        high=high,
        low=low,
        close=prices,
        name='K线'
    ))
    
    # 添加成交量柱状图（使用次坐标轴）
    fig.add_trace(go.Bar(
        x=dates,
        y=volume,
        name='成交量',
        marker_color='rgba(0,0,255,0.3)',
        yaxis='y2'
    ))
    
    # 更新布局
    fig.update_layout(
        title=f"{stock_code} {stock_name} - K线图",
        xaxis_title="日期",
        yaxis_title="价格",
        yaxis2=dict(
            title="成交量",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        height=620,
        xaxis_rangeslider_visible=False,  # 隐藏底部的范围滑块
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
    )
    
    return fig

# 新增辅助函数

def show_database_statistics():
    """展示数据库统计信息"""
    if not matcher_service:
        return "匹配服务未初始化"
        
    stats = matcher_service.query_database_statistics()
    if "error" in stats:
        return f"获取数据库统计信息出错: {stats['error']}"
    
    # 生成统计报告
    report = []
    report.append(f"数据库统计信息 (生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    report.append(f"总股票数: {stats['stock_count']} 只")
    report.append(f"总记录数: {stats['record_count']} 条")
    report.append(f"数据日期范围: {stats['earliest_date']} 至 {stats['latest_date']}")
    
    # 股票数据统计
    report.append("\n拥有最多数据的股票:")
    for i, stock in enumerate(stats.get('top_stocks', [])):
        report.append(f"{i+1}. {stock['stock_code']}: {stock['record_count']}条记录 ({stock['earliest_date']} - {stock['latest_date']})")
    
    # 最近日期数据覆盖情况
    report.append("\n最近30个交易日数据覆盖情况:")
    for date_info in stats.get('recent_dates', []):
        report.append(f"{date_info['trade_date']}: {date_info['stock_count']}只股票")
    
    return "\n".join(report)

def query_stock_info(stock_code, start_date=None, end_date=None):
    """查询特定股票的数据信息"""
    if not matcher_service:
        return "匹配服务未初始化"
        
    # 获取最近交易日
    latest_trading_day = matcher_service.get_latest_trading_day()
    
    # 如果未指定结束日期，使用最近交易日
    if not end_date:
        end_date = latest_trading_day
    
    # 如果未指定开始日期，使用结束日期前60天
    if not start_date:
        start_date = (datetime.datetime.strptime(end_date, "%Y-%m-%d") - 
                     datetime.timedelta(days=60)).strftime("%Y-%m-%d")
    
    # 查询股票数据
    data = matcher_service.query_stock_data(
        stock_codes=stock_code,
        start_date=start_date,
        end_date=end_date,
        output_format="dataframe"
    )
    
    if data is None or len(data) == 0:
        return f"未找到股票 {stock_code} 的数据"
    
    # 返回数据统计信息
    info = []
    info.append(f"股票 {stock_code} 数据统计 (查询范围: {start_date} 至 {end_date})")
    info.append(f"找到 {len(data)} 条记录")
    
    if len(data) > 0:
        info.append(f"日期范围: {data['trade_date'].min()} 至 {data['trade_date'].max()}")
        
        # 如果有价格数据，计算统计信息
        if 'close' in data.columns:
            info.append(f"价格范围: {data['close'].min():.2f} - {data['close'].max():.2f}")
            info.append(f"平均价格: {data['close'].mean():.2f}")
            info.append(f"价格变化: {(data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100:.2f}%")
    
    return "\n".join(info) 