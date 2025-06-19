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
        """获取优化版HTML分析提示词 - 通用型网页监控专用"""
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

**B. 智能选择器生成策略（含具体示例）**

1. **HTML嵌套结构分析示例**：
   ```html
   <!-- 典型的版本更新页面结构 -->
   <div id="main-container">
     <div class="version-section">           <!-- 版本区块容器 -->
       <h2>1121版本更新说明（2025-6-6）</h2>    <!-- 版本标题 -->
     </div>
     <div class="content-section">           <!-- 内容区块容器 -->
       <h3>指南</h3>                        <!-- 分类标题 -->
       <div class="table-container">
         <table>
           <tbody>
             <tr>
               <td>变更点</td>
               <td>具体说明和<a href="...">文档链接</a></td>  <!-- 目标内容 -->
             </tr>
           </tbody>
         </table>
       </div>
     </div>
   </div>
   ```

2. **渐进式选择器构建模板**：
   ```css
   /* 步骤1：确定基准容器 */
   div[id="main-container"]
   
   /* 步骤2：定位版本区块（版本标题） */
   div[id="main-container"] h2:first-of-type
   
   /* 步骤3：定位内容区块（跳过版本标题区块） */
   div[id="main-container"] div.content-section
   /* 或使用相邻选择器 */
   div[id="main-container"] h2:first-of-type ~ div
   
   /* 步骤4：精确定位目标内容 */
   div[id="main-container"] h2:first-of-type ~ div table tbody tr td:nth-child(2)
   ```

3. **相邻选择器精确使用指导**：
   - **直接相邻（+）**：`h2 + div` - h2后紧接着的第一个div
   - **通用相邻（~）**：`h2 ~ div` - h2后面所有的兄弟div
   - **子元素定位**：`div > table` - div的直接子元素table
   - **后代元素定位**：`div table` - div内部任意层级的table

4. **选择器唯一性和精确性保证**：
   - 每个字段使用完全不同的路径组合
   - 通过:nth-child()、:first-of-type等精确定位
   - 结合属性选择器增强稳定性：`[id*="body"]`、`[class*="table"]`
   - 避免歧义：优先使用结构关系而非纯位置计数

**C. 复杂页面处理技巧**
- **时序数据处理**：对于包含多个版本/时间的页面，准确定位最新数据
- **嵌套结构处理**：使用空格组合符处理多层嵌套：`container section table tbody tr td`
- **相邻元素处理**：使用相邻组合符：`h2:first-of-type + div`, `td + td`
- **内容特征定位**：结合属性选择器：`a[href*=".zip"]`, `td[class*="version"]`

**D. 逐层结构分解分析（关键）**
1. **第一层：页面主容器识别**：
   - 识别包含所有数据的最外层容器（如body、main、content等）
   - 分析数据的整体分布模式和排列顺序

2. **第二层：数据区块边界**：
   - 定位各个版本/分类/项目的区块边界
   - 理解区块之间的分隔方式（标题、容器、间距等）

3. **第三层：内部结构解析**：
   - 分析每个区块内部的组织方式（表格、列表、段落等）
   - 理解数据字段在结构中的具体位置关系

4. **第四层：目标元素精确定位**：
   - 确定每个字段的精确HTML元素位置
   - 分析元素的嵌套层次和相邻关系

**E. 选择器构建步骤化方法**
1. **基准锚点确立**：
   - 选择最稳定且唯一的元素作为起始定位点
   - 优先选择具有明确标识的元素（ID、特殊class、结构特征）

2. **路径精确构建**：
   - 从基准点开始，逐级构建到目标元素的精确路径
   - 每一级都要确保路径的唯一性和稳定性

3. **选择器验证测试**：
   - 模拟在提供的HTML中执行选择器
   - 确认能且仅能匹配到预期的目标元素
   - 验证选择器的路径逻辑正确性

**F. 复杂嵌套结构专项处理**
- **标题+容器+表格模式**：h2/h3标题 → div容器 → table数据的处理策略
- **多级tbody结构**：准确导航tbody → tr → td的层级关系
- **表格列精确定位**：使用nth-child()准确定位特定列（如第二列说明内容）
- **相邻元素关系**：理解和利用相邻选择器（+, ~）处理复杂布局

**G. 强制性模拟验证机制（必须执行）**

**验证步骤模板（每个选择器都必须执行）：**

1. **选择器路径分解验证**：
   ```
   选择器：div[id="body123"] h2:first-of-type ~ div table tbody tr td:nth-child(2)
   
   分解验证：
   步骤1：div[id="body123"] ✓ 匹配主容器
   步骤2：h2:first-of-type ✓ 匹配第一个版本标题
   步骤3：~ div ✓ 匹配标题后的兄弟div容器
   步骤4：table tbody tr ✓ 匹配表格行
   步骤5：td:nth-child(2) ✓ 匹配第二列（说明列）
   
   最终验证：能精确匹配到版本区块内的所有说明内容
   ```

