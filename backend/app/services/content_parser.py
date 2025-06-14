"""
智能内容解析器
根据AI定义的提取规则，从HTML内容中提取结构化数据
"""
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.services.ai_notifier import NotificationAnalysis

logger = logging.getLogger(__name__)

class ContentParser:
    """智能内容解析器"""
    
    def __init__(self):
        pass
    
    def extract_fields(
        self, 
        analysis: NotificationAnalysis, 
        old_content: str, 
        new_content: str
    ) -> Dict[str, Any]:
        """
        根据AI分析结果提取结构化字段
        
        Args:
            analysis: AI分析结果，包含提取规则
            old_content: 变化前的内容
            new_content: 变化后的内容
            
        Returns:
            提取的结构化数据字典
        """
        extracted_data = {}
        
        if not analysis.extraction_rules:
            logger.info("没有定义提取规则，跳过字段提取")
            return extracted_data
        
        logger.info(f"开始提取字段，规则数量: {len(analysis.extraction_rules)}")
        
        for field_name, rule in analysis.extraction_rules.items():
            try:
                value = self._extract_single_field(field_name, rule, old_content, new_content)
                if value is not None:
                    extracted_data[field_name] = value
                    logger.debug(f"成功提取字段 {field_name}: {value}")
                else:
                    logger.warning(f"字段 {field_name} 提取失败，规则: {rule}")
            except Exception as e:
                logger.error(f"提取字段 {field_name} 时出错: {e}，规则: {rule}")
                
        logger.info(f"字段提取完成，成功提取 {len(extracted_data)} 个字段")
        return extracted_data
    
    def _extract_single_field(
        self, 
        field_name: str, 
        rule: str, 
        old_content: str, 
        new_content: str
    ) -> Optional[str]:
        """
        提取单个字段的值
        
        Args:
            field_name: 字段名
            rule: 提取规则
            old_content: 变化前的内容
            new_content: 变化后的内容
            
        Returns:
            提取的值，如果提取失败返回None
        """
        # 处理特殊规则
        if "datetime.now()" in rule:
            return self._extract_current_time(rule)
        
        # 确定要从哪个内容中提取
        if "old_summary" in rule or "old_content" in rule:
            content = old_content
        elif "new_summary" in rule or "new_content" in rule:
            content = new_content
        else:
            # 默认从新内容中提取
            content = new_content
        
        # 提取正则表达式
        regex_pattern = self._extract_regex_from_rule(rule)
        if not regex_pattern:
            logger.warning(f"无法从规则中提取正则表达式: {rule}")
            return None
        
        # 执行正则匹配
        try:
            match = re.search(regex_pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                # 如果有捕获组，返回第一个捕获组
                if match.groups():
                    result = match.group(1)
                else:
                    result = match.group(0)

                # 兜底清理：移除明显的HTML标签残留
                result = self._clean_html_residue(result)
                return result
            else:
                logger.debug(f"正则表达式 {regex_pattern} 在内容中未找到匹配")
                return None
        except re.error as e:
            logger.error(f"正则表达式错误 {regex_pattern}: {e}")
            return None
    
    def _extract_regex_from_rule(self, rule: str) -> Optional[str]:
        """
        从提取规则中提取正则表达式
        
        Args:
            rule: 提取规则字符串
            
        Returns:
            正则表达式字符串，如果提取失败返回None
        """
        # 查找冒号后的正则表达式
        if "：" in rule:
            return rule.split("：", 1)[1].strip()
        elif ":" in rule:
            return rule.split(":", 1)[1].strip()
        else:
            # 如果没有冒号，假设整个规则就是正则表达式
            return rule.strip()
    
    def _extract_current_time(self, rule: str) -> str:
        """
        提取当前时间

        Args:
            rule: 时间格式规则

        Returns:
            格式化的当前时间字符串
        """
        try:
            # 提取时间格式
            if "strftime(" in rule:
                format_start = rule.find("strftime('") + 10
                format_end = rule.find("')", format_start)
                if format_start > 9 and format_end > format_start:
                    time_format = rule[format_start:format_end]
                    return datetime.now().strftime(time_format)

            # 默认格式
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        except Exception as e:
            logger.error(f"时间提取错误: {e}")
            return datetime.now().strftime('%Y-%m-%d %H:%M')

    def _clean_html_residue(self, text: str) -> str:
        """
        兜底清理：移除明显的HTML标签残留

        Args:
            text: 待清理的文本

        Returns:
            清理后的文本
        """
        if not text:
            return text

        # 移除完整的HTML标签
        text = re.sub(r'<[^>]+>', '', text)

        # 移除HTML实体
        text = re.sub(r'&[a-zA-Z0-9#]+;', '', text)

        # 清理多余的空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        return text

# 全局解析器实例
_content_parser: Optional[ContentParser] = None

def get_content_parser() -> ContentParser:
    """获取内容解析器实例"""
    global _content_parser
    if _content_parser is None:
        _content_parser = ContentParser()
    return _content_parser
