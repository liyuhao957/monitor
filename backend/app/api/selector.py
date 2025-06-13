"""
可视化元素选择器 API
提供代理渲染和元素选择功能
"""
import asyncio
import logging
import os
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.services.ai_selector import AISelector, SelectorRequest

logger = logging.getLogger(__name__)
router = APIRouter()

# 活跃会话存储
active_sessions: Dict[str, Dict[str, Any]] = {}

class UrlRequest(BaseModel):
    url: str

class SelectorResult(BaseModel):
    css_selector: str
    xpath: str
    mode_recommend: str
    example_text: str
    tag: str
    timestamp: int

class AIGenerateRequest(BaseModel):
    element_html: str
    context_html: str
    user_intent: str
    element_text: str
    element_attributes: Dict[str, Any]

@router.post("/load")
async def create_selector_session(request: UrlRequest):
    """
    创建新的选择器会话，返回会话ID
    """
    try:
        # 格式化URL
        url = request.url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # 生成会话ID
        session_id = str(int(asyncio.get_event_loop().time() * 1000))
        
        # 存储会话信息
        active_sessions[session_id] = {"url": url}
        logger.info(f"Created selector session: {session_id} for URL: {url}")
        
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error creating selector session: {e}")
        raise HTTPException(status_code=500, detail="创建会话失败")

@router.get("/render/{session_id}", response_class=HTMLResponse)
async def render_page_with_injector(session_id: str):
    """
    使用Playwright渲染页面并注入选择器脚本
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="会话不存在或已过期")

    target_url = active_sessions[session_id].get("url")
    if not target_url:
        raise HTTPException(status_code=400, detail="会话中未找到URL")

    logger.info(f"Rendering page for session {session_id}: {target_url}")

    try:
        # 读取注入脚本
        injector_path = Path(__file__).parent.parent.parent / "static" / "injector.js"
        if not injector_path.exists():
            raise HTTPException(status_code=500, detail="注入脚本文件不存在")
        
        injector_script = injector_path.read_text(encoding='utf-8')
        
        # 使用Playwright渲染页面
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # 设置用户代理和视口
            await page.set_viewport_size({"width": 1280, "height": 720})

            # 导航到目标URL，等待页面完全加载
            await page.goto(target_url, wait_until='domcontentloaded', timeout=30000)

            # 等待一段时间让JavaScript渲染完成
            await page.wait_for_timeout(3000)

            # 获取页面HTML内容
            html_content = await page.content()

            await browser.close()
        
        # 注入脚本到HTML
        injected_html = inject_script_to_html(html_content, injector_script, target_url)
        
        logger.info(f"Successfully rendered and injected script for session {session_id}")
        return HTMLResponse(content=injected_html)
        
    except PlaywrightTimeoutError:
        logger.error(f"Timeout loading page for session {session_id}: {target_url}")
        raise HTTPException(status_code=408, detail="页面加载超时")
    except Exception as e:
        logger.error(f"Error rendering page for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="页面渲染失败")

def inject_script_to_html(html_content: str, script_content: str, base_url: str) -> str:
    """
    将JavaScript脚本注入到HTML的body标签闭合之前，并修复相对路径问题
    """
    import re
    from urllib.parse import urljoin, urlparse

    # 解析基础URL
    parsed_url = urlparse(base_url)
    base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # 添加base标签来修复相对路径问题
    base_tag = f'<base href="{base_domain}/">'

    # 创建脚本标签
    script_tag = f'<script type="text/javascript">\n{script_content}\n</script>'

    # 在head中添加base标签
    if '<head>' in html_content:
        html_content = html_content.replace('<head>', f'<head>\n{base_tag}')
    elif '<html>' in html_content:
        html_content = html_content.replace('<html>', f'<html>\n<head>{base_tag}</head>')
    else:
        # 如果没有head标签，在开头添加
        html_content = f'<head>{base_tag}</head>\n{html_content}'

    # 查找</body>标签并在其前面插入脚本
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{script_tag}\n</body>')
    else:
        # 如果没有</body>标签，添加到HTML末尾
        html_content += f'\n{script_tag}'

    return html_content

@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """
    清理会话
    """
    if session_id in active_sessions:
        del active_sessions[session_id]
        logger.info(f"Cleaned up session: {session_id}")
        return {"message": "会话已清理"}
    else:
        raise HTTPException(status_code=404, detail="会话不存在")

@router.get("/sessions")
async def list_active_sessions():
    """
    列出所有活跃会话（调试用）
    """
    return {"active_sessions": list(active_sessions.keys())}

@router.post("/ai-generate")
async def ai_generate_selector(request: AIGenerateRequest):
    """
    使用AI生成最优选择器
    """
    try:
        # 获取API配置
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.oaipro.com/v1")

        if not api_key:
            raise HTTPException(status_code=500, detail="未配置OpenAI API Key")

        # 创建AI选择器生成器
        ai_selector = AISelector(api_key=api_key, base_url=base_url)

        # 构建请求
        selector_request = SelectorRequest(
            element_html=request.element_html,
            context_html=request.context_html,
            user_intent=request.user_intent,
            element_text=request.element_text,
            element_attributes=request.element_attributes
        )

        # 生成选择器
        result = ai_selector.generate_selector(selector_request)

        # 转换为API响应格式
        return {
            "css_selector": result.css_selector,
            "xpath": result.xpath,
            "recommended_type": result.recommended_type,
            "mode_recommend": request.user_intent,
            "example_text": request.element_text,
            "tag": "ai-generated",
            "timestamp": int(asyncio.get_event_loop().time() * 1000),
            "description": result.description,
            "confidence": result.confidence,
            "intent": request.user_intent,
            "type_analysis": result.type_analysis
        }

    except Exception as e:
        logger.error(f"AI选择器生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI选择器生成失败: {str(e)}")
