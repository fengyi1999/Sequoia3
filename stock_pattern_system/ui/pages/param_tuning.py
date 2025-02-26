"""
参数调优页面

提供交互式参数调优功能，测试不同参数组合的性能，优化DTW匹配效果。
"""
import os
import json
import uuid
import numpy as np
import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# 检查是否使用模拟服务
from stock_pattern_system.ui.pages.mock_services import normalize_series

# 使用模拟服务，而不是实际服务
# from stock_pattern_system.app.services.dtw_matcher import DTWMatcher
# from stock_pattern_system.app.services.dtw_param_tuner import DTWParamTuner, generate_test_data
# from stock_pattern_system.app.services.pattern_templates import PatternTemplateManager

# 创建一个简单的DTW参数调谐器，用于演示
class SimpleDTWParamTuner:
    """简单的DTW参数调谐器"""
    
    def __init__(self):
        """初始化调谐器"""
        pass
    
    def generate_test_data(self, data_type, length=50, noise_level=0.1):
        """生成测试数据"""
        x = np.linspace(0, 1, length)
        
        if data_type == 'sine':
            # 简单的正弦波
            pattern = np.sin(2 * np.pi * x)
        elif data_type == 'head_and_shoulders_top':
            # 头肩顶形态
            pattern = np.zeros(length)
            left_shoulder_idx = int(length * 0.2)
            pattern[:left_shoulder_idx] = np.sin(np.linspace(0, np.pi, left_shoulder_idx)) * 0.7
            head_start = left_shoulder_idx
            head_end = int(length * 0.6)
            pattern[head_start:head_end] = np.sin(np.linspace(0, np.pi, head_end - head_start)) * 1.0
            right_shoulder_idx = head_end
            pattern[right_shoulder_idx:] = np.sin(np.linspace(0, np.pi, length - right_shoulder_idx)) * 0.7
        elif data_type == 'double_bottom':
            # 双底形态
            pattern = 1 - np.sin(2 * np.pi * x)
        elif data_type == 'random':
            # 随机波动
            pattern = np.random.randn(length)
        else:
            pattern = np.zeros(length)
        
        # 添加噪声
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, length)
            pattern += noise
        
        # 归一化
        pattern = normalize_series(pattern)
        return pattern
    
    def test_parameters(self, template_pattern, test_pattern, window=None, use_fast_dtw=True, 
                      distance_metric='euclidean', early_stopping=False, early_stopping_threshold=0.5):
        """测试DTW参数的效果"""
        # 模拟计算DTW距离
        # 在实际应用中，这里应该调用实际的DTW实现
        
        # 创建示例变形路径 - 在实际应用中应计算真实路径
        path_length = min(len(template_pattern), len(test_pattern))
        path = []
        for i in range(path_length):
            # 简单的对角线路径，实际DTW路径会更复杂
            path.append((i, i))
        
        # 根据窗口大小调整相似度
        if window is not None and window != "None":
            # 假设较小的窗口会导致更快但可能不太准确的结果
            window_size = int(window)
            similarity = 0.8 + 0.1 * np.random.random() - 0.05 * window_size / path_length
        else:
            # 无窗口限制，理论上更准确但更慢
            similarity = 0.9 + 0.1 * np.random.random()
        
        # 模拟计算时间
        # 在实际应用中应测量真实计算时间
        if use_fast_dtw == "True":
            computation_time = 0.2 + 0.1 * np.random.random()  # 快速DTW更快
        else:
            computation_time = 0.5 + 0.3 * np.random.random()  # 标准DTW更慢
        
        # 应用提前终止的影响
        if early_stopping == "True":
            # 提前终止可能导致稍快的时间但可能影响准确性
            computation_time *= 0.8
            if np.random.random() < 0.3:  # 30%的概率略微降低准确性
                similarity *= 0.95
        
        return {
            'similarity': similarity,
            'computation_time': computation_time,
            'path': path
        }

# 创建调谐器实例
param_tuner = SimpleDTWParamTuner()

