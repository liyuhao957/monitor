#!/usr/bin/env python3
"""
测试通知一致性：验证AI代码输出与飞书通知的一致性
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.code_executor import execute_notification_formatter

def test_notification_consistency():
    """测试通知一致性"""
    
    print("🔍 测试通知一致性：AI代码输出 vs 飞书通知")
    print("=" * 60)
    
    # 找到OPPO任务
    oppo_task = None
    for task in settings.tasks:
        if task.name == "OPPO":
            oppo_task = task
            break
    
    if not oppo_task or not oppo_task.ai_formatter_code:
        print("❌ 未找到OPPO任务或AI代码")
        return
    
    print(f"✅ 找到OPPO任务")
    print(f"📝 notification_template: {oppo_task.notification_template}")
    print(f"💻 ai_formatter_code长度: {len(oppo_task.ai_formatter_code)} 字符")
    
    # 模拟实际监控时的数据
    test_data = {
        "major_version": "1155",
        "minor_version": "V9.8.0", 
        "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/e4d31728063eb9e67443bdda8e6849f6.zip"
    }
    
    task_info = {
        "name": "OPPO",
        "url": "https://ie-activity-cn.heytapimage.com/static/minigame/CN/docs/index.html#/download/index",
        "current_time": "2025-06-17 15:46:59"  # 使用飞书通知中的时间
    }
    
    try:
        # 执行AI代码
        ai_output = execute_notification_formatter(
            oppo_task.ai_formatter_code,
            test_data,
            task_info
        )
        
        print("\n📄 AI代码实际输出:")
        print("-" * 50)
        print(ai_output)
        print("-" * 50)
        
        # 分析输出特征
        print("\n🔍 输出特征分析:")
        
        # 检查标题格式
        if "## 🎮 OPPO小游戏调试器版本更新" in ai_output:
            print("✅ 标题格式：使用 ## 标题（与飞书通知一致）")
        elif "🎮 **OPPO小游戏调试器版本更新**" in ai_output:
            print("❌ 标题格式：使用 ** 加粗（与AI预览一致，但与飞书不符）")
        
        # 检查时间格式
        if "⏰ **更新时间**: " in ai_output:
            print("✅ 时间格式：使用加粗格式（与飞书通知一致）")
        elif "⏰ **检测时间**: " in ai_output:
            print("❌ 时间格式：使用检测时间（与AI预览一致，但与飞书不符）")
        
        # 检查表格格式
        if "| 项目 | 版本信息 |" in ai_output:
            print("✅ 表格格式：两列表格（与飞书通知一致）")
        elif "| 项目 | 版本号 | 操作 |" in ai_output:
            print("❌ 表格格式：三列表格（与AI预览一致，但与飞书不符）")
        
        # 检查链接格式
        if "[📥 点击下载](" in ai_output:
            print("✅ 链接格式：完整markdown链接（正确）")
        elif "📥 点击下载" in ai_output and "[" not in ai_output:
            print("❌ 链接格式：纯文本（飞书渲染问题）")
        
        # 检查版本号
        if "1155" in ai_output and "V9.8.0" in ai_output:
            print("✅ 版本号：正确使用动态数据")
        else:
            print("❌ 版本号：未正确使用动态数据")
        
        print("\n🎯 结论:")
        print("如果AI代码输出与飞书通知格式一致，说明问题已解决")
        print("如果仍有差异，可能是飞书markdown渲染的问题")
        
        return ai_output
        
    except Exception as e:
        print(f"❌ AI代码执行失败: {e}")
        return None

def compare_with_feishu_notification():
    """与飞书通知进行对比"""
    
    print("\n" + "=" * 60)
    print("📱 飞书通知内容（您提供的）:")
    print("-" * 50)
    
    feishu_notification = """## 🎮 OPPO小游戏调试器版本更新

⏰ 更新时间: 2025-06-17 15:46:59

### 📋 版本详情

| 项目 | 版本信息 |
|------|----------|
| 🔢 引擎大版本号 | `1155` |
| 📱 引擎小版本号 | `V9.8.0` |
| 📦 下载地址 | 📥 点击下载 |

🔗 查看完整版本列表
💡 监控任务: OPPO | 🤖 自动监控通知"""
    
    print(feishu_notification)
    print("-" * 50)
    
    print("\n🔍 飞书通知特征:")
    print("- 标题：## 格式")
    print("- 时间：⏰ 更新时间（无加粗）")
    print("- 表格：两列格式")
    print("- 链接：显示为纯文本（可能是飞书渲染问题）")

if __name__ == "__main__":
    ai_output = test_notification_consistency()
    compare_with_feishu_notification()
    
    if ai_output:
        print("\n🤔 如果AI输出正确但飞书显示不同，可能的原因：")
        print("1. 飞书markdown渲染限制")
        print("2. 链接格式在飞书中的特殊处理")
        print("3. 加粗格式在飞书卡片中的显示差异")
