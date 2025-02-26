"""
模拟服务模块

提供UI测试所需的假数据和功能，用于替代实际的后端服务。
"""
import numpy as np
import uuid
import json
from datetime import datetime

class MockPatternMatcherService:
    """模拟的形态匹配服务"""
    
    def __init__(self):
        """初始化模拟服务"""
        self.template_manager = MockTemplateManager()
    
    def get_pattern_templates(self):
        """获取所有形态模板"""
        return self.template_manager.get_all_templates()
    
    def get_pattern_template(self, pattern_id):
        """获取指定ID的形态模板"""
        return self.template_manager.get_template(pattern_id)
    
    def match_pattern(self, pattern_id=None, pattern_data=None, market_types=None, 
                    indicators=None, start_date=None, end_date=None, 
                    top_n=20, min_similarity=0.7):
        """模拟形态匹配功能"""
        # 生成一些模拟的匹配结果
        matches = []
        
        # 确保至少有一些结果
        stock_codes = ['000001', '600000', '601318', '000858', '600519', 
                      '000333', '601166', '600036', '300059', '002230']
        stock_names = ['平安银行', '浦发银行', '中国平安', '五粮液', '贵州茅台', 
                      '美的集团', '兴业银行', '招商银行', '东方财富', '科大讯飞']
        
        for i in range(min(len(stock_codes), top_n)):
            # 生成随机相似度，满足阈值条件
            similarity = max(min_similarity, min_similarity + 0.25 * np.random.random())
            
            match = {
                'code': stock_codes[i],
                'name': stock_names[i],
                'similarity': similarity,
                'match_details': {
                    'position': 10,
                    'length': 50,
                    'data': self._generate_random_pattern(50)
                }
            }
            matches.append(match)
        
        # 按相似度排序
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches
    
    def get_predefined_templates(self):
        """获取预定义形态模板"""
        return [t for t in self.template_manager.get_all_templates() if t.get('pattern_type') == 'predefined']
    
    def get_custom_templates(self):
        """获取自定义形态模板"""
        return [t for t in self.template_manager.get_all_templates() if t.get('pattern_type') == 'custom']
    
    def _generate_random_pattern(self, length=50):
        """生成随机形态数据"""
        return list(np.random.random(length) * 0.5 + 0.25)


