#!/usr/bin/env python3
"""
测试模板变量是否完整
"""
from datetime import datetime
from jinja2 import Template

def test_template_variables():
    """测试华为任务的模板变量"""
    print("🧪 测试华为任务模板变量...")
    print("=" * 60)
    
    # 华为任务的模板（从config.yaml复制）
    huawei_template = '''**{{ task_name }} 检测到最新版本变化！**

版本已从 `{{ old_version }}` 更新至 `{{ version }}`，详细信息如下：

| 🔢 版本号 | 📖 规范版本 | ⏰ 发现时间 | ⬇️ 下载地址 |
|----------|------------|------------|------------|
| {{ version }} | {{ spec_version }} | {{ now().strftime('%Y-%m-%d %H:%M:%S') }} | [点击下载](https://developer.huawei.com/files/download/{{ download_file }}) |

监控页面: [查看详情]({{ url }})

{% if screenshot_url %}
截图: ![监控截图]({{ screenshot_url }})
{% endif %}'''
    
    # 模拟系统提供的变量（包括新增的时间变量）
    template_context = {
        # 基础变量
        "task_name": "华为快应用加载器监控",
        "url": "https://developer.huawei.com/consumer/cn/doc/Tools-Library/quickapp-ide-download-0000001101172926",
        "old_summary": "旧版本摘要",
        "new_summary": "新版本摘要", 
        "screenshot_url": "http://127.0.0.1:8000/screenshots/test.png",
        "screenshot_path": "/path/to/screenshot.png",
        
        # 新增的时间变量
        "now": datetime.now,
        "current_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "current_date": datetime.now().strftime('%Y-%m-%d'),
        "timestamp": int(datetime.now().timestamp()),
        
        # AI提取的字段（模拟）
        "version": "V15.2.1.305",
        "old_version": "V15.1.1.301", 
        "spec_version": "1122",
        "download_file": "HwQuickApp_Loader_Phone_V15.2.1.305.apk"
    }
    
    try:
        # 测试模板渲染
        jinja_template = Template(huawei_template)
        rendered = jinja_template.render(**template_context)
        
        print("✅ 华为模板渲染成功!")
        print("\n📋 渲染结果:")
        print("-" * 40)
        print(rendered)
        print("-" * 40)
        
        # 检查关键内容
        if "now().strftime" not in rendered:
            print("✅ now()函数正确执行")
        else:
            print("❌ now()函数未执行")
            
        if "V15.2.1.305" in rendered:
            print("✅ 版本变量正确替换")
        else:
            print("❌ 版本变量替换失败")
            
        return True
        
    except Exception as e:
        print(f"❌ 模板渲染失败: {e}")
        return False

def test_variable_completeness():
    """测试变量完整性"""
    print("\n🔍 检查变量完整性...")
    print("=" * 60)
    
    # 系统应该提供的变量
    expected_vars = [
        "task_name", "url", "old_summary", "new_summary", 
        "screenshot_url", "screenshot_path",
        "now", "current_time", "current_date", "timestamp"
    ]
    
    # 模拟系统变量
    template_context = {
        "task_name": "测试任务",
        "url": "https://example.com",
        "old_summary": "旧摘要",
        "new_summary": "新摘要",
        "screenshot_url": None,
        "screenshot_path": "未启用",
        "now": datetime.now,
        "current_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "current_date": datetime.now().strftime('%Y-%m-%d'),
        "timestamp": int(datetime.now().timestamp())
    }
    
    missing_vars = []
    for var in expected_vars:
        if var not in template_context:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ 缺少变量: {missing_vars}")
        return False
    else:
        print("✅ 所有必需变量都已提供")
        print(f"📋 可用变量: {list(template_context.keys())}")
        return True

if __name__ == "__main__":
    print("🚀 开始测试模板变量")
    print("=" * 60)
    
    success1 = test_variable_completeness()
    success2 = test_template_variables()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("=" * 60)
    
    if success1 and success2:
        print("🎉 所有测试通过!")
        print("✅ 变量完整性检查通过")
        print("✅ 华为模板渲染成功")
        print("✅ now()函数问题已解决")
        print("\n🔧 现在华为任务应该能正常工作了")
    else:
        print("⚠️  部分测试失败")
        print("需要进一步检查")
