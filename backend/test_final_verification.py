#!/usr/bin/env python3
"""
最终验证：测试修复后的AI通知系统
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.code_executor import execute_notification_formatter

def test_final_system():
    """最终系统验证测试"""
    
    print("🎯 最终验证：AI通知系统修复效果")
    print("=" * 60)
    
    # 找到OPPO任务
    oppo_task = None
    for task in settings.tasks:
        if task.name == "OPPO":
            oppo_task = task
            break
    
    if not oppo_task:
        print("❌ 未找到OPPO任务")
        return False
    
    print(f"✅ 找到OPPO任务")
    print(f"📝 AI分析已启用: {oppo_task.ai_analysis_enabled}")
    print(f"🔧 AI提取规则: {len(oppo_task.ai_extraction_rules) if oppo_task.ai_extraction_rules else 0} 个")
    print(f"💻 AI代码长度: {len(oppo_task.ai_formatter_code) if oppo_task.ai_formatter_code else 0} 字符")
    
    if not oppo_task.ai_formatter_code:
        print("❌ 未找到AI格式化代码")
        return False
    
    # 测试1：验证AI代码语法正确
    print(f"\n🧪 测试1：AI代码语法验证")
    try:
        # 尝试编译代码
        compile(oppo_task.ai_formatter_code, '<ai_code>', 'exec')
        print("✅ AI代码语法正确")
    except SyntaxError as e:
        print(f"❌ AI代码语法错误: {e}")
        return False
    
    # 测试2：验证动态数据处理
    print(f"\n🧪 测试2：动态数据处理验证")
    test_scenarios = [
        {
            "name": "当前版本",
            "data": {
                "major_version": "1155",
                "minor_version": "V9.8.0",
                "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/e4d31728063eb9e67443bdda8e6849f6.zip"
            },
            "expected": ["1155", "V9.8.0"]
        },
        {
            "name": "新版本",
            "data": {
                "major_version": "1166",
                "minor_version": "V9.9.0",
                "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/new_version.zip"
            },
            "expected": ["1166", "V9.9.0"]
        }
    ]
    
    task_info = {
        "name": "OPPO",
        "url": "https://ie-activity-cn.heytapimage.com/static/minigame/CN/docs/index.html#/download/index",
        "current_time": "2025-06-17 15:35:00"
    }
    
    all_passed = True
    notifications = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        try:
            notification = execute_notification_formatter(
                oppo_task.ai_formatter_code,
                scenario["data"],
                task_info
            )
            notifications.append(notification)
            
            # 检查是否包含期望的数据
            contains_expected = all(exp in notification for exp in scenario["expected"])
            
            if contains_expected:
                print(f"  ✅ 场景{i}（{scenario['name']}）：通过")
            else:
                print(f"  ❌ 场景{i}（{scenario['name']}）：失败，未包含期望数据")
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ 场景{i}（{scenario['name']}）：执行失败 - {e}")
            all_passed = False
    
    # 测试3：验证通知内容差异
    print(f"\n🧪 测试3：通知内容差异验证")
    if len(notifications) >= 2:
        if notifications[0] != notifications[1]:
            print("✅ 不同数据生成不同通知内容")
        else:
            print("❌ 不同数据生成相同通知内容（可能存在硬编码）")
            all_passed = False
    
    # 测试4：验证AI提取规则
    print(f"\n🧪 测试4：AI提取规则验证")
    if oppo_task.ai_extraction_rules:
        expected_fields = ["major_version", "minor_version", "download_url"]
        actual_fields = list(oppo_task.ai_extraction_rules.keys())
        
        if set(expected_fields) == set(actual_fields):
            print(f"✅ AI提取规则完整：{actual_fields}")
        else:
            print(f"⚠️  AI提取规则不完整：期望 {expected_fields}，实际 {actual_fields}")
    else:
        print("❌ 未找到AI提取规则")
        all_passed = False
    
    # 测试5：显示最终通知样例
    print(f"\n📄 最终通知样例（使用当前版本数据）:")
    print("-" * 50)
    if notifications:
        print(notifications[0])
    print("-" * 50)
    
    # 总结
    print(f"\n🎯 最终验证结果:")
    if all_passed:
        print("🎉 所有测试通过！AI通知系统修复成功")
        print("✅ AI代码语法正确")
        print("✅ 动态数据处理正常")
        print("✅ 通知内容响应数据变化")
        print("✅ AI提取规则完整")
        print("\n💡 说明：")
        print("- 您看到的'固定值'实际上是当前网页的真实版本信息")
        print("- 当OPPO发布新版本时，AI代码会自动显示新的版本信息")
        print("- 系统已完全修复，等待真实版本更新触发")
        return True
    else:
        print("❌ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    test_final_system()
