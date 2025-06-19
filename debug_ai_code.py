#!/usr/bin/env python3
"""
调试华为快应用引擎更新说明的AI代码
"""
import re
from datetime import datetime

def debug_ai_code():
    # 模拟存储的内容格式（基于多规则分段）
    mock_page_content = """=== 提取规则 1: css:#body0000001079803874 > div:nth-child(1) ===
1121版本更新说明（2025-6-6）

=== 提取规则 2: css:#body0000001079803874 > div:nth-child(2) ===
<table>
<tr class="cellrowborder">
<td><p>安装开发工具</p></td>
<td><p>"快应用官方示例"、"快应用研发助手"打开入口集成到加载器中。</p>
<li>详情请参见"<a href="https://developer.huawei.com/consumer/cn/doc/quickApp-Guides/quickapp-installtool-0000001126543467">开发准备&gt;安装开发工具</a>"。</li>
</td>
</tr>
<tr class="cellrowborder">
<td><p>华为快应用加载器使用指导</p></td>
<td><p>"快应用官方示例"、"快应用研发助手"使用指导。</p>
<li>详情请参见"<a href="https://developer.huawei.com/consumer/cn/doc/quickApp-Guides/quickapp-loader-user-guide-0000001115925960">附录&gt;华为快应用加载器使用指导</a>"。</li>
</td>
</tr>
</table>"""

    print("🧪 调试华为快应用引擎更新说明AI代码")
    print("=" * 60)
    print(f"📝 模拟页面内容长度: {len(mock_page_content)} 字符")
    print("📝 内容预览:")
    print("-" * 40)
    print(mock_page_content[:300] + "...")
    print("-" * 40)

    # 执行AI代码逻辑
    extracted_data = {'page_content': mock_page_content}
    task_info = {'name': '华为快应用引擎更新说明'}

    try:
        result = format_notification(extracted_data, task_info)
        print(f"✅ AI代码执行成功")
        print(f"📏 生成内容长度: {len(result)} 字符")
        print("📄 生成内容:")
        print("-" * 40)
        print(result)
        print("-" * 40)
    except Exception as e:
        print(f"❌ AI代码执行失败: {e}")
        import traceback
        traceback.print_exc()

def format_notification(extracted_data: dict, task_info: dict) -> str:
    """华为快应用引擎更新说明的AI代码"""
    try:
        page_content = extracted_data.get('page_content', '')

        # 解析分段内容
        sections = {}
        current_section = None
        current_content = []

        for line in page_content.split('\n'):
            line = line.strip()
            if line.startswith('=== 提取规则'):
                if current_section is not None:
                    sections[current_section] = '\n'.join(current_content)
                match = re.search(r'=== 提取规则 (\d+):', line)
                if match:
                    current_section = int(match.group(1))
                    current_content = []
            elif line and current_section is not None:
                current_content.append(line)

        if current_section is not None:
            sections[current_section] = '\n'.join(current_content)

        print(f"🔍 解析出 {len(sections)} 个分段: {list(sections.keys())}")
        for k, v in sections.items():
            print(f"  分段 {k}: {len(v)} 字符")

        # 从分段1提取版本号和日期
        version_number = "未知版本"
        update_date = "未知日期"

        if 1 in sections:
            title_content = sections[1]
            print(f"📋 分段1内容: {title_content}")
            # 提取版本号
            version_match = re.search(r'(\d+)版本更新说明', title_content)
            if version_match:
                version_number = version_match.group(1)
                print(f"✅ 提取版本号: {version_number}")

            # 提取日期
            date_match = re.search(r'((\d{4}-\d{1,2}-\d{1,2}))', title_content)
            if date_match:
                update_date = date_match.group(1)
                print(f"✅ 提取日期: {update_date}")

        # 从分段2提取表格内容
        update_items = []

        if 2 in sections:
            table_content = sections[2]
            print(f"📋 分段2内容长度: {len(table_content)} 字符")

            # 提取表格行
            rows = re.findall(r'<tr[^>]*>.*?</tr>', table_content, re.DOTALL)
            print(f"🔍 找到 {len(rows)} 个表格行")

            for i, row in enumerate(rows):
                print(f"  行 {i+1}: {len(row)} 字符")
                if 'cellrowborder' in row and 'thead' not in row:
                    # 提取变更点
                    change_point_match = re.search(r'<p[^>]*>([^<]+)</p>', row)
                    change_point = change_point_match.group(1).strip() if change_point_match else ""

                    if change_point and change_point != "变更点":
                        print(f"    变更点: {change_point}")
                        # 提取说明内容
                        td_cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                        if len(td_cells) >= 2:
                            description_cell = td_cells[1]

                            # 提取列表项
                            list_items = re.findall(r'<li[^>]*>([^<]+)</li>', description_cell)

                            # 提取参考链接
                            link_match = re.search(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', description_cell)

                            description_parts = []
                            if list_items:
                                description_parts.extend(list_items)

                            if link_match:
                                link_url = link_match.group(1)
                                link_text = link_match.group(2)
                                description_parts.append(f"参考文档:[{link_text}]({link_url})")

                            if description_parts:
                                update_items.append({
                                    'change_point': change_point,
                                    'description': description_parts
                                })
                                print(f"    ✅ 添加更新项: {len(description_parts)} 个描述")

        print(f"📊 总共提取 {len(update_items)} 个更新项")

        # 生成通知内容
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        notification = f"🚀 **华为快应用引擎更新通知**\n\n"
        notification += f"📋 **版本信息**\n"
        notification += f"• 版本号:{version_number}\n"
        notification += f"• 发布日期:{update_date}\n\n"

        if update_items:
            notification += f"📝 **更新内容**\n"
            for i, item in enumerate(update_items, 1):
                notification += f"\n**{i}. {item['change_point']}**\n"
                for desc in item['description']:
                    notification += f"• {desc}\n"
        else:
            notification += f"📝 **更新内容**\n• 暂无详细更新内容\n"

        notification += f"\n⏰ **检测时间**:{current_time}"

        return notification

    except Exception as e:
        return f"❌ 处理华为快应用引擎更新通知时出错:{str(e)}"

if __name__ == "__main__":
    debug_ai_code()
