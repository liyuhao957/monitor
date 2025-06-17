#!/usr/bin/env python3
"""
测试版本变化时AI代码的动态数据处理
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.code_executor import execute_notification_formatter

def test_version_change_scenarios():
    """测试不同版本变化场景下AI代码的表现"""
    
    # 找到OPPO任务
    oppo_task = None
    for task in settings.tasks:
        if task.name == "OPPO":
            oppo_task = task
            break
    
    if not oppo_task or not oppo_task.ai_formatter_code:
        print("❌ 未找到OPPO任务或AI代码")
        return
    
    print("🧪 测试AI代码在版本变化时的动态数据处理")
    print("=" * 60)
    
    # 测试场景1：当前版本（模拟AI预览显示的情况）
    print("\n📋 场景1：当前版本（AI预览显示的数据）")
    current_data = {
        "major_version": "1155",
        "minor_version": "V9.8.0",
        "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/e4d31728063eb9e67443bdda8e6849f6.zip"
    }
    
    task_info = {
        "name": "OPPO",
        "url": "https://ie-activity-cn.heytapimage.com/static/minigame/CN/docs/index.html#/download/index",
        "current_time": "2025-06-17 15:21:44"
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
        
        # 检查是否包含当前版本信息
        if "1155" in notification1 and "V9.8.0" in notification1:
            print("✅ 正确显示当前版本信息")
        else:
            print("❌ 未正确显示当前版本信息")
            
    except Exception as e:
        print(f"❌ 代码执行失败: {e}")
        return
    
    # 测试场景2：版本更新（大版本号变化）
    print("\n📋 场景2：大版本号更新（1155 → 1166）")
    updated_data_major = {
        "major_version": "1166",  # 大版本号更新
        "minor_version": "V9.8.0",  # 小版本号不变
        "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/new_major_version.zip"
    }
    
    task_info["current_time"] = "2025-06-17 15:30:00"
    
    try:
        notification2 = execute_notification_formatter(
            oppo_task.ai_formatter_code,
            updated_data_major,
            task_info
        )
        print("✅ 代码执行成功")
        print("📄 生成的通知内容:")
        print("-" * 40)
        print(notification2)
        print("-" * 40)
        
        # 检查是否使用了新的大版本号
        if "1166" in notification2 and "V9.8.0" in notification2:
            print("🎉 成功！AI代码正确使用了新的大版本号")
        else:
            print("❌ 失败！AI代码未正确使用新的大版本号")
            
        # 对比两次通知
        if notification1 != notification2:
            print("✅ 通知内容发生变化，响应版本更新")
        else:
            print("❌ 通知内容未变化，可能存在问题")
            
    except Exception as e:
        print(f"❌ 代码执行失败: {e}")
    
    # 测试场景3：版本更新（小版本号变化）
    print("\n📋 场景3：小版本号更新（V9.8.0 → V9.9.0）")
    updated_data_minor = {
        "major_version": "1155",  # 大版本号不变
        "minor_version": "V9.9.0",  # 小版本号更新
        "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/new_minor_version.zip"
    }
    
    task_info["current_time"] = "2025-06-17 15:35:00"
    
    try:
        notification3 = execute_notification_formatter(
            oppo_task.ai_formatter_code,
            updated_data_minor,
            task_info
        )
        print("✅ 代码执行成功")
        print("📄 生成的通知内容:")
        print("-" * 40)
        print(notification3)
        print("-" * 40)
        
        # 检查是否使用了新的小版本号
        if "1155" in notification3 and "V9.9.0" in notification3:
            print("🎉 成功！AI代码正确使用了新的小版本号")
        else:
            print("❌ 失败！AI代码未正确使用新的小版本号")
            
    except Exception as e:
        print(f"❌ 代码执行失败: {e}")
    
    # 测试场景4：完全不同的版本
    print("\n📋 场景4：完全不同的版本（模拟未来更新）")
    future_data = {
        "major_version": "1200",
        "minor_version": "V10.0.0",
        "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/future_version.zip"
    }
    
    task_info["current_time"] = "2025-06-17 16:00:00"
    
    try:
        notification4 = execute_notification_formatter(
            oppo_task.ai_formatter_code,
            future_data,
            task_info
        )
        print("✅ 代码执行成功")
        print("📄 生成的通知内容:")
        print("-" * 40)
        print(notification4)
        print("-" * 40)
        
        # 检查是否使用了未来版本数据
        if "1200" in notification4 and "V10.0.0" in notification4:
            print("🎉 成功！AI代码正确使用了未来版本数据")
        else:
            print("❌ 失败！AI代码未正确使用未来版本数据")
            
    except Exception as e:
        print(f"❌ 代码执行失败: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 总结分析:")
    print("1. 如果所有场景都显示正确的动态数据，说明AI代码没有硬编码问题")
    print("2. 您看到的'固定值'实际上是当前网页的真实版本信息")
    print("3. 当版本真正更新时，AI代码会自动使用新的版本信息")
    print("4. 要验证真实效果，需要等待OPPO官方发布新版本")

if __name__ == "__main__":
    test_version_change_scenarios()
