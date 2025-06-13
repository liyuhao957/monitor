"""
内容获取API - 用于获取页面内容以供AI分析
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.core.config import Task
from app.services.monitor import fetch_page_content

logger = logging.getLogger(__name__)
router = APIRouter()

class ContentFetchRequest(BaseModel):
    """内容获取请求"""
    name: str
    url: HttpUrl
    rule: str

class ContentFetchResponse(BaseModel):
    """内容获取响应"""
    success: bool
    content: str = ""
    content_preview: str = ""  # 内容预览（前200字符）
    content_length: int = 0
    error: str = ""

@router.post("/fetch", response_model=ContentFetchResponse)
async def fetch_content(request: ContentFetchRequest):
    """获取页面内容"""
    try:
        # 创建临时任务对象
        temp_task = Task(
            name=request.name,
            url=request.url,
            frequency="1m",  # 临时值
            rule=request.rule,
            enabled=True,
            ai_analysis_enabled=False  # 仅获取内容，不需要AI分析
        )
        
        logger.info(f"获取页面内容 - 任务: {request.name}, URL: {request.url}")
        
        # 获取页面内容
        content = await fetch_page_content(temp_task)
        
        if content:
            content_preview = (content[:200] + '...') if len(content) > 200 else content
            logger.info(f"内容获取成功 - 任务: {request.name}, 长度: {len(content)}")
            return ContentFetchResponse(
                success=True,
                content=content,
                content_preview=content_preview,
                content_length=len(content)
            )
        else:
            logger.warning(f"内容获取为空 - 任务: {request.name}")
            return ContentFetchResponse(
                success=False,
                error="页面内容为空，请检查URL和提取规则"
            )
            
    except Exception as e:
        logger.error(f"内容获取失败 - 任务: {request.name}, 错误: {e}")
        return ContentFetchResponse(
            success=False,
            error=f"获取页面内容失败: {str(e)}"
        )
