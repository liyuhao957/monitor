#!/usr/bin/env python3
"""
测试AI配置持久化
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ai_config_persistence():
    """测试AI配置的保存和加载"""
    
    print("🔍 测试AI配置持久化")
    print("=" * 60)
    
    # 测试1：检查OPPO任务的AI配置
    print("\n📋 测试1：检查OPPO任务的AI配置")
    try:
        from app.core.config import settings
        
        oppo_task = None
        for task in settings.tasks:
            if task.name == "OPPO":
                oppo_task = task
                break
        
        if oppo_task:
            print(f"✅ 找到OPPO任务")
            print(f"🤖 AI分析启用: {oppo_task.ai_analysis_enabled}")
            print(f"📝 AI描述: {oppo_task.ai_description[:50] if oppo_task.ai_description else 'None'}...")
            
            if oppo_task.ai_extraction_rules:
                print(f"🔧 AI提取规则: {len(oppo_task.ai_extraction_rules)} 个字段")
                for field, rule in oppo_task.ai_extraction_rules.items():
                    print(f"   - {field}: {rule[:30]}...")
            else:
                print("❌ 缺少AI提取规则")
            
            if oppo_task.ai_formatter_code:
                print(f"💻 AI格式化代码: {len(oppo_task.ai_formatter_code)} 字符")
                # 检查代码是否包含关键函数
                if "def format_notification" in oppo_task.ai_formatter_code:
                    print("   ✅ 包含format_notification函数")
                else:
                    print("   ❌ 缺少format_notification函数")
            else:
                print("❌ 缺少AI格式化代码")
        else:
            print("❌ 未找到OPPO任务")
            
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
    
    # 测试2：测试API返回的数据结构
    print("\n🌐 测试2：测试API返回的数据结构")
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # 获取所有任务
        response = client.get("/api/tasks/")
        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ API返回 {len(tasks)} 个任务")
            
            # 检查OPPO任务的字段
            oppo_api_task = None
            for task in tasks:
                if task.get("name") == "OPPO":
                    oppo_api_task = task
                    break
            
            if oppo_api_task:
                print("✅ API中找到OPPO任务")
                
                # 检查AI相关字段
                ai_fields = [
                    "ai_analysis_enabled",
                    "ai_description", 
                    "ai_extraction_rules",
                    "ai_formatter_code"
                ]
                
                for field in ai_fields:
                    if field in oppo_api_task:
                        value = oppo_api_task[field]
                        if value:
                            if isinstance(value, str):
                                print(f"   ✅ {field}: {len(value)} 字符")
                            elif isinstance(value, dict):
                                print(f"   ✅ {field}: {len(value)} 个字段")
                            else:
                                print(f"   ✅ {field}: {value}")
                        else:
                            print(f"   ⚠️  {field}: 空值")
                    else:
                        print(f"   ❌ 缺少字段: {field}")
            else:
                print("❌ API中未找到OPPO任务")
        else:
            print(f"❌ API请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")
    
    # 测试3：模拟前端编辑流程
    print("\n🖥️  测试3：模拟前端编辑流程")
    try:
        # 模拟前端获取任务数据
        from app.core.config import settings
        
        oppo_task = None
        for task in settings.tasks:
            if task.name == "OPPO":
                oppo_task = task
                break
        
        if oppo_task:
            # 模拟前端openEditDialog逻辑
            print("📝 模拟前端编辑对话框打开...")
            
            # 检查AI配置状态
            if oppo_task.ai_analysis_enabled and oppo_task.ai_formatter_code:
                template_display = '✅ AI通知模板已配置\n\n如需重新生成，请使用下方的"生成AI模板预览"功能。'
                print(f"✅ 前端应显示: {template_display[:30]}...")
            else:
                print("❌ 前端将显示空模板")
            
            # 检查字段完整性
            required_fields = ["ai_analysis_enabled", "ai_description", "ai_extraction_rules", "ai_formatter_code"]
            missing_fields = []
            
            for field in required_fields:
                if not hasattr(oppo_task, field) or getattr(oppo_task, field) is None:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 缺少字段: {missing_fields}")
            else:
                print("✅ 所有AI字段完整")
        else:
            print("❌ 未找到测试任务")
            
    except Exception as e:
        print(f"❌ 前端流程测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 AI配置持久化测试总结:")
    print("✅ 后端配置：检查AI字段的保存和加载")
    print("✅ API接口：验证AI字段在API中的传输")
    print("✅ 前端逻辑：模拟编辑对话框的状态恢复")
    print("\n💡 如果所有测试通过，AI配置应该能正确持久化")

if __name__ == "__main__":
    test_ai_config_persistence()
