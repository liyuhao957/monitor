#!/usr/bin/env python3
"""
修复配置文件中AI代码的格式问题
"""
import yaml
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def fix_ai_code():
    """修复OPPO任务的AI代码格式问题"""
    
    print("🔧 修复AI代码格式问题...")
    
    # 找到OPPO任务
    oppo_task = None
    for task in settings.tasks:
        if task.name == "OPPO":
            oppo_task = task
            break
    
    if not oppo_task:
        print("❌ 未找到OPPO任务")
        return
    
    print(f"📝 当前AI代码长度: {len(oppo_task.ai_formatter_code) if oppo_task.ai_formatter_code else 0}")
    
    if oppo_task.ai_formatter_code:
        print("🔍 当前代码前200字符:")
        print(oppo_task.ai_formatter_code[:200])
        print("...")
    
    # 生成正确的AI代码
    correct_ai_code = '''def format_notification(extracted_data: dict, task_info: dict) -> str:
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
        title = f"🎮 {task_name}小游戏调试器版本更新"

        # 构建表格内容
        table_content = "| 项目 | 版本信息 |\\n"
        table_content += "|------|----------|\\n"
        table_content += f"| 🔢 引擎大版本号 | `{major_version}` |\\n"
        table_content += f"| 📱 引擎小版本号 | `{minor_version}` |\\n"

        # 处理下载链接
        if download_url and download_url != '未知':
            download_link = f"[📥 点击下载]({download_url})"
            table_content += f"| 📦 下载地址 | {download_link} |\\n"
        else:
            table_content += "| 📦 下载地址 | 暂无可用链接 |\\n"

        # 组装完整通知
        notification = f"## {title}\\n\\n"
        notification += f"⏰ **更新时间**: {current_time}\\n\\n"
        notification += "### 📋 版本详情\\n\\n"
        notification += table_content
        notification += "\\n🔗 [查看完整版本列表](https://ie-activity-cn.heytapimage.com/static/minigame/CN/docs/index.html#/download/index)\\n\\n"
        notification += "---\\n"
        notification += f"💡 **监控任务**: {task_name} | 🤖 **自动监控通知**"

        return notification

    except Exception as e:
        return f"❌ 通知格式化失败: {str(e)}"'''
    
    # 更新任务的AI代码
    oppo_task.ai_formatter_code = correct_ai_code
    
    # 保存配置
    config_path = "../config.yaml"
    
    try:
        # 构建配置字典
        config_dict = {
            "api_settings": {
                "ai_provider": "openai",
                "deepseek_api_key": "sk-33c4b6f409f149cf89139fb4c4900439",
                "deepseek_base_url": "https://api.deepseek.com",
                "deepseek_model": "deepseek-chat",
                "openai_api_key": "sk-6KwYGpsonYqWBAxrg9hEyjfEL7Bpak478TjuxCA7gf52GdvGVDfQ",
                "openai_base_url": "https://api.oaipro.com/v1",
                "openai_model": "claude-sonnet-4-20250514"
            },
            "tasks": [],
            "notification_presets": settings.notification_presets
        }
        
        # 转换任务列表
        for task in settings.tasks:
            task_dict = task.model_dump()
            # 将HttpUrl对象转换为字符串
            if 'url' in task_dict:
                task_dict['url'] = str(task_dict['url'])
            config_dict["tasks"].append(task_dict)
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, width=1000)
        
        print("✅ AI代码修复完成")
        print(f"💾 配置已保存到: {config_path}")
        print(f"📝 新代码长度: {len(correct_ai_code)} 字符")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_ai_code()
