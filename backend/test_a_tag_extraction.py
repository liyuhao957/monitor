#!/usr/bin/env python3
"""
测试a标签文本提取修复
验证content_parser正确提取a标签的文本内容而非href
"""

import sys
sys.path.append('.')

from app.services.content_parser import HTMLContentParser
from app.services.ai_notifier import NotificationAnalysis
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_a_tag_extraction():
    """测试a标签提取行为"""
    # 测试HTML内容
    test_html = '''
    <ul>
        <li><code>1155</code> <a href="https://example.com/download.zip" target="_blank">OPPO 小游戏调试器 V9.8.0</a></li>
        <li><code>1144</code> <a href="https://example.com/old.zip" target="_blank">OPPO 小游戏调试器 V9.7.0</a></li>
    </ul>
    '''
    
    # 创建解析器
    parser = HTMLContentParser()
    
    # 测试不同的提取规则
    test_cases = [
        {
            "name": "默认提取（应该提取文本）",
            "field": "version",
            "rule": "css:li:first-child a",
            "expected": "OPPO 小游戏调试器 V9.8.0"
        },
        {
            "name": "明确提取文本",
            "field": "version_text",
            "rule": "css:li:first-child a::text",
            "expected": "OPPO 小游戏调试器 V9.8.0"
        },
        {
            "name": "提取href属性",
            "field": "download_url",
            "rule": "css:li:first-child a::attr(href)",
            "expected": "https://example.com/download.zip"
        },
        {
            "name": "提取大版本号",
            "field": "major_version",
            "rule": "css:li:first-child code",
            "expected": "1155"
        }
    ]
    
    print("=" * 60)
    print("测试a标签提取行为")
    print("=" * 60)
    
    for test in test_cases:
        print(f"\n测试: {test['name']}")
        print(f"规则: {test['rule']}")
        
        try:
            result = parser._extract_single_field(
                test['field'], 
                test['rule'], 
                "", 
                test_html
            )
            
            print(f"结果: {result}")
            print(f"期望: {test['expected']}")
            
            if result == test['expected']:
                print("✅ 通过")
            else:
                print("❌ 失败")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print("\n" + "=" * 60)
    print("修复说明：")
    print("1. css:a 现在默认提取文本内容")
    print("2. css:a::attr(href) 明确提取href属性")
    print("3. 这样更符合通用监控系统的需求")
    print("=" * 60)

if __name__ == "__main__":
    test_a_tag_extraction() 