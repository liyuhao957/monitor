"""
HTML智能内容解析器
根据AI定义的CSS/XPath提取规则，从HTML内容中提取结构化数据
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from lxml import html as lxml_html

from app.services.ai_notifier import NotificationAnalysis

logger = logging.getLogger(__name__)

class HTMLContentParser:
    """HTML智能内容解析器"""
    
    def __init__(self):
        pass
    
    def extract_fields(
        self, 
        analysis: NotificationAnalysis, 
        old_content: str, 
        new_content: str
    ) -> Dict[str, Any]:
        """
        根据AI分析结果从HTML内容中提取结构化字段
        
        Args:
            analysis: AI分析结果，包含提取规则
            old_content: 变化前的HTML内容
            new_content: 变化后的HTML内容
            
        Returns:
            提取的结构化数据字典
        """
        extracted_data = {}
        
        if not analysis.extraction_rules:
            logger.info("没有定义提取规则，跳过字段提取")
            return extracted_data
        
        logger.info(f"开始从HTML内容提取字段，规则数量: {len(analysis.extraction_rules)}")
        
        for field_name, rule in analysis.extraction_rules.items():
            try:
                value = self._extract_single_field(field_name, rule, old_content, new_content)
                if value is not None:
                    extracted_data[field_name] = value
                    logger.debug(f"成功提取字段 {field_name}: {value}")
                else:
                    logger.warning(f"字段 {field_name} 提取失败，规则: {rule}")
                    extracted_data[field_name] = None
            except Exception as e:
                logger.error(f"提取字段 {field_name} 时出错: {e}，规则: {rule}")
                extracted_data[field_name] = None
                
        logger.info(f"字段提取完成，成功提取 {len([v for v in extracted_data.values() if v is not None])} 个字段")
        return extracted_data
    
    def _extract_single_field(
        self, 
        field_name: str, 
        rule: str, 
        old_content: str, 
        new_content: str
    ) -> Optional[str]:
        """
        从HTML内容中提取单个字段的值
        
        Args:
            field_name: 字段名
            rule: 提取规则 (css: 或 xpath: 格式)
            old_content: 变化前的HTML内容
            new_content: 变化后的HTML内容
            
        Returns:
            提取的值，如果提取失败返回None
        """
        # 处理特殊规则：当前时间
        if "datetime.now()" in rule:
            return self._extract_current_time(rule)
        
        # 确定要从哪个内容中提取
        if "old_" in field_name.lower():
            content = old_content
        else:
            # 默认从新内容中提取
            content = new_content
        
        if not content:
            logger.warning(f"字段 {field_name} 对应的内容为空")
            return None
        
        # 根据规则类型进行提取
        if rule.startswith('css:'):
            return self._extract_with_css(field_name, rule[4:].strip(), content)
        elif rule.startswith('xpath:'):
            return self._extract_with_xpath(field_name, rule[6:].strip(), content)
        else:
            logger.warning(f"未知的规则格式: {rule}，必须以 'css:' 或 'xpath:' 开头")
            return None
    
    def _extract_with_css(self, field_name: str, selector: str, html_content: str) -> Optional[str]:
        """
        使用CSS选择器从HTML中提取内容
        
        Args:
            field_name: 字段名
            selector: CSS选择器
            html_content: HTML内容
            
        Returns:
            提取的值，如果提取失败返回None
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 处理特殊的属性提取语法：selector::attr(attribute_name)
            if '::attr(' in selector:
                base_selector, attr_part = selector.split('::attr(', 1)
                attr_name = attr_part.rstrip(')')
                element = soup.select_one(base_selector.strip())
                if element and element.has_attr(attr_name):
                    result = element[attr_name]
                    logger.info(f"字段 {field_name} CSS属性提取成功: {result}")
                    return result
                else:
                    logger.warning(f"字段 {field_name} CSS选择器 {base_selector} 未找到元素或属性 {attr_name}")
                    return None
            
            # 处理特殊的文本提取语法：selector::text
            elif selector.endswith('::text'):
                base_selector = selector[:-6].strip()
                element = soup.select_one(base_selector)
                if element:
                    result = element.get_text(strip=True)
                    logger.info(f"字段 {field_name} CSS文本提取成功: {result}")
                    return result
                else:
                    logger.warning(f"字段 {field_name} CSS选择器 {base_selector} 未找到元素")
                    return None
            
            # 默认行为：提取元素的文本内容
            else:
                element = soup.select_one(selector)
                if element:
                    result = element.get_text(strip=True)
                    logger.info(f"字段 {field_name} CSS文本提取成功: {result}")
                    return result
                else:
                    logger.warning(f"字段 {field_name} CSS选择器 {selector} 未找到元素")
                    return None
                    
        except Exception as e:
            logger.error(f"CSS选择器提取出错 {selector}: {e}")
            return None
    
    def _extract_with_xpath(self, field_name: str, xpath: str, html_content: str) -> Optional[str]:
        """
        使用XPath从HTML中提取内容
        
        Args:
            field_name: 字段名
            xpath: XPath表达式
            html_content: HTML内容
            
        Returns:
            提取的值，如果提取失败返回None
        """
        try:
            tree = lxml_html.fromstring(html_content)
            elements = tree.xpath(xpath)
            
            if elements:
                # 取第一个匹配结果
                element = elements[0]
                
                if isinstance(element, str):
                    # XPath直接返回字符串（如属性值或文本）
                    result = element.strip()
                    logger.info(f"字段 {field_name} XPath字符串提取成功: {result}")
                    return result
                else:
                    # XPath返回元素，提取文本内容
                    result = element.text_content().strip()
                    logger.info(f"字段 {field_name} XPath元素提取成功: {result}")
                    return result
            else:
                logger.warning(f"字段 {field_name} XPath {xpath} 未找到匹配元素")
                return None
                
        except Exception as e:
            logger.error(f"XPath提取出错 {xpath}: {e}")
            return None
    
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

# 全局解析器实例
_content_parser: Optional[HTMLContentParser] = None

def get_content_parser() -> HTMLContentParser:
    """获取HTML内容解析器实例"""
    global _content_parser
    if _content_parser is None:
        _content_parser = HTMLContentParser()
    return _content_parser
