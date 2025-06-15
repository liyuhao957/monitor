"""
AI驱动的通知内容分析服务
使用OpenAI API分析监控内容变化并生成简洁美观的通知
"""
import logging
from typing import Optional, Dict
from openai import OpenAI
from pydantic import BaseModel

from app.core.config import Task

logger = logging.getLogger(__name__)

class NotificationAnalysis(BaseModel):
    """AI通知分析结果"""
    title: str
    content: str
    summary: str
    required_fields: Optional[Dict[str, str]] = None  # 需要提取的字段及其描述
    extraction_rules: Optional[Dict[str, str]] = None  # 字段提取规则

class AINotifier:
    """AI通知分析器"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-reasoner"):
        try:
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            self.model = model
            logger.info(f"AI通知分析器初始化成功，使用模型: {model}")
        except Exception as e:
            logger.error(f"AI通知分析器初始化失败: {e}")
            raise

    def analyze_content_structure(
        self,
        task: Task,
        content: str
    ) -> NotificationAnalysis:
        """分析页面内容结构并生成智能通知模板

        这是AI通知系统的核心功能，只在用户设置监控任务时调用一次。
        生成的模板和提取规则会保存到任务配置中，后续监控直接使用。
        """
        try:
            prompt = self._build_structure_analysis_prompt(task, content)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=32000  # DeepSeek推荐的最大token数
            )

            result = response.choices[0].message.content
            return self._parse_analysis_result(result)

        except Exception as e:
            logger.error(f"AI通知分析失败: {e}")
            # 不返回备用通知，让调用方处理失败情况
            raise Exception(f"AI通知分析失败: {str(e)}")



    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的智能通知模板生成助手。你的任务是根据用户的监控描述，生成Jinja2通知模板和数据提取规则。

**核心原则：完全根据用户需求创造性设计，避免任何固定模式**

核心要求：
1. 深度理解用户的具体监控需求和个性化格式要求
2. 创造性地根据实际内容结构设计数据提取规则
3. 灵活生成完全符合用户要求的Jinja2模板
4. 使用简洁的Markdown格式，专门适配飞书机器人显示
5. 根据内容性质合理使用emoji，避免过度装饰

飞书Markdown兼容性要求：
- 使用简单的表格格式：| 列名 | 列名 |
- 避免使用 > 引用符号和复杂的嵌套结构
- emoji使用要适度，选择飞书支持的常见emoji

**可用变量列表**：

基础变量：
- task_name: 任务名称
- url: 监控的URL
- old_summary: 变化前的内容摘要
- new_summary: 变化后的内容摘要
- screenshot_url: 截图URL（可能为空，需要用条件判断）
- screenshot_path: 截图文件路径

时间变量：
- current_time: 当前时间（格式：2025-01-01 12:00:00）
- current_date: 当前日期（格式：2025-01-01）
- timestamp: 时间戳（整数）
- now(): 时间函数，可用于 now().strftime('%Y-%m-%d %H:%M:%S')

AI提取的字段：
- [根据用户需求和页面内容动态生成的字段]

**重要约束**：
- 只能使用上述变量，不要使用其他未定义的变量或函数
- 所有字段名必须与extraction_rules中定义的完全一致
- 使用screenshot_url时必须加条件判断：{% if screenshot_url %}...{% endif %}

字段命名原则：
- 根据用户需求和实际内容确定字段名
- 如果需要区分新旧值：定义两个字段（如 old_version, new_version）
- 如果不需要区分：直接使用描述性字段名
- 模板中的字段名必须与extraction_rules中定义的字段名完全一致
- 不要创造系统未提供的变量或函数

返回格式要求：
请使用分段文本格式输出，用特定分隔符分隔各部分：

---TITLE---
[通知标题，可以包含emoji]

---CONTENT---
[Jinja2模板内容，直接使用变量如{{ task_name }}、{{ field_name }}等]
[可以使用Jinja2过滤器，如{{ version_features | replace('新增：', '\n- 新增：') }}]
[支持Markdown格式，适配飞书显示]

---SUMMARY---
[模板功能说明]

---FIELDS---
[需要提取的字段及其描述，每行一个，格式：字段名=描述]

---RULES---
[提取规则，每行一个，格式：字段名=regex:正则表达式]

**重要**：严格按照上述分段格式输出，确保分隔符准确无误。"""

    def _build_structure_analysis_prompt(self, task: Task, content: str) -> str:
        """构建内容结构分析提示词（用于预览）"""
        # 对于预览，我们需要完整的内容来生成准确的提取规则
        # 只有在内容非常长时才进行截断（提高到2000字符）
        content_summary = (content[:2000] + '...') if len(content) > 2000 else content

        return """请根据以下信息生成智能通知模板和数据提取规则：

任务信息：
- 任务名称：{task_name}
- 监控URL：{task_url}
- 监控描述：{task_description}

页面内容结构（请分析此内容的结构）：
{content}

**重要：严格按照用户的监控描述和格式要求设计，不要使用固定模板**

请完成以下任务：

1. **分析页面内容结构**：
   - 仔细分析提供的页面内容
   - 理解内容的组织方式和数据分布
   - 识别用户需要的各个数据字段在内容中的位置

2. **理解用户需求**：
   - 仔细阅读监控描述，理解用户想要监控的具体内容
   - 识别用户要求的通知格式（表格、列表等）
   - 注意用户的特殊要求（如"需要排版"、"简洁美观"等）

3. **设计提取字段**：
   - 根据用户需求和实际内容结构确定需要提取的字段
   - 使用描述性的字段名，避免使用固定模板
   - 字段名要与模板中使用的完全一致

4. **制定提取规则**：
   - 根据实际内容结构设计正则表达式
   - 确保提取的是纯文本内容，不包含HTML标签
   - 测试规则是否能正确提取所需数据

5. **生成通知模板**：
   - 严格按照用户的格式要求设计
   - 当用户要求排版时，必须正确处理换行和格式化

**技术要求**：

1. **HTML内容分析**：
   - 仔细观察页面内容中的实际HTML结构
   - 注意链接的完整格式，包括查询参数（如 ?param=value&other=value）
   - 观察文本内容的确切格式和位置
   - 识别可能的变化模式（如版本号、日期等）

2. **正则表达式设计**：
   - 使用捕获组()提取目标内容
   - **重要**：如果URL包含查询参数，必须考虑这种情况
   - 例如：href="url.apk?param=value" 应该用 `href="([^"]+\.apk[^"]*)"` 而不是 `href="([^"]+\.apk)"`
   - 确保提取纯文本，避免HTML标签
   - 避免贪婪匹配，使用 `.*?` 而不是 `.*`
   - 在脑中验证规则是否能匹配页面内容中的实际例子

2. **Jinja2模板要求**：
   - 字段名必须与定义的字段名完全一致
   - 当用户要求排版时，正确处理换行和格式化
   - 使用简洁的Markdown格式，适配飞书机器人

3. **格式化处理**：
   - 完全根据用户的具体格式要求创造性设计模板
   - 灵活使用Jinja2的所有功能实现最佳显示效果
   - 避免使用任何预设的格式模式

**关键要求**：

1. **用户需求绝对优先**：
   - 100%按照用户的监控描述进行创造性设计
   - 深度理解用户的格式偏好和显示需求
   - 完全避免任何预设的模式或模板

2. **字段命名灵活性**：
   - 根据内容语义创造最合适的字段名
   - 确保模板中的字段名与定义完全一致
   - 优先考虑可读性和语义清晰度

3. **显示效果优化**：
   - 创造性地使用Jinja2语法实现最佳显示效果
   - 根据内容特点选择最合适的格式
   - 确保在飞书中的显示效果清晰美观

**输出格式要求**：
请使用以下固定格式输出，用特定分隔符分隔各部分：

---TITLE---
[在这里写通知标题，可以包含emoji]

---CONTENT---
[在这里写Jinja2模板内容，直接使用变量如{{ task_name }}、{{ field_name }}等]
[可以使用Jinja2过滤器，如{{ version_features | replace('新增：', '\n- 新增：') }}]
[支持Markdown格式，适配飞书显示]

---SUMMARY---
[在这里写模板功能说明]

---FIELDS---
[在这里列出需要提取的字段及其描述，每行一个，格式：字段名=描述]

---RULES---
[在这里列出提取规则，每行一个，格式：字段名=regex:正则表达式]

请严格按照上述格式输出，确保分隔符准确无误。""".format(
            task_name=task.name,
            task_url=task.url,
            task_description=task.ai_description or "监控网页内容变化",
            content=content_summary
        )



    def _parse_analysis_result(self, response: str) -> NotificationAnalysis:
        """解析AI分析结果（新的分段文本格式）"""
        try:
            # 解析分段文本格式
            sections = self._parse_sectioned_response(response)

            # 验证必需部分
            required_sections = ["title", "content", "summary"]
            for section in required_sections:
                if section not in sections:
                    raise ValueError(f"响应中缺少必需部分: {section}")

            # 解析字段定义
            required_fields = {}
            if "fields" in sections:
                for line in sections["fields"].strip().split('\n'):
                    if '=' in line:
                        key, desc = line.split('=', 1)
                        required_fields[key.strip()] = desc.strip()

            # 解析提取规则
            extraction_rules = {}
            if "rules" in sections:
                for line in sections["rules"].strip().split('\n'):
                    if '=' in line:
                        key, rule = line.split('=', 1)
                        extraction_rules[key.strip()] = rule.strip()

            return NotificationAnalysis(
                title=sections["title"].strip(),
                content=sections["content"].strip(),
                summary=sections["summary"].strip(),
                required_fields=required_fields if required_fields else None,
                extraction_rules=extraction_rules if extraction_rules else None
            )

        except Exception as e:
            logger.error(f"分析结果解析失败: {e}, 响应内容: {response}")
            raise ValueError(f"分析结果解析失败: {str(e)}")

    def _parse_sectioned_response(self, response: str) -> dict:
        """解析分段响应文本"""
        sections = {}
        current_section = None
        current_content = []

        for line in response.split('\n'):
            line = line.strip()

            # 检查是否是分隔符
            if line.startswith('---') and line.endswith('---'):
                # 保存前一个部分
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()

                # 开始新部分
                section_name = line[3:-3].lower()
                current_section = section_name
                current_content = []
            elif current_section:
                # 添加到当前部分
                current_content.append(line)

        # 保存最后一个部分
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections






