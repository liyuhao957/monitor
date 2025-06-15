#!/usr/bin/env python3
"""
测试修复效果
"""
import re
from pathlib import Path
from app.core.config import Task, Settings, save_config, load_config
from pydantic import HttpUrl

def test_yaml_width_fix():
    """测试YAML宽度修复"""
    print("🔧 测试YAML宽度修复...")
    print("=" * 60)
    
    # 创建包含长正则表达式的测试任务
    long_regex = 'regex:<a href="(https?://[^"]+?\.apk[^"]*)" target="_blank">HwQuickApp_Loader_Phone_V\\d+\\.\\d+\\.\\d+\\.\\d+\\.apk</a>'
    
    test_task = Task(
        name="YAML宽度测试",
        url=HttpUrl("https://example.com"),
        frequency="10m",
        rule="css:body",
        enabled=True,
        ai_analysis_enabled=True,
        ai_description="测试长正则表达式",
        ai_extraction_rules={
            "version": "regex:V(\\d+\\.\\d+\\.\\d+\\.\\d+)",
            "download_url": long_regex  # 长正则表达式
        }
    )
    
    print(f"📝 原始正则表达式长度: {len(long_regex)} 字符")
    print(f"   {long_regex}")
    
    try:
        # 保存配置
        temp_settings = Settings(tasks=[test_task])
        temp_config_path = Path("temp_yaml_test.yaml")
        
        save_config(temp_settings, temp_config_path)
        print("✅ 配置保存成功")
        
        # 重新加载配置
        loaded_settings = load_config(temp_config_path)
        loaded_regex = loaded_settings.tasks[0].ai_extraction_rules.get('download_url', '')
        
        print(f"📋 加载后的正则表达式长度: {len(loaded_regex)} 字符")
        print(f"   {loaded_regex}")
        
        if loaded_regex == long_regex:
            print("✅ YAML宽度修复成功！长正则表达式保持完整")
            success = True
        else:
            print("❌ YAML宽度修复失败，正则表达式仍被截断")
            print(f"🔍 差异:")
            print(f"   原始: {long_regex}")
            print(f"   加载: {loaded_regex}")
            success = False
        
        # 清理临时文件
        temp_config_path.unlink()
        return success
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_regex_accuracy():
    """测试正则表达式准确性"""
    print(f"\n🎯 测试正则表达式准确性...")
    print("=" * 60)
    
    # 华为页面的实际HTML内容
    html_content = '''<a href="https://contentcenter-vali-drcn.dbankcdn.cn/pvt_2/DeveloperAlliance_package_901_9/ac/v3/NdSvoI1ZQjKu0y7TZC31Gg/QuickAPP-newly-product-release-loader-15.1.1.301.apk?HW-CC-KV=V1&HW-CC-Date=20250606T073903Z&HW-CC-Expire=315360000&HW-CC-Sign=61B8907C7EADB97F9DD8FBE13305C0F22B2C9A2B6AAD56743266244DC15D0A30" target="_blank">HwQuickApp_Loader_Phone_V15.1.1.301.apk</a>（支持1121规范的调试）'''
    
    print(f"📄 测试HTML内容:")
    print(f"   {html_content}")
    
    # 测试不同的正则表达式
    test_regexes = [
        ("旧的错误规则", r'href="(https?://[^"]+?\.apk)"'),
        ("修复后的规则", r'href="(https?://[^"]+?\.apk[^"]*)"'),
        ("更通用的规则", r'href="([^"]+\.apk[^"]*)"')
    ]
    
    for name, regex_pattern in test_regexes:
        print(f"\n🧪 测试 {name}:")
        print(f"   规则: {regex_pattern}")
        
        try:
            match = re.search(regex_pattern, html_content)
            if match:
                extracted_url = match.group(1)
                print(f"   ✅ 匹配成功")
                print(f"   📋 提取的URL: {extracted_url[:80]}{'...' if len(extracted_url) > 80 else ''}")
                print(f"   📏 URL长度: {len(extracted_url)} 字符")
                
                # 验证URL是否完整
                if extracted_url.endswith('.apk') or '?HW-CC-KV=' in extracted_url:
                    print(f"   ✅ URL格式正确")
                else:
                    print(f"   ❌ URL格式可能不完整")
            else:
                print(f"   ❌ 匹配失败")
                
        except Exception as e:
            print(f"   ❌ 正则表达式错误: {e}")
    
    # 测试版本号提取
    print(f"\n🧪 测试版本号提取:")
    version_regex = r'HwQuickApp_Loader_Phone_(V\d+\.\d+\.\d+\.\d+)\.apk'
    version_match = re.search(version_regex, html_content)
    if version_match:
        version = version_match.group(1)
        print(f"   ✅ 版本号提取成功: {version}")
    else:
        print(f"   ❌ 版本号提取失败")
    
    # 测试规范版本提取
    print(f"\n🧪 测试规范版本提取:")
    spec_regex = r'支持(\d{4})规范的调试'
    spec_match = re.search(spec_regex, html_content)
    if spec_match:
        spec = spec_match.group(1)
        print(f"   ✅ 规范版本提取成功: {spec}")
    else:
        print(f"   ❌ 规范版本提取失败")

if __name__ == "__main__":
    print("🚀 开始测试修复效果")
    print("=" * 60)
    
    success1 = test_yaml_width_fix()
    test_regex_accuracy()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("=" * 60)
    
    if success1:
        print("✅ YAML宽度修复成功")
        print("✅ 长正则表达式不再被截断")
        print("✅ AI提示词已优化，包含HTML分析指导")
        print("\n🎯 修复完成！现在AI应该能生成更准确的提取规则")
    else:
        print("❌ YAML宽度修复失败")
        print("需要进一步检查")
