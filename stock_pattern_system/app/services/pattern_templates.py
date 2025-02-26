"""
股票形态模板库模块

提供常见股票技术形态模板和用户自定义形态支持。
包含预定义的经典股票形态，如头肩顶、头肩底、双顶、双底等。
"""
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 默认形态模板文件
DEFAULT_TEMPLATES_FILE = os.path.join(PROJECT_ROOT, "data", "pattern_templates.json")

# 常见股票技术形态生成函数
def generate_head_and_shoulders_top(length=50, noise_level=0.05):
    """
    生成头肩顶形态
    头肩顶是一种反转形态，通常出现在上升趋势的顶部，预示着趋势即将反转为下降趋势。

    Args:
        length (int): 形态长度
        noise_level (float): 噪声水平，用于增加随机性

    Returns:
        numpy.ndarray: 生成的形态数据
    """
    x = np.linspace(0, 1, length)
    pattern = np.zeros(length)
    
    # 生成基础形态
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
    
    # 添加随机噪声
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, length)
        pattern += noise
    
    # 归一化到[0,1]范围
    pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
    
    return pattern

def generate_head_and_shoulders_bottom(length=50, noise_level=0.05):
    """
    生成头肩底形态
    头肩底是一种反转形态，通常出现在下降趋势的底部，预示着趋势即将反转为上升趋势。

    Args:
        length (int): 形态长度
        noise_level (float): 噪声水平，用于增加随机性

    Returns:
        numpy.ndarray: 生成的形态数据
    """
    # 生成头肩顶并翻转
    pattern = 1 - generate_head_and_shoulders_top(length, noise_level)
    return pattern

def generate_double_top(length=50, noise_level=0.05):
    """
    生成双顶形态
    双顶是一种反转形态，通常出现在上升趋势的顶部，由两个相近高点组成，预示着趋势反转。

    Args:
        length (int): 形态长度
        noise_level (float): 噪声水平，用于增加随机性

    Returns:
        numpy.ndarray: 生成的形态数据
    """
    x = np.linspace(0, 1, length)
    pattern = np.zeros(length)
    
    # 第一个顶部: 0-40%
    top1_end = int(length * 0.4)
    pattern[:top1_end] = np.sin(np.linspace(0, np.pi, top1_end)) * 0.9
    
    # 中间回调: 40-60%
    middle_start = top1_end
    middle_end = int(length * 0.6)
    pattern[middle_start:middle_end] = np.sin(np.linspace(np.pi, 2*np.pi, middle_end-middle_start)) * 0.3 + 0.6
    
    # 第二个顶部: 60-100%
    second_top_start = middle_end
    pattern[second_top_start:] = np.sin(np.linspace(0, np.pi, length-second_top_start)) * 0.9
    
    # 添加随机噪声
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, length)
        pattern += noise
    
    # 归一化到[0,1]范围
    pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
    
    return pattern

def generate_double_bottom(length=50, noise_level=0.05):
    """
    生成双底形态
    双底是一种反转形态，通常出现在下降趋势的底部，由两个相近低点组成，预示着趋势反转。

    Args:
        length (int): 形态长度
        noise_level (float): 噪声水平，用于增加随机性

    Returns:
        numpy.ndarray: 生成的形态数据
    """
    # 生成双顶并翻转
    pattern = 1 - generate_double_top(length, noise_level)
    return pattern

def generate_ascending_triangle(length=50, noise_level=0.05):
    """
    生成上升三角形形态
    上升三角形是一种延续形态，通常出现在上升趋势中，表示短暂整理后趋势将继续上升。

    Args:
        length (int): 形态长度
        noise_level (float): 噪声水平，用于增加随机性

    Returns:
        numpy.ndarray: 生成的形态数据
    """
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
    
    # 添加随机噪声
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, length)
        pattern += noise
    
    # 归一化到[0,1]范围
    pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
    
    return pattern

