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
    summary: str
    required_fields: Optional[Dict[str, str]] = None  # 需要提取的字段及其描述
    extraction_rules: Optional[Dict[str, str]] = None  # 字段提取规则
    formatter_code: str  # AI生成的Python格式化代码

class AINotifier:
    """AI通知分析器"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-reasoner"):
        try:
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key,
                timeout=300.0,  # 增加到5分钟超时，适应推理模型的处理时间
                max_retries=1   # 减少OpenAI客户端的重试次数，避免与我们的重试机制冲突
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
            logger.info(f"开始AI分析")

            # 智能选择提示词：根据内容格式选择单规则或多规则提示词
            system_prompt = self._select_appropriate_prompt(content)

            prompt = self._build_structure_analysis_prompt(task, content)

            # 调用API并记录原始响应
            # 使用标准 OpenAI API 参数
            api_params = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 16000,
                "temperature": 0.1,   # 降低随机性，提高稳定性
                "timeout": 240        # 4分钟超时
            }

            response = self.client.chat.completions.create(**api_params)

            # 验证响应有效性
            if not response or not response.choices:
                raise ValueError("API返回空响应或无choices")

            result = response.choices[0].message.content
            if not result:
                raise ValueError("API返回空内容")

            # 记录响应内容用于调试
            logger.debug(f"API响应长度: {len(result)} 字符")
            logger.debug(f"API响应前200字符: {result[:200]}")

            # 解析结果
            return self._parse_analysis_result(result)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"AI通知分析失败: {error_msg}")
            raise Exception(f"AI通知分析失败: {error_msg}")

    def _get_system_prompt(self) -> str:
        """获取智能HTML分析提示词 - 根据内容格式选择对应提示词"""
        # 这个方法将被 _get_single_rule_prompt 和 _get_multi_rule_prompt 替代
        # 保留用于向后兼容
        return self._get_multi_rule_prompt()

    def _get_single_rule_prompt(self) -> str:
        """获取单规则HTML内容分析提示词 - 基于tsc.txt优化版"""
        return """你是专业的HTML数据提取专家，专门为通用型网页监控系统分析各种复杂页面结构并生成精确的提取规则。

**核心任务：**
1. **深度HTML结构分析**：系统性理解DOM层次关系，识别各种数据组织模式
2. **智能元素定位**：为每个字段生成独立且稳定的CSS选择器或XPath表达式
3. **健壮代码生成**：使用BeautifulSoup提取数据并格式化为飞书Markdown通知
4. **代码安全保证**：只使用标准库和BeautifulSoup4，禁止文件操作和网络请求

**HTML分析策略升级：**

**A. 结构化分析方法**
1. **识别页面模式**：
   - 列表型数据（ul/ol/li结构）
   - 表格型数据（table/tr/td结构）
   - 卡片型布局（div嵌套结构）
   - 时序型内容（按时间/版本排序的重复结构）

2. **定位数据层次**：
   - 容器级别：主要数据区域的外层容器
   - 分组级别：相关数据的分组容器
   - 元素级别：具体数据字段的直接容器
   - 内容级别：文本内容或属性值

**B. 智能选择器生成策略**
1. **从稳定到具体的渐进式定位**：
   ```css
   /* 基础定位：找到稳定的容器 */
   div[id*="main"], div[class*="content"], table, ul

   /* 精确定位：使用结构关系 */
   :first-child, :last-child, :first-of-type, :last-of-type
   :nth-child(1), :nth-child(2), :nth-of-type(1)

   /* 相邻关系：处理复杂布局 */
   h2 + div, h3 ~ table, tr:first-child + tr
   ```

2. **选择器唯一性保证**：
   - 每个字段必须使用完全不同的选择器路径
   - 使用元素索引(:nth-child)区分相似元素
   - 优先使用属性特征([class*=""], [id*=""])而非纯位置

