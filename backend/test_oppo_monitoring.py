#!/usr/bin/env python3
"""
测试OPPO监控任务是否正常工作，验证AI代码是否使用动态数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.code_executor import execute_notification_formatter

def test_oppo_monitoring():
    """测试OPPO监控任务的AI代码执行"""
    
    # 找到OPPO任务
    oppo_task = None
    for task in settings.tasks:
        if task.name == "OPPO":
            oppo_task = task
            break
    
    if not oppo_task:
        print("❌ 未找到OPPO任务")
        return
    
    print(f"🔍 找到OPPO任务: {oppo_task.name}")
    print(f"📝 AI分析已启用: {oppo_task.ai_analysis_enabled}")
    print(f"💻 AI代码长度: {len(oppo_task.ai_formatter_code) if oppo_task.ai_formatter_code else 0} 字符")
    
    if not oppo_task.ai_formatter_code:
        print("❌ 未找到AI格式化代码")
        return
    
    # 测试场景1：当前版本数据
    print("\n🧪 测试场景1：当前版本数据")
    current_data = {
        "major_version": "1155",
        "minor_version": "V9.8.0",
        "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/e4d31728063eb9e67443bdda8e6849f6.zip"
    }
    
    task_info = {
        "name": "OPPO",
        "url": "https://ie-activity-cn.heytapimage.com/static/minigame/CN/docs/index.html#/download/index",
        "current_time": "2025-06-17 15:10:00"
    }
    
    try:
        notification1 = execute_notification_formatter(
            oppo_task.ai_formatter_code,
            current_data,
            task_info
        )
        print("✅ 代码执行成功")
        print("📄 生成的通知内容:")
        print("-" * 40)
        print(notification1)
        print("-" * 40)
        
        # 验证是否使用了动态数据
        if "1155" in notification1 and "V9.8.0" in notification1:
            print("✅ 正确使用了当前版本数据")
        else:
            print("❌ 未正确使用当前版本数据")
            
    except Exception as e:
        print(f"❌ 代码执行失败: {e}")
        return
    
    # 测试场景2：新版本数据（模拟版本更新）
    print("\n🧪 测试场景2：新版本数据（模拟版本更新）")
    new_data = {
        "major_version": "1166",  # 新的大版本号
        "minor_version": "V9.9.0",  # 新的小版本号
        "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/new_version.zip"  # 新的下载链接
    }
    
    task_info["current_time"] = "2025-06-17 15:15:00"
    
    try:
        notification2 = execute_notification_formatter(
            oppo_task.ai_formatter_code,
            new_data,
            task_info
        )
        print("✅ 代码执行成功")
        print("📄 生成的通知内容:")
        print("-" * 40)
        print(notification2)
        print("-" * 40)
        
        # 验证是否使用了新的动态数据
        if "1166" in notification2 and "V9.9.0" in notification2:
            print("🎉 成功！AI代码正确使用了新版本的动态数据")
            print("✅ 硬编码问题已修复")
        else:
            print("❌ 失败！AI代码仍在使用固定值")
            
        # 对比两次通知内容
        if notification1 != notification2:
            print("✅ 两次通知内容不同，说明AI代码响应数据变化")
        else:
            print("❌ 两次通知内容相同，可能仍存在硬编码问题")
            
    except Exception as e:
        print(f"❌ 代码执行失败: {e}")
    
    # 测试场景3：缺失数据处理
    print("\n🧪 测试场景3：缺失数据处理")
    incomplete_data = {
        "major_version": "1177",
        # 缺少 minor_version 和 download_url
    }
    
    try:
        notification3 = execute_notification_formatter(
            oppo_task.ai_formatter_code,
            incomplete_data,
            task_info
        )
        print("✅ 代码执行成功（处理缺失数据）")
        print("📄 生成的通知内容:")
        print("-" * 40)
        print(notification3)
        print("-" * 40)
        
        if "未知" in notification3 or "暂无" in notification3:
            print("✅ 正确处理了缺失数据")
        else:
            print("⚠️  缺失数据处理可能需要改进")
            
    except Exception as e:
        print(f"❌ 缺失数据处理失败: {e}")

if __name__ == "__main__":
    test_oppo_monitoring()