2. **HTML模拟执行测试**：
   - 基于提供的HTML片段，逐步执行选择器
   - 确认每一步都能找到预期元素
   - 验证最终匹配的元素数量和内容类型
   - 检查是否误匹配到其他版本的内容

3. **选择器比较和唯一性验证**：
   ```
   字段A选择器：div[id="body"] h2:first-of-type
   字段B选择器：div[id="body"] h2:first-of-type ~ div table td:nth-child(2)
   字段C选择器：div[id="body"] h2:first-of-type ~ div table a
   
   验证结果：✓ 三个选择器完全不同，无重复或交叉
   ```

4. **内容提取验证**：
   - 确认提取的是文本内容还是属性值
   - 验证内容格式符合字段要求
   - 检查是否包含预期的信息（版本号、更新说明、链接等）

**验证失败处理**：
- 如果任何验证步骤失败，必须重新分析HTML结构
- 调整选择器路径直到通过所有验证
- 如果无法生成有效选择器，明确报告分析失败

**H. 属性提取语法明确**
- **文本内容**：`css:selector` 或 `css:selector::text` → 提取元素文本
- **链接地址**：`css:a::attr(href)` → 提取href属性值
- **图片地址**：`css:img::attr(src)` → 提取src属性值
- **其他属性**：`css:element::attr(属性名)` → 提取指定属性
- **特别注意**：必须明确指定提取意图，避免歧义

**I. 错误处理与健壮性设计**
- 每个字段提取都要有完整的异常处理
- 提供合理的默认值应对数据缺失
- 确保选择器的高精确性，避免结构变化导致的失效
- 确保部分字段失败不影响整体通知生成

**J. 代码生成要求（严格遵守）**
- **函数签名**：`def format_notification(extracted_data: dict, task_info: dict) -> str:`
- **动态数据获取**：使用`extracted_data.get('字段名', '默认值')`，严禁硬编码
- **时间处理**：使用`datetime.now().strftime('%Y-%m-%d %H:%M:%S')`
- **异常处理**：每个数据访问都要有try-except保护
- **输出格式**：生成结构清晰的飞书Markdown通知
- **代码规范**：不使用import语句，不使用Markdown代码块标记，只生成一个函数定义

