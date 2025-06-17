#!/usr/bin/env python3
"""
测试内容格式化器

验证新的通用内容格式化系统是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.content_formatter import get_content_formatter


def test_huawei_formatter():
    """测试华为快应用引擎更新说明的格式化器"""
    print("🧪 测试华为快应用引擎更新说明格式化器")
    print("=" * 60)
    
    # 模拟实际的content_block内容
    test_content = """1121版本更新说明（2025-6-6） 指南 变更点 说明 安装开发工具 "快应用官方示例"、"快应用研发助手"打开入口集成到加载器中。 详情请参见"[开发准备>安装开发工具](https://developer.huawei.com/consumer/cn/doc/quickApp-Guides/quickapp-installtool-0000001126543467)"。 华为快应用加载器使用指导 "快应用官方示例"、"快应用研发助手"使用指导。 详情请参见"[附录>华为快应用加载器使用指导](https://developer.huawei.com/consumer/cn/doc/quickApp-Guides/quickapp-loader-user-guide-0000001115925960)"。"""
    
    print("📝 原始内容:")
    print("-" * 40)
    print(test_content)
    print("-" * 40)
    
    # 测试格式化器
    formatter = get_content_formatter()
    template_context = {"content_block": test_content}
    
    formatted_context = formatter.format_content("华为快应用引擎更新说明", template_context)
    formatted_content = formatted_context["content_block"]
    
    print("\n✨ 格式化后内容:")
    print("-" * 40)
    print(formatted_content)
    print("-" * 40)
    
    # 验证格式化效果
    checks = [
        ("去掉'指南 变更点 说明'", "指南 变更点 说明" not in formatted_content),
        ("安装开发工具加粗", "**安装开发工具**：" in formatted_content),
        ("华为快应用加载器使用指导加粗", "**华为快应用加载器使用指导**：" in formatted_content),
        ("链接图标", "📋 详情请参见：" in formatted_content),
        ("包含换行分隔", "\n\n" in formatted_content),
    ]
    
    print("\n🔍 格式化效果检查:")
    print("-" * 40)
    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}: {'通过' if result else '失败'}")
        if not result:
            all_passed = False
    
    print("-" * 40)
    if all_passed:
        print("🎉 所有检查通过！格式化器工作正常")
    else:
        print("⚠️ 部分检查失败，需要调试")
    
    return all_passed


def test_custom_formatter():
    """测试自定义格式化器注册"""
    print("\n🧪 测试自定义格式化器注册")
    print("=" * 60)
    
    def custom_test_formatter(content: str) -> str:
        """测试用的自定义格式化器"""
        content = content.replace("测试", "**测试**")
        content = content.replace("内容", "📝 内容")
        return content
    
    formatter = get_content_formatter()
    
    # 注册自定义格式化器
    formatter.register_formatter("测试任务", custom_test_formatter)
    
    # 测试自定义格式化器
    test_content = "这是测试内容，包含测试和内容关键词。"
    template_context = {"content_block": test_content}
    
    print("📝 原始内容:")
    print(test_content)
    
    formatted_context = formatter.format_content("测试任务", template_context)
    formatted_content = formatted_context["content_block"]
    
    print("\n✨ 格式化后内容:")
    print(formatted_content)
    
    # 验证自定义格式化效果
    success = "**测试**" in formatted_content and "📝 内容" in formatted_content
    
    if success:
        print("\n✅ 自定义格式化器注册和使用成功！")
    else:
        print("\n❌ 自定义格式化器测试失败")
    
    return success


def test_supported_tasks():
    """测试支持的任务列表"""
    print("\n🧪 测试支持的任务列表")
    print("=" * 60)
    
    formatter = get_content_formatter()
    supported_tasks = formatter.get_supported_tasks()
    
    print("📋 当前支持的任务:")
    for task in supported_tasks:
        print(f"  - {task}")
    
    expected_tasks = ["华为快应用引擎更新说明"]
    success = all(task in supported_tasks for task in expected_tasks)
    
    if success:
        print("\n✅ 支持的任务列表正确！")
    else:
        print("\n❌ 支持的任务列表不完整")
    
    return success


if __name__ == "__main__":
    print("🚀 开始测试内容格式化器")
    print("=" * 80)
    
    results = []
    
    # 运行所有测试
    results.append(test_huawei_formatter())
    results.append(test_custom_formatter())
    results.append(test_supported_tasks())
    
    # 总结测试结果
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 所有测试通过！({passed}/{total})")
        print("✅ 内容格式化器系统工作正常")
    else:
        print(f"⚠️ 部分测试失败 ({passed}/{total})")
        print("❌ 需要检查和修复问题")
    
    print("=" * 80)
