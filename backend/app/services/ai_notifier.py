"""
AI驱动的通知内容分析服务
使用OpenAI API分析监控内容变化并生成简洁美观的通知
"""
import json
import logging
from typing import Optional, Dict, Any
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
        """分析页面内容结构并生成智能通知模板（用于预览）"""
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

    def analyze_content_change(
        self,
        task: Task,
        old_content: str,
        new_content: str
    ) -> NotificationAnalysis:
        """分析内容变化并生成智能通知（用于实际监控）"""
        try:
            prompt = self._build_analysis_prompt(task, old_content, new_content)

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

**核心原则：严格按照用户需求设计，不使用固定模板**

核心要求：
1. 仔细分析用户的具体监控需求和格式要求
2. 根据实际内容结构设计数据提取规则
3. 生成符合用户要求的Jinja2模板
4. 使用简洁的Markdown格式，专门适配飞书机器人显示
5. 包含合适的emoji，但避免使用飞书不支持的复杂符号

飞书Markdown兼容性要求：
- 使用简单的表格格式：| 列名 | 列名 |
- 避免使用 > 引用符号和复杂的嵌套结构
- emoji使用要适度，选择飞书支持的常见emoji

基础可用变量：
- task_name: 任务名称
- url: 监控的URL
- old_summary: 变化前的内容摘要
- new_summary: 变化后的内容摘要
- screenshot_url: 截图URL（可能为空，需要用条件判断）

字段命名原则：
- 根据用户需求和实际内容确定字段名
- 如果需要区分新旧值：定义两个字段（如 old_version, new_version）
- 如果不需要区分：直接使用描述性字段名
- 模板中的字段名必须与定义的字段名完全一致

