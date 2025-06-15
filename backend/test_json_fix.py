#!/usr/bin/env python3
"""
测试JSON转义修复功能
"""

def test_json_escaping_fix():
    """测试JSON转义修复功能"""
    from app.services.ai_notifier import AINotifier
    
    # 创建AI通知器实例
    notifier = AINotifier("test_key", "test_url", "test_model")
    
    print("🔧 测试JSON转义修复功能...")
    print("=" * 60)
    
    # 测试用例：包含各种转义问题的JSON字符串
    test_cases = [
        {
            "name": "无效管道符转义",
            "input": '{"content": "{{ variable \\| filter }}"}',
            "expected_fix": '{"content": "{{ variable | filter }}"}',
            "description": "修复 \\| 为 |"
        },
        {
            "name": "有效转义保留",
            "input": '{"content": "Line 1\\nLine 2\\tTabbed"}',
            "expected_fix": '{"content": "Line 1\\nLine 2\\tTabbed"}',
            "description": "保留有效的 \\n 和 \\t"
        },
        {
            "name": "混合转义问题",
            "input": '{"content": "{{ var \\| filter }}\\nNew line"}',
            "expected_fix": '{"content": "{{ var | filter }}\\nNew line"}',
            "description": "修复无效转义，保留有效转义"
        },
        {
            "name": "复杂模板",
            "input": '{"content": "{% for item in items \\| filter %}{{ item }}{% endfor %}"}',
            "expected_fix": '{"content": "{% for item in items | filter %}{{ item }}{% endfor %}"}',
            "description": "修复Jinja2模板中的管道符"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试 {i}: {test_case['name']}")
        print(f"描述: {test_case['description']}")
        print(f"输入: {test_case['input']}")
        
        try:
            # 调用修复函数
            fixed_json = notifier._fix_json_escaping(test_case['input'])
            print(f"修复后: {fixed_json}")
            
            # 检查修复结果
            if fixed_json == test_case['expected_fix']:
                print("✅ 修复正确")
            else:
                print("❌ 修复结果不符合预期")
                print(f"期望: {test_case['expected_fix']}")
                all_passed = False
            
            # 尝试解析JSON验证有效性
            import json
            try:
                json.loads(fixed_json)
                print("✅ JSON格式有效")
            except json.JSONDecodeError as e:
                print(f"❌ JSON格式无效: {e}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ 修复过程出错: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("=" * 60)
    
    if all_passed:
        print("🎉 所有测试通过!")
        print("✅ JSON转义修复功能正常工作")
        print("✅ 可以处理常见的转义问题")
        print("✅ 保留有效的转义序列")
        print("✅ 生成有效的JSON格式")
    else:
        print("⚠️  部分测试失败")
        print("需要进一步调试修复逻辑")
    
    return all_passed

def test_real_ai_response():
    """测试真实AI响应的修复"""
    print("\n" + "=" * 60)
    print("🤖 测试真实AI响应修复:")
    print("=" * 60)
    
    # 模拟之前出错的AI响应
    problematic_response = '''```json
{
  "title": "🔄 荣耀调试器版本更新通知",
  "content": "检测到荣耀调试器版本更新，请及时查看！\\n\\n**任务名称**：{{ task_name }}\\n**监控链接**：{{ url }}\\n\\n最新版本信息如下：\\n\\n| 属性 | 值 |\\n|------|------|\\n| 荣耀快应用引擎版本号 | {{ new_summary.honor_quickapp_engine }} |\\n| 荣耀引擎版本号 | {{ new_summary.honor_engine }} |\\n| 快应用联盟平台版本号 | {{ new_summary.quickapp_alliance }} |\\n| 下载地址 | [📥 点击下载]({{ new_summary.download_url }}) |\\n| 调试器版本号 | {{ new_summary.debugger_version }} |\\n| 版本功能 | {{ new_summary.features \\| replace('新增：', '\\n\\n• **新增**：') \\| replace('优化：', '\\n\\n• **优化**：') \\| trim }} |\\n\\n{% if screenshot_url %}\\n**更新内容截图**：\\n![更新截图]({{ screenshot_url }})\\n{% endif %}",
  "summary": "监控荣耀调试器版本更新，当检测到版本号变化时生成表格通知，包含六大核心字段并优化功能说明排版"
}
```'''
    
    from app.services.ai_notifier import AINotifier
    notifier = AINotifier("test_key", "test_url", "test_model")
    
    try:
        # 尝试解析这个响应
        result = notifier._parse_analysis_result(problematic_response)
        print("✅ 成功解析AI响应!")
        print(f"标题: {result.title}")
        print(f"模板长度: {len(result.content)} 字符")
        print("✅ JSON转义修复功能有效")
        return True
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return False

if __name__ == "__main__":
    success1 = test_json_escaping_fix()
    success2 = test_real_ai_response()
    
    print("\n" + "=" * 60)
    print("🎯 最终结果:")
    print("=" * 60)
    
    if success1 and success2:
        print("🎉 JSON转义修复功能完全正常!")
        print("现在可以处理AI返回的复杂JSON响应了")
    else:
        print("⚠️  还需要进一步优化")
