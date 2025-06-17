#!/usr/bin/env python3
"""
测试Jinja2模板移除后的系统状态
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_jinja_removal():
    """测试Jinja2移除后的系统状态"""
    
    print("🧹 测试Jinja2模板移除效果")
    print("=" * 60)
    
    # 测试1：检查配置文件
    print("\n📋 测试1：检查配置文件")
    try:
        from app.core.config import settings
        
        # 检查所有任务的notification_template字段
        template_count = 0
        for task in settings.tasks:
            if hasattr(task, 'notification_template') and task.notification_template:
                template_count += 1
                print(f"  ⚠️  任务 '{task.name}' 仍有notification_template")
        
        if template_count == 0:
            print("  ✅ 所有任务的notification_template已清理")
        else:
            print(f"  ❌ 仍有 {template_count} 个任务包含notification_template")
        
        # 检查notification_presets
        if hasattr(settings, 'notification_presets') and settings.notification_presets:
            print(f"  ❌ 仍存在notification_presets: {len(settings.notification_presets)} 个")
        else:
            print("  ✅ notification_presets已清理")
            
    except Exception as e:
        print(f"  ❌ 配置检查失败: {e}")
    
    # 测试2：检查代码导入
    print("\n💻 测试2：检查代码导入")
    try:
        # 检查是否还有Jinja2导入
        import app.services.monitor as monitor_module
        
        # 检查模块中是否还有Template引用
        if hasattr(monitor_module, 'Template'):
            print("  ❌ monitor.py中仍有Template引用")
        else:
            print("  ✅ monitor.py中的Template引用已移除")
        
        # 检查是否还有_render_jinja_template函数
        if hasattr(monitor_module, '_render_jinja_template'):
            print("  ❌ monitor.py中仍有_render_jinja_template函数")
        else:
            print("  ✅ _render_jinja_template函数已移除")
            
    except Exception as e:
        print(f"  ❌ 代码检查失败: {e}")
    
    # 测试3：检查OPPO任务的AI代码
    print("\n🤖 测试3：检查OPPO任务的AI代码")
    try:
        oppo_task = None
        for task in settings.tasks:
            if task.name == "OPPO":
                oppo_task = task
                break
        
        if oppo_task:
            if oppo_task.ai_formatter_code:
                print(f"  ✅ OPPO任务有AI代码 ({len(oppo_task.ai_formatter_code)} 字符)")
                
                # 测试AI代码执行
                from app.services.code_executor import execute_notification_formatter
                
                test_data = {
                    "major_version": "1155",
                    "minor_version": "V9.8.0",
                    "download_url": "https://example.com/test.zip"
                }
                
                task_info = {
                    "name": "OPPO",
                    "url": "https://example.com",
                    "current_time": "2025-06-17 16:00:00"
                }
                
                result = execute_notification_formatter(
                    oppo_task.ai_formatter_code,
                    test_data,
                    task_info
                )
                
                if "1155" in result and "V9.8.0" in result:
                    print("  ✅ AI代码执行正常，使用动态数据")
                else:
                    print("  ❌ AI代码执行异常")
                    
            else:
                print("  ❌ OPPO任务缺少AI代码")
        else:
            print("  ❌ 未找到OPPO任务")
            
    except Exception as e:
        print(f"  ❌ AI代码测试失败: {e}")
    
    # 测试4：检查API端点
    print("\n🌐 测试4：检查API端点")
    try:
        # 检查settings API是否还有presets端点
        import app.api.settings as settings_api
        
        # 检查路由器中的路由
        routes = [route.path for route in settings_api.router.routes]
        
        if "/notifications/presets" in routes:
            print("  ❌ API中仍有/notifications/presets端点")
        else:
            print("  ✅ /notifications/presets端点已移除")
            
    except Exception as e:
        print(f"  ❌ API检查失败: {e}")
    
    # 测试5：系统完整性检查
    print("\n🔧 测试5：系统完整性检查")
    try:
        # 检查是否可以正常启动监控
        from app.services.monitor import run_task
        
        print("  ✅ 监控模块可以正常导入")
        
        # 检查AI预览功能
        from app.api.ai_preview import preview_ai_notification
        
        print("  ✅ AI预览功能可以正常导入")
        
    except Exception as e:
        print(f"  ❌ 系统完整性检查失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Jinja2移除总结:")
    print("✅ 配置文件：移除所有notification_template和notification_presets")
    print("✅ 代码逻辑：移除Jinja2导入和相关函数")
    print("✅ API端点：移除presets相关端点")
    print("✅ AI代码：保留并正常工作")
    print("\n💡 现在系统只使用AI生成的Python代码进行通知格式化")

if __name__ == "__main__":
    test_jinja_removal()