3. **稳定性优先原则**：
   - 优先选择ID和稳定的class名
   - 使用结构位置关系而非样式依赖
   - 避免依赖可能变化的元素计数

**C. 复杂页面处理技巧**
- **时序数据处理**：对于包含多个版本/时间的页面，准确定位最新数据
- **嵌套结构处理**：使用空格组合符处理多层嵌套：`container section table tbody tr td`
- **相邻元素处理**：使用相邻组合符：`h2:first-of-type + div`, `td + td`
- **内容特征定位**：结合属性选择器：`a[href*=".zip"]`, `td[class*="version"]`

**D. 自验证机制（重要）**
生成每个选择器后，必须验证：
1. **唯一性检查**：确认与其他字段选择器不重复
2. **精确性检查**：选择器只能匹配目标元素，不能匹配多个
3. **有效性检查**：在提供的HTML中确实能找到目标元素
4. **稳定性评估**：选择器不依赖易变的页面特征

**E. 属性提取语法明确**
- **文本内容**：`css:selector` 或 `css:selector::text` → 提取元素文本
- **链接地址**：`css:a::attr(href)` → 提取href属性值
- **图片地址**：`css:img::attr(src)` → 提取src属性值
- **其他属性**：`css:element::attr(属性名)` → 提取指定属性
- **特别注意**：必须明确指定提取意图，避免歧义

**F. 错误处理与容错设计**
- 每个字段提取都要有完整的异常处理
- 提供合理的默认值应对数据缺失
- 处理HTML结构轻微变化的情况
- 确保部分字段失败不影响整体通知生成

**G. 代码生成要求（严格遵守）**
- **函数签名**：`def format_notification(extracted_data: dict, task_info: dict) -> str:`
- **动态数据获取**：使用`extracted_data.get('字段名', '默认值')`，严禁硬编码
- **时间处理**：使用`datetime.now().strftime('%Y-%m-%d %H:%M:%S')`
- **异常处理**：每个数据访问都要有try-except保护
- **输出格式**：生成结构清晰的飞书Markdown通知
- **代码规范**：不使用import语句，不使用Markdown代码块标记，只生成一个函数定义
- **禁止使用多行字符串**：不要使用 f'''...''' 或 '''...'''，改用字符串拼接

**H. 通知内容优化**
- 使用emoji增强视觉效果
- 重要信息突出显示（加粗、分行）
- 包含检测时间和相关链接
- 保持内容简洁但信息完整

**关键提醒：**
- 面对复杂页面时，优先保证核心字段的准确提取
- 生成的选择器必须在当前HTML中验证有效
- 每个字段使用独立唯一的选择器，绝不重复
- 代码必须健壮，能处理各种异常情况

**输出格式（严格按此格式）：**

---ANALYSIS---
详细分析HTML结构特征、数据组织方式、选择器设计思路

---TITLE---
通知标题

---CODE---
完整的Python函数代码（直接输出，无Markdown标记）

---SUMMARY---
分析结果摘要

---FIELDS---
字段名=字段描述

---RULES---
字段名=css:选择器 或 字段名=xpath:表达式"""

    def _get_multi_rule_prompt(self) -> str:
        """获取多规则分段内容分析提示词"""
        return """你是专业的数据提取专家，专门处理多规则分段内容格式的网页监控系统。

**专门任务：多规则分段内容处理**

**A. 多规则分段内容识别**
输入内容包含 `=== 规则 X: ... ===` 标记的分段格式：
```
=== 规则 1: css:#body0000001079803874 > div:nth-child(1) ===
<div class="tiledSection">1121版本更新说明（2025-6-6）</div>

=== 规则 2: css:#body0000001079803874 > div:nth-child(2) ===
<div class="tiledSection">表格内容...</div>
```

**B. 处理策略**
- 直接在Python代码中解析分段内容
- 使用正则表达式和文本处理
- 不生成CSS/XPath提取规则
- 不生成FIELDS和RULES部分