class MockTemplateManager:
    """模拟的形态模板管理器"""
    
    def __init__(self):
        """初始化模拟模板管理器"""
        self.templates = self._create_sample_templates()
    
    def get_all_templates(self):
        """获取所有形态模板"""
        return self.templates
    
    def get_template(self, pattern_id):
        """获取指定ID的形态模板"""
        for template in self.templates:
            if template.get('pattern_id') == pattern_id:
                return template
        return None
    
    def _create_sample_templates(self):
        """创建一些示例模板"""
        templates = []
        
        # 创建预定义形态
        predefined_patterns = [
            {
                "pattern_id": "head_and_shoulders_top",
                "name": "头肩顶",
                "description": "头肩顶是一种反转形态，通常出现在上升趋势的顶部，预示着趋势即将反转为下降趋势。",
                "data": self._generate_head_and_shoulders_top(50),
                "tags": ["看跌", "高"],
                "pattern_type": "predefined"
            },
            {
                "pattern_id": "double_bottom",
                "name": "双底",
                "description": "双底是一种反转形态，通常出现在下降趋势的底部，由两个相近低点组成，预示着趋势反转。",
                "data": self._generate_double_bottom(50),
                "tags": ["看涨", "高"],
                "pattern_type": "predefined"
            },
            {
                "pattern_id": "ascending_triangle",
                "name": "上升三角形",
                "description": "上升三角形是一种延续形态，通常出现在上升趋势中，表示短暂整理后趋势将继续上升。",
                "data": self._generate_ascending_triangle(50),
                "tags": ["看涨", "中"],
                "pattern_type": "predefined"
            }
        ]
        
        # 创建一些自定义形态
        custom_patterns = [
            {
                "pattern_id": f"custom_{uuid.uuid4().hex[:8]}",
                "name": "自定义反弹形态",
                "description": "股价在下跌后出现的反弹形态，可能是短期反弹或趋势反转。",
                "data": self._generate_random_pattern(50),
                "tags": ["自定义", "反弹"],
                "pattern_type": "custom",
                "created_at": datetime.now().isoformat()
            },
            {
                "pattern_id": f"custom_{uuid.uuid4().hex[:8]}",
                "name": "自定义突破形态",
                "description": "股价突破阻力位或支撑位的形态，预示着新一轮行情的开始。",
                "data": self._generate_random_pattern(50),
                "tags": ["自定义", "突破"],
                "pattern_type": "custom",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        templates.extend(predefined_patterns)
        templates.extend(custom_patterns)
        
        return templates
    
    def _generate_random_pattern(self, length=50):
        """生成随机形态数据"""
        return list(np.random.random(length) * 0.5 + 0.25)
    
    def _generate_head_and_shoulders_top(self, length=50):
        """生成头肩顶形态"""
        x = np.linspace(0, 1, length)
        pattern = np.zeros(length)
        
        # 左肩: 0-20%
        left_shoulder_idx = int(length * 0.2)
        pattern[:left_shoulder_idx] = np.sin(np.linspace(0, np.pi, left_shoulder_idx)) * 0.7
        
        # 头部: 20-60%
        head_start = left_shoulder_idx
        head_end = int(length * 0.6)
        pattern[head_start:head_end] = np.sin(np.linspace(0, np.pi, head_end - head_start)) * 1.0
        
        # 右肩: 60-100%
        right_shoulder_idx = head_end
        pattern[right_shoulder_idx:] = np.sin(np.linspace(0, np.pi, length - right_shoulder_idx)) * 0.7
        
        # 归一化到[0,1]范围
        pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
        
        return list(pattern)
    
    def _generate_double_bottom(self, length=50):
        """生成双底形态"""
        x = np.linspace(0, 1, length)
        pattern = np.zeros(length)
        
        # 第一个底部
        bottom1_end = int(length * 0.4)
        pattern[:bottom1_end] = 1 - np.sin(np.linspace(0, np.pi, bottom1_end)) * 0.9
        
        # 中间回升
        middle_start = bottom1_end
        middle_end = int(length * 0.6)
        pattern[middle_start:middle_end] = 1 - np.sin(np.linspace(np.pi, 2*np.pi, middle_end-middle_start)) * 0.3 - 0.6
        
        # 第二个底部
        bottom2_start = middle_end
        pattern[bottom2_start:] = 1 - np.sin(np.linspace(0, np.pi, length-bottom2_start)) * 0.9
        
        # 归一化到[0,1]范围
        pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
        
        return list(pattern)
    
    def _generate_ascending_triangle(self, length=50):
        """生成上升三角形形态"""
        x = np.linspace(0, 1, length)
        pattern = np.zeros(length)
        
        # 上轨：水平线
        upper_line = 0.8 * np.ones(length)
        
        # 下轨：上升线
        lower_line = 0.2 + x * 0.6
        
        # 在上下轨之间生成波动
        for i in range(length):
            # 波动幅度随着时间推移逐渐减小
            amplitude = (1.0 - x[i]) * 0.8
            # 生成在上下轨之间的点，波动幅度逐渐减小
            wave = np.sin(x[i] * 10 * np.pi) * amplitude
            min_val = lower_line[i]
            max_val = upper_line[i]
            pattern[i] = (max_val + min_val) / 2 + wave * (max_val - min_val) / 2
        
        # 归一化到[0,1]范围
        pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
        
        return list(pattern)


# 实用函数
def normalize_series(series):
    """归一化序列数据到[0,1]范围"""
    series = np.array(series)
    min_val = np.min(series)
    max_val = np.max(series)
    
    if np.isclose(min_val, max_val):
        return np.zeros_like(series)
        
    normalized = (series - min_val) / (max_val - min_val)
    return normalized 