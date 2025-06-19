"""
AI预览API - 用于预览AI智能通知效果
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict

from app.services.ai_notifier import analyze_notification_content, NotificationAnalysis
from app.core.config import Task

logger = logging.getLogger(__name__)
router = APIRouter()

class AIPreviewRequest(BaseModel):
    """AI预览请求"""
    task_name: str
    task_url: HttpUrl
    ai_description: str
    page_content: str  # 真实的页面内容

class AIPreviewResponse(BaseModel):
    """AI预览响应"""
    success: bool
    title: Optional[str] = None
    content: Optional[str] = None  # 预览内容（使用AI代码生成的示例）
    summary: Optional[str] = None
    extraction_rules: Optional[Dict[str, str]] = None  # AI生成的提取规则
    formatter_code: Optional[str] = None  # AI生成的Python格式化代码
    error: Optional[str] = None

@router.post("/preview", response_model=AIPreviewResponse)
async def preview_ai_notification(request: AIPreviewRequest):
    """预览AI智能通知效果"""
    try:
        # 创建临时任务对象
        temp_task = Task(
            name=request.task_name,
            url=request.task_url,
            frequency="30m",  # 临时值
            rule="css:body",  # 临时值
            enabled=True,
            ai_analysis_enabled=True,
            ai_description=request.ai_description
        )
        
        # 使用真实的页面内容
        # AI 直接分析页面内容结构，生成适合的提取规则
        page_content = request.page_content
        
        logger.info(f"预览AI分析 - 任务: {request.task_name}, 描述: {request.ai_description}")

        # 调用AI分析，直接基于页面内容结构生成提取规则
        result = analyze_notification_content(temp_task, page_content)
        
        if result:
            logger.info(f"AI预览成功 - 任务: {request.task_name}")

            # 尝试执行AI生成的代码来生成预览内容
            preview_content = None
            if result.formatter_code:
                try:
                    from app.services.code_executor import execute_notification_formatter
                    from app.services.content_parser import get_content_parser

                    extracted_data = {}

                    # 如果有提取规则，使用规则提取数据（单规则HTML内容）
                    if result.extraction_rules:
                        content_parser = get_content_parser()
                        for field, rule in result.extraction_rules.items():
                            # 使用 ContentParser 的 _extract_single_field 方法
                            value = content_parser._extract_single_field(field, rule, "", page_content)
                            if value is not None:
                                extracted_data[field] = value
                                logger.info(f"成功提取字段 {field}: {value[:100]}...")
                            else:
                                logger.warning(f"字段 {field} 提取失败，规则: {rule}")
                    else:
                        # 没有提取规则，直接传递原始页面内容（多规则分段内容）
                        extracted_data['page_content'] = page_content
                        logger.info(f"多规则分段内容，直接传递页面内容，长度: {len(page_content)}")

                    logger.info(f"数据提取完成，共提取 {len(extracted_data)} 个字段: {list(extracted_data.keys())}")

                    # 执行AI生成的格式化代码
                    preview_content = execute_notification_formatter(
                        result.formatter_code,
                        extracted_data,
                        {
                            "name": request.task_name,
                            "url": str(request.task_url)
                        }
                    )
                    logger.info(f"AI代码执行成功，生成预览内容")
                except Exception as e:
                    logger.warning(f"AI代码执行失败，使用默认预览: {e}")
                    # AI代码执行失败，直接在错误中报告，不生成备用内容
                    raise Exception(f"AI代码执行预览失败: {e}")

            return AIPreviewResponse(
                success=True,
                title=result.title,
                content=preview_content, # 如果成功则有内容，失败则无
                summary=result.summary,
                extraction_rules=result.extraction_rules,
                formatter_code=result.formatter_code
            )
        else:
            logger.warning(f"AI预览返回空结果 - 任务: {request.task_name}")
            return AIPreviewResponse(
                success=False,
                error="AI分析返回空结果，请检查监控描述是否清晰"
            )
            
    except Exception as e:
        logger.error(f"AI预览失败 - 任务: {request.task_name}, 错误: {e}")
        return AIPreviewResponse(
            success=False,
            error=f"AI分析失败: {str(e)}"
        )

class GetSavedAITemplateRequest(BaseModel):
    """获取已保存的AI模板请求"""
    task_name: str

@router.post("/get-saved-template", response_model=AIPreviewResponse)
async def get_saved_ai_template(request: GetSavedAITemplateRequest):
    """获取任务已保存的AI模板预览（不重新调用AI）"""
    try:
        # 查找任务
        from app.core.config import settings
        task = next((t for t in settings.tasks if t.name == request.task_name), None)
        
        if not task:
            return AIPreviewResponse(
                success=False,
                error=f"任务 '{request.task_name}' 不存在"
            )
        
        if not task.ai_analysis_enabled or not task.ai_formatter_code:
            return AIPreviewResponse(
                success=False,
                error="该任务未配置AI模板"
            )
        
        # 生成预览
        try:
            from app.services.code_executor import execute_notification_formatter
            from app.services.storage import get_last_result
            from app.services.content_parser import get_content_parser
            
            extracted_data = {}
            
            # 首先尝试使用任务的实际存储数据
            try:
                stored_content = get_last_result(task.name)
                
                if stored_content and task.ai_extraction_rules:
                    # 使用真实的存储内容提取数据
                    content_parser = get_content_parser()
                    for field, rule in task.ai_extraction_rules.items():
                        value = content_parser._extract_single_field(field, rule, "", stored_content)
                        if value is not None:
                            extracted_data[field] = value
                            logger.info(f"从存储内容提取字段 {field}: {value[:50]}...")
                    
                    logger.info(f"从存储数据提取了 {len(extracted_data)} 个字段")
            except Exception as e:
                logger.warning(f"无法读取存储数据: {e}")
            
            # 如果没有成功提取到数据，使用智能生成的示例数据
            if not extracted_data and task.ai_extraction_rules:
                logger.info("使用智能生成的示例数据")
                for field in task.ai_extraction_rules:
                    field_lower = field.lower()
                    
                    # 基于字段名智能生成示例数据
                    if 'version' in field_lower:
                        if 'engine' in field_lower and 'honor' in field_lower:
                            extracted_data[field] = '10.0.2.200'
                        elif 'debugger' in field_lower:
                            extracted_data[field] = '80.0.2.200'
                        elif 'minor' in field_lower or 'small' in field_lower:
                            extracted_data[field] = 'V9.8.0'
                        elif 'major' in field_lower or 'big' in field_lower:
                            extracted_data[field] = '1155'
                        else:
                            # 通用版本号格式
                            extracted_data[field] = 'V1.2.3' if '.' in field else '1000'
                    elif 'url' in field_lower or 'link' in field_lower or 'download' in field_lower:
                        extracted_data[field] = 'https://example.com/download'
                    elif 'feature' in field_lower or 'description' in field_lower:
                        extracted_data[field] = '功能更新描述'
                    elif 'name' in field_lower or 'product' in field_lower:
                        extracted_data[field] = '产品名称'
                    elif any(num in field_lower for num in ['number', 'num', 'no', 'id']):
                        extracted_data[field] = '12345'
                    else:
                        extracted_data[field] = f'[{field}的值]'
            
            from datetime import datetime
            
            preview_content = execute_notification_formatter(
                task.ai_formatter_code,
                extracted_data,
                {
                    "name": task.name,
                    "url": task.url,
                    "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
            return AIPreviewResponse(
                success=True,
                title="AI模板预览",
                content=preview_content,
                summary=f"基于示例数据生成的预览效果",
                extraction_rules=task.ai_extraction_rules,
                formatter_code=task.ai_formatter_code
            )
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"执行AI模板代码失败: {e}\n详细错误:\n{error_detail}")
            logger.error(f"提取的数据: {extracted_data}")
            return AIPreviewResponse(
                success=False,
                error=f"模板代码执行失败: {e}"
            )
            
    except Exception as e:
        logger.error(f"获取已保存的AI模板失败 - 任务: {request.task_name}, 错误: {e}")
        return AIPreviewResponse(
            success=False,
            error=f"获取失败: {str(e)}"
        )
