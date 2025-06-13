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
    content: Optional[str] = None
    summary: Optional[str] = None
    extraction_rules: Optional[Dict[str, str]] = None  # AI生成的提取规则
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
        # 为了让AI能够分析变化，我们创建一个轻微修改的版本作为"变化后"的内容
        old_content = request.page_content
        # 简单地在内容末尾添加一个标记来模拟变化，AI会基于真实内容生成提取规则
        new_content = request.page_content + " [模拟变化]"
        
        logger.info(f"预览AI分析 - 任务: {request.task_name}, 描述: {request.ai_description}")
        
        # 调用AI分析
        result = analyze_notification_content(temp_task, old_content, new_content)
        
        if result:
            logger.info(f"AI预览成功 - 任务: {request.task_name}")
            return AIPreviewResponse(
                success=True,
                title=result.title,
                content=result.content,
                summary=result.summary,
                extraction_rules=result.extraction_rules
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
