#!/usr/bin/env python3
"""
检查模板状态和AI流程
"""

def check_current_status():
    """检查当前任务状态"""
    from app.core.config import settings
    
    print("🔍 检查当前任务状态...")
    print("=" * 60)
    
    # 查找荣耀调试器任务
    honor_task = None
    for task in settings.tasks:
        if task.name == "荣耀调试器":
            honor_task = task
            break
    
    if not honor_task:
        print("❌ 未找到荣耀调试器任务")
        return
    
    print(f"📋 任务名称: {honor_task.name}")
    print(f"🔗 URL: {honor_task.url}")
    print(f"⚙️  AI分析启用: {honor_task.ai_analysis_enabled}")
    print(f"📝 AI描述: {honor_task.ai_description}")
    print(f"📄 通知模板: {honor_task.notification_template}")
    print(f"🔧 提取规则: {honor_task.ai_extraction_rules}")
    
    print("\n" + "=" * 60)
    print("📊 状态分析:")
    print("=" * 60)
    
    if honor_task.ai_analysis_enabled:
        print("✅ AI分析已启用")
        
        if honor_task.notification_template:
            if honor_task.notification_template in settings.notification_presets:
                print("⚠️  使用预设模板，不是AI生成的模板")
            else:
                print("✅ 使用自定义模板（可能是AI生成的）")
                print(f"模板长度: {len(honor_task.notification_template)} 字符")
        else:
            print("❌ 没有通知模板 - 系统会跳过通知")
        
        if honor_task.ai_extraction_rules:
            print(f"✅ 有AI提取规则，共 {len(honor_task.ai_extraction_rules)} 个字段")
            for field, rule in honor_task.ai_extraction_rules.items():
                print(f"   - {field}: {rule}")
        else:
            print("❌ 没有AI提取规则")
    else:
        print("❌ AI分析未启用")
    
    print("\n" + "=" * 60)
    print("🎯 下一步建议:")
    print("=" * 60)
    
    if honor_task.ai_analysis_enabled and not honor_task.notification_template:
        print("1. 在前端打开荣耀调试器任务编辑")
        print("2. 点击'获取页面内容'")
        print("3. 点击'🤖 生成AI模板预览'")
        print("4. 确认模板内容后点击'保存'")
        print("5. 重新运行监控测试")
    elif honor_task.notification_template and not honor_task.ai_extraction_rules:
        print("1. 模板存在但缺少提取规则")
        print("2. 需要重新生成AI模板")
    elif honor_task.notification_template and honor_task.ai_extraction_rules:
        print("✅ 配置完整，可以进行监控测试")
    else:
        print("❓ 配置状态异常，建议重新设置")

def test_ai_generation():
    """测试AI生成功能"""
    print("\n" + "=" * 60)
    print("🤖 测试AI生成功能:")
    print("=" * 60)
    
    try:
        from app.services.ai_notifier import get_ai_notifier
        
        ai_notifier = get_ai_notifier()
        if ai_notifier:
            print("✅ AI通知器初始化成功")
            print(f"模型: {ai_notifier.model}")
            print(f"API地址: {ai_notifier.base_url}")
        else:
            print("❌ AI通知器初始化失败")
            print("请检查API配置")
            
    except Exception as e:
        print(f"❌ AI功能测试失败: {e}")

if __name__ == "__main__":
    check_current_status()
    test_ai_generation()
