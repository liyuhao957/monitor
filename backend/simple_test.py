#!/usr/bin/env python3
"""
简单测试JSON转义修复
"""
import json
from app.services.ai_notifier import AINotifier

def test_fix():
    notifier = AINotifier("test", "test", "test")
    
    # 测试问题JSON
    problematic = '{"content": "{{ var \\| filter }}\\n\\nText"}'
    print(f"原始: {problematic}")
    
    try:
        fixed = notifier._fix_json_escaping(problematic)
        print(f"修复后: {fixed}")
        
        # 尝试解析
        data = json.loads(fixed)
        print("✅ JSON解析成功")
        print(f"内容: {data['content']}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    test_fix()
