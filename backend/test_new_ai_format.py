#!/usr/bin/env python3
"""
测试新的AI分段文本格式
"""
from app.services.ai_notifier import AINotifier

def test_new_format_parsing():
    """测试新的分段文本解析"""
    print("🧪 测试新的AI分段文本格式解析...")
    print("=" * 60)
    
    # 模拟AI的新格式响应
    mock_response = """
这里是一些AI的解释文字，会被忽略...

---TITLE---
🚀 荣耀调试器版本更新通知

---CONTENT---
🔥 {{ task_name }} 检测到新版本发布！

📊 **版本变化**: {{ old_summary }} → {{ new_summary }}
🔗 监控页面: {{ url }}

**更新详情**
| 项目 | 值 |
|------|-----|
| 荣耀快应用引擎版本号 | {{ honor_quickapp_engine }} |
| 荣耀引擎版本号 | {{ honor_engine }} |
| 快应用联盟平台版本号 | {{ quickapp_alliance_platform }} |
| 调试器版本号 | {{ debugger_version }} |
| 下载地址 | [点击下载]({{ download_url }}) |

**版本功能**
{{ version_features | replace('新增：', '\n🆕 **新增**: ') | replace('优化：', '\n⚡ **优化**: ') | trim }}

{% if screenshot_url %}📸 **截图**: [查看截图]({{ screenshot_url }}){% endif %}

---SUMMARY---
监控荣耀调试器版本更新，当版本号变化时生成包含版本详情和功能更新的表格通知，特别处理版本功能的排版显示

---FIELDS---
honor_quickapp_engine=荣耀快应用引擎版本号
honor_engine=荣耀引擎版本号
quickapp_alliance_platform=快应用联盟平台版本号
download_url=调试器下载地址
debugger_version=调试器版本号
version_features=版本功能描述文本

---RULES---
honor_quickapp_engine=regex:^(\S+)\s
honor_engine=regex:^\S+\s+(\S+)\s
quickapp_alliance_platform=regex:^\S+\s+\S+\s+(\S+)\s
download_url=regex:href="(.*?)"
debugger_version=regex:点击下载</a>\s+(\S+)\s
version_features=regex:点击下载</a>\s+\S+\s+(.*)$

这里还可能有更多AI的解释文字...
"""
    
    # 创建AI通知器实例
    notifier = AINotifier("test_key", "test_url", "test_model")
    
    try:
        # 测试解析
        result = notifier._parse_analysis_result(mock_response)
        
        print("✅ 解析成功!")
        print(f"\n📝 标题: {result.title}")
        print(f"\n📄 模板内容:\n{result.content}")
        print(f"\n📋 摘要: {result.summary}")
        print(f"\n🏷️  字段定义: {result.required_fields}")
        print(f"\n🔍 提取规则: {result.extraction_rules}")
        
        # 验证Jinja2模板语法
        if '{{' in result.content and '}}' in result.content:
            print("\n✅ 包含Jinja2变量语法")
        
        if '|' in result.content and 'replace(' in result.content:
            print("✅ 包含Jinja2过滤器语法")
            
        # 测试模板渲染
        print("\n🧪 测试Jinja2模板渲染...")
        from jinja2 import Template
        template = Template(result.content)
        
        # 模拟数据
        test_data = {
            'task_name': '荣耀调试器',
            'old_summary': 'V15.1.1.301',
            'new_summary': 'V15.2.1.305',
            'url': 'https://developer.honor.com/cn/doc/guides/101380',
            'honor_quickapp_engine': '9.0.18',
            'honor_engine': '6161',
            'quickapp_alliance_platform': '1123',
            'debugger_version': '12.0.18.301',
            'download_url': 'https://example.com/debugger.apk',
            'version_features': '新增：快应用feature支持。优化：性能提升。',
            'screenshot_url': 'http://127.0.0.1:8000/screenshots/test.png'
        }
        
        rendered = template.render(**test_data)
        print("✅ Jinja2模板渲染成功!")
        print("\n📋 渲染结果:")
        print("-" * 40)
        print(rendered)
        print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return False

def test_section_parsing():
    """测试分段解析功能"""
    print("\n🔬 测试分段解析功能...")
    print("=" * 60)
    
    notifier = AINotifier("test_key", "test_url", "test_model")
    
    test_text = """
一些前置文字
---TITLE---
测试标题
---CONTENT---
第一行内容
第二行内容
---SUMMARY---
这是摘要
一些后置文字
"""
    
    try:
        sections = notifier._parse_sectioned_response(test_text)
        print("✅ 分段解析成功!")
        print(f"解析到 {len(sections)} 个部分:")
        for key, value in sections.items():
            print(f"  {key}: {repr(value)}")
        
        return True
    except Exception as e:
        print(f"❌ 分段解析失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试新的AI分段文本格式")
    print("=" * 60)
    
    success1 = test_section_parsing()
    success2 = test_new_format_parsing()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("=" * 60)
    
    if success1 and success2:
        print("🎉 所有测试通过!")
        print("✅ 新的分段文本格式工作正常")
        print("✅ 彻底解决了JSON转义问题")
        print("✅ Jinja2模板可以正常渲染")
        print("\n🔧 现在可以重新测试AI预览功能了")
    else:
        print("⚠️  部分测试失败")
        print("需要进一步调试")