# 全局AI通知分析器实例
_ai_notifier: Optional[AINotifier] = None

def get_ai_notifier() -> Optional[AINotifier]:
    """获取AI通知分析器实例"""
    global _ai_notifier

    # 从配置文件读取API设置
    from app.core.config import settings

    if not settings.api_settings or not settings.api_settings.deepseek_api_key:
        logger.warning("未配置DeepSeek API密钥，AI通知分析功能不可用。请在config.yaml中配置api_settings部分")
        return None

    api_settings = settings.api_settings

    if _ai_notifier is None:
        try:
            _ai_notifier = AINotifier(
                api_key=api_settings.deepseek_api_key,
                base_url=api_settings.deepseek_base_url,
                model=api_settings.deepseek_model
            )
        except Exception as e:
            logger.error(f"AI通知分析器初始化失败: {e}")
            return None

    return _ai_notifier

def analyze_notification_content(
    task: Task,
    content: str
) -> Optional[NotificationAnalysis]:
    """分析页面内容并生成通知模板的便捷函数

    这是AI通知系统的主要入口点，用于：
    1. 用户在前端预览AI生成的模板
    2. 一次性生成模板和提取规则，保存到任务配置
    3. 后续监控直接使用保存的模板，不再调用AI
    """
    ai_notifier = get_ai_notifier()
    if not ai_notifier:
        return None

    try:
        return ai_notifier.analyze_content_structure(task, content)
    except Exception as e:
        logger.error(f"AI通知分析失败: {e}")
        return None