def generate_descending_triangle(length=50, noise_level=0.05):
    """
    生成下降三角形形态
    下降三角形是一种延续形态，通常出现在下降趋势中，表示短暂整理后趋势将继续下降。

    Args:
        length (int): 形态长度
        noise_level (float): 噪声水平，用于增加随机性

    Returns:
        numpy.ndarray: 生成的形态数据
    """
    x = np.linspace(0, 1, length)
    pattern = np.zeros(length)
    
    # 下轨：水平线
    lower_line = 0.2 * np.ones(length)
    
    # 上轨：下降线
    upper_line = 0.8 - x * 0.6
    
    # 在上下轨之间生成波动
    for i in range(length):
        # 波动幅度随着时间推移逐渐减小
        amplitude = (1.0 - x[i]) * 0.8
        # 生成在上下轨之间的点，波动幅度逐渐减小
        wave = np.sin(x[i] * 10 * np.pi) * amplitude
        min_val = lower_line[i]
        max_val = upper_line[i]
        pattern[i] = (max_val + min_val) / 2 + wave * (max_val - min_val) / 2
    
    # 添加随机噪声
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, length)
        pattern += noise
    
    # 归一化到[0,1]范围
    pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
    
    return pattern

def generate_flag(length=50, uptrend=True, noise_level=0.05):
    """
    生成旗形形态
    旗形是一种短期整理形态，通常出现在强劲趋势中，表示短暂休整后趋势将继续。

    Args:
        length (int): 形态长度
        uptrend (bool): 是否为上升趋势
        noise_level (float): 噪声水平，用于增加随机性

    Returns:
        numpy.ndarray: 生成的形态数据
    """
    x = np.linspace(0, 1, length)
    pattern = np.zeros(length)
    
    # 前部分：趋势线
    trend_part = int(length * 0.3)
    if uptrend:
        pattern[:trend_part] = 0.2 + x[:trend_part] * 0.6
    else:
        pattern[:trend_part] = 0.8 - x[:trend_part] * 0.6
    
    # 旗形部分：小幅度震荡回调
    flag_start = trend_part
    if uptrend:
        base_line = 0.8 - np.linspace(0, 0.2, length - flag_start)
        for i in range(flag_start, length):
            idx = i - flag_start
            pattern[i] = base_line[idx] + np.sin(idx * 0.8) * 0.05
    else:
        base_line = 0.2 + np.linspace(0, 0.2, length - flag_start)
        for i in range(flag_start, length):
            idx = i - flag_start
            pattern[i] = base_line[idx] + np.sin(idx * 0.8) * 0.05
    
    # 添加随机噪声
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, length)
        pattern += noise
    
    # 归一化到[0,1]范围
    pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
    
    return pattern

def generate_cup_and_handle(length=50, noise_level=0.05):
    """
    生成杯柄形态
    杯柄形态是一种延续形态，通常出现在上升趋势中，表示短暂回调后趋势将继续上升。

    Args:
        length (int): 形态长度
        noise_level (float): 噪声水平，用于增加随机性

    Returns:
        numpy.ndarray: 生成的形态数据
    """
    x = np.linspace(0, 1, length)
    pattern = np.zeros(length)
    
    # 杯部分：0-70%
    cup_end = int(length * 0.7)
    # 使用U形曲线
    cup_x = np.linspace(-np.pi/2, np.pi/2, cup_end)
    pattern[:cup_end] = 0.5 + 0.5 * np.cos(cup_x)
    
    # 柄部分：70-100%
    handle_start = cup_end
    # 小幅回调然后上升
    handle_x = np.linspace(0, np.pi, length - handle_start)
    handle_pattern = 0.8 - 0.2 * np.sin(handle_x)
    pattern[handle_start:] = handle_pattern
    
    # 添加随机噪声
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, length)
        pattern += noise
    
    # 归一化到[0,1]范围
    pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
    
    return pattern

