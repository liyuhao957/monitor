#!/usr/bin/env python3
"""
测试AI生成代码的硬编码修复
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import Task
from app.services.ai_notifier import analyze_notification_content
from pydantic import HttpUrl

def test_oppo_ai_generation():
    """测试OPPO任务的AI代码生成，验证是否修复了硬编码问题"""
    
    # 创建OPPO任务
    task = Task(
        name="OPPO",
        url=HttpUrl("https://ie-activity-cn.heytapimage.com/static/minigame/CN/docs/index.html#/download/index"),
        frequency="1m",
        rule="xpath://*[@id=\"main\"]/ul[1]",
        enabled=True,
        ai_analysis_enabled=True,
        ai_description="我只想监控OPPO小游戏调试器的最新版本更新。V9.8.0这样的是小版本号，1155这样的是大版本号，当最新版本号发生变化时（如从OPPO 小游戏调试器 V9.8.0变为OPPO 小游戏调试器 V9.0.0 和 1155变为1166），请生成一个表格格式的通知，包含：OPPO引擎大版本号、OPPO引擎小版本号、下载地址。通知格式要求：使用表格、包含emoji、简洁美观、版本功能需要排版。"
    )
    
    # 模拟页面内容
    page_content = """1155 <a href="https://ie-activity-cn.heytapimage.com/static/quickgame/tools/e4d31728063eb9e67443bdda8e6849f6.zip" target="_blank">OPPO 小游戏调试器 V9.8.0</a>1144 <a href="https://ie-activity-cn.heytapimage.com/static/quickgame/tools/old_version.zip" target="_blank">OPPO 小游戏调试器 V9.7.0</a>"""
    
    print("🔍 开始测试AI代码生成...")
    print("=" * 60)
    
    try:
        # 调用AI生成模板
        result = analyze_notification_content(task, page_content)
        
        if result:
            print("✅ AI模板生成成功!")
            print(f"\n📌 模板标题: {result.title}")
            print(f"\n📋 模板说明: {result.summary}")
            
            if result.extraction_rules:
                print(f"\n🔧 提取规则:")
                for field, rule in result.extraction_rules.items():
                    print(f"  - {field}: {rule}")
            
            if result.formatter_code:
                print(f"\n💻 生成的Python代码:")
                print("=" * 40)
                print(result.formatter_code)
                print("=" * 40)
                
                # 检查代码中是否包含硬编码值
                print(f"\n🔍 硬编码检查:")
                hardcoded_indicators = ["1155", "V9.8.0", "https://ie-activity-cn.heytapimage.com"]
                found_hardcoded = []
                
                for indicator in hardcoded_indicators:
                    if indicator in result.formatter_code:
                        found_hardcoded.append(indicator)
                
                if found_hardcoded:
                    print(f"❌ 仍然存在硬编码值: {found_hardcoded}")
                    print("🚨 修复失败，AI仍在生成固定值")
                else:
                    print("✅ 未检测到明显的硬编码值")
                    print("🎉 修复成功，AI使用动态数据")
                
                # 测试代码执行
                print(f"\n🧪 测试代码执行:")
                try:
                    from app.services.code_executor import execute_notification_formatter
                    
                    # 模拟提取的数据
                    test_extracted_data = {
                        "major_version": "1166",  # 不同的版本号
                        "minor_version": "V9.9.0",  # 不同的版本号
                        "download_url": "https://example.com/new_version.zip",  # 不同的URL
                        "full_name": "OPPO 小游戏调试器 V9.9.0"
                    }
                    
                    test_task_info = {
                        "name": "OPPO测试",
                        "url": "https://example.com",
                        "current_time": "2025-06-17 15:00:00"
                    }
                    
                    notification_content = execute_notification_formatter(
                        result.formatter_code,
                        test_extracted_data,
                        test_task_info
                    )
                    
                    print("✅ 代码执行成功")
                    print(f"\n📄 生成的通知内容:")
                    print("-" * 40)
                    print(notification_content)
                    print("-" * 40)
                    
                    # 检查通知内容是否使用了测试数据
                    if "1166" in notification_content and "V9.9.0" in notification_content:
                        print("🎉 成功！通知内容使用了动态数据")
                    elif "1155" in notification_content or "V9.8.0" in notification_content:
                        print("❌ 失败！通知内容仍使用固定值")
                    else:
                        print("⚠️  无法确定是否使用动态数据")
                        
                except Exception as e:
                    print(f"❌ 代码执行失败: {e}")
            else:
                print("❌ 未生成Python代码")
        else:
            print("❌ AI模板生成返回空结果")
            
    except Exception as e:
        print(f"❌ AI模板生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_oppo_ai_generation()
