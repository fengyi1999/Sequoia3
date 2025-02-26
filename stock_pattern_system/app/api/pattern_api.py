"""
形态匹配API接口

提供形态匹配和管理的API
"""
import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path

from ..services.pattern_matcher import PatternMatcher
from ..models.pattern import PatternModel
from ..models.stock import StockModel

# 创建Blueprint
pattern_api = Blueprint('pattern_api', __name__)

# 初始化匹配服务
matcher = None

def get_matcher():
    """
    获取或初始化匹配服务实例
    
    Returns:
        PatternMatcher: 匹配服务实例
    """
    global matcher
    if matcher is None:
        # 创建缓存目录
        project_root = Path(__file__).parent.parent.parent
        cache_dir = os.path.join(project_root, 'data', 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        # 初始化匹配服务
        matcher = PatternMatcher(
            cache_dir=cache_dir,
            use_clustering=True,
            n_clusters=20
        )
        
        # 尝试训练聚类模型（如果之前没有训练过）
        matcher.train_clustering()
        
    return matcher

@pattern_api.route('/api/patterns', methods=['GET'])
def get_patterns():
    """获取所有形态模板"""
    try:
        pattern_model = PatternModel()
        patterns = pattern_model.get_patterns()
        
        return jsonify({
            'success': True,
            'patterns': patterns
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pattern_api.route('/api/patterns/<int:pattern_id>', methods=['GET'])
def get_pattern(pattern_id):
    """获取指定形态模板"""
    try:
        pattern_model = PatternModel()
        pattern = pattern_model.get_pattern(pattern_id)
        
        if not pattern:
            return jsonify({
                'success': False,
                'error': '形态不存在'
            }), 404
            
        return jsonify({
            'success': True,
            'pattern': pattern
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pattern_api.route('/api/patterns', methods=['POST'])
def create_pattern():
    """创建新形态模板"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
            
        required_fields = ['name', 'data']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必要字段: {field}'
                }), 400
        
        # 获取匹配服务
        matcher = get_matcher()
        
        # 保存形态并查找匹配
        pattern_id = matcher.save_pattern_and_matches(
            name=data['name'],
            pattern_data=data['data'],
            description=data.get('description'),
            indicator=data.get('indicator', 'close'),
            top_n=data.get('top_n', 50),
            threshold=data.get('threshold', 0.6)
        )
        
        if not pattern_id:
            return jsonify({
                'success': False,
                'error': '保存形态失败'
            }), 500
            
        # 获取新创建的形态
        pattern_model = PatternModel()
        pattern = pattern_model.get_pattern(pattern_id)
        
        return jsonify({
            'success': True,
            'pattern': pattern,
            'message': '形态创建成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pattern_api.route('/api/patterns/<int:pattern_id>', methods=['DELETE'])
def delete_pattern(pattern_id):
    """删除形态模板"""
    try:
        pattern_model = PatternModel()
        success = pattern_model.delete_pattern(pattern_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': '删除形态失败'
            }), 500
            
        return jsonify({
            'success': True,
            'message': '形态删除成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pattern_api.route('/api/patterns/<int:pattern_id>/matches', methods=['GET'])
def get_pattern_matches(pattern_id):
    """获取形态的匹配结果"""
    try:
        min_similarity = request.args.get('min_similarity', type=float, default=0.6)
        limit = request.args.get('limit', type=int, default=50)
        
        pattern_model = PatternModel()
        matches = pattern_model.get_match_results(
            pattern_id=pattern_id,
            limit=limit,
            min_similarity=min_similarity
        )
        
        return jsonify({
            'success': True,
            'matches': matches
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pattern_api.route('/api/match', methods=['POST'])
def match_pattern():
    """使用提供的形态进行匹配"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
            
        if 'pattern' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要字段: pattern'
            }), 400
        
        # 获取参数
        pattern_data = data['pattern']
        top_n = data.get('top_n', 20)
        threshold = data.get('threshold', 0.7)
        indicator = data.get('indicator', 'close')
        use_clustering = data.get('use_clustering')
        
        # 获取匹配服务
        matcher = get_matcher()
        
        # 进行匹配
        matches = matcher.find_pattern_matches(
            pattern_data=pattern_data,
            top_n=top_n,
            threshold=threshold,
            indicator=indicator,
            use_clustering=use_clustering
        )
        
        return jsonify({
            'success': True,
            'matches': matches
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pattern_api.route('/api/stock_data', methods=['GET'])
def get_stock_data():
    """获取股票数据"""
    try:
        stock_code = request.args.get('code')
        indicator = request.args.get('indicator', 'close')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not stock_code:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: code'
            }), 400
            
        # 获取股票数据
        stock_model = StockModel()
        data = stock_model.get_stock_history(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            indicators=[indicator] if indicator else None
        )
        
        # 转换为JSON友好格式
        result = {
            'stock_code': stock_code,
            'data': data.to_dict(orient='records') if not data.empty else []
        }
        
        return jsonify({
            'success': True,
            'stock_data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pattern_api.route('/api/stocks', methods=['GET'])
def get_stocks():
    """获取股票列表"""
    try:
        market_type = request.args.get('market_type')
        limit = request.args.get('limit', type=int, default=100)
        offset = request.args.get('offset', type=int, default=0)
        
        # 获取股票列表
        stock_model = StockModel()
        stocks = stock_model.get_stock_list(
            market_type=market_type,
            limit=limit,
            offset=offset
        )
        
        # 转换为list of dict
        result = [dict(stock) for stock in stocks]
        
        return jsonify({
            'success': True,
            'stocks': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pattern_api.route('/api/train_clustering', methods=['POST'])
def train_clustering():
    """重新训练聚类模型"""
    try:
        data = request.json or {}
        
        # 获取参数
        indicator = data.get('indicator', 'close')
        days = data.get('days', 60)
        force_retrain = data.get('force_retrain', False)
        
        # 获取匹配服务
        matcher = get_matcher()
        
        # 训练聚类模型
        success = matcher.train_clustering(
            indicator=indicator,
            days=days,
            force_retrain=force_retrain
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': '训练聚类模型失败'
            }), 500
            
        return jsonify({
            'success': True,
            'message': '聚类模型训练成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 