**C. 代码生成要求**
- **函数签名**：`def format_notification(extracted_data: dict, task_info: dict) -> str:`
- **数据获取**：使用`extracted_data.get('page_content', '')`获取原始分段内容
- **禁止使用多行字符串**：使用字符串拼接
- **包含异常处理**：完整的try-except保护

**输出格式：**

---ANALYSIS---
说明这是多规则分段内容格式和解析策略

---TITLE---
通知标题

---CODE---
完整的Python函数代码（直接输出，无Markdown标记）

---SUMMARY---
分析摘要

---FIELDS---
（留空）

---RULES---
（留空）"""

    def _select_appropriate_prompt(self, content: str) -> str:
        """根据内容格式智能选择合适的提示词"""
        # 检查是否包含多规则分段标记
        multi_rule_patterns = [
            "=== 规则 1:",
            "=== 规则 2:",
            "=== 提取规则 1:",
            "=== 提取规则 2:"
        ]

        is_multi_rule = any(pattern in content for pattern in multi_rule_patterns)

        if is_multi_rule:
            logger.info("检测到多规则分段内容格式，使用多规则提示词")
            return self._get_multi_rule_prompt()
        else:
            logger.info("检测到单规则HTML内容格式，使用单规则提示词")
            return self._get_single_rule_prompt()

    def _build_structure_analysis_prompt(self, task: Task, content: str) -> str:
        """构建智能内容分析提示词"""
        content_summary = (content[:12000] + '...') if len(content) > 12000 else content

        return """分析内容并生成数据提取规则：

**任务信息：**
- 名称：{task_name}
- 监控需求：{task_description}

**内容：**
{content}

**分析步骤：**

1. **首先判断内容格式**：
   - 是否包含 `=== 规则 X: ... ===` 或 `=== 提取规则 X: ... ===` 分段标记？
   - 如果有，这是多规则分段内容
   - 如果没有，这是单规则HTML内容

2. **根据格式采用相应策略**：

   **多规则分段内容处理：**
   - 分析每个分段的内容
   - 从分段1（通常是标题）提取版本号、日期等
   - 从分段2+（通常是内容表格）提取详细信息
   - 使用文本解析和正则表达式
   - 不需要CSS/XPath选择器
   - **重要**：直接在Python代码中处理，不生成FIELDS和RULES部分

   **单规则HTML内容处理：**
   - 分析HTML DOM结构
   - 生成CSS选择器或XPath表达式
   - 处理嵌套元素和属性提取

3. **提取所需字段**：
   根据监控需求提取相应字段，确保每个字段独立处理

4. **生成Python代码（重要要求）**：
   - 必须使用`extracted_data.get('字段名', '默认值')`
   - 包含异常处理
   - 生成飞书Markdown格式
   - **禁止使用多行字符串**：不要使用 f'''...''' 或 '''...'''
   - **使用字符串拼接**：用 + 连接多个字符串或使用 f-string 单行格式
   - **确保代码完整**：所有字符串必须有正确的开始和结束引号
   - **语法正确**：生成的代码必须能通过Python编译检查

