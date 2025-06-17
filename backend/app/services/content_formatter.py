"""
内容格式化器

基于实践经验设计的通用内容格式化系统，解决Jinja2模板复杂文本处理的局限性。
"""

import re
import logging
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)


class ContentFormatter:
    """通用内容格式化器
    
    解决复杂文本格式化问题，特别是当Jinja2模板的replace功能无法处理复杂情况时。
    """
    
    def __init__(self):
        # 注册格式化规则
        self._formatters: Dict[str, Callable[[str], str]] = {
            "华为快应用引擎更新说明": self._format_huawei_quickapp_content,
        }
    
    def format_content(self, task_name: str, template_context: Dict) -> Dict:
        """格式化模板上下文中的内容
        
        Args:
            task_name: 任务名称
            template_context: 模板上下文字典
            
        Returns:
            格式化后的模板上下文
        """
        if task_name in self._formatters and "content_block" in template_context:
            content_block = template_context.get("content_block", "")
            if content_block:
                try:
                    formatted_content = self._formatters[task_name](content_block)
                    template_context["content_block"] = formatted_content
                    logger.info(f"[{task_name}] 内容格式化完成")
                except Exception as e:
                    logger.error(f"[{task_name}] 内容格式化失败: {e}")
        
        return template_context
    
    def _format_huawei_quickapp_content(self, content: str) -> str:
        """格式化华为快应用引擎更新说明内容

        基于实践经验的格式化规则：
        1. 去掉"指南 变更点 说明"标识
        2. 格式化变更项名称为加粗标题
        3. 添加合适的换行分隔
        4. 格式化链接显示
        5. 修复超链接中的换行问题

        Args:
            content: 原始内容

        Returns:
            格式化后的内容
        """
        # 去掉"指南 变更点 说明"标识
        content = content.replace("指南 变更点 说明", "")

        # 先处理链接显示，添加图标
        content = content.replace("详情请参见", "\n📋 详情请参见：")

        # 然后格式化变更项名称为加粗标题，并添加换行分隔
        # 注意：避免在链接文本中进行替换
        # 使用更精确的匹配，只在非链接上下文中替换
        content = re.sub(r'(?<!\[)安装开发工具(?!\])', '\n\n**安装开发工具**：', content)
        content = re.sub(r'(?<!\[)华为快应用加载器使用指导(?!\])', '\n\n**华为快应用加载器使用指导**：', content)

        # 修复超链接中的换行问题
        # 匹配 [文本\n\n文本] 格式并合并
        content = re.sub(r'\[([^\]]+)\n\n([^\]]+)\]', r'[\1\2]', content)

        # 清理多余的空白字符
        content = re.sub(r'\n{3,}', '\n\n', content)  # 最多保留两个连续换行
        content = content.strip()

        return content
    
    def register_formatter(self, task_name: str, formatter_func: Callable[[str], str]):
        """注册新的格式化器
        
        Args:
            task_name: 任务名称
            formatter_func: 格式化函数，接收content字符串，返回格式化后的字符串
        """
        self._formatters[task_name] = formatter_func
        logger.info(f"已注册格式化器: {task_name}")
    
    def get_supported_tasks(self) -> list:
        """获取支持格式化的任务列表"""
        return list(self._formatters.keys())


# 全局格式化器实例
_content_formatter: Optional[ContentFormatter] = None


def get_content_formatter() -> ContentFormatter:
    """获取内容格式化器实例"""
    global _content_formatter
    if _content_formatter is None:
        _content_formatter = ContentFormatter()
    return _content_formatter


# 格式化器使用示例
def example_custom_formatter(content: str) -> str:
    """自定义格式化器示例
    
    Args:
        content: 原始内容
        
    Returns:
        格式化后的内容
    """
    # 示例：将所有标题转换为加粗格式
    content = re.sub(r'^([^：\n]+)：', r'**\1**：', content, flags=re.MULTILINE)
    
    # 示例：为链接添加图标
    content = content.replace("详情请参见", "🔗 详情请参见")
    
    return content


# 使用示例：
# formatter = get_content_formatter()
# formatter.register_formatter("自定义任务名", example_custom_formatter)
