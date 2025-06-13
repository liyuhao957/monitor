#!/usr/bin/env python3
"""
测试AI智能通知功能
"""
import os
import asyncio
from app.core.config import Task
from app.services.ai_notifier import analyze_notification_content
from pydantic import HttpUrl

# 设置环境变量
os.environ['OPENAI_API_KEY'] = 'sk-6KwYGpsonYqWBAxrg9hEyjfEL7Bpak478TjuxCA7gf52GdvGVDfQ'
os.environ['OPENAI_BASE_URL'] = 'https://api.oaipro.com/v1'

async def test_ai_notification():
    """测试AI通知分析功能"""
    
    # 创建测试任务
    task = Task(
        name="华为快应用加载器监控",
        url=HttpUrl("https://developer.huawei.com/consumer/cn/doc/Tools-Library/quickapp-ide-download-0000001101172926"),
        frequency="30m",
        rule="css:#ZH-CN_TOPIC_0000001101172926__li16222518142",
        enabled=True,
        screenshot=True,
        ai_analysis_enabled=True,
        ai_description="我想监控V15.1.1.301版本的更新，包括版本号变化、下载链接更新、支持规范变化"
    )
    
    # 模拟内容变化
    old_content = """
    <tr>
        <td>V15.0.1.303</td>
        <td><a href="https://contentcenter-vali-drcn.dbankcdn.cn/pvt_2/DeveloperAlliance_package_901_9/ac/v3/NdSvoI1ZQjKu0y7TZC31Gg/QuickAPP-newly-product-release-loader-15.1.1.301.apk">HwQuickApp_Loader_Phone_V15.1.1.301.apk</a></td>
        <td>（支持1121规范的调试）</td>
    </tr>
    """
    
    new_content = """
    <tr>
        <td>V15.0.1.304</td>
        <td><a href="https://contentcenter-vali-drcn.dbankcdn.cn/pvt_2/DeveloperAlliance_package_901_9/ac/v3/NdSvoI1ZQjKu0y7TZC31Gg/QuickAPP-newly-product-release-loader-15.1.1.302.apk">HwQuickApp_Loader_Phone_V15.1.1.302.apk</a></td>
        <td>（支持1122规范的调试）</td>
    </tr>
    """
    
    print("🤖 开始测试AI模板生成...")
    print(f"📋 任务名称: {task.name}")
    print(f"📝 监控描述: {task.ai_description}")
    print("\n" + "="*50)

    try:
        # 调用AI生成模板
        result = analyze_notification_content(task, old_content, new_content)

        if result:
            print("✅ AI模板生成成功!")
            print(f"\n📌 模板标题: {result.title}")
            print(f"\n📄 Jinja2模板内容:\n{result.content}")
            print(f"\n📋 模板说明: {result.summary}")

            # 保存AI生成的模板
            task.notification_template = result.content
            print(f"\n💾 AI生成的模板已保存到任务配置")

            # 测试模板渲染
            print(f"\n🧪 测试模板渲染效果:")
            from jinja2 import Template
            template = Template(result.content)
            rendered = template.render(
                task_name=task.name,
                url=task.url,
                old_summary="V15.0.1.303版本，支持1121规范",
                new_summary="V15.0.1.304版本，支持1122规范",
                screenshot_url="https://example.com/screenshot.png"
            )
            print(rendered)

        else:
            print("❌ AI模板生成返回空结果")

    except Exception as e:
        print(f"❌ AI模板生成失败: {e}")
        print("🔄 将使用传统通知模板")

if __name__ == "__main__":
    asyncio.run(test_ai_notification())
