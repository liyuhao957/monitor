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

            prompt = self._build_structure_analysis_prompt(task, content)

            # 调用API并记录原始响应
            # 使用标准 OpenAI API 参数
            api_params = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
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
        """获取平衡版HTML分析提示词"""
        return """你是专业的HTML数据提取专家，分析HTML结构并生成精确的提取规则和格式化代码。

**核心任务：**
1. **HTML结构分析**：理解DOM层次关系，识别数据组织模式（table、list、div嵌套等）
2. **精确元素定位**：为每个字段生成独立的CSS选择器或XPath表达式
3. **Python代码生成**：使用BeautifulSoup提取数据并格式化为飞书Markdown通知
4. **代码安全保证**：只使用标准库和BeautifulSoup4，禁止文件操作和网络请求

**HTML提取策略：**
- **优先CSS选择器**：语法简洁，适合结构化数据提取
  - 位置选择：`tr:first-child td:nth-child(2)`, `li:last-child`
  - 属性选择：`a[href*='.apk']`, `td[class='version']`
  - 文本提取：`div.content::text`, `span::text`
  - 属性提取：`a::attr(href)`, `img::attr(src)`
- **XPath补充**：处理复杂位置关系和条件查询
  - 文本内容：`//td[contains(text(),'版本')]/following-sibling::td[1]/text()`
  - 属性值：`//a[contains(@href,'.apk')]/@href`

**重要：提取规则必须明确指定意图**
- **默认提取文本**：`css:a` 或 `css:a::text` → 提取元素的文本内容
- **提取链接地址**：`css:a::attr(href)` → 提取href属性值  
- **提取图片地址**：`css:img::attr(src)` → 提取src属性值
- **其他属性提取**：`css:element::attr(属性名)` → 提取指定属性

**特别注意<a>标签**：
- 如果需要版本号、名称等文本信息：使用 `css:a` 或 `css:a::text`
- 如果需要下载链接、跳转地址：使用 `css:a::attr(href)`
- 不再有默认的特殊处理，必须明确表达提取意图！

**关键原则：**
- **每个字段独立选择器**：绝不重复使用相同的选择器
- **精确定位目标**：避免匹配多个元素，使用nth-child()等精确定位
- **通用性设计**：选择器应适应页面结构的合理变化
- **错误处理完整**：包含数据缺失、解析失败等情况的处理

**严禁硬编码（关键）：**
❌ 错误示例：`version = "V15.1.1.301"`, `url = "https://固定链接"`  
✅ 正确方式：`version = extracted_data.get('version', '未知')`
✅ 动态获取：`download_url = extracted_data.get('download_url', '')`

**代码结构要求（严格）：**
- **函数名必须为：format_notification**
- **函数签名必须为：def format_notification(extracted_data: dict, task_info: dict) -> str:**
- 不使用import语句（模块已预导入）
- 不使用Markdown代码块标记
- 必须使用英文标点符号
- 使用try-except处理异常
- 返回飞书Markdown格式内容
- **关键**：只生成一个函数定义，绝不重复函数定义行

---ANALYSIS---
简要分析HTML结构和数据位置

---TITLE---
通知标题

---CODE---
完整的Python函数代码（直接输出，无Markdown标记）

---SUMMARY---
简要说明

---FIELDS---
字段名=描述

---RULES---
字段名=css:选择器 或 字段名=xpath:表达式"""

    def _build_structure_analysis_prompt(self, task: Task, content: str) -> str:
        """构建平衡版HTML分析提示词"""
        content_summary = (content[:12000] + '...') if len(content) > 12000 else content

        return """分析HTML内容并生成数据提取规则：

**任务信息：**
- 名称：{task_name}
- 需求：{task_description}

**HTML内容：**
{content}

**分析要求：**

**1. HTML结构分析**
- 识别数据组织方式（table、ul/li、div嵌套等）
- 理解每个目标数据在DOM中的位置关系
- 找出数据字段的HTML容器和层次结构
- 分析是否存在多个相似元素需要精确定位

**2. 字段定位策略**
- 为每个需要的字段确定具体的HTML元素
- 分析字段是文本内容、链接href、还是其他属性
- 设计独立的选择器，避免重复使用
- 考虑页面结构变化的稳定性

**3. 选择器生成原则**
- **优先CSS选择器**：简洁直观，例如：
  - `table tr:first-child td:nth-child(1)` - 表格第一行第一列
  - `td a[href*='.apk']` - 包含.apk链接的单元格
  - `li:last-child span.version` - 最后一个列表项的版本
- **XPath作为补充**：复杂定位，例如：
  - `//td[contains(text(),'版本')]/following-sibling::td[1]` - 包含"版本"文本后的相邻单元格
- **属性提取语法**：
  - CSS: `a[href]::attr(href)`, `span::text`
  - XPath: `//a/@href`, `//span/text()`

**特别注意<a>标签的处理**：
- 默认行为已改变：`css:a` 现在提取文本内容，而不是href
- 提取版本号等文本：`css:li:first-child a` 或 `css:li:first-child a::text`
- 提取下载链接：必须明确使用 `css:li:first-child a::attr(href)`
- 千万不要混淆！根据字段含义选择正确的提取方式

**4. 代码生成要求**
- 使用BeautifulSoup解析HTML
- 为每个字段编写独立的提取逻辑
- **关键**：使用`extracted_data.get('字段名', '默认值')`获取动态数据
- 包含完整的错误处理（数据为空、解析失败等）
- 生成飞书Markdown格式的通知内容
- 不使用import语句，不使用Markdown代码块标记
- **重要**：只写一个函数定义，不要重复函数名或函数定义行

**硬编码检测：**
确保代码中没有写死任何具体数值、链接或文本，所有数据都从extracted_data动态获取。

**验证步骤：**
- 确认每个选择器在HTML中能准确定位到目标元素
- 验证提取的内容格式正确，无HTML标签残留
- 检查选择器的唯一性，避免匹配多个元素

请按照标准输出格式（ANALYSIS、TITLE、CODE、SUMMARY、FIELDS、RULES）完成分析。""".format(
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