def create_param_tuning_layout():
    """创建参数调优页面布局"""
    
    # 窗口大小选项
    window_options = [
        {"label": "无窗口限制", "value": "None"},
        {"label": "5", "value": "5"},
        {"label": "10", "value": "10"},
        {"label": "15", "value": "15"},
        {"label": "20", "value": "20"},
        {"label": "30", "value": "30"},
    ]
    
    # 是否使用快速DTW选项
    fast_dtw_options = [
        {"label": "是", "value": "True"},
        {"label": "否", "value": "False"},
    ]
    
    # 是否启用提前终止选项
    early_stopping_options = [
        {"label": "是", "value": "True"},
        {"label": "否", "value": "False"},
    ]
    
    # 测试数据类型选项
    test_data_options = [
        {"label": "正弦波", "value": "sine"},
        {"label": "头肩顶形态", "value": "head_and_shoulders_top"},
        {"label": "双顶形态", "value": "double_top"},
        {"label": "三角形形态", "value": "ascending_triangle"},
    ]
    
    layout = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2("DTW参数调优", className="mb-4"),
                            html.P("测试不同参数组合的性能，优化DTW匹配效果，提高形态识别的准确性和速度。"),
                        ],
                        width=12,
                    )
                ]
            ),
            
            # 参数设置面板
            dbc.Row(
                [
                    # 参数设置
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.H4("参数设置", className="card-title")),
                                    dbc.CardBody(
                                        [
                                            # 测试数据设置
                                            html.H5("测试数据设置", className="mb-3"),
                                            
                                            # 测试数据类型
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("测试数据类型"),
                                                    dcc.Dropdown(
                                                        id="test-data-type-dropdown",
                                                        options=test_data_options,
                                                        value="sine",
                                                        placeholder="选择测试数据类型",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 数据长度
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("数据长度"),
                                                    dcc.Slider(
                                                        id="data-length-slider",
                                                        min=20,
                                                        max=200,
                                                        step=10,
                                                        marks={
                                                            20: "20",
                                                            50: "50",
                                                            100: "100",
                                                            150: "150",
                                                            200: "200",
                                                        },
                                                        value=100,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 噪声水平
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("噪声水平"),
                                                    dcc.Slider(
                                                        id="noise-level-slider",
                                                        min=0,
                                                        max=0.5,
                                                        step=0.05,
                                                        marks={
                                                            0: "0",
                                                            0.1: "0.1",
                                                            0.2: "0.2",
                                                            0.3: "0.3",
                                                            0.4: "0.4",
                                                            0.5: "0.5",
                                                        },
                                                        value=0.1,
                                                    ),
                                                ],
                                                className="mb-4",
                                            ),
                                            
                                            html.Hr(),
                                            
                                            # DTW参数设置
                                            html.H5("DTW参数设置", className="mb-3"),
                                            
                                            # 窗口大小
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("窗口大小"),
                                                    dcc.Dropdown(
                                                        id="window-size-dropdown",
                                                        options=window_options,
                                                        value="None",
                                                        placeholder="选择窗口大小",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 是否使用快速DTW
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("使用快速DTW"),
                                                    dcc.RadioItems(
                                                        id="fast-dtw-radio",
                                                        options=fast_dtw_options,
                                                        value="True",
                                                        labelStyle={"display": "inline-block", "margin-right": "10px"},
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 是否启用提前终止
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("启用提前终止"),
                                                    dcc.RadioItems(
                                                        id="early-stopping-radio",
                                                        options=early_stopping_options,
                                                        value="True",
                                                        labelStyle={"display": "inline-block", "margin-right": "10px"},
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 提前终止阈值
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("提前终止阈值"),
                                                    dcc.Slider(
                                                        id="early-stopping-threshold-slider",
                                                        min=0.2,
                                                        max=2.0,
                                                        step=0.2,
                                                        marks={
                                                            0.2: "0.2",
                                                            0.6: "0.6",
                                                            1.0: "1.0",
                                                            1.4: "1.4",
                                                            1.8: "1.8",
                                                        },
                                                        value=1.0,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            
                                            # 缓存大小
                                            dbc.FormGroup(
                                                [
                                                    dbc.Label("缓存大小"),
                                                    dcc.Slider(
                                                        id="cache-size-slider",
                                                        min=0,
                                                        max=2000,
                                                        step=200,
                                                        marks={
                                                            0: "0",
                                                            500: "500",
                                                            1000: "1000",
                                                            1500: "1500",
                                                            2000: "2000",
                                                        },
                                                        value=1000,
                                                    ),
                                                ],
                                                className="mb-4",
                                            ),
                                            
                                            # 测试按钮
                                            dbc.Button(
                                                "测试单个参数组合",
                                                id="test-params-button",
                                                color="primary",
                                                className="mr-2",
                                            ),
                                            dbc.Button(
                                                "执行网格搜索",
                                                id="grid-search-button",
                                                color="success",
                                                className="ml-2",
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow",
                            ),
                        ],
                        width=4,
                    ),
                    
                    # 测试数据预览和结果
                    dbc.Col(
                        [
                            # 测试数据预览
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.H4("测试数据预览", className="card-title")),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="test-data-preview-graph",
                                                figure=go.Figure().update_layout(
                                                    title="测试数据",
                                                    xaxis_title="时间",
                                                    yaxis_title="值",
                                                    height=300,
                                                ),
                                                config={"displayModeBar": False},
                                            ),
                                        ]
                                    ),
                                ],
                                className="shadow mb-4",
                            ),
                            
                            # 单个参数测试结果
                            html.Div(
                                [
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(html.H4("参数测试结果", className="card-title")),
                                            dbc.CardBody(
                                                [
                                                    # 结果指标
                                                    html.Div(
                                                        [
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Card(
                                                                            dbc.CardBody(
                                                                                [
                                                                                    html.H5("相似度", className="card-title"),
                                                                                    html.H3(id="similarity-value", className="text-primary"),
                                                                                ]
                                                                            ),
                                                                            className="text-center border-primary",
                                                                        ),
                                                                        width=4,
                                                                    ),
                                                                    dbc.Col(
                                                                        dbc.Card(
                                                                            dbc.CardBody(
                                                                                [
                                                                                    html.H5("计算时间", className="card-title"),
                                                                                    html.H3(id="computation-time", className="text-info"),
                                                                                ]
                                                                            ),
                                                                            className="text-center border-info",
                                                                        ),
                                                                        width=4,
                                                                    ),
                                                                    dbc.Col(
                                                                        dbc.Card(
                                                                            dbc.CardBody(
                                                                                [
                                                                                    html.H5("缓存命中率", className="card-title"),
                                                                                    html.H3(id="cache-hit-rate", className="text-success"),
                                                                                ]
                                                                            ),
                                                                            className="text-center border-success",
                                                                        ),
                                                                        width=4,
                                                                    ),
                                                                ],
                                                                className="mb-4",
                                                            ),
                                                            
                                                            # 对齐路径图
                                                            dcc.Graph(
                                                                id="warping-path-graph",
                                                                figure=go.Figure().update_layout(
                                                                    title="DTW对齐路径",
                                                                    xaxis_title="序列1",
                                                                    yaxis_title="序列2",
                                                                    height=300,
                                                                ),
                                                            ),
                                                        ],
                                                        id="single-param-results",
                                                        style={"display": "none"},
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="shadow",
                                    ),
                                ],
                                id="test-results-container",
                            ),
                        ],
                        width=8,
                    ),
                ],
                className="mb-4",
            ),
            
            # 网格搜索结果
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H3("网格搜索结果", className="mb-3"),
                                    
                                    # 结果表格
                                    dash_table.DataTable(
                                        id="grid-search-results-table",
                                        columns=[
                                            {"name": "窗口大小", "id": "window"},
                                            {"name": "快速DTW", "id": "use_fast_dtw"},
                                            {"name": "提前终止", "id": "early_stopping"},
                                            {"name": "终止阈值", "id": "early_stopping_threshold"},
                                            {"name": "缓存大小", "id": "cache_size"},
                                            {"name": "准确率", "id": "accuracy"},
                                            {"name": "计算时间", "id": "time"},
                                            {"name": "综合得分", "id": "combined_score"},
                                        ],
                                        data=[],
                                        sort_action="native",
                                        filter_action="native",
                                        style_table={"overflowX": "auto"},
                                        style_cell={
                                            "textAlign": "left",
                                            "padding": "10px",
                                        },
                                        style_header={
                                            "backgroundColor": "rgb(230, 230, 230)",
                                            "fontWeight": "bold",
                                        },
                                        style_data_conditional=[
                                            {
                                                "if": {"row_index": "odd"},
                                                "backgroundColor": "rgb(248, 248, 248)",
                                            },
                                            {
                                                "if": {"column_id": "combined_score", "filter_query": "{combined_score} = max({combined_score})"},
                                                "backgroundColor": "#baffba",
                                                "fontWeight": "bold",
                                            },
                                        ],
                                        page_size=10,
                                    ),
                                    
                                    # 结果可视化
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dcc.Graph(
                                                    id="param-comparison-graph",
                                                    figure=go.Figure().update_layout(
                                                        title="参数比较",
                                                        xaxis_title="参数值",
                                                        yaxis_title="性能指标",
                                                        height=400,
                                                    ),
                                                ),
                                                width=6,
                                            ),
                                            dbc.Col(
                                                dcc.Graph(
                                                    id="accuracy-time-scatter",
                                                    figure=go.Figure().update_layout(
                                                        title="准确率vs时间",
                                                        xaxis_title="计算时间",
                                                        yaxis_title="准确率",
                                                        height=400,
                                                    ),
                                                ),
                                                width=6,
                                            ),
                                        ],
                                        className="mt-4",
                                    ),
                                    
                                    # 推荐参数
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(html.H4("推荐参数", className="card-title")),
                                            dbc.CardBody(
                                                [
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                [
                                                                    html.H5("准确度优先", className="text-center"),
                                                                    html.Div(id="accuracy-params"),
                                                                ],
                                                                width=4,
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    html.H5("速度优先", className="text-center"),
                                                                    html.Div(id="speed-params"),
                                                                ],
                                                                width=4,
                                                            ),
                                                            dbc.Col(
                                                                [
                                                                    html.H5("平衡配置", className="text-center"),
                                                                    html.Div(id="balanced-params"),
                                                                ],
                                                                width=4,
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="mt-4 shadow",
                                    ),
                                ],
                                id="grid-search-results-container",
                                style={"display": "none"},
                            )
                        ],
                        width=12,
                    )
                ],
                className="mt-4",
            ),
            
            # 存储组件
            dcc.Store(id="test-data-store"),
            dcc.Store(id="test-results-store"),
            dcc.Store(id="grid-search-results-store"),
        ]
    )
    
    return layout

