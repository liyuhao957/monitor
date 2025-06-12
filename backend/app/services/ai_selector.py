"""
AI驱动的选择器生成服务
使用ChatGPT API分析页面结构并生成最优选择器
"""
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SelectorRequest(BaseModel):
    """选择器生成请求"""
    element_html: str
    context_html: str
    user_intent: str
    element_text: str
    element_attributes: Dict[str, str]

class SelectorResponse(BaseModel):
    """选择器生成响应"""
    css_selector: str
    xpath: str
    description: str
    confidence: int

class AISelector:
    """AI选择器生成器"""

    def __init__(self, api_key: str, base_url: str = "https://api.oaipro.com/v1"):
        try:
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key
            )
            logger.info("OpenAI客户端初始化成功")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
            raise
    
    def generate_selector(self, request: SelectorRequest) -> SelectorResponse:
        """生成最优选择器"""
        try:
            prompt = self._build_prompt(request)
            
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
            return self._parse_response(result)
            
        except Exception as e:
            logger.error(f"AI选择器生成失败: {e}")
            raise Exception(f"AI选择器生成失败: {str(e)}")
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的网页元素选择器生成专家。你的任务是分析HTML结构和用户意图，生成最稳定、最可靠的CSS选择器和XPath。

核心要求：
1. 生成的选择器必须能准确匹配到目标元素
2. 选择器要具有良好的稳定性，能抵抗页面小幅改动
3. 优先使用稳定的属性（id、data-*、稳定的class）
4. 避免使用易变的属性（动态生成的class、style等）
5. 根据用户意图选择合适的选择策略
6. **重要：忽略以下临时属性，这些是选择器工具添加的，不应该用于生成选择器：**
   - data-selected-original-style
   - outline、outline-offset、background-color等样式属性
   - 任何包含"selected"、"highlight"、"outline"的属性

用户意图说明：
- "fixed": 监控固定位置的元素内容变化
- "latest": 监控列表中最新的一条（通常是第一个元素）
- "list": 监控整个列表的变化
- "specific": 监控列表中特定位置的元素
- "auto": 让你自动判断最合适的监控方式

请返回JSON格式：
{
    "css_selector": "最优的CSS选择器",
    "xpath": "最优的XPath选择器",
    "description": "选择器的说明和选择理由",
    "confidence": 95
}

confidence是你对这个选择器的信心度(0-100)，必须>=90才能返回。如果信心度<90，请返回错误说明。"""

    def _build_prompt(self, request: SelectorRequest) -> str:
        """构建用户提示词"""
        return f"""请分析以下精确路径信息并生成最优选择器：

用户意图：{request.user_intent}

目标元素HTML：
{request.element_html}

完整路径信息（从根元素到目标元素的精确路径）：
{request.context_html}

目标元素文本内容：
{request.element_text}

目标元素属性：
{json.dumps(request.element_attributes, ensure_ascii=False, indent=2)}

请根据以上信息生成最稳定、最可靠的选择器。特别注意：

**关键要求：**
1. **利用完整路径信息** - 上面提供的路径信息包含了从根元素到目标元素的完整路径，包括每个层级的唯一标识符
2. **选择器必须唯一且精确** - 使用路径信息中的唯一标识符（id、稳定的class等）来确保选择器的唯一性
3. **根据用户意图生成：**
   - "latest": 生成能选中**这个特定路径下列表**的第一个元素的选择器
   - "fixed": 生成能精确定位到这个具体元素的选择器
4. **优先级顺序（基于路径信息）：**
   - 首选：路径中有id的层级，构建从该id开始的选择器
   - 次选：路径中有稳定class的层级，构建包含这些class的选择器
   - 最后：使用完整的结构路径，确保从根到目标的唯一性

**示例：**
- 好的选择器：`main .content ul li:first-child` 或 `//main//section[@class="content"]//ul/li[1]`
- 更好的选择器：`main section.content ul li:first-child` 或 `//main/section[@class="content"]/ul/li[1]`
- 坏的选择器：`ul li:first-child` 或 `//ul/li[1]`（太泛化）
- 坏的选择器：`.content ul li:first-child`（可能有多个.content）

**重要提醒：**
从上下文信息可以看出，目标元素在 main > section.content > ul 的结构中。请生成包含完整路径的选择器，确保从页面根部开始的唯一性。

请返回JSON格式的结果。"""

    def _parse_response(self, response: str) -> SelectorResponse:
        """解析AI响应"""
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
                raise ValueError("响应中未找到JSON格式数据")
            
            data = json.loads(json_str)
            
            # 验证必需字段
            required_fields = ["css_selector", "xpath", "description", "confidence"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"响应中缺少必需字段: {field}")
            
            # 验证信心度
            if data["confidence"] < 90:
                raise ValueError(f"AI信心度过低: {data['confidence']}")
            
            return SelectorResponse(**data)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 响应内容: {response}")
            raise ValueError(f"AI响应格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            raise ValueError(f"响应解析失败: {str(e)}")
