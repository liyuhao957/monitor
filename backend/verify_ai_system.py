#!/usr/bin/env python3
"""
验证AI通知系统简化后的功能
"""

def verify_imports():
    """验证所有必要的导入"""
    try:
        from app.services.ai_notifier import analyze_notification_content, NotificationAnalysis
        from app.services import monitor
        from app.api.ai_preview import router
        print("✅ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def verify_function_signatures():
    """验证函数签名正确"""
    try:
        from app.services.ai_notifier import analyze_notification_content
        import inspect
        
        # 检查 analyze_notification_content 函数签名
        sig = inspect.signature(analyze_notification_content)
        params = list(sig.parameters.keys())
        
        expected_params = ['task', 'content']
        if params == expected_params:
            print("✅ analyze_notification_content 函数签名正确")
            return True
        else:
            print(f"❌ analyze_notification_content 函数签名错误: 期望 {expected_params}, 实际 {params}")
            return False
    except Exception as e:
        print(f"❌ 函数签名验证失败: {e}")
        return False

def verify_deleted_functions():
    """验证已删除的函数确实不存在"""
    try:
        from app.services.ai_notifier import analyze_notification_content_change
        print("❌ analyze_notification_content_change 函数仍然存在，应该已被删除")
        return False
    except ImportError:
        print("✅ analyze_notification_content_change 函数已成功删除")
        return True
    except Exception as e:
        print(f"❌ 验证删除函数时出错: {e}")
        return False

def main():
    """主验证函数"""
    print("🔍 开始验证AI通知系统简化...")
    print("=" * 50)
    
    tests = [
        ("导入验证", verify_imports),
        ("函数签名验证", verify_function_signatures), 
        ("删除函数验证", verify_deleted_functions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}:")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print(f"📊 验证结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 AI通知系统简化成功！")
        print("\n📋 系统现在的工作流程:")
        print("1. 用户设置监控任务时，调用 analyze_notification_content 生成模板")
        print("2. 生成的模板和提取规则保存到任务配置")
        print("3. 监控时直接使用保存的模板，不再调用AI")
        print("4. 节省API调用，保证一致性")
    else:
        print("⚠️  部分测试失败，请检查相关问题")

if __name__ == "__main__":
    main()