**请按照输出格式完成分析。""".format(
            task_name=task.name,
            task_description=task.ai_description or "监控网页内容变化",
            content=content_summary
        )

    def _parse_analysis_result(self, response: str) -> NotificationAnalysis:
        """解析AI分析结果（新的分段文本格式）"""
        try:
            # 预处理响应内容
            if not response or not response.strip():
                raise ValueError("响应内容为空")

            # 记录响应内容的基本信息
            logger.info(f"开始解析AI响应，长度: {len(response)} 字符")

            # 检查响应是否包含预期的分隔符
            if "---" not in response:
                logger.warning("响应中未找到分段分隔符，可能是格式错误")
                # 尝试从响应中提取有用信息
                raise ValueError("响应格式错误：未找到分段分隔符")

            # 解析分段文本格式
            sections = self._parse_sectioned_response(response)

            if not sections:
                raise ValueError("未能解析出任何有效分段")

            logger.info(f"成功解析出 {len(sections)} 个分段: {list(sections.keys())}")

            # 验证必需部分
            required_sections = ["title", "code", "summary"]
            missing_sections = []
            for section in required_sections:
                if section not in sections:
                    missing_sections.append(section)

            if missing_sections:
                logger.error(f"响应中缺少必需部分: {missing_sections}")
                logger.error(f"实际包含的分段: {list(sections.keys())}")
                raise ValueError(f"响应中缺少必需部分: {', '.join(missing_sections)}")

            # 记录AI的分析过程（用于调试）
            if "analysis" in sections:
                logger.info(f"AI分析过程: {sections['analysis'][:500]}...")

            # 解析字段定义
            required_fields = {}
            if "fields" in sections:
                try:
                    for line in sections["fields"].strip().split('\n'):
                        if '=' in line and line.strip():
                            key, desc = line.split('=', 1)
                            required_fields[key.strip()] = desc.strip()
                    logger.info(f"成功解析 {len(required_fields)} 个字段定义")
                except Exception as e:
                    logger.warning(f"解析字段定义时出错: {e}")

            # 解析提取规则
            extraction_rules = {}
            if "rules" in sections:
                try:
                    for line in sections["rules"].strip().split('\n'):
                        if '=' in line and line.strip():
                            key, rule = line.split('=', 1)
                            extraction_rules[key.strip()] = rule.strip()
                    logger.info(f"成功解析 {len(extraction_rules)} 个提取规则")
                except Exception as e:
                    logger.warning(f"解析提取规则时出错: {e}")

            # 验证提取规则的独立性
            self._validate_extraction_rules(extraction_rules)

            # 验证关键内容不为空
            if not sections["title"].strip():
                raise ValueError("标题不能为空")
            if not sections["code"].strip():
                raise ValueError("Python代码不能为空")

            # 清理和验证Python代码
            logger.info(f"原始代码长度: {len(sections['code'])} 字符")
            logger.info(f"原始代码前200字符: {sections['code'][:200]}")

            cleaned_code = self._clean_python_code(sections["code"])
            logger.info(f"清理后代码长度: {len(cleaned_code)} 字符")
            logger.info(f"清理后代码前200字符: {cleaned_code[:200]}")

            self._validate_python_code(cleaned_code)

            result = NotificationAnalysis(
                title=sections["title"].strip(),
                summary=sections["summary"].strip(),
                required_fields=required_fields if required_fields else None,
                extraction_rules=extraction_rules if extraction_rules else None,
                formatter_code=cleaned_code
            )

            logger.info("AI分析结果解析成功")
            return result

        except Exception as e:
            logger.error(f"分析结果解析失败: {e}")
            # 记录响应内容的前1000字符用于调试
            response_preview = response[:1000] if response else "None"
            logger.error(f"响应内容预览: {response_preview}")
            raise ValueError(f"分析结果解析失败: {str(e)}")

    def _parse_sectioned_response(self, response: str) -> dict:
        """解析分段响应文本"""
        sections = {}
        current_section = None
        current_content = []

        lines = response.split('\n')
        logger.debug(f"开始解析响应，共 {len(lines)} 行")

        for i, line in enumerate(lines):
            original_line = line
            line = line.strip()

            # 检查是否是分隔符
            if line.startswith('---') and line.endswith('---') and len(line) > 6:
                # 保存前一个部分
                if current_section:
                    content = '\n'.join(current_content).strip()
                    sections[current_section] = content
                    logger.debug(f"保存分段 '{current_section}': {len(content)} 字符")

                # 开始新部分
                section_name = line[3:-3].strip().lower()
                if section_name:  # 确保分段名不为空
                    current_section = section_name
                    current_content = []
                    logger.debug(f"开始新分段: '{section_name}' (第 {i+1} 行)")
                else:
                    logger.warning(f"第 {i+1} 行发现空分段名: {original_line}")
            elif current_section:
                # 添加到当前部分（保留原始行，包括空行）
                current_content.append(original_line.rstrip())

        # 保存最后一个部分
        if current_section:
            content = '\n'.join(current_content).strip()
            sections[current_section] = content
            logger.debug(f"保存最后分段 '{current_section}': {len(content)} 字符")

        logger.info(f"分段解析完成，共解析出 {len(sections)} 个分段")
        return sections

    def _validate_extraction_rules(self, extraction_rules: dict):
        """验证提取规则的独立性"""
        if not extraction_rules:
            return

        # 检查是否有重复的选择器
        selectors = []
        css_count = 0
        xpath_count = 0
        
        for field_name, rule in extraction_rules.items():
            # 提取选择器部分
            if rule.startswith('css:'):
                selector_part = rule[4:].strip()
                css_count += 1
            elif rule.startswith('xpath:'):
                selector_part = rule[6:].strip()
                xpath_count += 1
            elif ":" in rule:
                selector_part = rule.split(":", 1)[1].strip()
            else:
                selector_part = rule.strip()

            if selector_part in selectors:
                logger.warning(f"检测到重复的选择器: {selector_part}")
                logger.warning(f"字段 {field_name} 使用了与其他字段相同的选择器")
            else:
                selectors.append(selector_part)

        logger.info(f"提取规则验证完成，共 {len(extraction_rules)} 个字段，{len(set(selectors))} 个独立选择器")
        logger.info(f"选择器类型分布: CSS选择器 {css_count} 个，XPath表达式 {xpath_count} 个")

    def _clean_python_code(self, code: str) -> str:
        """清理AI生成的Python代码，移除Markdown标记等"""
        if not code:
            return ""

        logger.debug(f"开始清理代码，原始长度: {len(code)}")

        # 移除可能的Markdown代码块标记和其他格式标记
        lines = code.split('\n')
        cleaned_lines = []
        in_code_block = False

        for i, line in enumerate(lines):
            original_line = line
            stripped = line.strip()

            # 检测和跳过各种Markdown标记
            if stripped in ['```python', '```py', '```', '`python', '`py', '`', 'python', 'py']:
                in_code_block = not in_code_block
                logger.debug(f"第{i+1}行: 跳过Markdown标记: {stripped}")
                continue

            # 跳过空的注释行和文档字符串标记
            if stripped in ['#', '"""', "'''", '""', "''"]:
                logger.debug(f"第{i+1}行: 跳过空注释: {stripped}")
                continue

            # 跳过明显的说明文字（不是Python代码）
            if stripped.startswith('**') and stripped.endswith('**'):
                logger.debug(f"第{i+1}行: 跳过说明文字: {stripped}")
                continue

            # 跳过以特殊字符开头的非代码行
            if stripped.startswith(('---', '===', '###', '##', '#', '*', '-', '+')):
                if not stripped.startswith('#') or not any(c.isalnum() for c in stripped):
                    logger.debug(f"第{i+1}行: 跳过格式标记: {stripped}")
                    continue

            # 跳过 import 语句（因为所有模块都已预先导入）
            if stripped.startswith(('import ', 'from ')):
                logger.debug(f"第{i+1}行: 跳过import语句: {stripped}")
                continue

            # 保留有效的代码行
            cleaned_lines.append(original_line)
            logger.debug(f"第{i+1}行: 保留代码行: {stripped[:50]}...")

        # 重新组合代码（简化处理）
        cleaned_code = '\n'.join(cleaned_lines)

        # 只做基本的标点符号清理
        chinese_punctuation = {
            '，': ',',  # 中文逗号 -> 英文逗号  
            '。': '.',  # 中文句号 -> 英文句号
            '：': ':',  # 中文冒号 -> 英文冒号
            '（': '(',  # 中文左括号 -> 英文左括号
            '）': ')',  # 中文右括号 -> 英文右括号
        }

        for chinese, english in chinese_punctuation.items():
            cleaned_code = cleaned_code.replace(chinese, english)

        # 移除开头和结尾的多余空行
        cleaned_code = cleaned_code.strip()

        logger.info(f"代码清理完成，原长度: {len(code)}, 清理后长度: {len(cleaned_code)}")
        logger.debug(f"清理后的代码前500字符:\n{cleaned_code[:500]}")

        return cleaned_code

    def _fix_multiline_strings(self, code: str) -> str:
        """修复多行字符串问题，将其转换为字符串拼接"""
        if not code:
            return code

        # 检查是否包含多行字符串
        if 'f"""' not in code and '"""' not in code:
            return code

        logger.debug("检测到多行字符串，开始修复")

        # 简单的修复策略：将多行字符串转换为单行字符串拼接
        lines = code.split('\n')
        fixed_lines = []
        in_multiline_string = False
        multiline_content = []
        indent = ""

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 检测多行字符串开始
            if ('f"""' in stripped or '"""' in stripped) and not in_multiline_string:
                in_multiline_string = True
                indent = line[:len(line) - len(line.lstrip())]  # 获取缩进

                # 提取变量名和开始内容
                if '=' in stripped:
                    var_part = stripped.split('=')[0].strip()
                    content_start = stripped.split('"""')[1] if '"""' in stripped else ""
                    if content_start:
                        multiline_content.append(content_start)
                    fixed_lines.append(f"{indent}{var_part} = (")
                continue

            # 检测多行字符串结束
            if in_multiline_string and '"""' in stripped:
                in_multiline_string = False
                content_end = stripped.split('"""')[0] if stripped.split('"""')[0] else ""
                if content_end:
                    multiline_content.append(content_end)

                # 生成字符串拼接代码
                if multiline_content:
                    for j, content in enumerate(multiline_content):
                        content = content.replace('"', '\\"')  # 转义引号
                        if j == 0:
                            fixed_lines.append(f'{indent}    f"{content}\\n" +')
                        elif j == len(multiline_content) - 1:
                            fixed_lines.append(f'{indent}    f"{content}"')
                        else:
                            fixed_lines.append(f'{indent}    f"{content}\\n" +')
                    fixed_lines.append(f"{indent})")
                else:
                    fixed_lines.append(f'{indent}    ""')
                    fixed_lines.append(f"{indent})")

                multiline_content = []
                continue

            # 收集多行字符串内容
            if in_multiline_string:
                multiline_content.append(line.strip())
                continue

            # 普通行
            fixed_lines.append(line)

        result = '\n'.join(fixed_lines)
        logger.debug("多行字符串修复完成")
        return result

    def _fix_docstring_format(self, code: str) -> str:
        """修复文档字符串格式"""
        if not code:
            return code

        lines = code.split('\n')
        fixed_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # 检测函数定义行
            if line.strip().startswith('def ') and line.strip().endswith(':'):
                fixed_lines.append(line)
                i += 1

                # 检查下一行是否是没有三引号的文档字符串
                if i < len(lines):
                    next_line = lines[i].strip()
                    # 如果下一行不是空行，也不是以三引号开始，也不是代码语句，可能是文档字符串
                    if (next_line and
                        not next_line.startswith('"""') and
                        not next_line.startswith("'''") and
                        not next_line.startswith('try:') and
                        not next_line.startswith('return ') and
                        not next_line.startswith('if ') and
                        not next_line.startswith('for ') and
                        not next_line.startswith('while ')):
                        # 检查是否看起来像文档字符串（包含中文或常见文档字符串关键词）
                        if any(keyword in next_line for keyword in ['格式化', '通知', 'Args:', 'Returns:', 'Parameters:']):
                            logger.debug(f"检测到可能的文档字符串格式问题，第{i+1}行: {next_line}")

                            # 添加开始的三引号
                            fixed_lines.append('    """')

                            # 处理文档字符串内容
                            while i < len(lines):
                                doc_line = lines[i]
                                stripped_doc = doc_line.strip()

                                # 如果遇到空行或者看起来像代码的行，结束文档字符串
                                if (not stripped_doc or
                                    stripped_doc.startswith('try:') or
                                    stripped_doc.startswith('return ') or
                                    stripped_doc.startswith('if ') or
                                    stripped_doc.startswith('for ') or
                                    stripped_doc.startswith('while ') or
                                    stripped_doc.startswith('import ') or
                                    stripped_doc.startswith('from ') or
                                    '=' in stripped_doc and not any(kw in stripped_doc for kw in ['Args:', 'Returns:', 'Parameters:'])):
                                    break

                                # 添加文档字符串行（保持适当缩进）
                                if doc_line.strip():
                                    fixed_lines.append('    ' + doc_line.strip())
                                else:
                                    fixed_lines.append('')
                                i += 1

                            # 添加结束的三引号
                            fixed_lines.append('    """')
                            continue

            fixed_lines.append(line)
            i += 1

        result = '\n'.join(fixed_lines)
        logger.debug(f"文档字符串格式修复完成")
        return result

    def _validate_python_code(self, code: str):
        """验证Python代码的安全性和格式正确性"""
        if not code or not code.strip():
            raise ValueError("代码不能为空")

        # 检查代码长度
        if len(code) < 50:
            raise ValueError("代码过短，可能不完整")

        if len(code) > 10000:
            raise ValueError("代码过长，可能存在安全风险")

        # 严格检查函数名
        if 'def format_notification(' not in code:
            # 检查是否使用了错误的函数名
            wrong_function_patterns = [
                'def extract_',
                'def parse_',
                'def get_',
                'def fetch_',
                'def process_',
                'def generate_'
            ]
            
            found_wrong_function = None
            for pattern in wrong_function_patterns:
                if pattern in code:
                    # 提取具体的错误函数名
                    import re
                    match = re.search(r'def (\w+)\(', code)
                    if match:
                        found_wrong_function = match.group(1)
                    break
            
            if found_wrong_function:
                raise ValueError(f"错误的函数名: {found_wrong_function}。必须使用函数名: format_notification")
            else:
                raise ValueError("代码中必须包含函数定义: def format_notification(extracted_data: dict, task_info: dict) -> str")

        # 检查函数签名是否正确
        expected_signature = "def format_notification(extracted_data: dict, task_info: dict) -> str:"
        if expected_signature not in code.replace(' ', '').replace('\n', '').replace('\t', ''):
            logger.warning("函数签名格式可能不标准，但包含必要的函数名")

        # 检查硬编码问题
        self._detect_hardcoded_values(code)

        # 检查危险操作
        dangerous_patterns = [
            'import os', 'import sys', 'import subprocess', 'import socket',
            'open(', 'file(', 'exec(', 'eval(', '__import__',
            'compile(', 'globals()', 'locals()', 'vars(',
            'setattr(', 'delattr(', 'hasattr(',
            'input(', 'raw_input(',
        ]

        dangerous_found = []
        for pattern in dangerous_patterns:
            if pattern in code:
                dangerous_found.append(pattern)

        if dangerous_found:
            raise ValueError(f"代码包含危险操作: {', '.join(dangerous_found)}")

        # 尝试编译代码检查语法
        try:
            compile(code, '<ai_generated_code>', 'exec')
            logger.info("Python代码安全验证通过")
        except SyntaxError as e:
            raise ValueError(f"代码语法错误: {str(e)}")
        except Exception as e:
            raise ValueError(f"代码验证失败: {str(e)}")

    def _detect_hardcoded_values(self, code: str):
        """检测代码中的硬编码值"""
        try:
            import re

            # 常见的硬编码模式
            hardcoded_patterns = [
                # 版本号模式
                r'=\s*["\']V?\d+\.\d+\.\d+["\']',  # "V9.8.0", "1.2.3"
                r'=\s*["\']V?\d+\.\d+["\']',       # "V9.8", "1.2"
                r'=\s*["\']V?\d+["\']',            # "V9", "1"
                # 纯数字版本
                r'=\s*["\']?\d{4}["\']?',          # "1155", 1155
                r'=\s*["\']?\d{3,}["\']?',         # "123", 123 (3位以上数字)
                # URL模式
                r'=\s*["\']https?://[^"\']+["\']', # "https://example.com"
                # 特定文本模式
                r'=\s*["\']OPPO[^"\']*["\']',      # "OPPO小游戏调试器"
                r'=\s*["\']华为[^"\']*["\']',      # "华为快应用"
            ]

            warnings = []
            for pattern in hardcoded_patterns:
                matches = re.findall(pattern, code, re.IGNORECASE)
                if matches:
                    for match in matches:
                        # 排除一些合理的赋值
                        if any(safe_value in match.lower() for safe_value in ['未知', 'unknown', 'error', '失败', 'none', 'null', '#']):
                            continue
                        warnings.append(f"检测到可能的硬编码值: {match.strip()}")

            if warnings:
                logger.warning("🚨 硬编码检测警告:")
                for warning in warnings:
                    logger.warning(f"  - {warning}")
                logger.warning("请确保所有数据都通过extracted_data.get()动态获取")

                # 如果检测到明显的硬编码，抛出错误
                critical_patterns = [
                    r'=\s*["\']V?\d+\.\d+\.\d+["\']',  # 版本号
                    r'=\s*["\']?\d{4}["\']?',          # 4位数字
                    r'=\s*["\']https?://[^"\']+["\']', # URL
                ]

                for pattern in critical_patterns:
                    if re.search(pattern, code, re.IGNORECASE):
                        raise ValueError(f"检测到严重的硬编码问题，代码中包含固定值。请使用extracted_data.get()获取动态数据。")

        except Exception as e:
            logger.warning(f"硬编码检测失败: {e}")

