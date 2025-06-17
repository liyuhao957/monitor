#!/usr/bin/env python3
"""
更新OPPO任务配置，保存修复后的AI代码
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.ai_notifier import analyze_notification_content
from pydantic import HttpUrl

def update_oppo_task():
    """更新OPPO任务的AI配置"""
    
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
    
    # 模拟页面内容（用于生成AI模板）
    page_content = """1155 <a href="https://ie-activity-cn.heytapimage.com/static/quickgame/tools/e4d31728063eb9e67443bdda8e6849f6.zip" target="_blank">OPPO 小游戏调试器 V9.8.0</a>1144 <a href="https://ie-activity-cn.heytapimage.com/static/quickgame/tools/old_version.zip" target="_blank">OPPO 小游戏调试器 V9.7.0</a>"""
    
    try:
        # 重新生成AI模板
        print("🤖 重新生成AI模板...")
        result = analyze_notification_content(oppo_task, page_content)
        
        if result and result.formatter_code:
            # 更新任务配置
            oppo_task.ai_formatter_code = result.formatter_code
            if result.extraction_rules:
                oppo_task.ai_extraction_rules = result.extraction_rules
            
            # 保存配置
            import yaml
            config_path = "../config.yaml"  # 使用根目录的配置文件

            # 将settings转换为字典并保存
            config_dict = {
                "tasks": [],
                "notification_presets": settings.notification_presets
            }

            # 转换任务列表，处理特殊字段
            for task in settings.tasks:
                task_dict = task.model_dump()
                # 将HttpUrl对象转换为字符串
                if 'url' in task_dict:
                    task_dict['url'] = str(task_dict['url'])
                config_dict["tasks"].append(task_dict)

            # 添加其他配置项
            if hasattr(settings, 'api_settings') and settings.api_settings:
                config_dict["api_settings"] = settings.api_settings.model_dump()

            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, width=1000)
            
            print("✅ OPPO任务配置更新成功!")
            print(f"📝 已保存AI格式化代码 ({len(result.formatter_code)} 字符)")
            if result.extraction_rules:
                print(f"🔧 已保存提取规则 ({len(result.extraction_rules)} 个字段)")
                for field, rule in result.extraction_rules.items():
                    print(f"  - {field}: {rule}")
            
            print("\n🎯 下次监控时将使用新的AI代码，不再出现固定值问题")
            
        else:
            print("❌ AI模板生成失败")
            
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_oppo_task()
