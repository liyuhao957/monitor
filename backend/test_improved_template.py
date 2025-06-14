#!/usr/bin/env python3
"""
测试改进后的AI模板生成
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import Task
from app.services.ai_notifier import analyze_notification_content

def test_improved_template():
    """测试改进后的AI模板生成"""
    
    # 创建测试任务
    task = Task(
        name="荣耀调试器",
        url="https://developer.honor.com/cn/doc/guides/101380",
        ai_description="我只想监控荣耀加载器的最新版本更新。当最新版本号发生变化时（如从V15.1.1.301变为V15.2.1.305），请生成一个表格格式的通知，包含：荣耀快应用引擎版本号、荣耀引擎版本号、快应用联盟平台版本号、下载地址、调试器版本号、版本功能。通知格式要求：使用表格、包含emoji、简洁美观、版本功能需要排版。",
        ai_analysis_enabled=True
    )
    
    # 模拟内容变化
    old_content = """
    <tr>
        <td>荣耀快应用引擎版本号</td>
        <td>V15.1.1.301</td>
    </tr>
    <tr>
        <td>荣耀引擎版本号</td>
        <td>V15.1.1.301</td>
    </tr>
    <tr>
        <td>快应用联盟平台版本号</td>
        <td>1121</td>
    </tr>
    <tr>
        <td>下载地址</td>
        <td><a href="https://example.com/old.apk">下载</a></td>
    </tr>
    <tr>
        <td>调试器版本号</td>
        <td>V15.1.1.301</td>
    </tr>
    <tr>
        <td>版本功能</td>
        <td>支持新功能A。支持新功能B。修复已知问题。</td>
    </tr>
    """
    
    new_content = """
    <tr>
        <td>荣耀快应用引擎版本号</td>
        <td>V15.2.1.305</td>
    </tr>
    <tr>
        <td>荣耀引擎版本号</td>
        <td>V15.2.1.305</td>
    </tr>
    <tr>
        <td>快应用联盟平台版本号</td>
        <td>1122</td>
    </tr>
    <tr>
        <td>下载地址</td>
        <td><a href="https://example.com/new.apk">下载</a></td>
    </tr>
    <tr>
        <td>调试器版本号</td>
        <td>V15.2.1.305</td>
    </tr>
    <tr>
        <td>版本功能</td>
        <td>新增功能C支持。优化性能表现。修复已知问题。增强稳定性。</td>
    </tr>
    """

    try:
        print("🧪 测试改进后的AI模板生成...")
        
        # 调用AI生成模板
        result = analyze_notification_content(task, old_content, new_content)

        if result:
            print("✅ AI模板生成成功!")
            print(f"\n📌 模板标题: {result.title}")
            print(f"\n📄 改进后的Jinja2模板内容:\n{result.content}")
            print(f"\n📋 模板说明: {result.summary}")
            
            # 测试模板渲染
            print(f"\n🧪 测试模板渲染效果:")
            from jinja2 import Template
            template = Template(result.content)
            
            # 模拟提取的字段数据
            test_data = {
                'task_name': task.name,
                'url': task.url,
                'old_debugger_version': 'V15.1.1.301',
                'new_debugger_version': 'V15.2.1.305',
                'new_honor_engine': 'V15.2.1.305',
                'new_engine_version': 'V15.2.1.305',
                'new_alliance_version': '1122',
                'new_download_url': 'https://example.com/new.apk',
                'new_features': '新增功能C支持。优化性能表现。修复已知问题。增强稳定性。',
                'screenshot_url': 'http://127.0.0.1:8000/screenshots/test.png'
            }
            
            rendered = template.render(**test_data)
            print("=" * 50)
            print("渲染结果:")
            print("=" * 50)
            print(rendered)
            print("=" * 50)
            
            # 检查是否有多余空行
            lines = rendered.split('\n')
            empty_line_count = sum(1 for line in lines if line.strip() == '')
            print(f"\n📊 空行统计: 总共 {empty_line_count} 个空行")
            
            if empty_line_count > 5:  # 允许一些合理的空行
                print("⚠️  警告: 空行数量较多，可能需要进一步优化")
            else:
                print("✅ 空行控制良好")

        else:
            print("❌ AI模板生成返回空结果")

    except Exception as e:
        print(f"❌ AI模板生成失败: {e}")

if __name__ == "__main__":
    test_improved_template()