# 注册回调
def register_callbacks(app):
    """注册回调函数"""
    
    # 更新测试数据预览
    @app.callback(
        [
            Output("test-data-preview-graph", "figure"),
            Output("test-data-store", "data"),
        ],
        [
            Input("test-data-type-dropdown", "value"),
            Input("data-length-slider", "value"),
            Input("noise-level-slider", "value"),
        ],
    )
    def update_test_data_preview(data_type, data_length, noise_level):
        """更新测试数据预览"""
        # 生成测试数据
        if data_type == "sine":
            # 生成正弦波
            x = np.linspace(0, 4 * np.pi, data_length)
            original_series = np.sin(x)
            series_name = "正弦波"
        elif data_type == "head_and_shoulders_top":
            # 使用模拟数据生成
            original_series = param_tuner.generate_test_data("head_and_shoulders_top", data_length, noise_level=0)
            series_name = "头肩顶形态"
        elif data_type == "double_top":
            # 使用模拟数据生成
            original_series = param_tuner.generate_test_data("double_bottom", data_length, noise_level=0)
            series_name = "双顶形态"
        elif data_type == "ascending_triangle":
            # 使用模拟数据生成
            original_series = param_tuner.generate_test_data("ascending_triangle", data_length, noise_level=0)
            series_name = "上升三角形形态"
        else:
            # 默认使用正弦波
            x = np.linspace(0, 4 * np.pi, data_length)
            original_series = np.sin(x)
            series_name = "正弦波"
            
        # 添加噪声
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, size=data_length)
            noisy_series = original_series + noise
        else:
            noisy_series = original_series
            
        # 创建参考序列和测试序列
        reference_series = original_series
        test_series = noisy_series
        
        # 创建图表
        fig = go.Figure()
        
        # 添加原始序列
        fig.add_trace(go.Scatter(
            y=reference_series,
            mode='lines',
            name='参考序列'
        ))
        
        # 添加噪声序列
        fig.add_trace(go.Scatter(
            y=test_series,
            mode='lines',
            name='测试序列 (含噪声)'
        ))
        
        # 更新布局
        fig.update_layout(
            title=f"{series_name} 测试数据 (噪声水平: {noise_level})",
            xaxis_title="时间",
            yaxis_title="值",
            height=300,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 存储数据
        stored_data = {
            "reference_series": reference_series.tolist(),
            "test_series": test_series.tolist(),
            "data_type": data_type,
            "noise_level": noise_level
        }
        
        return fig, stored_data
    
    # 测试单个参数组合
    @app.callback(
        [
            Output("single-param-results", "style"),
            Output("similarity-value", "children"),
            Output("computation-time", "children"),
            Output("cache-hit-rate", "children"),
            Output("warping-path-graph", "figure"),
            Output("test-results-store", "data"),
        ],
        [Input("test-params-button", "n_clicks")],
        [
            State("test-data-store", "data"),
            State("window-size-dropdown", "value"),
            State("fast-dtw-radio", "value"),
            State("early-stopping-radio", "value"),
            State("early-stopping-threshold-slider", "value"),
            State("cache-size-slider", "value"),
        ],
    )
    def test_single_param_combination(n_clicks, test_data, window_size, fast_dtw, early_stopping, early_stopping_threshold, cache_size):
        """测试单个参数组合"""
        if not n_clicks or not test_data:
            return {"display": "none"}, "", "", "", go.Figure(), None
        
        # 解析参数
        window = None if window_size == "None" else int(window_size)
        use_fast_dtw = fast_dtw == "True"
        use_early_stopping = early_stopping == "True"
        
        # 获取测试数据
        reference_series = np.array(test_data["reference_series"])
        test_series = np.array(test_data["test_series"])
        
        # 使用我们的模拟参数测试函数
        result = param_tuner.test_parameters(
            reference_series, 
            test_series,
            window=window_size,
            use_fast_dtw=fast_dtw,
            early_stopping=early_stopping,
            early_stopping_threshold=early_stopping_threshold
        )
        
        # 提取结果
        similarity = result['similarity']
        computation_time = result['computation_time']
        path = result['path']
        
        # 模拟缓存命中率
        cache_hit_rate = 0.8 if cache_size > 0 else 0.0
        
        # 准备结果
        similarity_text = f"{similarity:.4f}"
        time_text = f"{computation_time*1000:.2f} ms"
        cache_text = f"{cache_hit_rate*100:.1f}%"
        
        # 创建DTW路径图
        fig = go.Figure()
        
        # 计算距离矩阵用于热图
        n, m = len(reference_series), len(test_series)
        distance_matrix = np.zeros((n, m))
        for i in range(n):
            for j in range(m):
                distance_matrix[i, j] = (reference_series[i] - test_series[j]) ** 2
                
        # 绘制距离矩阵热图
        fig.add_trace(go.Heatmap(
            z=distance_matrix,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="距离")
        ))
        
        # 提取路径坐标
        path_x = [p[1] for p in path]  # 第二个序列的索引作为x
        path_y = [p[0] for p in path]  # 第一个序列的索引作为y
        
        # 绘制DTW路径
        fig.add_trace(go.Scatter(
            x=path_x,
            y=path_y,
            mode="lines+markers",
            name="DTW路径",
            line=dict(color="red", width=2),
            marker=dict(color="red", size=4)
        ))
        
        # 更新布局
        fig.update_layout(
            title=f"DTW对齐路径 (相似度: {similarity:.4f})",
            xaxis_title="测试序列索引",
            yaxis_title="参考序列索引",
            height=400,
            showlegend=True
        )
        
        # 存储结果
        results = {
            "similarity": similarity,
            "computation_time": computation_time,
            "cache_hit_rate": cache_hit_rate,
            "params": {
                "window": window,
                "use_fast_dtw": use_fast_dtw,
                "early_stopping": use_early_stopping,
                "early_stopping_threshold": early_stopping_threshold,
                "cache_size": cache_size
            }
        }
        
        return {"display": "block"}, similarity_text, time_text, cache_text, fig, results
    
    # 执行网格搜索
    @app.callback(
        [
            Output("grid-search-results-container", "style"),
            Output("grid-search-results-table", "data"),
            Output("param-comparison-graph", "figure"),
            Output("accuracy-time-scatter", "figure"),
            Output("accuracy-params", "children"),
            Output("speed-params", "children"),
            Output("balanced-params", "children"),
            Output("grid-search-results-store", "data"),
        ],
        [Input("grid-search-button", "n_clicks")],
        [
            State("test-data-store", "data"),
            State("window-size-dropdown", "value"),
            State("fast-dtw-radio", "value"),
            State("early-stopping-radio", "value"),
            State("early-stopping-threshold-slider", "value"),
            State("cache-size-slider", "value"),
        ],
    )
    def execute_grid_search(n_clicks, test_data, window_size, fast_dtw, early_stopping, early_stopping_threshold, cache_size):
        """执行网格搜索"""
        if not n_clicks or not test_data:
            return {"display": "none"}, [], go.Figure(), go.Figure(), "", "", "", None
        
        # 创建参数网格
        param_grid = {
            "window": [None, 5, 10, 20],
            "use_fast_dtw": [True, False],
            "early_stopping": [True, False],
            "early_stopping_threshold": [0.5, 1.0, 1.5],
            "cache_size": [0, 500, 1000]
        }
        
        # 获取测试数据
        reference_series = np.array(test_data["reference_series"])
        
        # 模拟网格搜索结果
        results = []
        window_values = [None, 5, 10, 20]
        fastdtw_values = [True, False]
        
        # 生成一些模拟结果
        for window in window_values:
            for use_fast_dtw in fastdtw_values:
                for early_stop in [True, False]:
                    # 模拟精度 - 窗口越大，精度越高，但计算时间也越长
                    accuracy = 0.85 + 0.1 * np.random.random()
                    if window:
                        # 较小窗口可能降低精度
                        window_size_factor = min(1.0, window / 20)
                        accuracy *= 0.9 + 0.1 * window_size_factor
                        
                    # 模拟计算时间 - 窗口越大，计算时间越长
                    if use_fast_dtw:
                        time_base = 0.2  # 快速DTW基准时间
                    else:
                        time_base = 0.5  # 标准DTW基准时间
                        
                    # 窗口影响计算时间
                    if window:
                        time_factor = max(0.5, window / 20)
                    else:
                        time_factor = 1.5  # 无窗口限制计算更久
                    
                    computation_time = time_base * time_factor * (0.8 + 0.4 * np.random.random())
                    
                    # 如果使用提前终止，计算时间可能减少，但精度也可能下降
                    if early_stop:
                        computation_time *= 0.8
                        accuracy *= 0.95
                    
                    # 添加一些随机变化
                    accuracy += 0.05 * (np.random.random() - 0.5)
                    computation_time *= 0.8 + 0.4 * np.random.random()
                    
                    # 确保精度在合理范围内
                    accuracy = max(0.7, min(0.98, accuracy))
                    
                    result = {
                        "params": {
                            "window": window,
                            "use_fast_dtw": use_fast_dtw,
                            "early_stopping": early_stop,
                            "early_stopping_threshold": early_stopping_threshold,
                            "cache_size": cache_size
                        },
                        "accuracy": accuracy,
                        "time": computation_time
                    }
                    results.append(result)
        
        # 准备表格数据
        table_data = []
        for result in results:
            params = result["params"]
            # 计算综合得分 - 精度/时间
            combined_score = result["accuracy"] / (result["time"] + 0.001)
            
            table_data.append({
                "window": str(params.get("window")),
                "use_fast_dtw": str(params.get("use_fast_dtw")),
                "early_stopping": str(params.get("early_stopping")),
                "early_stopping_threshold": f"{params.get('early_stopping_threshold'):.1f}",
                "cache_size": str(params.get("cache_size")),
                "accuracy": f"{result.get('accuracy'):.4f}",
                "time": f"{result.get('time')*1000:.2f} ms",
                "combined_score": f"{combined_score:.2f}"
            })
        
        # 创建参数比较图
        param_fig = go.Figure()
        
        # 将结果按窗口大小分组
        window_groups = {}
        for result in results:
            window = result["params"].get("window")
            if window not in window_groups:
                window_groups[window] = []
            window_groups[window].append(result)
        
        # 计算每个窗口大小的平均准确率和时间
        window_values = []
        accuracy_values = []
        time_values = []
        
        for window, group in window_groups.items():
            window_values.append(str(window))
            accuracy_values.append(np.mean([r["accuracy"] for r in group]))
            time_values.append(np.mean([r["time"] for r in group]))
        
        # 添加准确率曲线
        param_fig.add_trace(go.Bar(
            x=window_values,
            y=accuracy_values,
            name="准确率",
            marker_color="blue",
            opacity=0.7
        ))
        
        # 添加时间曲线（使用次坐标轴）
        param_fig.add_trace(go.Scatter(
            x=window_values,
            y=time_values,
            name="计算时间(秒)",
            marker_color="red",
            mode="lines+markers",
            yaxis="y2"
        ))
        
        # 更新布局
        param_fig.update_layout(
            title="窗口大小参数比较",
            xaxis_title="窗口大小",
            yaxis_title="准确率",
            yaxis2=dict(
                title="计算时间(秒)",
                overlaying="y",
                side="right",
                showgrid=False
            ),
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 创建准确率vs时间散点图
        scatter_fig = px.scatter(
            x=[r["time"] for r in results],
            y=[r["accuracy"] for r in results],
            color=[str(r["params"].get("window")) for r in results],
            size=[1000/(r["time"]+0.001) for r in results],
            hover_data={
                "窗口大小": [str(r["params"].get("window")) for r in results],
                "快速DTW": [str(r["params"].get("use_fast_dtw")) for r in results],
                "提前终止": [str(r["params"].get("early_stopping")) for r in results],
                "准确率": [f"{r['accuracy']:.4f}" for r in results],
                "时间(ms)": [f"{r['time']*1000:.2f}" for r in results]
            }
        )
        
        scatter_fig.update_layout(
            title="准确率 vs 计算时间",
            xaxis_title="计算时间(秒)",
            yaxis_title="准确率",
            height=400,
            showlegend=True,
            legend_title="窗口大小"
        )
        
        # 获取推荐参数
        # 准确度优先 - 从结果中找出准确率最高的
        accuracy_sorted = sorted(results, key=lambda r: r["accuracy"], reverse=True)
        accuracy_params = accuracy_sorted[0]["params"] if accuracy_sorted else {}
        
        # 速度优先 - 从结果中找出计算时间最短的
        speed_sorted = sorted(results, key=lambda r: r["time"])
        speed_params = speed_sorted[0]["params"] if speed_sorted else {}
        
        # 平衡配置 - 综合得分最高的
        balanced_sorted = sorted(results, key=lambda r: r["accuracy"] / (r["time"] + 0.001), reverse=True)
        balanced_params = balanced_sorted[0]["params"] if balanced_sorted else {}
        
        # 创建参数显示
        def create_param_card(params):
            return html.Div([
                dbc.ListGroup([
                    dbc.ListGroupItem(f"窗口大小: {params.get('window')}"),
                    dbc.ListGroupItem(f"快速DTW: {params.get('use_fast_dtw')}"),
                    dbc.ListGroupItem(f"提前终止: {params.get('early_stopping')}"),
                    dbc.ListGroupItem(f"终止阈值: {params.get('early_stopping_threshold')}"),
                    dbc.ListGroupItem(f"缓存大小: {params.get('cache_size')}"),
                ], className="small")
            ])
        
        accuracy_card = create_param_card(accuracy_params)
        speed_card = create_param_card(speed_params)
        balanced_card = create_param_card(balanced_params)
        
        # 存储结果
        stored_results = {
            "results": results,
            "recommendations": {
                "accuracy": accuracy_params,
                "speed": speed_params,
                "balanced": balanced_params
            }
        }
        
        return {"display": "block"}, table_data, param_fig, scatter_fig, accuracy_card, speed_card, balanced_card, stored_results 