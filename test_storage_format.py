#!/usr/bin/env python3
"""
测试存储内容格式
"""
import sys
from pathlib import Path

# 添加backend目录到Python路径
sys.path.append(str(Path(__file__).parent / "backend"))

# 模拟从API获取内容的过程
def simulate_content_fetch():
    """模拟多规则内容获取过程"""
    
    # 模拟规则1的内容（标题）
    rule1_content = "1121版本更新说明（2025-6-6）"
    
    # 模拟规则2的内容（表格）
    rule2_content = """<table>
<tr class="cellrowborder">
<td><p>安装开发工具</p></td>
<td><p>"快应用官方示例"、"快应用研发助手"打开入口集成到加载器中。</p>
<li>详情请参见"<a href="https://developer.huawei.com/consumer/cn/doc/quickApp-Guides/quickapp-installtool-0000001126543467">开发准备&gt;安装开发工具</a>"。</li>
</td>
</tr>
</table>"""
    
    # 多规则任务的内容合并方式（来自monitor.py第207行）
    all_content = [rule1_content, rule2_content]
    combined_content = "\n\n".join(all_content)
    
    print("🔍 模拟多规则内容获取")
    print("=" * 50)
    print(f"📏 规则1内容长度: {len(rule1_content)} 字符")
    print(f"📏 规则2内容长度: {len(rule2_content)} 字符")
    print(f"📏 合并后总长度: {len(combined_content)} 字符")
    print()
    print("📝 合并后的内容:")
    print("-" * 40)
    print(combined_content)
    print("-" * 40)
    
    # 检查是否包含AI代码期望的分段标记
    if "=== 提取规则" in combined_content:
        print("✅ 包含AI代码期望的分段标记")
    else:
        print("❌ 不包含AI代码期望的分段标记")
        print("💡 这就是问题所在！AI代码期望分段格式，但实际存储的是合并后的原始内容")
    
    return combined_content

def test_ai_code_with_real_format(content):
    """用实际格式测试AI代码"""
    print("\n🧪 用实际存储格式测试AI代码")
    print("=" * 50)
    
    # AI代码的分段解析逻辑
    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('=== 提取规则'):
            if current_section is not None:
                sections[current_section] = '\n'.join(current_content)
            import re
            match = re.search(r'=== 提取规则 (\d+):', line)
            if match:
                current_section = int(match.group(1))
                current_content = []
        elif line and current_section is not None:
            current_content.append(line)

    if current_section is not None:
        sections[current_section] = '\n'.join(current_content)
    
    print(f"🔍 AI代码解析结果: {len(sections)} 个分段")
    
    if not sections:
        print("❌ AI代码无法解析任何分段")
        print("💡 这解释了为什么生成的通知只有基本框架")
        
        # 尝试直接解析内容
        print("\n🔧 尝试修复：直接解析原始内容")
        lines = content.split('\n')
        if len(lines) >= 2:
            title_line = lines[0].strip()
            table_content = '\n'.join(lines[2:])  # 跳过空行
            
            print(f"📋 标题行: {title_line}")
            print(f"📋 表格内容长度: {len(table_content)} 字符")
            
            # 提取版本号
            import re
            version_match = re.search(r'(\d+)版本更新说明', title_line)
            if version_match:
                version_number = version_match.group(1)
                print(f"✅ 成功提取版本号: {version_number}")
            else:
                print("❌ 无法提取版本号")
    
    return sections

if __name__ == "__main__":
    content = simulate_content_fetch()
    test_ai_code_with_real_format(content)
