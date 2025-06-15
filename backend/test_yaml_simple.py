#!/usr/bin/env python3
"""
简单测试YAML字符串处理
"""
import yaml

def test_yaml_string_handling():
    """测试YAML字符串处理"""
    print("🔍 测试YAML字符串处理...")
    
    # 模拟被截断的正则表达式
    problematic_regex = 'regex:<a href="(https?://[^"]+?)">HwQuickApp_Loader_Phone_V\\d+\\.\\d+\\.\\d+\\.\\d+\\.apk</a>'
    
    print(f"📝 测试正则表达式: {problematic_regex}")
    print(f"📏 长度: {len(problematic_regex)} 字符")
    
    # 测试1: 直接YAML序列化
    test_data = {
        "ai_extraction_rules": {
            "version": "regex:V(\\d+\\.\\d+\\.\\d+\\.\\d+)",
            "download_url": problematic_regex
        }
    }
    
    try:
        yaml_str = yaml.dump(test_data, allow_unicode=True, sort_keys=False, indent=2)
        print(f"\n✅ YAML序列化成功")
        print(f"📄 YAML输出:")
        print("-" * 40)
        print(yaml_str)
        print("-" * 40)
        
        # 重新解析
        parsed = yaml.safe_load(yaml_str)
        parsed_regex = parsed["ai_extraction_rules"]["download_url"]
        
        print(f"📋 解析后的正则表达式: {parsed_regex}")
        print(f"📏 解析后长度: {len(parsed_regex)} 字符")
        
        if parsed_regex == problematic_regex:
            print("✅ 字符串保持完整")
        else:
            print("❌ 字符串被截断或修改")
            print(f"🔍 差异:")
            print(f"   原始: {problematic_regex}")
            print(f"   解析: {parsed_regex}")
            
    except Exception as e:
        print(f"❌ YAML处理失败: {e}")

def test_yaml_quoting():
    """测试YAML引号处理"""
    print(f"\n🔍 测试YAML引号处理...")
    
    problematic_regex = 'regex:<a href="(https?://[^"]+?)">HwQuickApp_Loader_Phone_V\\d+\\.\\d+\\.\\d+\\.\\d+\\.apk</a>'
    
    # 测试不同的引号方式
    test_cases = [
        ("无引号", problematic_regex),
        ("单引号", f"'{problematic_regex}'"),
        ("双引号", f'"{problematic_regex}"'),
        ("YAML字面量", f"|\n  {problematic_regex}"),
        ("YAML折叠", f">\n  {problematic_regex}")
    ]
    
    for name, test_value in test_cases:
        print(f"\n📝 测试 {name}:")
        try:
            test_data = {"test_field": test_value}
            yaml_str = yaml.dump(test_data, allow_unicode=True, sort_keys=False, indent=2)
            parsed = yaml.safe_load(yaml_str)
            parsed_value = parsed["test_field"]
            
            print(f"   ✅ 成功 - 长度: {len(parsed_value)}")
            if parsed_value.strip() == problematic_regex:
                print(f"   ✅ 内容完整")
            else:
                print(f"   ❌ 内容不匹配")
                
        except Exception as e:
            print(f"   ❌ 失败: {e}")

if __name__ == "__main__":
    test_yaml_string_handling()
    test_yaml_quoting()