返回格式必须是有效的JSON：
{
  "title": "根据用户需求设计的标题",
  "content": "根据用户要求设计的Jinja2模板",
  "summary": "模板功能说明",
  "required_fields": {
    "字段名": "字段描述"
  },
  "extraction_rules": {
    "字段名": "根据实际内容设计的提取规则"
  }
}"""

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

1. **正则表达式原则**：
   - 使用捕获组()提取目标内容
   - 根据实际内容结构设计，不要使用固定模式
   - 确保提取纯文本，避免HTML标签
   - 避免贪婪匹配，使用 `.*?` 而不是 `.*`

2. **Jinja2模板要求**：
   - 字段名必须与定义的字段名完全一致
   - 当用户要求排版时，正确处理换行和格式化
   - 使用简洁的Markdown格式，适配飞书机器人

3. **格式化处理**：
   - 对于长文本（如功能列表），使用split()和循环处理
   - 当用户明确要求排版时，确保每个项目独立成行
   - 正确的循环格式：
     ```
     {{%- set items = field_name.split('分隔符') -%}}
     {{%- for item in items if item.strip() %}}
     - {{{{ item.strip() }}}}
     {{%- endfor %}}
     ```

**关键要求**：

1. **用户需求优先**：
   - 严格按照用户的监控描述设计
   - 当用户要求"排版"时，必须确保内容正确换行显示
   - 不要使用固定的字段名或格式模板

2. **字段命名一致性**：
   - 模板中使用的字段名必须与定义的字段名完全一致
   - 根据实际需求确定字段名，不要使用固定模板

3. **格式化要求**：
   - 当处理列表内容时，确保每个项目独立成行
   - 正确使用Jinja2语法控制换行
   - 适配飞书机器人显示

请根据用户的具体需求生成JSON格式的响应。""".format(
            task_name=task.name,
            task_url=task.url,
            task_description=task.ai_description or "监控网页内容变化",
            content=content_summary
        )

    def _build_analysis_prompt(self, task: Task, old_content: str, new_content: str) -> str:
        """构建分析提示词"""
        # 对于AI预览，我们需要完整的内容来生成准确的提取规则
        # 只有在内容非常长时才进行截断（提高到2000字符）
        old_summary = (old_content[:2000] + '...') if len(old_content) > 2000 else old_content
        new_summary = (new_content[:2000] + '...') if len(new_content) > 2000 else new_content
        
        return """请根据以下信息生成智能通知模板和数据提取规则：

任务信息：
- 任务名称：{task_name}
- 监控URL：{task_url}
- 监控描述：{task_description}

示例内容变化（用于理解监控重点）：
变化前：
{old_summary}

变化后：
{new_summary}

**重要：严格按照用户的监控描述和格式要求设计，不要使用固定模板**

请完成以下任务：

1. **分析用户具体需求**：
   - 仔细阅读监控描述，理解用户想要监控的具体内容
   - 识别用户要求的通知格式（表格、列表等）
   - 注意用户的特殊要求（如"需要排版"、"简洁美观"等）

2. **设计提取字段**：
   - 根据用户需求和实际内容结构确定需要提取的字段
   - 使用描述性的字段名，避免使用固定模板
   - 字段名要与模板中使用的完全一致

3. **制定提取规则**：
   - 根据实际内容结构设计正则表达式
   - 确保提取的是纯文本内容，不包含HTML标签

4. **生成通知模板**：
   - 严格按照用户的格式要求设计
   - 当用户要求排版时，必须正确处理换行和格式化

**技术要求**：

1. **正则表达式原则**：
   - 使用捕获组()提取目标内容
   - 根据实际内容结构设计，不要使用固定模式
   - 确保提取纯文本，避免HTML标签
   - 避免贪婪匹配，使用 `.*?` 而不是 `.*`

2. **Jinja2模板要求**：
   - 字段名必须与定义的字段名完全一致
   - 当用户要求排版时，正确处理换行和格式化
   - 使用简洁的Markdown格式，适配飞书机器人

3. **格式化处理**：
   - 对于长文本（如功能列表），使用split()和循环处理
   - 当用户明确要求排版时，确保每个项目独立成行
   - 正确的循环格式：
     ```
     {{%- set items = field_name.split('分隔符') -%}}
     {{%- for item in items if item.strip() %}}
     - {{{{ item.strip() }}}}
     {{%- endfor %}}
     ```

**关键要求**：

1. **用户需求优先**：
   - 严格按照用户的监控描述设计
   - 当用户要求"排版"时，必须确保内容正确换行显示
   - 不要使用固定的字段名或格式模板

2. **字段命名一致性**：
   - 模板中使用的字段名必须与定义的字段名完全一致
   - 根据实际需求确定字段名，不要使用固定模板

3. **格式化要求**：
   - 当处理列表内容时，确保每个项目独立成行
   - 正确使用Jinja2语法控制换行
   - 适配飞书机器人显示

请根据用户的具体需求生成JSON格式的响应。""".format(
            task_name=task.name,
            task_url=task.url,
            task_description=task.ai_description or "监控网页内容变化",
            old_summary=old_summary,
            new_summary=new_summary
        )

    def _parse_analysis_result(self, response: str) -> NotificationAnalysis:
        """解析AI分析结果"""
        try:
            # 尝试提取JSON部分
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
            else:
                raise ValueError("响应中未找到JSON格式")

            data = json.loads(json_str)
            
            # 验证必需字段
            required_fields = ["title", "content", "summary"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"缺少必需字段: {field}")

            # 可选字段验证
            if "required_fields" in data and not isinstance(data["required_fields"], dict):
                raise ValueError("required_fields必须是字典类型")
            if "extraction_rules" in data and not isinstance(data["extraction_rules"], dict):
                raise ValueError("extraction_rules必须是字典类型")

            return NotificationAnalysis(**data)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 响应内容: {response}")
            raise ValueError(f"AI响应格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"分析结果解析失败: {e}")
            raise ValueError(f"分析结果解析失败: {str(e)}")




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
    """分析页面内容并生成通知模板的便捷函数（用于预览）"""
    ai_notifier = get_ai_notifier()
    if not ai_notifier:
        return None

    try:
        return ai_notifier.analyze_content_structure(task, content)
    except Exception as e:
        logger.error(f"AI通知分析失败: {e}")
        return None

def analyze_notification_content_change(
    task: Task,
    old_content: str,
    new_content: str
) -> Optional[NotificationAnalysis]:
    """分析内容变化并生成通知的便捷函数（用于实际监控）"""
    if not task.ai_analysis_enabled:
        return None

    ai_notifier = get_ai_notifier()
    if not ai_notifier:
        return None

    try:
        return ai_notifier.analyze_content_change(task, old_content, new_content)
    except Exception as e:
        logger.error(f"AI通知分析失败: {e}")
        return None
