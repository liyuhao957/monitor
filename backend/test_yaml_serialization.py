#!/usr/bin/env python3
"""
测试YAML序列化问题
"""
import yaml
import json
from pathlib import Path
from app.core.config import Task, Settings, save_config, load_config, get_config_path
from pydantic import HttpUrl

def test_yaml_serialization_issue():
    """测试YAML序列化是否会截断长字符串"""
    print("🔍 测试YAML序列化问题...")
    print("=" * 60)
    
    # 创建一个包含长正则表达式的测试任务
    long_regex = 'regex:<a href="(https?://[^"]+?)">HwQuickApp_Loader_Phone_V\\d+\\.\\d+\\.\\d+\\.\\d+\\.apk</a>'
    
    test_task = Task(
        name="测试任务",
        url=HttpUrl("https://example.com"),
        frequency="10m",
        rule="css:body",
        enabled=True,
        ai_analysis_enabled=True,
        ai_description="测试描述",
        ai_extraction_rules={
            "version": "regex:V(\\d+\\.\\d+\\.\\d+\\.\\d+)",
            "spec": "regex:支持(\\d{4})规范",
            "download_url": long_regex  # 这是一个长的正则表达式
        }
    )
    
    print(f"📝 原始长正则表达式:")
    print(f"   {long_regex}")
    print(f"   长度: {len(long_regex)} 字符")
    
    # 测试Pydantic序列化
    print(f"\n🧪 测试Pydantic序列化...")
    try:
        # Step 1: model_dump_json
        json_str = test_task.model_dump_json(indent=2)
        print(f"✅ Pydantic JSON序列化成功")
        
        # 检查JSON中的长正则表达式
        json_data = json.loads(json_str)
        saved_regex = json_data.get('ai_extraction_rules', {}).get('download_url', '')
        print(f"📋 JSON中的正则表达式:")
        print(f"   {saved_regex}")
        print(f"   长度: {len(saved_regex)} 字符")
        
        if saved_regex == long_regex:
            print("✅ JSON序列化保持完整")
        else:
            print("❌ JSON序列化已截断")
            
    except Exception as e:
        print(f"❌ Pydantic序列化失败: {e}")
        return False
    
    # 测试YAML序列化
    print(f"\n🧪 测试YAML序列化...")
    try:
        # Step 2: yaml.dump
        config_data = json.loads(json_str)
        yaml_str = yaml.dump(config_data, allow_unicode=True, sort_keys=False, indent=2)
        print(f"✅ YAML序列化成功")
        
        # 检查YAML中的长正则表达式
        yaml_data = yaml.safe_load(yaml_str)
        yaml_regex = yaml_data.get('ai_extraction_rules', {}).get('download_url', '')
        print(f"📋 YAML中的正则表达式:")
        print(f"   {yaml_regex}")
        print(f"   长度: {len(yaml_regex)} 字符")
        
        if yaml_regex == long_regex:
            print("✅ YAML序列化保持完整")
        else:
            print("❌ YAML序列化已截断")
            print(f"🔍 截断位置: {yaml_regex}")
            
    except Exception as e:
        print(f"❌ YAML序列化失败: {e}")
        return False
    
    # 测试完整的save_config流程
    print(f"\n🧪 测试完整的save_config流程...")
    try:
        # 创建临时配置
        temp_settings = Settings(tasks=[test_task])
        temp_config_path = Path("temp_test_config.yaml")
        
        # 保存配置
        save_config(temp_settings, temp_config_path)
        print(f"✅ save_config执行成功")
        
        # 读取保存的文件
        with open(temp_config_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        
        print(f"📄 保存的YAML文件内容:")
        print("-" * 40)
        print(saved_content)
        print("-" * 40)
        
        # 重新加载配置
        loaded_settings = load_config(temp_config_path)
        loaded_regex = loaded_settings.tasks[0].ai_extraction_rules.get('download_url', '')
        
        print(f"📋 重新加载的正则表达式:")
        print(f"   {loaded_regex}")
        print(f"   长度: {len(loaded_regex)} 字符")
        
        if loaded_regex == long_regex:
            print("✅ 完整流程保持数据完整")
        else:
            print("❌ 完整流程数据被截断")
            print(f"🔍 原始: {long_regex}")
            print(f"🔍 加载: {loaded_regex}")
        
        # 清理临时文件
        temp_config_path.unlink()
        
        return loaded_regex == long_regex
        
    except Exception as e:
        print(f"❌ 完整流程测试失败: {e}")
        return False

def test_yaml_line_length_limits():
    """测试YAML是否有行长度限制"""
    print(f"\n🔍 测试YAML行长度限制...")
    print("=" * 60)
    
    # 创建不同长度的字符串
    test_strings = [
        "短字符串",
        "中等长度的字符串" * 5,
        "很长的字符串" * 20,
        "超级长的字符串包含特殊字符<>\"'()[]{}|\\/" * 10
    ]
    
    for i, test_str in enumerate(test_strings):
        print(f"\n📝 测试字符串 {i+1} (长度: {len(test_str)}):")
        print(f"   {test_str[:100]}{'...' if len(test_str) > 100 else ''}")
        
        try:
            # 测试YAML序列化
            test_data = {"test_field": test_str}
            yaml_str = yaml.dump(test_data, allow_unicode=True, sort_keys=False, indent=2)
            
            # 重新解析
            parsed_data = yaml.safe_load(yaml_str)
            parsed_str = parsed_data.get("test_field", "")
            
            if parsed_str == test_str:
                print(f"   ✅ 长度 {len(test_str)} - 保持完整")
            else:
                print(f"   ❌ 长度 {len(test_str)} - 被截断")
                print(f"   🔍 原始长度: {len(test_str)}, 解析长度: {len(parsed_str)}")
                
        except Exception as e:
            print(f"   ❌ 长度 {len(test_str)} - 序列化失败: {e}")

if __name__ == "__main__":
    print("🚀 开始YAML序列化问题排查")
    print("=" * 60)
    
    success = test_yaml_serialization_issue()
    test_yaml_line_length_limits()
    
    print("\n" + "=" * 60)
    print("📊 排查结果总结:")
    print("=" * 60)
    
    if success:
        print("✅ YAML序列化功能正常")
        print("🤔 问题可能在其他地方...")
    else:
        print("❌ 发现YAML序列化问题")
        print("🎯 这就是配置被截断的根本原因！")