def generate_wedge(length=50, rising=True, noise_level=0.05):
    """
    生成楔形形态
    楔形形态是一种反转形态，上升楔形通常出现在上升趋势末期，下降楔形通常出现在下降趋势末期。

    Args:
        length (int): 形态长度
        rising (bool): 是否为上升楔形
        noise_level (float): 噪声水平，用于增加随机性

    Returns:
        numpy.ndarray: 生成的形态数据
    """
    x = np.linspace(0, 1, length)
    pattern = np.zeros(length)
    
    if rising:
        # 上升楔形：两条上升线，但上轨的斜率小于下轨
        upper_line = 0.3 + x * 0.4
        lower_line = 0.1 + x * 0.7
    else:
        # 下降楔形：两条下降线，但下轨的斜率小于上轨
        upper_line = 0.9 - x * 0.7
        lower_line = 0.7 - x * 0.4
    
    # 在上下轨之间生成波动
    for i in range(length):
        wave = np.sin(x[i] * 8 * np.pi)
        min_val = lower_line[i]
        max_val = upper_line[i]
        pattern[i] = (max_val + min_val) / 2 + wave * (max_val - min_val) / 3
    
    # 添加随机噪声
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, length)
        pattern += noise
    
    # 归一化到[0,1]范围
    pattern = (pattern - np.min(pattern)) / (np.max(pattern) - np.min(pattern))
    
    return pattern

# 预定义形态字典
PATTERN_GENERATORS = {
    "head_and_shoulders_top": {
        "function": generate_head_and_shoulders_top,
        "name": "头肩顶",
        "description": "头肩顶是一种反转形态，通常出现在上升趋势的顶部，预示着趋势即将反转为下降趋势。",
        "trend_indication": "看跌",
        "reliability": "高"
    },
    "head_and_shoulders_bottom": {
        "function": generate_head_and_shoulders_bottom,
        "name": "头肩底",
        "description": "头肩底是一种反转形态，通常出现在下降趋势的底部，预示着趋势即将反转为上升趋势。",
        "trend_indication": "看涨",
        "reliability": "高"
    },
    "double_top": {
        "function": generate_double_top,
        "name": "双顶",
        "description": "双顶是一种反转形态，通常出现在上升趋势的顶部，由两个相近高点组成，预示着趋势反转。",
        "trend_indication": "看跌",
        "reliability": "高"
    },
    "double_bottom": {
        "function": generate_double_bottom,
        "name": "双底",
        "description": "双底是一种反转形态，通常出现在下降趋势的底部，由两个相近低点组成，预示着趋势反转。",
        "trend_indication": "看涨",
        "reliability": "高"
    },
    "ascending_triangle": {
        "function": generate_ascending_triangle,
        "name": "上升三角形",
        "description": "上升三角形是一种延续形态，通常出现在上升趋势中，表示短暂整理后趋势将继续上升。",
        "trend_indication": "看涨",
        "reliability": "中"
    },
    "descending_triangle": {
        "function": generate_descending_triangle,
        "name": "下降三角形",
        "description": "下降三角形是一种延续形态，通常出现在下降趋势中，表示短暂整理后趋势将继续下降。",
        "trend_indication": "看跌",
        "reliability": "中"
    },
    "bull_flag": {
        "function": lambda length=50, noise_level=0.05: generate_flag(length, True, noise_level),
        "name": "牛旗形",
        "description": "牛旗形是一种短期整理形态，通常出现在上升趋势中，表示短暂休整后趋势将继续上升。",
        "trend_indication": "看涨",
        "reliability": "中"
    },
    "bear_flag": {
        "function": lambda length=50, noise_level=0.05: generate_flag(length, False, noise_level),
        "name": "熊旗形",
        "description": "熊旗形是一种短期整理形态，通常出现在下降趋势中，表示短暂休整后趋势将继续下降。",
        "trend_indication": "看跌",
        "reliability": "中"
    },
    "cup_and_handle": {
        "function": generate_cup_and_handle,
        "name": "杯柄形态",
        "description": "杯柄形态是一种延续形态，通常出现在上升趋势中，表示短暂回调后趋势将继续上升。",
        "trend_indication": "看涨",
        "reliability": "高"
    },
    "rising_wedge": {
        "function": lambda length=50, noise_level=0.05: generate_wedge(length, True, noise_level),
        "name": "上升楔形",
        "description": "上升楔形通常出现在上升趋势末期，是一种反转形态，预示着趋势即将反转为下降趋势。",
        "trend_indication": "看跌",
        "reliability": "中"
    },
    "falling_wedge": {
        "function": lambda length=50, noise_level=0.05: generate_wedge(length, False, noise_level),
        "name": "下降楔形",
        "description": "下降楔形通常出现在下降趋势末期，是一种反转形态，预示着趋势即将反转为上升趋势。",
        "trend_indication": "看涨",
        "reliability": "中"
    }
}

