#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单元测试运行脚本
这个脚本用于运行股票形态匹配系统的所有单元测试。
"""

import os
import sys
import unittest
import pytest
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run_unittest():
    """
    使用unittest框架运行所有测试
    """
    # 发现并运行所有测试
    test_loader = unittest.TestLoader()
    test_dir = os.path.join(project_root, "stock_pattern_system", "tests", "unit")
    test_suite = test_loader.discover(test_dir, pattern="test_*.py")
    
    # 运行测试套件
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    # 返回测试结果
    return test_result.wasSuccessful()


def run_pytest():
    """
    使用pytest框架运行所有测试
    """
    # 设置测试目录
    test_dir = os.path.join(project_root, "stock_pattern_system", "tests", "unit")
    
    # 运行pytest
    return pytest.main(["-v", test_dir])


if __name__ == "__main__":
    print("=" * 80)
    print("运行股票形态匹配系统单元测试")
    print("=" * 80)
    
    # 根据命令行参数选择测试框架
    if len(sys.argv) > 1 and sys.argv[1] == "--pytest":
        print("使用pytest框架运行测试...\n")
        exit_code = run_pytest()
        success = exit_code == 0
    else:
        print("使用unittest框架运行测试...\n")
        success = run_unittest()
    
    # 输出测试结果
    print("\n" + "=" * 80)
    if success:
        print("测试结果: 全部通过")
        sys.exit(0)
    else:
        print("测试结果: 存在失败的测试")
        sys.exit(1) 