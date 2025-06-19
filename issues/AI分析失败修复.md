# AI分析失败修复

## 问题描述
监控任务"OPPO"的小版本号提取错误：
- 期望：提取`V9.8.0` 
- 实际：提取了下载链接URL

## 根本原因分析

### 1. content_parser的特殊处理逻辑
在`backend/app/services/content_parser.py`第142-149行：
```python
# 如果是链接，提取href属性
if element.name == 'a' and element.has_attr('href'):
    result = element['href']
    logger.info(f"字段 {field_name} CSS链接提取成功: {result}")
    return result
```

当CSS选择器匹配到`<a>`标签时，系统会**自动提取href属性**而不是文本内容。

### 2. AI生成的规则不够明确
AI生成的规则可能是：
- `minor_version=css:li:first-child a`

由于没有明确指定提取文本还是属性，触发了默认的href提取行为。

### 3. 影响范围
- 所有需要从`<a>`标签提取文本的字段都会受影响
- 导致版本号、产品名称等文本内容被错误提取为URL

## 修复方案

### 方案1：改进AI提示词（推荐）
让AI生成更明确的提取规则：
- 提取文本：`css:li:first-child a::text`
- 提取链接：`css:li:first-child a::attr(href)`

优点：
- 不改变现有系统行为
- 向后兼容
- 更清晰的语义

### 方案2：移除默认href提取
修改content_parser，对`<a>`标签也默认提取文本。

缺点：
- 可能影响现有任务
- 需要检查所有依赖此行为的配置

## 实施步骤

### 1. 更新AI提示词
在`ai_notifier.py`的系统提示词中强调：
- 必须明确指定提取类型
- 提供清晰的示例
- 说明`<a>`标签的特殊性

### 2. 验证修复效果
- 重新分析OPPO任务
- 确认生成正确的提取规则
- 测试其他任务兼容性

### 3. 长期改进
- 增加规则验证逻辑
- 提供更好的调试信息
- 考虑支持正则表达式提取部分文本

## 问题描述
用户反馈：`❌ AI分析失败: AI代码执行预览失败: 代码中未找到 format_notification 函数`

## 问题分析

### 错误根源
1. **配置文件中的AI代码正确**：包含 `format_notification` 函数
2. **AI预览时重新生成错误代码**：生成了 `extract_oppo_debugger_info` 函数而不是 `format_notification`
3. **代码执行器检查失败**：在 `code_executor.py` 第125行检查函数名时报错

### 错误流程
```
用户触发AI预览 → AI重新生成代码 → 生成错误函数名 → 代码执行器验证失败 → 报错
```

### 日志证据
```
2025-06-19 11:52:44,022 - 清理后代码前200字符: def extract_oppo_debugger_info(soup):
2025-06-19 11:52:44,031 - 代码执行失败: 代码中未找到 format_notification 函数
```

## 修复方案

### 方案选择
**选择方案：严格验证 + AI提示词修复**
- ✅ 修复AI系统提示词，明确要求 `format_notification` 函数
- ✅ 增强验证逻辑，发现错误函数名直接报错（不自动修正）
- ❌ 不做容错处理，确保AI学会生成正确格式

### 具体修复内容

#### 1. AI系统提示词修复
文件：`backend/app/services/ai_notifier.py` - `_get_system_prompt()`

**增加严格要求：**
```
**代码结构要求（严格）：**
- **函数名必须为：format_notification**
- **函数签名必须为：def format_notification(extracted_data: dict, task_info: dict) -> str:**
```

#### 2. 代码验证逻辑增强
文件：`backend/app/services/ai_notifier.py` - `_validate_python_code()`

**新增检查：**
- 严格检查函数名是否为 `format_notification`
- 识别常见错误函数名模式并报告具体错误
- 检查函数签名格式

**错误报告示例：**
```python
if found_wrong_function:
    raise ValueError(f"错误的函数名: {found_wrong_function}。必须使用函数名: format_notification")
```

## 验证计划

### 测试场景
1. **AI预览功能测试**：确保生成正确的 `format_notification` 函数
2. **错误函数名测试**：验证错误检查机制工作正常
3. **现有任务测试**：确保不影响已配置的任务

### 成功标准
- AI预览不再报"未找到 format_notification 函数"错误
- 生成的代码格式统一规范
- 错误信息清晰准确

## 执行状态
- [x] 修复AI系统提示词
- [x] 增强代码验证逻辑
- [ ] 测试验证
- [ ] 完成确认

## 技术细节

### 函数标准格式
```python
def format_notification(extracted_data: dict, task_info: dict) -> str:
    """
    格式化通知内容
    Args:
        extracted_data: 提取的数据字典
        task_info: 任务信息
    Returns:
        str: 格式化后的飞书Markdown通知内容
    """
    # 格式化逻辑
```

### 系统工作流程
```
数据提取 → extracted_data → format_notification() → 飞书通知格式
``` 