**K. 通知内容优化**
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

    def _build_structure_analysis_prompt(self, task: Task, content: str) -> str:
        """构建优化版HTML分析提示词"""
        content_summary = (content[:12000] + '...') if len(content) > 12000 else content

        return """深度分析HTML内容并生成高精度数据提取规则：

**任务信息：**
- 名称：{task_name}
- 监控需求：{task_description}

**HTML内容：**
{content}

**深度分析要求：**

**第一步：页面结构识别**
1. **判断页面类型**：
   - 是否为列表型页面（多个相似项目）？
   - 是否为表格型页面（行列数据）？
   - 是否为时序型页面（按时间/版本排序）？
   - 是否为单项型页面（单个数据对象）？

2. **识别数据组织方式**：
   - 数据是否有明显的容器边界？
   - 相关数据是否分组在一起？
   - 是否存在重复的HTML结构模式？
   - 最重要的数据位于页面什么位置？

**第二步：逐层结构分解分析**
1. **第一层：页面主容器识别**：
   - 识别包含所有数据的最外层容器（如div[id="body..."]、main、content等）
   - 分析数据的整体分布模式：是按版本排序？按时间排序？按重要性排序？
   - 确定最新/最重要数据的位置特征（通常在第一个位置）

2. **第二层：数据区块边界精确定位**：
   - 定位各个版本/分类/项目的区块边界（如每个版本的开始和结束）
   - 理解区块的分隔标识：h2版本标题？div容器？特殊class？
   - 分析第一个（最新）区块的完整范围

3. **第三层：内部结构精确解析**：
   - 分析目标区块内部的组织方式：h3分类标题 → div容器 → table数据表格？
   - 理解表格结构：thead表头 → tbody数据体 → tr行 → td列的层次关系
   - 识别数据字段在表格中的精确位置（如第二列是说明内容）

4. **第四层：目标元素终极定位**：
   - 确定每个字段的精确HTML元素路径
   - 分析元素的完整嵌套层次：从区块根节点到目标内容的完整路径
   - 验证路径的唯一性：确保选择器不会匹配到其他版本的数据

**第三步：核心数据字段映射**
1. **字段来源精确分析**：
   - 版本号：从h2标题文本中提取（如"1121版本更新说明"中的"1121"）
   - 更新内容：从第一个版本区块内所有表格的说明列（td:nth-child(2)）中提取
   - 文档链接：从说明列内的<a>标签href属性中提取
   - 发布时间：从版本标题的日期部分提取（如"（2025-6-6）"）

2. **提取目标明确化**：
   - 每个字段的具体提取目标是什么？（文本内容/属性值/链接地址）
   - 字段内容的预期格式是什么？（纯文本/HTML/特定模式）
   - 如何处理字段内容的清理和格式化？

**第四步：基准锚点建立和路径构建**
1. **基准锚点确立**：
   - 寻找最稳定且唯一的起始定位点（如div[id="body0000001079803874"]）
   - 确定第一个版本区块的精确边界（如第一个h2标题元素）
   - 验证基准点的唯一性和稳定性

2. **逐级路径精确构建**：
   - **版本号路径**：从基准点 → 第一个h2标题 → 提取文本内容
   - **更新内容路径**：从第一个h2 → 相邻的div容器 → 所有table → tbody → tr → td:nth-child(2)
   - **链接路径**：从更新内容的td元素 → 内部的a标签 → href属性
   - **时间路径**：从版本号的h2标题 → 提取日期部分

3. **路径唯一性保证**：
   - 确保每个字段使用完全不同的选择器路径
   - 通过结构关系（:first-of-type, :nth-child, + 等）精确区分相似元素
   - 验证路径不会误匹配到其他版本或区块的数据

**第五步：强制性选择器模拟验证（关键步骤）**

**必须执行的验证流程：**

1. **逐步路径分解模拟**：
   ```
   示例验证过程：
   HTML结构：<div id="body123"><h2>版本标题</h2><div><table><tbody><tr><td>变更</td><td>说明内容</td></tr></tbody></table></div></div>
   
   选择器：div[id="body123"] h2:first-of-type ~ div table tbody tr td:nth-child(2)
   
   执行验证：
   ✓ div[id="body123"] → 找到主容器
   ✓ h2:first-of-type → 找到第一个版本标题
   ✓ ~ div → 找到标题后的兄弟div容器
   ✓ table tbody tr → 找到表格行
   ✓ td:nth-child(2) → 找到第二列内容
   
   结果：成功匹配到"说明内容"
   ```

2. **HTML片段实际测试**：
   - 在提供的HTML片段中"执行"每个选择器
   - 明确说明匹配到的具体内容
   - 确认内容的数量和类型符合预期
   - 验证不会误匹配到其他版本的数据

3. **选择器差异性确认**：
   - 列出所有字段的选择器
   - 逐一比较确保完全不同
   - 说明每个选择器的独特路径特征

4. **提取内容预期描述**：
   - 明确说明每个选择器将提取什么内容
   - 确认提取方式（文本/属性）正确
   - 预估提取结果的格式和内容

**第六步：高精度代码生成**
1. **字段提取逻辑精确实现**：
   - 为每个字段生成独立且精确的提取逻辑
   - 使用验证通过的选择器，确保提取的准确性
   - 包含完整的异常处理和合理的默认值
   - 确保所有数据都从extracted_data动态获取，严禁硬编码

2. **内容处理和格式化**：
   - 对提取的版本号进行清理（如从"1121版本更新说明（2025-6-6）"中提取"1121"）
   - 对更新内容进行合理的格式化和换行处理
   - 对链接进行去重和有效性过滤
   - 对时间信息进行标准化处理

3. **通知格式精致设计**：
   - 生成结构清晰、信息丰富的飞书Markdown通知
   - 使用合适的emoji增强视觉效果
   - 重要信息突出显示（版本号、更新内容等）
   - 包含检测时间、相关链接等完整信息

**特别注意事项：**
- **复杂页面策略**：如果页面结构复杂，优先保证核心字段的准确提取
- **降级方案**：如果某些字段难以准确定位，提供简化的提取方案
- **通用性考虑**：生成的方案应该适用于同类型的页面变化

**HTML结构分析重点：**
请仔细观察提供的HTML内容，特别关注：
- 数据的嵌套层次和组织方式
- 重复出现的结构模式
- 具有标识意义的ID、class或属性
- 数据之间的位置关系（相邻、父子、兄弟关系）

**输出要求（必须包含验证过程）：**
1. **ANALYSIS**：
   - 页面结构特征和数据组织方式分析
   - 选择器设计思路和构建过程
   - **关键**：必须包含每个选择器的模拟验证过程
   - 验证结果确认和问题解决方案

2. **TITLE**：简洁的通知标题

3. **CODE**：
   - 完整的Python格式化函数
   - 包含所有字段处理和错误处理
   - 使用验证通过的选择器

4. **SUMMARY**：
   - 分析结果和实施要点摘要
   - 选择器验证结果总结

5. **FIELDS**：每个字段的详细描述和提取目标

6. **RULES**：
   - 每个字段对应的精确选择器规则
   - 每个规则必须通过模拟验证
   - 确保选择器之间完全不重复

**成功标准（必须全部满足）：**
1. **选择器精确性**：生成的选择器在当前HTML中100%有效，能精确定位到目标元素
2. **唯一性保证**：每个字段使用完全不同的选择器，绝无重复或交叉匹配
3. **路径正确性**：选择器路径逻辑正确，从基准点到目标元素的每一步都准确
4. **内容准确性**：提取的内容完全符合字段预期，格式正确无误
5. **代码健壮性**：代码健壮，异常处理完善，能处理各种边界情况
6. **通知质量**：通知内容清晰美观，信息完整，格式规范
7. **模拟验证通过**：所有选择器都通过基于提供HTML的模拟验证测试

**失败即停止**：如果任何一个标准无法满足，应明确报告分析失败，不提供不准确的方案""".format(
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


