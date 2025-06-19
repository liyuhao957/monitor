"""
内容获取API - 用于获取页面内容以供AI分析
"""
import logging
from typing import Optional, List
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
    rule: Optional[str] = None  # 单规则（向后兼容）
    rules: Optional[List[str]] = None  # 多规则支持

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
        # 验证输入
        if not request.rule and not request.rules:
            return ContentFetchResponse(
                success=False,
                error="必须提供 rule 或 rules 参数"
            )
        
        # 处理多规则或单规则
        if request.rules and len(request.rules) > 0:
            # 多规则模式
            logger.info(f"获取页面内容 (多规则) - 任务: {request.name}, URL: {request.url}, 规则数量: {len(request.rules)}")
            
            all_content = []
            for i, rule in enumerate(request.rules):
                # 为每个规则创建临时任务
                temp_task = Task(
                    name=f"{request.name}_rule_{i+1}",
                    url=request.url,
                    frequency="1m",
                    rule=rule,
                    enabled=True,
                    ai_analysis_enabled=False
                )
                
                # 获取单个规则的内容
                rule_content = await fetch_page_content(temp_task)
                if rule_content:
                    all_content.append(f"=== 提取规则 {i+1}: {rule} ===\n{rule_content}")
                    logger.info(f"规则 {i+1} 提取成功，长度: {len(rule_content)}")
                else:
                    logger.warning(f"规则 {i+1} 提取为空: {rule}")
                    all_content.append(f"=== 提取规则 {i+1}: {rule} ===\n[无内容]")
            
            # 合并所有内容
            combined_content = "\n\n".join(all_content)
            
        else:
            # 单规则模式（向后兼容）
            logger.info(f"获取页面内容 (单规则) - 任务: {request.name}, URL: {request.url}")
            
            temp_task = Task(
                name=request.name,
                url=request.url,
                frequency="1m",
                rule=request.rule,
                enabled=True,
                ai_analysis_enabled=False
            )
            
            combined_content = await fetch_page_content(temp_task)
        
        if combined_content:
            content_preview = (combined_content[:200] + '...') if len(combined_content) > 200 else combined_content
            logger.info(f"内容获取成功 - 任务: {request.name}, 总长度: {len(combined_content)}")
            return ContentFetchResponse(
                success=True,
                content=combined_content,
                content_preview=content_preview,
                content_length=len(combined_content)
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