class PatternTemplateManager:
    """形态模板管理器，提供形态模板的加载、保存和管理功能"""
    
    def __init__(self, templates_file=None):
        """
        初始化形态模板管理器
        
        Args:
            templates_file (str, optional): 形态模板文件路径，默认使用DEFAULT_TEMPLATES_FILE
        """
        self.templates_file = templates_file or DEFAULT_TEMPLATES_FILE
        self.templates = []
        self._ensure_template_file()
        self.load_templates()
    
    def _ensure_template_file(self):
        """确保模板文件和目录存在"""
        templates_dir = os.path.dirname(self.templates_file)
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir, exist_ok=True)
        
        # 如果文件不存在，创建一个空的模板文件
        if not os.path.exists(self.templates_file):
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
    
    def load_templates(self):
        """加载形态模板"""
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.templates = []
    
    def save_templates(self):
        """保存形态模板"""
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, ensure_ascii=False, indent=2)
    
    def get_templates(self):
        """获取所有形态模板"""
        return self.templates
    
    def get_all_templates(self):
        """获取所有形态模板（get_templates的别名）"""
        return self.get_templates()
    
    def get_template(self, pattern_id):
        """
        获取指定ID的形态模板
        
        Args:
            pattern_id (str): 形态ID
            
        Returns:
            dict: 形态模板，如果不存在返回None
        """
        for template in self.templates:
            if template.get('pattern_id') == pattern_id:
                return template
        return None
    
    def add_template(self, name, data, description=None, tags=None, pattern_type=None):
        """
        添加形态模板
        
        Args:
            name (str): 形态名称
            data (list): 形态数据
            description (str, optional): 形态描述
            tags (list, optional): 标签列表
            pattern_type (str, optional): 形态类型
            
        Returns:
            str: 新添加的形态模板ID
        """
        # 生成唯一ID
        pattern_id = f"pattern_{len(self.templates) + 1}_{int(datetime.now().timestamp())}"
        
        # 创建模板
        template = {
            "pattern_id": pattern_id,
            "name": name,
            "description": description,
            "data": data,
            "tags": tags or [],
            "pattern_type": pattern_type,
            "created_at": datetime.now().isoformat()
        }
        
        # 添加到模板列表
        self.templates.append(template)
        
        # 保存模板
        self.save_templates()
        
        return pattern_id
    
    def update_template(self, pattern_id, **kwargs):
        """
        更新形态模板
        
        Args:
            pattern_id (str): 形态ID
            **kwargs: 要更新的字段
            
        Returns:
            bool: 是否更新成功
        """
        for i, template in enumerate(self.templates):
            if template.get('pattern_id') == pattern_id:
                # 更新字段
                for key, value in kwargs.items():
                    template[key] = value
                
                # 更新最后修改时间
                template['updated_at'] = datetime.now().isoformat()
                
                # 更新模板列表
                self.templates[i] = template
                
                # 保存模板
                self.save_templates()
                
                return True
        
        return False
    
    def delete_template(self, pattern_id):
        """
        删除形态模板
        
        Args:
            pattern_id (str): 形态ID
            
        Returns:
            bool: 是否删除成功
        """
        for i, template in enumerate(self.templates):
            if template.get('pattern_id') == pattern_id:
                # 从模板列表中删除
                del self.templates[i]
                
                # 保存模板
                self.save_templates()
                
                return True
        
        return False
    
    def import_predefined_templates(self, length=50, noise_level=0.05):
        """
        导入预定义形态模板
        
        Args:
            length (int): 形态长度
            noise_level (float): 噪声水平
            
        Returns:
            list: 导入的形态模板ID列表
        """
        imported_ids = []
        
        for pattern_id, pattern_info in PATTERN_GENERATORS.items():
            # 检查形态是否已存在
            existing_template = self.get_template(pattern_id)
            if existing_template:
                continue
            
            # 生成形态数据
            pattern_data = pattern_info['function'](length, noise_level)
            
            # 添加到模板
            template_id = self.add_template(
                name=pattern_info['name'],
                data=pattern_data.tolist(),
                description=pattern_info['description'],
                tags=[pattern_info['trend_indication'], pattern_info['reliability']],
                pattern_type="predefined"
            )
            
            imported_ids.append(template_id)
        
        return imported_ids
    
    def create_custom_template(self, name, data, description=None, tags=None):
        """
        创建自定义形态模板
        
        Args:
            name (str): 形态名称
            data (list): 形态数据
            description (str, optional): 形态描述
            tags (list, optional): 标签列表
            
        Returns:
            str: 新创建的形态模板ID
        """
        return self.add_template(
            name=name,
            data=data,
            description=description,
            tags=tags,
            pattern_type="custom"
        )
    
    def get_predefined_templates(self):
        """
        获取所有预定义形态模板
        
        Returns:
            list: 预定义形态模板列表
        """
        return [t for t in self.templates if t.get('pattern_type') == 'predefined']
    
    def get_custom_templates(self):
        """
        获取所有自定义形态模板
        
        Returns:
            list: 自定义形态模板列表
        """
        return [t for t in self.templates if t.get('pattern_type') == 'custom']