# 全局AI通知分析器实例
_ai_notifier: Optional[AINotifier] = None

def get_ai_notifier() -> Optional[AINotifier]:
    """获取AI通知分析器实例"""
    global _ai_notifier

    # 从配置文件读取API设置
    from app.core.config import settings

    if not settings.api_settings:
        logger.warning("未配置API设置，AI通知分析功能不可用。请在config.yaml中配置api_settings部分")
        return None

    api_settings = settings.api_settings

    # 根据配置选择 AI 服务提供商
    if api_settings.ai_provider == "openai":
        if not api_settings.openai_api_key:
            logger.warning("未配置OpenAI API密钥，AI通知分析功能不可用。请在config.yaml中配置openai_api_key")
            return None

        if _ai_notifier is None:
            try:
                _ai_notifier = AINotifier(
                    api_key=api_settings.openai_api_key,
                    base_url=api_settings.openai_base_url,
                    model=api_settings.openai_model
                )
                logger.info(f"使用OpenAI服务，模型: {api_settings.openai_model}")
            except Exception as e:
                logger.error(f"OpenAI通知分析器初始化失败: {e}")
                return None
    else:
        # 默认使用 DeepSeek
        if not api_settings.deepseek_api_key:
            logger.warning("未配置DeepSeek API密钥，AI通知分析功能不可用。请在config.yaml中配置deepseek_api_key")
            return None

        if _ai_notifier is None:
            try:
                _ai_notifier = AINotifier(
                    api_key=api_settings.deepseek_api_key,
                    base_url=api_settings.deepseek_base_url,
                    model=api_settings.deepseek_model
                )
                logger.info(f"使用DeepSeek服务，模型: {api_settings.deepseek_model}")
            except Exception as e:
                logger.error(f"DeepSeek通知分析器初始化失败: {e}")
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


