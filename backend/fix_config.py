#!/usr/bin/env python3
"""
修复配置文件中的Pydantic对象序列化问题
"""
import yaml
import re

def fix_config_file():
    """修复配置文件中的URL格式问题"""
    
    print("🔧 开始修复配置文件...")
    
    # 读取损坏的配置文件
    config_path = "../config.yaml"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📖 读取配置文件成功，长度: {len(content)} 字符")
        
        # 提取OPPO任务的AI代码（重要！）
        oppo_ai_code_match = re.search(
            r'ai_formatter_code: "(.*?)"(?=\s+enabled: true\s+frequency: 1m\s+name: OPPO)',
            content,
            re.DOTALL
        )
        
        oppo_ai_code = None
        if oppo_ai_code_match:
            oppo_ai_code = oppo_ai_code_match.group(1)
            print(f"✅ 成功提取OPPO AI代码，长度: {len(oppo_ai_code)} 字符")
        else:
            print("⚠️  未找到OPPO AI代码")
        
        # 修复URL格式 - 将Pydantic对象格式转换为简单字符串
        url_pattern = r'url: !!python/object:pydantic\.networks\.HttpUrl\s+_url: !!python/object/new:pydantic_core\._pydantic_core\.Url\s+- (.+?)(?=\n-|\napi_settings|\nnotification_presets|\Z)'
        
        def replace_url(match):
            url = match.group(1).strip()
            return f'url: {url}'
        
        fixed_content = re.sub(url_pattern, replace_url, content, flags=re.MULTILINE | re.DOTALL)
        
        # 计算修复的URL数量
        original_urls = len(re.findall(url_pattern, content, re.MULTILINE | re.DOTALL))
        print(f"🔗 修复了 {original_urls} 个URL格式")
        
        # 创建新的配置结构
        new_config = {
            "api_settings": {
                "ai_provider": "openai",
                "deepseek_api_key": "sk-33c4b6f409f149cf89139fb4c4900439",
                "deepseek_base_url": "https://api.deepseek.com",
                "deepseek_model": "deepseek-chat",
                "openai_api_key": "sk-6KwYGpsonYqWBAxrg9hEyjfEL7Bpak478TjuxCA7gf52GdvGVDfQ",
                "openai_base_url": "https://api.oaipro.com/v1",
                "openai_model": "claude-sonnet-4-20250514"
            },
            "tasks": [
                {
                    "name": "华为快应用加载器监控",
                    "url": "https://developer.huawei.com/consumer/cn/doc/Tools-Library/quickapp-ide-download-0000001101172926",
                    "frequency": "10m",
                    "rule": "xpath://*[@id=\"ZH-CN_TOPIC_0000001101172926__li16222518142\"]",
                    "enabled": False,
                    "screenshot": False,
                    "notification_title": "华为",
                    "notification": None,
                    "notification_template": "检测到华为快应用加载器新版本发布！\n\n| 🔖 字段       | 📝 详情                 |\n|--------------|------------------------|\n| 🆕 最新版本   | {{ version_number }}   |\n| 📚 规范版本   | {{ spec_version }}     |\n| ⏱️ 发现时间  | {{ current_time }}     |\n| ⬇️ 下载地址   | [点击下载]({{ download_url }}) |",
                    "storage_strategy": "file",
                    "ai_analysis_enabled": True,
                    "ai_description": "我想监控华为快应用加载器的最新版本更新,当最新版本号发生变化时（如从V15.1.1.301变为V15.2.1.305），请生成一个表格格式的通知，包含：版本号（V15.1.1.301类似这样）、规范版本（类似1121）、发现时间、下载地址。通知格式要求：使用表格、包含emoji、简洁美观。",
                    "ai_extraction_rules": {
                        "version_number": "regex:HwQuickApp_Loader_Phone_(V\\d+\\.\\d+\\.\\d+\\.\\d+)",
                        "spec_version": "regex:支持(\\d{4})规范的调试",
                        "download_url": "regex:<a href=\"(https:[^\"]+)\""
                    },
                    "ai_formatter_code": None
                },
                {
                    "name": "荣耀调试器",
                    "url": "https://developer.honor.com/cn/doc/guides/101380",
                    "frequency": "10m",
                    "rule": "xpath://*[@id=\"doc-content-text\"]/div[2]/table/tbody/tr[2]",
                    "enabled": False,
                    "screenshot": False,
                    "notification_title": "荣耀",
                    "notification": None,
                    "notification_template": "# {{ task_name }} 检测到版本更新！\n\n**监控URL:** {{ url }}\n\n| 项目 | 新版本信息 |\n|------|------------|\n| 🚀 荣耀快应用引擎版本号 | {{ honor_fast_app_engine_version }} |\n| ⚙️ 荣耀引擎版本号 | {{ honor_engine_version }} |\n| 🤝 快应用联盟平台版本号 | {{ fast_app_alliance_platform_version }} |\n| 📥 下载地址 | [点击下载]({{ download_url }}) |\n| 🔧 调试器版本号 | {{ debugger_version }} |\n| 📝 版本功能 | {{ version_features | replace('新增：', '\\n- 新增：') | replace('优化：', '\\n- 优化：') }} |\n\n{% if screenshot_url %}\n**截图:** [查看截图]({{ screenshot_url }})\n{% endif %}",
                    "storage_strategy": "file",
                    "ai_analysis_enabled": True,
                    "ai_description": "我只想监控荣耀加载器的最新版本更新。当最新版本号发生变化时（如从V15.1.1.301变为V15.2.1.305），请生成一个表格格式的通知，包含：荣耀快应用引擎版本号、荣耀引擎版本号、快应用联盟平台版本号、下载地址、调试器版本号、版本功能。通知格式要求：使用表格、包含emoji、简洁美观、版本功能需要排版。",
                    "ai_extraction_rules": {
                        "honor_fast_app_engine_version": "regex:^(\\d+\\.\\d+\\.\\d+)",
                        "honor_engine_version": "regex:^\\d+\\.\\d+\\.\\d+\\s+(\\d+)",
                        "fast_app_alliance_platform_version": "regex:^\\d+\\.\\d+\\.\\d+\\s+\\d+\\s+(\\d+)",
                        "download_url": "regex:<a href=\"(.*?)\"",
                        "debugger_version": "regex:</a>\\s+(\\d+\\.\\d+\\.\\d+\\.\\d+)",
                        "version_features": "regex:\\d+\\.\\d+\\.\\d+\\.\\d+\\s+(.*)"
                    },
                    "ai_formatter_code": None
                },
                {
                    "name": "OPPO",
                    "url": "https://ie-activity-cn.heytapimage.com/static/minigame/CN/docs/index.html#/download/index",
                    "frequency": "1m",
                    "rule": "xpath://*[@id=\"main\"]/ul[1]",
                    "enabled": True,
                    "screenshot": False,
                    "notification_title": "OPPO快游戏",
                    "notification": None,
                    "notification_template": "🎮 **OPPO小游戏调试器版本更新**\n\n⏰ **检测时间**: 2025-06-17 14:31:17\n\n📋 **最新版本信息**:\n\n| 项目 | 版本号 | 操作 |\n|------|--------|------|\n| 🔧 引擎大版本 | `1155` | - |\n| 🎯 引擎小版本 | `V9.8.0` | - |\n| 📥 下载地址 | [点击下载](https://ie-activity-cn.heytapimage.com/static/quickgame/tools/e4d31728063eb9e67443bdda8e6849f6.zip) | 💾 |\n\n---\n🔗 **监控页面**: [OPPO开发者文档](https://ie-activity-cn.heytapimage.com/static/minigame/CN/docs/index.html#/download/index)\n💡 **提示**: 请及时更新到最新版本以获得最佳开发体验",
                    "storage_strategy": "file",
                    "ai_analysis_enabled": True,
                    "ai_description": "我只想监控OPPO小游戏调试器的最新版本更新。V9.8.0这样的是小版本号，1155这样的是大版本号，当最新版本号发生变化时（如从OPPO 小游戏调试器 V9.8.0变为OPPO 小游戏调试器 V9.0.0 和 1155变为1166），请生成一个表格格式的通知，包含：OPPO引擎大版本号、OPPO引擎小版本号、下载地址。通知格式要求：使用表格、包含emoji、简洁美观、版本功能需要排版。",
                    "ai_extraction_rules": {
                        "major_version": "regex:(\\d+)\\s*<a[^>]*>OPPO 小游戏调试器",
                        "minor_version": "regex:>OPPO 小游戏调试器\\s+(V[\\d\\.]+)<",
                        "download_url": "regex:<a href=\"([^\"]+)\"[^>]*>OPPO 小游戏调试器"
                    },
                    "ai_formatter_code": oppo_ai_code.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\') if oppo_ai_code else None
                },
                {
                    "name": "华为快应用引擎更新说明",
                    "url": "https://developer.huawei.com/consumer/cn/doc/quickApp-Guides/quickapp-version-updates-0000001079803874",
                    "frequency": "1m",
                    "rule": "xpath://*[@id=\"body0000001079803874\"]",
                    "enabled": False,
                    "screenshot": False,
                    "notification_title": "华为快应用引擎更新说明",
                    "notification": None,
                    "notification_template": "> 更新时间：{{ current_time }}\n> 版本号：**{{ version_number }}**\n> 发布日期：{{ update_date }}\n\n**变更详情（需进一步格式化）**\n{{ changes_section_html }}\n\n*以上原始内容包含 HTML 标签与多行文本，⚠️ 需要Python代码处理以：*\n1. 拆分出每个\"变更项目名称 / 描述 / 链接\"\n2. 将 `<a>` 标签转为 `[标题](链接) 🔗`\n3. 为标题加粗，项目之间插入分隔线 `---`",
                    "storage_strategy": "file",
                    "ai_analysis_enabled": True,
                    "ai_description": "监控华为快应用引擎的版本更新说明，重点关注：\n\n1. **版本信息提取**：\n   - 版本号（如：1121）\n   - 更新日期（如：2025-6-6）\n\n2. **更新内容结构化**：\n   - 变更项目名称（如：安装开发工具、华为快应用加载器使用指导）\n   - 具体变更描述\n   - 相关文档链接\n\n3. **格式化要求**：\n   - 去除页面结构标识（如\"指南 变更点 说明\"等导航文本）\n   - 将变更项目名称格式化为加粗标题\n   - 为每个变更项添加清晰的分隔\n   - 保留并美化文档链接，添加图标标识\n   - 确保通知内容简洁易读，适合飞书显示\n\n4. **特殊处理需求**：\n   - 内容包含HTML链接标签，需要转换为Markdown格式\n   - 文本中可能包含特殊字符和空格，需要精确匹配\n   - 复杂的格式化逻辑建议使用Python代码处理，而非Jinja2模板\n\n5. **通知目标**：\n   - 及时通知开发团队华为快应用引擎的版本更新\n   - 突出显示重要的功能变更和工具更新\n   - 提供直接的文档链接便于查看详细信息",
                    "ai_extraction_rules": {
                        "version_number": "regex:(\\d{4})版本更新说明（\\d{4}-\\d{1,2}-\\d{1,2}）",
                        "update_date": "regex:\\d{4}版本更新说明（(\\d{4}-\\d{1,2}-\\d{1,2})）",
                        "changes_section_html": "regex:\\d{4}版本更新说明（\\d{4}-\\d{1,2}-\\d{1,2}）([\\s\\S]*?)(?=\\n?\\d{4}版本更新说明|$)"
                    },
                    "ai_formatter_code": None
                }
            ],
            "notification_presets": {
                "default": "**📈 网页内容变更告警**\n**- 任务名称**: `{{ task_name }}` **- 监控页面**: [点击访问]({{ url }})\n--- \n**📝 变更内容摘要**:\n**【变更前】** > {{ old_summary }}\n**【变更后】** > {{ new_summary }} {% if screenshot_url %} ---\n**🖼️ [查看快照]({{ screenshot_url }})** {% endif %}",
                "simple": "[监控] {{ task_name }} 发生内容变更，请及时查看。链接: {{ url }}",
                "card": "**📈 {{ task_name }} - 内容变更**\n\n> {{ new_summary }}\n\n--- - **监控页面**: [点击访问]({{ url }}) {% if screenshot_url %} - **页面快照**: [点击查看]({{ screenshot_url }}) {% endif %}"
            }
        }
        
        # 保存修复后的配置
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True, width=1000)
        
        print("✅ 配置文件修复完成")
        print(f"💾 已保存到: {config_path}")
        
        if oppo_ai_code:
            print("🎯 OPPO AI代码已保留")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_config_file()
