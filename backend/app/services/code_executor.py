"""
安全的Python代码执行器
用于执行AI生成的通知格式化代码
"""
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SafeCodeExecutor:
    """安全的代码执行器"""
    
    def __init__(self):
        # 预定义的安全全局变量
        self.safe_globals = {
            '__builtins__': {
                # 只允许安全的内置函数
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'sorted': sorted,
                'max': max,
                'min': min,
                'sum': sum,
                'abs': abs,
                'round': round,
                'isinstance': isinstance,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'print': print,  # 用于调试
                # 添加常用的逻辑和转换函数
                'all': all,
                'any': any,
                'ord': ord,
                'chr': chr,
                'bin': bin,
                'hex': hex,
                'oct': oct,
                'pow': pow,
                'divmod': divmod,
                'format': format,
                'repr': repr,
                'ascii': ascii,
                'bytes': bytes,
                'bytearray': bytearray,
                'memoryview': memoryview,
                'slice': slice,
                'reversed': reversed,
                'iter': iter,
                'next': next,
                # 添加常用的异常类，供AI生成的代码使用
                'Exception': Exception,
                'ValueError': ValueError,
                'TypeError': TypeError,
                'KeyError': KeyError,
                'IndexError': IndexError,
                'AttributeError': AttributeError,
            }
        }
        
        # 允许导入的安全模块
        self.safe_modules = {
            're': __import__('re'),
            'json': __import__('json'),
            'datetime': __import__('datetime'),
            'html': __import__('html'),
            'urllib': __import__('urllib'),
        }
        
        # 尝试导入BeautifulSoup
        try:
            from bs4 import BeautifulSoup
            self.safe_modules['BeautifulSoup'] = BeautifulSoup
            self.safe_modules['bs4'] = __import__('bs4')
        except ImportError:
            logger.warning("BeautifulSoup4 未安装，HTML解析功能将受限")
    
    def execute_formatter(
        self, 
        code: str, 
        extracted_data: Dict[str, Any], 
        task_info: Dict[str, Any]
    ) -> str:
        """
        安全执行格式化代码
        
        Args:
            code: AI生成的Python代码
            extracted_data: 提取的数据字典
            task_info: 任务信息
            
        Returns:
            str: 格式化后的通知内容
        """
        try:
            # 准备执行环境
            local_vars = {}
            global_vars = self.safe_globals.copy()
            global_vars.update(self.safe_modules)
            
            # 添加当前时间信息到task_info
            task_info = task_info.copy()
            task_info['current_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            task_info['current_date'] = datetime.now().strftime("%Y-%m-%d")
            task_info['timestamp'] = datetime.now().timestamp()
            
            logger.info(f"执行AI生成的格式化代码，数据字段: {list(extracted_data.keys())}")
            
            # 执行代码
            exec(code, global_vars, local_vars)
            
            # 检查是否定义了format_notification函数
            if 'format_notification' not in local_vars:
                raise ValueError("代码中未找到 format_notification 函数")
            
            format_func = local_vars['format_notification']
            
            # 调用格式化函数
            result = format_func(extracted_data, task_info)
            
            if not isinstance(result, str):
                raise ValueError(f"format_notification 函数必须返回字符串，实际返回: {type(result)}")
            
            logger.info(f"代码执行成功，生成通知内容长度: {len(result)} 字符")
            return result
            
        except Exception as e:
            error_msg = f"代码执行失败: {str(e)}"
            logger.error(error_msg)
            logger.error(f"错误详情: {traceback.format_exc()}")
            
            # 返回错误信息和原始数据
            fallback_content = self._generate_fallback_notification(extracted_data, task_info, error_msg)
            return fallback_content
    
    def _generate_fallback_notification(
        self, 
        extracted_data: Dict[str, Any], 
        task_info: Dict[str, Any], 
        error_msg: str
    ) -> str:
        """
        生成备用通知内容（当代码执行失败时）
        """
        content_parts = [
            f"🚨 **通知格式化失败**",
            f"",
            f"**任务名称**: {task_info.get('name', '未知')}",
            f"**监控地址**: {task_info.get('url', '未知')}",
            f"**检测时间**: {task_info.get('current_time', '未知')}",
            f"",
            f"**错误信息**: {error_msg}",
            f"",
            f"**提取的数据**:"
        ]
        
        for key, value in extracted_data.items():
            # 限制值的长度，避免过长的内容
            str_value = str(value)
            if len(str_value) > 200:
                str_value = str_value[:200] + "..."
            content_parts.append(f"- **{key}**: {str_value}")
        
        return "\n".join(content_parts)

# 全局执行器实例
_code_executor: Optional[SafeCodeExecutor] = None

def get_code_executor() -> SafeCodeExecutor:
    """获取代码执行器实例"""
    global _code_executor
    if _code_executor is None:
        _code_executor = SafeCodeExecutor()
    return _code_executor

def execute_notification_formatter(
    code: str, 
    extracted_data: Dict[str, Any], 
    task_info: Dict[str, Any]
) -> str:
    """
    执行通知格式化代码的便捷函数
    
    Args:
        code: AI生成的Python代码
        extracted_data: 提取的数据字典
        task_info: 任务信息
        
    Returns:
        str: 格式化后的通知内容
    """
    executor = get_code_executor()
    return executor.execute_formatter(code, extracted_data, task_info)
