#!/usr/bin/env python3
"""
测试JSON转义修复功能
"""
import json

def test_json_escaping_fix():
    """测试JSON转义修复功能"""
    from app.services.ai_notifier import AINotifier
    
    # 创建AI通知器实例
    notifier = AINotifier("test_key", "test_url", "test_model")
    
    print("🔧 测试JSON转义修复功能...")
    print("=" * 60)
    
    # 模拟实际出错的AI响应
    problematic_response = '''```json
{
  "title": "🚀 荣耀调试器版本更新通知",
  "content": "🔥 {{ task_name }} 检测到新版本发布！\\n\\n📊 **版本变化**: {{ old_summary }} → {{ new_summary }}\\n🔗 监控页面: {{ url }}\\n\\n**更新详情**\\n| 项目 | 值 |\\n|------|-----|\\n| 荣耀快应用引擎版本号 | {{ honor_quickapp_engine }} |\\n| 荣耀引擎版本号 | {{ honor_engine }} |\\n| 快应用联盟平台版本号 | {{ quickapp_alliance_platform }} |\\n| 调试器版本号 | {{ debugger_version }} |\\n| 下载地址 | [点击下载]({{ download_url }}) |\\n\\n**版本功能**\\n{{ version_features | replace('新增：', '\\n🆕 **新增**: ') | replace('优化：', '\\n⚡ **优化**: ') | trim }}\\n\\n {% if screenshot_url %}📸 **截图**: [查看截图]({{ screenshot_url }}){% endif %}",
  "summary": "监控荣耀调试器版本更新，当版本号变化时生成包含版本详情和功能更新的表格通知，特别处理版本功能的排版显示",
  "required_fields": {
    "honor_quickapp_engine": "荣耀快应用引擎版本号",
    "honor_engine": "荣耀引擎版本号", 
    "quickapp_alliance_platform": "快应用联盟平台版本号",
    "download_url": "调试器下载地址",
    "debugger_version": "调试器版本号",
    "version_features": "版本功能描述文本"
  },
  "extraction_rules": {
    "honor_quickapp_engine": "regex:^(\\\\S+)\\\\s",
    "honor_engine": "regex:^\\\\S+\\\\s+(\\\\S+)\\\\s", 
    "quickapp_alliance_platform": "regex:^\\\\S+\\\\s+\\\\S+\\\\s+(\\\\S+)\\\\s",
    "download_url": "regex:href=\\\"(.*?)\\\"",
    "debugger_version": "regex:点击下载<\\\\/a>\\\\s+(\\\\S+)\\\\s",
    "version_features": "regex:点击下载<\\\\/a>\\\\s+\\\\S+\\\\s+(.*)$"
  }
}
```'''
    
    try:
        print("🧪 测试修复AI响应...")
        result = notifier._parse_analysis_result(problematic_response)
        print("✅ 成功解析AI响应!")
        print(f"📝 标题: {result.title}")
        print(f"📏 模板长度: {len(result.content)} 字符")
        print(f"📋 字段数量: {len(result.required_fields) if result.required_fields else 0}")
        print(f"🔍 提取规则数量: {len(result.extraction_rules) if result.extraction_rules else 0}")
        
        # 验证模板中的Jinja2语法
        if '|' in result.content and '\\|' not in result.content:
            print("✅ Jinja2管道符修复正确")
        else:
            print("❌ Jinja2管道符修复失败")
            
        # 验证换行符
        if '\\n' in result.content and '\\\\n' not in result.content:
            print("✅ 换行符格式正确")
        else:
            print("❌ 换行符格式错误")
            
        return True
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return False

def test_individual_fixes():
    """测试各种转义修复情况"""
    from app.services.ai_notifier import AINotifier
    
    notifier = AINotifier("test_key", "test_url", "test_model")
    
    print("\n🔬 测试各种转义修复情况...")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "管道符转义修复",
            "input": '{"content": "{{ var \\| filter }}"}',
            "expected_contains": "{{ var | filter }}"
        },
        {
            "name": "双重换行符修复", 
            "input": '{"content": "Line1\\\\nLine2"}',
            "expected_contains": "Line1\\nLine2"
        },
        {
            "name": "正则表达式转义保留",
            "input": '{"rule": "regex:(\\\\S+)\\\\s+"}',
            "expected_contains": "(\\\\S+)\\\\s+"
        },
        {
            "name": "Jinja2模板修复",
            "input": '{"content": "{{ features \\| replace(\\"新增：\\", \\"\\\\n新增\\") }}"}',
            "expected_contains": "{{ features | replace"
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 测试 {i}: {test_case['name']}")
        print(f"输入: {test_case['input']}")
        
        try:
            fixed = notifier._fix_json_escaping(test_case['input'])
            print(f"修复后: {fixed}")
            
            # 验证JSON有效性
            json.loads(fixed)
            print("✅ JSON格式有效")
            
            # 验证修复效果
            if test_case['expected_contains'] in fixed:
                print("✅ 修复效果正确")
            else:
                print(f"❌ 修复效果不符合预期，期望包含: {test_case['expected_contains']}")
                all_passed = False
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON格式无效: {e}")
            all_passed = False
        except Exception as e:
            print(f"❌ 修复过程出错: {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("🚀 开始测试JSON转义修复功能")
    print("=" * 60)
    
    success1 = test_json_escaping_fix()
    success2 = test_individual_fixes()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("=" * 60)
    
    if success1 and success2:
        print("🎉 所有测试通过!")
        print("✅ JSON转义修复功能正常工作")
        print("✅ 可以处理AI生成的复杂JSON响应")
        print("✅ 修复逻辑覆盖了常见的转义问题")
        print("\n🔧 修复功能已优化，现在可以重新测试AI预览功能了")
    else:
        print("⚠️  部分测试失败")
        print("需要进一步调试修复逻辑")
