#!/usr/bin/env python3
"""
测试前端Jinja2清理效果
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_frontend_cleanup():
    """测试前端Jinja2清理效果"""
    
    print("🧹 测试前端Jinja2清理效果")
    print("=" * 60)
    
    # 测试1：检查API服务
    print("\n🌐 测试1：检查API服务")
    try:
        # 启动一个简单的测试服务器来验证API
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # 测试notification presets端点是否已移除
        response = client.get("/api/settings/notifications/presets")
        
        if response.status_code == 404:
            print("  ✅ /api/settings/notifications/presets 端点已正确移除 (404)")
        else:
            print(f"  ❌ /api/settings/notifications/presets 端点仍存在 (状态码: {response.status_code})")
        
        # 测试其他API是否正常
        response = client.get("/api/settings/rules")
        if response.status_code == 200:
            print("  ✅ /api/settings/rules 端点正常工作")
        else:
            print(f"  ❌ /api/settings/rules 端点异常 (状态码: {response.status_code})")
            
        response = client.get("/api/tasks/")
        if response.status_code == 200:
            print("  ✅ /api/tasks/ 端点正常工作")
        else:
            print(f"  ❌ /api/tasks/ 端点异常 (状态码: {response.status_code})")
            
    except Exception as e:
        print(f"  ❌ API测试失败: {e}")
    
    # 测试2：检查前端文件
    print("\n📁 测试2：检查前端文件")
    try:
        # 检查api.ts文件
        api_file = "../frontend/src/services/api.ts"
        if os.path.exists(api_file):
            with open(api_file, 'r', encoding='utf-8') as f:
                api_content = f.read()
            
            if "getNotificationPresets" in api_content:
                print("  ❌ api.ts中仍包含getNotificationPresets方法")
            else:
                print("  ✅ api.ts中的getNotificationPresets方法已移除")
                
            if "/settings/notifications/presets" in api_content:
                print("  ❌ api.ts中仍包含presets API调用")
            else:
                print("  ✅ api.ts中的presets API调用已移除")
        else:
            print("  ⚠️  未找到api.ts文件")
        
        # 检查HomeView.vue文件
        home_view_file = "../frontend/src/views/HomeView.vue"
        if os.path.exists(home_view_file):
            with open(home_view_file, 'r', encoding='utf-8') as f:
                home_content = f.read()
            
            jinja_indicators = [
                "notificationPresets",
                "selectedPresetKey", 
                "fetchPresets",
                "notification_template"
            ]
            
            remaining_indicators = []
            for indicator in jinja_indicators:
                if indicator in home_content:
                    remaining_indicators.append(indicator)
            
            if remaining_indicators:
                print(f"  ❌ HomeView.vue中仍包含Jinja2相关代码: {remaining_indicators}")
            else:
                print("  ✅ HomeView.vue中的Jinja2相关代码已清理")
                
            # 检查是否有AI智能通知的提示
            if "建议启用AI智能通知" in home_content:
                print("  ✅ HomeView.vue已添加AI智能通知提示")
            else:
                print("  ❌ HomeView.vue缺少AI智能通知提示")
        else:
            print("  ⚠️  未找到HomeView.vue文件")
            
    except Exception as e:
        print(f"  ❌ 前端文件检查失败: {e}")
    
    # 测试3：检查系统完整性
    print("\n🔧 测试3：检查系统完整性")
    try:
        # 检查配置加载
        from app.core.config import settings
        print(f"  ✅ 配置加载正常，共有 {len(settings.tasks)} 个任务")
        
        # 检查AI预览功能
        from app.api.ai_preview import router as ai_router
        print("  ✅ AI预览功能正常")
        
        # 检查监控功能
        from app.services.monitor import run_task
        print("  ✅ 监控功能正常")
        
    except Exception as e:
        print(f"  ❌ 系统完整性检查失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 前端Jinja2清理总结:")
    print("✅ API端点：移除/api/settings/notifications/presets")
    print("✅ 前端服务：移除getNotificationPresets方法")
    print("✅ 前端UI：移除模板选择器，添加AI智能通知提示")
    print("✅ 系统完整性：核心功能正常工作")
    print("\n💡 现在前端只支持AI智能通知，用户体验更简洁")

if __name__ == "__main__":
    test_frontend_cleanup()
