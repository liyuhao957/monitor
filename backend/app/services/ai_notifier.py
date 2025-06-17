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
        """获取系统提示词"""
        return """你是一个专业的通知格式化代码生成器。你需要分析网页内容，理解数据结构，然后生成Python代码来格式化通知内容。

**工作原则：结构化分析 → 精确映射 → 独立提取 → 代码生成**

**核心要求：**
1. 必须按照4个阶段顺序完成工作，不允许跳跃
2. 每个字段必须有独立的提取逻辑，绝不重复使用相同正则表达式
3. 深度理解HTML结构后再设计提取规则
4. 生成通用、安全、健壮的Python代码
5. 使用简洁的Markdown格式，适配飞书机器人显示

**代码安全性约束：**
- 只能使用标准库：re, json, datetime, html, urllib.parse
- 只能使用安全的第三方库：BeautifulSoup4 (from bs4 import BeautifulSoup)
- 禁止使用：os, subprocess, eval, exec, open, file操作
- 禁止网络请求：requests, urllib.request
- 禁止导入任意模块：__import__, importlib

**代码结构标准化：**
你必须生成标准格式的函数，注意：
1. 不要使用Markdown代码块标记（```python 或 ```）
2. 直接输出纯Python代码
3. 函数必须完整且可执行
4. **重要**：必须使用英文标点符号（, . ; : ! ? ( ) " '），不要使用中文标点符号（，。；：！？（）""''）
5. **禁止使用多行字符串**：不要使用 f'''...''' 或 '''...'''，只使用简单的字符串拼接
6. **使用字符串拼接**：用 + 连接多个字符串，或使用 f"单行字符串"

标准格式（注意文档字符串必须用三引号包围）：
def format_notification(extracted_data: dict, task_info: dict) -> str:
    \"\"\"
    格式化通知内容
    Args:
        extracted_data: 提取的数据字典
        task_info: 任务信息 (name, url, current_time等)
    Returns:
        str: 格式化后的通知内容
    \"\"\"
    try:
        # ✅ 正确：使用动态数据
        field1 = extracted_data.get('field1', '未知')
        field2 = extracted_data.get('field2', '未知')

        # ❌ 错误：绝对禁止硬编码具体值
        # field1 = "1155"  # 这样会导致固定值问题！
        # field2 = "V9.8.0"  # 这样会导致固定值问题！
        # download_url = "https://example.com/file.zip"  # 这样会导致固定值问题！

        return f"动态内容: {field1}, {field2}"
    except Exception as e:
        return f"格式化失败: {str(e)}"

**必须严格遵循的4个工作阶段：**

**阶段1：HTML结构深度分析**
- 逐层分析HTML的标签结构和层次关系
- 识别数据的组织模式（列表、表格、嵌套等）
- 理解目标数据在HTML中的确切位置和上下文
- 分析数据的格式特征（版本号、链接、文本等）

**阶段2：字段定位与映射**
- 明确每个用户需求字段对应的HTML元素
- 区分需要提取的是文本内容、属性值还是链接
- 建立字段与HTML位置的精确一对一映射关系
- 确保每个字段有独立的定位逻辑

**阶段3：提取策略设计**
- 为每个字段单独设计正则表达式，绝不重复使用
- 明确每个捕获组的具体作用和选择逻辑
- 确保不同字段从HTML的不同部分或用不同方式提取
- 设计时考虑数据的变化模式和稳定性
- **精确匹配原则**：
  - 当页面有多个相似格式的数据时（如多个版本号），要精确定位目标数据
  - 使用更具体的上下文模式，不要使用过于宽泛的正则表达式
  - 如果需要匹配"最后一个"某种模式，考虑使用负向预查或更精确的定位方式
  - **关键示例**：
    * 错误：`\d+\.\d+\.\d+\.\d+\s+(.+)$` - 会匹配第一个版本号后的所有内容
    * 正确：`</a>\s+\d+\.\d+\.\d+\.\d+\s+(.+)$` - 使用</a>标签定位最后一个版本号
    * 或者：`(\d+\.\d+\.\d+\.\d+)\s+([^<\d]+)$` - 确保只匹配非数字和非标签的内容
  - **多版本号处理规则**：
    * 如果有多个版本号，必须使用唯一的上下文标记区分
    * 使用HTML标签（如</a>）、特定文本、位置关系等作为锚点
    * 验证正则表达式只匹配目标内容，不包含其他版本号或无关数据

**阶段4：代码生成与验证**
- 生成完整的Python格式化函数
- 包含完整的错误处理逻辑
- 验证代码的安全性和健壮性
- 确保输出格式符合飞书Markdown要求

**通用性指导：**
- 识别数据的组织模式（表格、列表、嵌套结构）
- 理解HTML标签的语义和层次关系
- 设计通用的解析策略，而不是硬编码特定内容
- 考虑数据变化的可能性，编写健壮的代码

**输出质量保证：**
生成的通知内容必须：
- 使用Markdown格式，适配飞书显示
- 结构清晰，包含标题、时间、主要内容
- 链接转换为 [文本](URL) 格式
- 使用适当的emoji增强可读性
- 内容简洁，突出重点信息

**错误处理和健壮性：**
代码必须包含完整的错误处理：
- 数据为空的情况
- HTML解析失败的情况
- 正则匹配失败的情况
- 返回有意义的错误信息
- **重要**：即使部分数据缺失，也要生成包含可用数据的通知，不要直接返回"未获取到页面内容"

**输出格式要求：**
你必须按照以下格式输出，展示你的分阶段分析过程和最终结果：

---ANALYSIS---
**阶段1：HTML结构分析**
[详细分析HTML结构，识别数据组织方式]

**阶段2：字段映射**
[明确每个字段对应的HTML位置]

**阶段3：提取策略**
[为每个字段设计独立的提取方案]

**阶段4：代码生成**
[说明生成的Python代码的设计思路]

---TITLE---
[通知标题，可包含emoji]

---CODE---
[完整的Python格式化函数代码，注意：不要包含任何Markdown标记，直接输出纯Python代码]

---SUMMARY---
[代码功能说明和使用方法]

---FIELDS---
[字段名=描述，每行一个]

---RULES---
[字段名=regex:正则表达式，每行一个，确保每个字段使用不同的正则]

**严格要求：**
- 必须展示完整的4阶段分析过程
- 每个字段必须有独立的正则表达式
- Python代码必须安全、通用、健壮
- 分隔符必须准确无误"""

    def _build_structure_analysis_prompt(self, task: Task, content: str) -> str:
        """构建内容结构分析提示词（用于预览）"""
        # 对于预览，我们需要完整的内容来生成准确的提取规则
        # 但为了避免超时，限制在15000字符以内
        content_summary = (content[:15000] + '...') if len(content) > 15000 else content

        return """请严格按照4个阶段分析以下内容，生成数据提取规则和Python格式化代码：

**任务信息：**
- 任务名称：{task_name}
- 监控URL：{task_url}
- 用户监控需求：{task_description}

**页面HTML内容：**
{content}

**你必须严格按照以下4个阶段完成工作：**

**阶段1：HTML结构深度分析**
请仔细分析上述HTML内容：
- 识别HTML的标签结构和层次关系
- 理解数据是如何组织的（列表、表格、嵌套结构等）
- 找出用户需要的每个数据字段在HTML中的确切位置
- 分析数据的格式特征和变化模式

**阶段2：字段定位与映射**
根据用户需求，明确定义需要提取的字段：
- 列出用户需要的所有数据字段
- 为每个字段找到对应的HTML元素位置
- 确定每个字段需要提取的是文本内容、属性值还是链接
- 建立字段与HTML位置的精确映射关系

**阶段3：提取策略设计**
为每个字段设计独立的正则表达式：
- 每个字段必须有完全不同的正则表达式，绝不允许重复使用
- 明确每个正则表达式中捕获组的作用
- 确保正则表达式能准确提取目标内容
- 考虑数据的稳定性和变化模式
- **精确匹配要求**：
  - 分析HTML中是否有多个相似格式的数据（如多个版本号、多个链接等）
  - 使用具体的上下文标记来精确定位目标数据
  - 避免使用过于宽泛的模式，如 `(.+)$` 可能会匹配太多内容
  - 利用HTML标签、特定文本标记等作为定位锚点
  - 示例：要匹配特定位置的版本号，使用其前后的独特标记来定位

**阶段4：Python代码生成**
生成完整的Python格式化函数：
- 分析提取的数据结构和用户格式化需求
- 设计通用的数据处理逻辑（HTML解析、文本清理、链接转换等）
- 生成符合安全约束的Python代码
- 包含完整的错误处理和边界情况处理
- 确保输出格式适配飞书Markdown显示

**代码生成要求：**
1. **安全性**：只使用允许的标准库和BeautifulSoup4
2. **通用性**：代码应该能处理类似结构的页面变化
3. **健壮性**：包含完整的错误处理和数据验证
4. **可读性**：代码结构清晰，注释完整
5. **输出质量**：生成的通知内容格式美观，信息完整
6. **重要**：不要使用任何import语句！所有需要的模块（re, json, datetime, html, BeautifulSoup等）都已经预先导入，可以直接使用
7. **可用函数**：可以使用常用内置函数如 len, str, int, float, bool, list, dict, all, any, max, min, sum, sorted, enumerate, zip, map, filter 等
8. **关键要求**：**绝对不要硬编码任何具体的数据值**！必须使用 extracted_data.get() 方法获取动态数据
9. **动态数据使用**：所有版本号、链接、文本内容都必须从 extracted_data 参数中获取，不要写死任何当前看到的具体值

**验证与测试：**
- **必须**用你生成的每个正则表达式在提供的HTML内容中进行实际测试
- 说明每个正则表达式能提取到的具体内容片段（显示前100个字符）
- 如果提取结果为空或不符合预期，**必须**重新分析HTML结构并修正正则表达式
- 确保提取的内容完整且格式正确
- 验证生成的Python代码能正确处理提取的数据
- **特别注意**：
  - 如果提取到的内容包含了不应该包含的部分（如版本功能字段包含了其他版本号），说明正则表达式不够精确
  - 检查是否有多个匹配项，确保提取的是正确的那一个
  - 对于"最后一个"、"特定位置"的数据，要验证提取的确实是目标数据
- **版本功能字段特别验证**：
  - 如果页面有多个版本号，版本功能应该只包含功能描述文本
  - 不应该包含版本号、下载链接、HTML标签等其他内容
  - 示例：正确的版本功能 - "优化：性能提升50%"
  - 示例：错误的版本功能 - "6102 1123 点击下载 80.0.2.200 优化：性能提升50%"

**最终任务：**
根据以上4个阶段的分析，生成：
1. 每个字段独立且准确的正则提取规则
2. 完整的Python格式化函数代码
3. 适配飞书显示的Markdown格式输出

**关键提醒：**
- 必须展示完整的4阶段分析过程
- 每个字段必须使用完全不同的正则表达式
- Python代码必须安全、通用、健壮
- 代码必须能处理HTML解析、文本清理、链接转换等复杂格式化需求
- 输出内容必须简洁美观，适合飞书机器人显示

请严格按照要求的输出格式完成工作。""".format(
            task_name=task.name,
            task_url=task.url,
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

        # 检查是否有重复的正则表达式
        regex_patterns = []
        for field_name, rule in extraction_rules.items():
            # 提取正则表达式部分
            if ":" in rule:
                regex_part = rule.split(":", 1)[1].strip()
            else:
                regex_part = rule.strip()

            if regex_part in regex_patterns:
                logger.warning(f"检测到重复的正则表达式: {regex_part}")
                logger.warning(f"字段 {field_name} 使用了与其他字段相同的正则表达式")
            else:
                regex_patterns.append(regex_part)

        logger.info(f"提取规则验证完成，共 {len(extraction_rules)} 个字段，{len(set(regex_patterns))} 个独立正则表达式")

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

        # 重新组合代码
        cleaned_code = '\n'.join(cleaned_lines)

        # 修复多行字符串问题 - 将 f""" 替换为字符串拼接
        cleaned_code = self._fix_multiline_strings(cleaned_code)

        # 替换中文标点符号为英文标点符号（这是关键修复）
        chinese_punctuation = {
            '，': ',',  # 中文逗号 -> 英文逗号
            '。': '.',  # 中文句号 -> 英文句号
            '；': ';',  # 中文分号 -> 英文分号
            '：': ':',  # 中文冒号 -> 英文冒号
            '！': '!',  # 中文感叹号 -> 英文感叹号
            '？': '?',  # 中文问号 -> 英文问号
            '（': '(',  # 中文左括号 -> 英文左括号
            '）': ')',  # 中文右括号 -> 英文右括号
            '"': '"',  # 中文左双引号 -> 英文双引号
            '"': '"',  # 中文右双引号 -> 英文双引号
            ''': "'",  # 中文左单引号 -> 英文单引号
            ''': "'",  # 中文右单引号 -> 英文单引号
        }

        for chinese, english in chinese_punctuation.items():
            cleaned_code = cleaned_code.replace(chinese, english)

        # 移除开头和结尾的多余空行
        cleaned_code = cleaned_code.strip()

        # 修复文档字符串格式
        cleaned_code = self._fix_docstring_format(cleaned_code)

        # 确保代码以函数定义开始，并移除重复的函数定义行
        if cleaned_code:
            lines = cleaned_code.split('\n')

            # 查找第一个函数定义
            start_index = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    start_index = i
                    break

            if start_index >= 0:
                # 从第一个函数定义开始
                if start_index > 0:
                    lines = lines[start_index:]
                    logger.debug(f"从第{start_index+1}行开始提取函数定义")

                # 移除重复的函数定义行
                cleaned_lines = []
                seen_function_def = False
                for line in lines:
                    if line.strip().startswith('def format_notification'):
                        if not seen_function_def:
                            cleaned_lines.append(line)
                            seen_function_def = True
                        else:
                            logger.debug(f"跳过重复的函数定义行: {line.strip()}")
                    else:
                        cleaned_lines.append(line)

                cleaned_code = '\n'.join(cleaned_lines)

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
        """验证Python代码的安全性"""
        import ast

        # 危险的模块和函数
        dangerous_imports = [
            'os', 'subprocess', 'sys', 'eval', 'exec', 'open', 'file',
            'requests', 'urllib.request', '__import__', 'importlib',
            'pickle', 'marshal', 'shelve', 'dbm'
        ]

        # 允许的安全模块
        safe_imports = [
            're', 'json', 'datetime', 'html', 'urllib.parse', 'bs4', 'BeautifulSoup'
        ]

        try:
            logger.debug(f"开始验证Python代码，长度: {len(code)} 字符")

            # 解析代码为AST
            tree = ast.parse(code)
            logger.debug("AST解析成功")

            # 检查导入语句
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in dangerous_imports:
                            raise ValueError(f"禁止导入危险模块: {alias.name}")
                        if alias.name not in safe_imports and not alias.name.startswith('bs4'):
                            logger.warning(f"检测到未知模块导入: {alias.name}")

                elif isinstance(node, ast.ImportFrom):
                    if node.module in dangerous_imports:
                        raise ValueError(f"禁止从危险模块导入: {node.module}")
                    if node.module not in safe_imports and not (node.module and node.module.startswith('bs4')):
                        logger.warning(f"检测到未知模块导入: {node.module}")

                # 检查函数调用
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'open', '__import__']:
                            raise ValueError(f"禁止调用危险函数: {node.func.id}")

            # 检查是否包含必需的函数定义
            has_format_function = False
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'format_notification':
                    has_format_function = True
                    break

            if not has_format_function:
                raise ValueError("代码必须包含 format_notification 函数定义")

            # 检测硬编码值
            self._detect_hardcoded_values(code)

            logger.info("Python代码安全验证通过")

        except SyntaxError as e:
            logger.error(f"Python代码语法错误详情:")
            logger.error(f"  错误信息: {str(e)}")
            logger.error(f"  错误位置: 第{e.lineno}行, 第{e.offset}列")
            logger.error(f"  错误文本: {e.text}")

            # 显示出错行的上下文
            lines = code.split('\n')
            if e.lineno and 1 <= e.lineno <= len(lines):
                start = max(0, e.lineno - 3)
                end = min(len(lines), e.lineno + 2)
                logger.error("代码上下文:")
                for i in range(start, end):
                    marker = " >>> " if i == e.lineno - 1 else "     "
                    logger.error(f"{marker}{i+1:3d}: {lines[i]}")

            raise ValueError(f"Python代码语法错误: 第{e.lineno}行 - {str(e)}")
        except Exception as e:
            logger.error(f"Python代码验证异常: {str(e)}")
            raise ValueError(f"Python代码验证失败: {str(e)}")
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


