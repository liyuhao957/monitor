"""
AI驱动的选择器生成服务
使用ChatGPT API分析页面结构并生成最优选择器
"""
import json
import logging
from typing import Dict
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
    recommended_type: str  # 推荐的选择器类型: css, xpath
    description: str
    confidence: int
    type_analysis: dict  # 各类型选择器的分析结果

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
        return """你是一个专业的网页元素选择器生成专家。你的任务是分析HTML结构和用户意图，生成CSS选择器和XPath并智能推荐最优类型。

## 核心要求：
1. **生成两种选择器类型**：CSS选择器、XPath
2. **每个选择器都必须准确可用**，能够唯一定位到目标元素
3. **智能分析并推荐最适合的类型**
4. **提供详细的选择理由和分析**

## 选择器类型适用场景：

### CSS选择器适用场景（通常优先推荐）：
- 元素有稳定的id或class属性
- DOM结构相对简单且稳定
- 需要高性能（CSS选择器执行速度最快）
- 标准的父子、兄弟关系定位
- 现代网页开发规范的页面
- 元素有明确的CSS类名或属性选择器

### XPath适用场景：
- 需要基于文本内容进行定位
- 需要复杂的条件判断和逻辑
- 需要向上遍历（从子元素找父元素）
- DOM结构复杂且经常变化
- 需要使用函数（contains、starts-with等）
- CSS选择器无法表达的复杂选择逻辑
- 需要基于元素位置（第几个子元素）进行精确定位

## 重要注意事项：
**忽略以下临时属性（选择器工具添加的）：**
- data-selected-original-style
- outline、outline-offset、background-color等样式属性
- 任何包含"selected"、"highlight"、"outline"的属性

## 用户意图说明：
- "fixed": 监控固定位置的元素内容变化
- "latest": 监控列表中最新的一条（通常是第一个数据元素，跳过表头）
- "list": 监控整个列表的变化
- "specific": 监控列表中特定位置的元素
- "auto": 让你自动判断最合适的监控方式

## 表格处理特殊要求：
- **区分表头和数据行**：表头通常包含`<th>`元素，数据行包含`<td>`元素
- **latest意图处理**：对于表格，应该选择第一个数据行（包含`<td>`的行），而不是表头行
- **使用正确的行选择器**：
  - 如果第一行是表头：使用`tbody > tr:nth-child(2)`或`tbody > tr:has(td):first-child`
  - 如果没有表头：使用`tbody > tr:first-child`

## 返回JSON格式：
{
    "css_selector": "CSS选择器（必须可用）",
    "xpath": "XPath选择器（必须可用）",
    "recommended_type": "推荐类型：css|xpath",
    "description": "推荐理由和各选择器的说明",
    "confidence": 95,
    "type_analysis": {
        "css": {"score": 85, "reason": "CSS选择器分析和适用性评估"},
        "xpath": {"score": 90, "reason": "XPath选择器分析和适用性评估"}
    }
}

**重要**：confidence必须>=90，每个选择器都必须经过验证确保可用。推荐类型应该是type_analysis中得分最高的类型。"""

    def _build_prompt(self, request: SelectorRequest) -> str:
        """构建用户提示词"""
        return f"""请分析以下元素信息，生成四种类型的选择器并智能推荐最优类型：

## 分析目标：
**用户意图**：{request.user_intent}
**目标元素HTML**：
{request.element_html}

**完整路径信息**：
{request.context_html}

**目标元素文本内容**：
{request.element_text}

**目标元素属性**：
{json.dumps(request.element_attributes, ensure_ascii=False, indent=2)}

## 任务要求：

### 0. 路径分析步骤（必须执行！）
**严格按照pathSummary构建选择器路径**：
1. **逐层分析pathSummary**：从level 1开始，按顺序分析每一层
2. **使用实际的tag和position**：如果某层是"tag": "div", "position": "4/5"，必须使用div:nth-child(4)
3. **忽略class推测**：不要假设存在.tableBox等类名，严格按照pathSummary中的实际结构
4. **构建精确路径**：每一层都必须对应pathSummary中的一个level
5. **示例分析**：如果pathSummary显示level 15是"tag": "div", "position": "2/27"，则必须使用div:nth-child(2)

### 1. 上下文信息分析（关键！）
**必须仔细分析完整路径信息**：
- **检查pathSummary中的position信息**：如"position": "2/20"表示是第2个，共20个同类元素
- **识别非唯一元素**：如果isUnique为false，说明有多个相同元素，必须使用索引区分
- **构建精确路径**：从uniqueIdentifiers开始，逐层添加必要的索引和选择器
- **验证唯一性**：确保最终选择器在整个页面中只匹配一个元素

**重要**：如果pathSummary显示某个元素的position不是"1/1"，说明有多个同类元素，必须使用:nth-of-type()或[position()]来区分！

### 2. 元素特征分析
请分析目标元素的特征：
- 是否有稳定的id或class？
- DOM结构是否复杂？
- 文本内容是否有规律模式？
- 在页面中是否唯一？

### 2. 生成两种选择器（每个都必须可用）

**CSS选择器要求**：
- **严格按照pathSummary构建**：每一层都必须对应pathSummary中的一个level
- **CSS索引规则**：CSS的:nth-child()计算所有子元素，需要根据实际DOM位置调整
- **不要假设类名**：不要使用pathSummary中没有明确显示的类名（如.tableBox）
- **从uniqueIdentifiers开始**：找到最近的有id的层级作为起点
- **逐层添加路径**：使用 > 连接符，确保直接子元素关系
- **表格处理**：对于latest意图，如果目标是tr，确保选择数据行而不是表头行
- **验证语法**：确保CSS选择器语法完全正确，能够在浏览器中执行
- 示例：#doc-content-text > div:nth-child(4) > table > tbody > tr:nth-child(2)

**XPath要求**：
- **严格按照pathSummary构建**：每一层都必须对应pathSummary中的一个level
- **使用实际的tag和position**：如level 4显示"tag": "div", "position": "4/5"，必须使用div[4]
- **不要假设属性**：不要使用pathSummary中没有明确显示的属性（如@class='tableBox'）
- **从uniqueIdentifiers开始**：找到最近的有[@id]的层级作为起点
- **逐层添加路径**：按照pathSummary的顺序，逐层添加tag[position]
- **表格处理**：对于latest意图，如果目标是tr且position是"1/20"，检查是否需要使用[2]跳过表头
- 示例：//*[@id="doc-content-text"]/div[4]/table/tbody/tr[2]

### 3. 智能推荐逻辑
根据以下标准评分（0-100）：
- **CSS**: 有稳定id/class属性=高分，简单DOM结构=高分，现代网页=高分
- **XPath**: 需要文本匹配=高分，复杂DOM结构=高分，需要向上遍历=高分，CSS无法表达=高分

### 4. 验证要求（关键！）
每个选择器都必须：
- **绝对唯一**：在整个页面中只能匹配到一个元素
- **使用唯一路径**：必须从uniqueIdentifiers中的唯一父元素开始构建
- **避免歧义**：不能使用可能匹配多个元素的选择器
- **语法正确**：CSS和XPath语法都必须完全正确，能够在浏览器中执行
- **表格准确性**：对于表格元素，确保选择的是正确的行类型（数据行vs表头行）
- **索引准确性**：CSS的:nth-child()和XPath的[position()]必须使用正确的数字
- 具有良好的稳定性
- 符合用户意图（fixed/latest/list等）

**重要验证点**：
1. CSS选择器必须使用正确的:nth-child()索引，考虑所有子元素的位置
2. XPath必须使用正确的[position]索引，考虑同类型元素的位置
3. 对于latest意图的表格，确保选择第一个数据行而不是表头行
4. 两个选择器必须指向完全相同的元素
5. 生成后在脑中验证选择器的正确性

请返回完整的JSON格式结果。"""

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
            required_fields = ["css_selector", "xpath", "recommended_type", "description", "confidence", "type_analysis"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"响应中缺少必需字段: {field}")

            # 验证推荐类型
            valid_types = ["css", "xpath"]
            if data["recommended_type"] not in valid_types:
                raise ValueError(f"无效的推荐类型: {data['recommended_type']}")

            # 验证信心度
            if data["confidence"] < 90:
                raise ValueError(f"AI信心度过低: {data['confidence']}")

            # 验证type_analysis结构
            if not isinstance(data["type_analysis"], dict):
                raise ValueError("type_analysis必须是字典格式")

            return SelectorResponse(**data)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 响应内容: {response}")
            raise ValueError(f"AI响应格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            raise ValueError(f"响应解析失败: {str(e)}")
