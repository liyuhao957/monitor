#!/usr/bin/env python3
"""
测试改进后的AI提示词是否能生成更精确的正则表达式
"""
import logging
from app.services.ai_notifier import AINotifier
from app.core.config import Task

# 配置日志
logging.basicConfig(level=logging.INFO)

def test_honor_debugger_extraction():
    """测试荣耀调试器的数据提取"""
    print("🧪 测试改进后的AI提示词效果...")
    print("=" * 60)
    
    # 荣耀调试器的实际HTML内容
    html_content = '''10.0.2.200 6102 1123 <a href="https://contentplatform-drcn.hihonorcdn.com/developerPlatform/Debugger_v80.0.2.200/Debugger_v80.0.2.200_phoneDebugger_release_20250612_090344.apk" rel="noopener" style="color: #007dbb;">点击下载</a> 80.0.2.200 优化：adbutton组件用户体验优化'''
    
    print("📄 测试HTML内容:")
    print(f"   {html_content}")
    print()
    
    # 创建任务对象
    task = Task(
        name="荣耀调试器",
        url="https://developer.honor.com/cn/doc/guides/101380",
        frequency="1m",
        rule="xpath://*[@id=\"doc-content-text\"]/div[2]/table/tbody/tr[2]",
        enabled=True,
        ai_analysis_enabled=True,
        ai_description="我只想监控荣耀加载器的最新版本更新。当最新版本号发生变化时（如从V15.1.1.301变为V15.2.1.305），请生成一个表格格式的通知，包含：荣耀快应用引擎版本号、荣耀引擎版本号、快应用联盟平台版本号、下载地址、调试器版本号、版本功能。通知格式要求：使用表格、包含emoji、简洁美观、版本功能需要排版。"
    )
    
    print("📝 用户需求:")
    print(f"   {task.ai_description}")
    print()
    
    # 分析预期的正确提取结果
    print("✅ 预期的正确提取结果:")
    print("   - 荣耀快应用引擎版本号: 10.0.2.200")
    print("   - 荣耀引擎版本号: 6102")
    print("   - 快应用联盟平台版本号: 1123")
    print("   - 下载地址: https://contentplatform-drcn.hihonorcdn.com/.../Debugger_v80.0.2.200_phoneDebugger_release_20250612_090344.apk")
    print("   - 调试器版本号: 80.0.2.200")
    print("   - 版本功能: 优化：adbutton组件用户体验优化")
    print()
    
    # 分析问题
    print("❌ 当前问题:")
    print("   version_features 正则 `\\d+\\.\\d+\\.\\d+\\.\\d+\\s+(.+)$` 会匹配:")
    print("   '6102 1123 [点击下载] 80.0.2.200 优化：adbutton组件用户体验优化'")
    print("   而不是只匹配：'优化：adbutton组件用户体验优化'")
    print()
    
    print("🎯 改进后的提示词应该引导AI生成更精确的正则，例如:")
    print("   - 使用 `</a>\\s+\\d+\\.\\d+\\.\\d+\\.\\d+\\s+(.+)$` 来确保匹配最后一个版本号后的内容")
    print("   - 或使用其他锚点来精确定位")
    print()
    
    # 测试改进后的正则表达式
    import re
    
    print("🧪 测试不同的正则表达式:")
    
    test_patterns = [
        ("原始错误的正则", r'\d+\.\d+\.\d+\.\d+\s+(.+)$'),
        ("改进后的正则1", r'</a>\s+\d+\.\d+\.\d+\.\d+\s+(.+)$'),
        ("改进后的正则2", r'</a>\s+[\d.]+\s+(.+)$'),
        ("更精确的正则", r'</a>\s+\d+\.\d+\.\d+\.\d+\s+([^<]+)$')
    ]
    
    for name, pattern in test_patterns:
        print(f"\n   {name}: {pattern}")
        match = re.search(pattern, html_content)
        if match:
            result = match.group(1)
            print(f"   ✅ 匹配成功: '{result}'")
            print(f"   匹配是否正确: {'✅' if result.strip() == '优化：adbutton组件用户体验优化' else '❌'}")
        else:
            print(f"   ❌ 匹配失败")
    
    print("\n" + "=" * 60)
    print("💡 总结：改进后的提示词应该能引导AI：")
    print("   1. 识别页面中有多个版本号")
    print("   2. 使用HTML标签作为锚点来精确定位")
    print("   3. 生成更精确的正则表达式")
    print("   4. 在验证阶段检查提取结果是否包含了不该包含的内容")

if __name__ == "__main__":
    test_honor_debugger_extraction() 