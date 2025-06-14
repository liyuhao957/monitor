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

    def __init__(self, api_key: str, base_url: str = "https://api.oaipro.com/v1"):
        try:
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            logger.info("AI通知分析器初始化成功")
        except Exception as e:
            logger.error(f"AI通知分析器初始化失败: {e}")
            raise

    def analyze_content_change(
        self, 
        task: Task, 
        old_content: str, 
        new_content: str
    ) -> NotificationAnalysis:
        """分析内容变化并生成智能通知"""
        try:
            prompt = self._build_analysis_prompt(task, old_content, new_content)
            
            response = self.client.chat.completions.create(
                model="o3",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            result = response.choices[0].message.content
            return self._parse_analysis_result(result)
            
        except Exception as e:
            logger.error(f"AI通知分析失败: {e}")
            # 不返回备用通知，让调用方处理失败情况
            raise Exception(f"AI通知分析失败: {str(e)}")

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的智能通知模板生成助手。你的任务是根据用户的监控描述，不仅生成Jinja2通知模板，还要定义需要从内容中提取的结构化数据。

核心要求：
1. 分析用户的监控需求，确定需要提取哪些结构化数据
2. 定义数据提取规则，告诉系统如何从HTML内容中提取这些数据
3. 生成使用这些结构化数据的Jinja2模板
4. 使用简洁的Markdown格式，专门适配飞书机器人显示
5. 包含合适的emoji，但避免使用飞书不支持的复杂符号

飞书Markdown兼容性要求：
- 避免使用复杂的表格格式符号，如 |:--:|、|:------:|
- 使用简单的表格格式：| 列名 | 列名 |
- 避免使用 > 引用符号
- 避免使用复杂的嵌套结构
- emoji使用要适度，选择飞书支持的常见emoji

基础可用变量：
- task_name: 任务名称
- url: 监控的URL
- old_summary: 变化前的内容摘要（字符串）
- new_summary: 变化后的内容摘要（字符串）
- screenshot_url: 截图URL（可能为空，需要用条件判断）
- screenshot_path: 截图路径

动态变量定义：
你可以定义额外的变量，系统会根据你的提取规则自动生成这些变量。
例如：old_version, new_version, old_spec, new_spec, version_changed 等

返回格式必须是有效的JSON：
{
  "title": "模板标题（可使用变量）",
  "content": "Jinja2模板内容（简洁Markdown格式）",
  "summary": "模板功能说明",
  "required_fields": {
    "old_version": "变化前的版本号",
    "new_version": "变化后的版本号",
    "old_spec": "变化前的规范版本",
    "new_spec": "变化后的规范版本"
  },
  "extraction_rules": {
    "old_version": "使用正则表达式从old_summary中提取V开头的版本号：V(\\d+\\.\\d+\\.\\d+\\.\\d+)",
    "new_version": "使用正则表达式从new_summary中提取V开头的版本号：V(\\d+\\.\\d+\\.\\d+\\.\\d+)",
    "old_spec": "使用正则表达式从old_summary中提取支持规范数字：支持(\\d+)规范",
    "new_spec": "使用正则表达式从new_summary中提取支持规范数字：支持(\\d+)规范"
  }
}"""

    def _build_analysis_prompt(self, task: Task, old_content: str, new_content: str) -> str:
        """构建分析提示词"""
        # 对于AI预览，我们需要完整的内容来生成准确的提取规则
        # 只有在内容非常长时才进行截断（提高到2000字符）
        old_summary = (old_content[:2000] + '...') if len(old_content) > 2000 else old_content
        new_summary = (new_content[:2000] + '...') if len(new_content) > 2000 else new_content
        
        return f"""请根据以下信息生成智能通知模板和数据提取规则：

任务信息：
- 任务名称：{task.name}
- 监控URL：{task.url}
- 监控描述：{task.ai_description or "监控网页内容变化"}

示例内容变化（用于理解监控重点）：
变化前：
{old_summary}

变化后：
{new_summary}

请分析用户的监控需求，完成以下任务：

1. **分析监控重点**：根据监控描述，确定用户关心的具体数据（如版本号、规范、链接等）

2. **定义提取字段**：为每个关键数据定义字段名和描述

3. **制定提取规则**：为每个字段定义正则表达式或其他提取方法

4. **生成智能模板**：使用定义的字段生成美观的通知模板

要求：
- 使用Jinja2语法和简洁的Markdown格式
- 根据用户需求设计表格或列表格式
- 包含条件判断和emoji
- 提取规则要准确匹配示例内容
- 专门适配飞书机器人，避免复杂符号

**飞书兼容性要求**：
- 表格格式使用简单的 | 列名 | 列名 | 格式，避免对齐符号如 |:--:|
- 不使用 > 引用符号
- emoji使用要适度，选择常见支持的emoji
- 避免复杂的嵌套结构

**重要：正则表达式规则**
- 使用捕获组()来提取需要的内容，而不是匹配的关键词
- 例如：要提取"新增：功能描述"中的功能描述，应该用 `(?:新增|更新)：(.*?)` 而不是 `(新增|更新)：.*`
- 第一个捕获组的内容将作为字段值返回

**参考示例（飞书友好格式）**：
🚨 检测到引擎版本更新！

| 类型 | 内容 |
| 版本号 | `V9.0.18.300` |
| 上线时间 | `2025-05-13` |
| 荣耀版本 | `6101` |
| 联盟版本 | `1123` |

📋 更新内容
• 新增:快应用&卡片feature（system.network）中新增registerNetworkObserver接口
• 新增:快应用&卡片feature（system.battery）中新增registerObserver接口
• 优化:快应用后台状态判断优化

示例返回格式：
{{
  "title": "{{{{ task_name }}}} 更新通知",
  "content": "🚨 检测到引擎版本更新！\\n\\n| 类型 | 内容 |\\n| 版本号 | `{{{{ new_version }}}}` |\\n| 上线时间 | `{{{{ release_date }}}}` |\\n| 荣耀版本 | `{{{{ honor_version }}}}` |\\n\\n📋 更新内容\\n{{{{ update_features }}}}\\n\\n{{% if screenshot_url %}}📸 [查看截图]({{{{ screenshot_url }}}})\\n{{% endif %}}",
  "summary": "引擎版本更新通知模板",
  "required_fields": {{
    "new_version": "新版本号",
    "release_date": "发布时间",
    "honor_version": "荣耀版本",
    "update_features": "更新功能列表"
  }},
  "extraction_rules": {{
    "new_version": "从new_summary中提取V开头的版本号：V([0-9.]+)",
    "release_date": "从new_summary中提取日期：(\\d{{4}}-\\d{{2}}-\\d{{2}})",
    "honor_version": "从new_summary中提取荣耀版本号：荣耀版本.*?([0-9]+)",
    "update_features": "从new_summary中提取更新内容，转换为列表格式"
  }}
}}"""

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
    
    # 这里可以从环境变量或配置文件读取API密钥
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.oaipro.com/v1")
    
    if not api_key:
        logger.warning("未配置OPENAI_API_KEY，AI通知分析功能不可用")
        return None
    
    if _ai_notifier is None:
        try:
            _ai_notifier = AINotifier(api_key=api_key, base_url=base_url)
        except Exception as e:
            logger.error(f"AI通知分析器初始化失败: {e}")
            return None
    
    return _ai_notifier

def analyze_notification_content(
    task: Task, 
    old_content: str, 
    new_content: str
) -> Optional[NotificationAnalysis]:
    """分析通知内容的便捷函数"""
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
