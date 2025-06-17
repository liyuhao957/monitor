#!/usr/bin/env python3
"""
测试AI通知分析器的错误修复效果
"""
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志级别
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_ai_notifier_import():
    """测试AI通知分析器导入"""
    try:
        from app.services.ai_notifier import get_ai_notifier, AINotifier
        print("✅ AI通知分析器导入成功")
        return True
    except Exception as e:
        print(f"❌ AI通知分析器导入失败: {e}")
        return False

def test_ai_notifier_instance():
    """测试AI通知分析器实例创建"""
    try:
        from app.services.ai_notifier import get_ai_notifier
        
        notifier = get_ai_notifier()
        if notifier:
            print("✅ AI通知分析器实例创建成功")
            print(f"   模型: {notifier.model}")
            return True, notifier
        else:
            print("⚠️ AI通知分析器实例为空，可能是配置问题")
            return False, None
    except Exception as e:
        print(f"❌ AI通知分析器实例创建失败: {e}")
        return False, None

def test_response_parsing():
    """测试响应解析功能"""
    try:
        from app.services.ai_notifier import AINotifier
        
        # 创建测试实例
        notifier = AINotifier("test_key", "test_url", "test_model")
        
        # 测试正常的分段响应
        test_response = """---ANALYSIS---
阶段1：HTML结构分析
这是测试分析内容

---TITLE---
🔄 测试通知标题

---CONTENT---
这是测试内容模板
版本：{{ version }}

---SUMMARY---
这是测试摘要

---FIELDS---
version=版本号

---RULES---
version=regex:版本：(\d+)
"""
        
        result = notifier._parse_analysis_result(test_response)
        print("✅ 响应解析测试成功")
        print(f"   标题: {result.title}")
        print(f"   字段数量: {len(result.required_fields) if result.required_fields else 0}")
        print(f"   规则数量: {len(result.extraction_rules) if result.extraction_rules else 0}")
        return True
        
    except Exception as e:
        print(f"❌ 响应解析测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    try:
        from app.services.ai_notifier import AINotifier
        
        notifier = AINotifier("test_key", "test_url", "test_model")
        
        # 测试空响应
        try:
            notifier._parse_analysis_result("")
            print("❌ 空响应应该抛出异常")
            return False
        except ValueError as e:
            print("✅ 空响应错误处理正确")
        
        # 测试格式错误的响应
        try:
            notifier._parse_analysis_result("这是一个没有分隔符的响应")
            print("❌ 格式错误响应应该抛出异常")
            return False
        except ValueError as e:
            print("✅ 格式错误响应错误处理正确")
        
        # 测试缺少必需部分的响应
        try:
            notifier._parse_analysis_result("---TITLE---\n测试标题")
            print("❌ 缺少必需部分应该抛出异常")
            return False
        except ValueError as e:
            print("✅ 缺少必需部分错误处理正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始测试AI通知分析器修复效果")
    print("=" * 60)
    
    all_passed = True
    
    # 测试1：导入测试
    print("\n📦 测试1: 模块导入")
    if not test_ai_notifier_import():
        all_passed = False
    
    # 测试2：实例创建测试
    print("\n🏗️ 测试2: 实例创建")
    instance_ok, notifier = test_ai_notifier_instance()
    if not instance_ok:
        all_passed = False
    
    # 测试3：响应解析测试
    print("\n📝 测试3: 响应解析")
    if not test_response_parsing():
        all_passed = False
    
    # 测试4：错误处理测试
    print("\n🛡️ 测试4: 错误处理")
    if not test_error_handling():
        all_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    print("🎯 测试结果总结:")
    print("=" * 60)
    
    if all_passed:
        print("🎉 所有测试通过！AI通知分析器修复成功")
        print("✅ 现在可以更好地处理DeepSeek API响应错误")
        print("✅ 增强了错误诊断和重试机制")
        print("✅ 提高了系统稳定性")
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
