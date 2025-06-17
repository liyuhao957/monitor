#!/usr/bin/env python3
"""
测试和验证AI生成的代码执行问题
"""
import logging
from datetime import datetime
from app.core.config import settings
from app.services.code_executor import execute_notification_formatter
from app.services.storage import get_last_result
from app.services.content_parser import get_content_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_honor_debugger_code():
    """测试荣耀调试器的AI代码执行"""
    print("🧪 测试荣耀调试器AI代码执行...")
    print("=" * 60)
    
    # 查找荣耀调试器任务
    task = next((t for t in settings.tasks if t.name == '荣耀调试器'), None)
    if not task:
        print("❌ 未找到荣耀调试器任务")
        return
    
    print(f"✅ 找到任务: {task.name}")
    print(f"📝 AI描述: {task.ai_description}")
    print(f"🔧 提取规则: {list(task.ai_extraction_rules.keys())}")
    
    # 尝试读取存储的数据
    try:
        stored_content = get_last_result(task.name)
        if stored_content:
            print(f"\n📖 成功读取存储内容，长度: {len(stored_content)} 字符")
            print(f"内容预览: {stored_content[:100]}...")
            
            # 使用内容解析器提取数据
            content_parser = get_content_parser()
            extracted_data = {}
            
            print("\n🔍 开始提取数据...")
            for field, rule in task.ai_extraction_rules.items():
                value = content_parser._extract_single_field(field, rule, "", stored_content)
                if value is not None:
                    extracted_data[field] = value
                    print(f"  ✅ {field}: {value}")
                else:
                    print(f"  ❌ {field}: 提取失败")
            
            # 执行AI生成的格式化代码
            print(f"\n🚀 执行AI格式化代码...")
            try:
                result = execute_notification_formatter(
                    task.ai_formatter_code,
                    extracted_data,
                    {
                        "name": task.name,
                        "url": task.url,
                        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                )
                print(f"✅ 代码执行成功！")
                print(f"\n📨 生成的通知内容:")
                print("-" * 60)
                print(result)
                print("-" * 60)
                
            except Exception as e:
                print(f"❌ 代码执行失败: {e}")
                import traceback
                print("\n详细错误:")
                traceback.print_exc()
                
                # 打印代码片段以便调试
                print(f"\n📄 AI生成的代码片段（前500字符）:")
                print(task.ai_formatter_code[:500] if task.ai_formatter_code else "无代码")
                
                # 检查代码中的特殊字符
                if task.ai_formatter_code:
                    print(f"\n🔍 检查代码中的可疑字符...")
                    suspicious_patterns = [
                        ("点 击", "点击"),
                        ("联 盟", "联盟"),
                        ("地 址", "地址")
                    ]
                    for pattern, replacement in suspicious_patterns:
                        if pattern in task.ai_formatter_code:
                            print(f"  ⚠️ 发现可疑模式: '{pattern}' -> 应该是 '{replacement}'")
        else:
            print("❌ 无法读取存储内容")
            
    except Exception as e:
        print(f"❌ 读取存储失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_honor_debugger_code() 