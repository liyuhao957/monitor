#!/usr/bin/env python3
"""
测试去除固定模板后的AI提示词效果
"""

def test_prompt_content():
    """测试提示词内容是否已正确修改"""
    from app.services.ai_notifier import AINotifier
    
    # 创建AI通知器实例（不需要真实API密钥，只测试提示词）
    notifier = AINotifier("test_key", "test_url", "test_model")
    
    # 创建测试任务
    from app.core.config import Task
    from pydantic import HttpUrl
    
    task = Task(
        name="测试任务",
        url=HttpUrl("https://example.com"),
        frequency="30m",
        rule="css:body",
        enabled=True,
        ai_analysis_enabled=True,
        ai_description="测试监控描述"
    )
    
    # 获取系统提示词
    system_prompt = notifier._get_system_prompt()
    
    # 获取用户提示词
    user_prompt = notifier._build_structure_analysis_prompt(task, "测试内容")
    
    print("🔍 检查提示词修改效果...")
    print("=" * 60)
    
    # 检查是否移除了固定模板
    template_indicators = [
        "{{%- set items",
        "{{%- for item in items",
        "split('分隔符')",
        "item.strip()",
        "{{{{ item.strip() }}}}"
    ]
    
    found_templates = []
    for indicator in template_indicators:
        if indicator in system_prompt or indicator in user_prompt:
            found_templates.append(indicator)
    
    if found_templates:
        print("❌ 仍然包含固定模板代码:")
        for template in found_templates:
            print(f"   - {template}")
    else:
        print("✅ 已成功移除所有固定模板代码")
    
    # 检查是否强调了创造性
    creativity_indicators = [
        "创造性",
        "灵活",
        "避免任何固定模式",
        "完全根据用户需求",
        "100%按照用户"
    ]
    
    found_creativity = []
    for indicator in creativity_indicators:
        if indicator in system_prompt or indicator in user_prompt:
            found_creativity.append(indicator)
    
    print(f"\n📝 创造性强调词汇: {len(found_creativity)}/5")
    for word in found_creativity:
        print(f"   ✅ {word}")
    
    print("\n" + "=" * 60)
    print("📋 系统提示词关键部分:")
    print("=" * 60)
    
    # 显示核心原则部分
    lines = system_prompt.split('\n')
    for i, line in enumerate(lines):
        if "核心原则" in line:
            for j in range(i, min(i+10, len(lines))):
                print(lines[j])
            break
    
    print("\n" + "=" * 60)
    print("🎯 优化效果总结:")
    print("=" * 60)
    
    if not found_templates and len(found_creativity) >= 3:
        print("🎉 提示词优化成功!")
        print("✅ 移除了所有固定模板代码")
        print("✅ 增强了创造性和灵活性表述")
        print("✅ AI现在会更加灵活地根据用户需求生成模板")
    else:
        print("⚠️  提示词可能需要进一步优化")

if __name__ == "__main__":
    test_prompt_content()