# 辅助函数
def normalize_pattern(pattern):
    """
    归一化形态数据到[0,1]范围
    
    Args:
        pattern (list or numpy.ndarray): 输入形态数据
        
    Returns:
        numpy.ndarray: 归一化后的形态数据
    """
    pattern = np.asarray(pattern, dtype=np.float64)
    min_val = np.min(pattern)
    max_val = np.max(pattern)
    
    if np.isclose(min_val, max_val):
        return np.zeros_like(pattern)
        
    normalized = (pattern - min_val) / (max_val - min_val)
    return normalized

def extract_pattern_from_data(data, start_idx, end_idx, column='close'):
    """
    从股票数据中提取形态
    
    Args:
        data (pandas.DataFrame): 股票数据
        start_idx (int): 开始索引
        end_idx (int): 结束索引
        column (str): 使用的列名
        
    Returns:
        numpy.ndarray: 提取的形态数据
    """
    if column not in data.columns:
        raise ValueError(f"列名 {column} 不存在于数据中")
        
    # 提取数据
    pattern = data.loc[start_idx:end_idx, column].values
    
    # 归一化
    return normalize_pattern(pattern)

def create_pattern_template_from_stock(stock_data, start_date, end_date, name, description=None, tags=None, column='close'):
    """
    从股票数据创建形态模板
    
    Args:
        stock_data (pandas.DataFrame): 股票数据
        start_date (str): 开始日期
        end_date (str): 结束日期
        name (str): 形态名称
        description (str, optional): 形态描述
        tags (list, optional): 标签列表
        column (str): 使用的列名
        
    Returns:
        dict: 创建的形态模板
    """
    # 确保日期列存在
    date_col = 'date' if 'date' in stock_data.columns else 'trade_date'
    if date_col not in stock_data.columns:
        raise ValueError("股票数据缺少日期列")
    
    # 筛选日期范围内的数据
    mask = (stock_data[date_col] >= start_date) & (stock_data[date_col] <= end_date)
    filtered_data = stock_data.loc[mask]
    
    if filtered_data.empty:
        raise ValueError(f"在日期范围 {start_date} 到 {end_date} 内没有数据")
    
    # 提取并归一化数据
    pattern_data = normalized_pattern = normalize_pattern(filtered_data[column].values)
    
    # 创建模板
    template = {
        "name": name,
        "description": description,
        "data": pattern_data.tolist(),
        "tags": tags or [],
        "source": {
            "stock_code": stock_data.get('code', [None])[0],
            "stock_name": stock_data.get('name', [None])[0],
            "start_date": start_date,
            "end_date": end_date,
            "column": column
        },
        "created_at": datetime.now().isoformat()
    }
    
    return template 