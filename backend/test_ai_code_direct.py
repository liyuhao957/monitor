#!/usr/bin/env python3
"""
直接测试AI生成的代码，不依赖配置文件
"""

# AI生成的代码（从配置文件中提取）
ai_formatter_code = '''def format_notification(extracted_data: dict, task_info: dict) -> str:
    """
    格式化OPPO小游戏调试器版本更新通知
    Args:
    extracted_data: 提取的数据字典
    task_info: 任务信息 (name, url, current_time等)
    Returns:
    str: 格式化后的通知内容
    """
    try:
        # 获取提取的数据
        major_version = extracted_data.get('major_version', '未知')
        minor_version = extracted_data.get('minor_version', '未知')
        download_url = extracted_data.get('download_url', '')

        # 获取任务信息
        task_name = task_info.get('name', 'OPPO')
        current_time = task_info.get('current_time', '')

        # 构建通知内容
        title = f"🎮 {task_name} 小游戏调试器版本更新"

        # 构建表格内容
        table_content = "| 项目 | 版本信息 |\\n"
        table_content += "|------|----------|\\n"
        table_content += f"| 🔢 引擎大版本号 | `{major_version}` |\\n"
        table_content += f"| 📱 引擎小版本号 | `{minor_version}` |\\n"

        # 处理下载链接
        if download_url and download_url != '未知':
            download_link = f"[📥 点击下载]({download_url})"
            table_content += f"| 💾 下载地址 | {download_link} |\\n"
        else:
            table_content += "| 💾 下载地址 | 暂无可用链接 |\\n"

        # 组装完整通知
        notification = f"## {title}\\n\\n"
        notification += f"⏰ **更新时间**: {current_time}\\n\\n"
        notification += "### 📋 版本详情\\n\\n"
        notification += table_content
        notification += "\\n---\\n"
        notification += "💡 **提示**: 请及时更新到最新版本以获得最佳开发体验"

        return notification

    except Exception as e:
        return f"❌ 通知格式化失败: {str(e)}"'''

def test_ai_code():
    """测试AI生成的代码"""
    print("🧪 测试AI生成的代码...")
    print("=" * 60)
    
    # 测试场景1：当前版本数据
    print("\n📋 测试场景1：当前版本数据")
    current_data = {
        "major_version": "1155",
        "minor_version": "V9.8.0",
        "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/e4d31728063eb9e67443bdda8e6849f6.zip"
    }
    
    task_info = {
        "name": "OPPO",
        "url": "https://ie-activity-cn.heytapimage.com/static/minigame/CN/docs/index.html#/download/index",
        "current_time": "2025-06-17 15:20:00"
    }
    
    try:
        # 执行AI代码
        exec(ai_formatter_code, globals())
        
        notification1 = format_notification(current_data, task_info)
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
    print("\n📋 测试场景2：新版本数据（模拟版本更新）")
    new_data = {
        "major_version": "1166",  # 新的大版本号
        "minor_version": "V9.9.0",  # 新的小版本号
        "download_url": "https://ie-activity-cn.heytapimage.com/static/quickgame/tools/new_version.zip"  # 新的下载链接
    }
    
    task_info["current_time"] = "2025-06-17 15:25:00"
    
    try:
        notification2 = format_notification(new_data, task_info)
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
    print("\n📋 测试场景3：缺失数据处理")
    incomplete_data = {
        "major_version": "1177",
        # 缺少 minor_version 和 download_url
    }
    
    try:
        notification3 = format_notification(incomplete_data, task_info)
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
    test_ai_code()
