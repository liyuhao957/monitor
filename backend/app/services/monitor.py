import asyncio
import difflib
import logging
import re
import html
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from urllib.parse import quote

from lxml import etree, html as lxml_html
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.core.config import Task, settings
from app.services import storage, notifier
from app.services.ai_notifier import analyze_notification_content_change
from app.services.content_parser import get_content_parser
from jinja2 import Template

# Configure logging
logger = logging.getLogger(__name__)

# Define base directories
SCREENSHOTS_DIR = Path(__file__).parent.parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 30

def _normalize_text(text: str) -> str:
    """Standardize text by decoding HTML entities, and unifying whitespace."""
    text = html.unescape(text)  # Decode HTML entities like &amp;
    text = re.sub(r'<[^>]+>', '', text)  # Strip HTML tags
    text = re.sub(r'\s+', ' ', text).strip()  # Replace multiple whitespace chars with a single space
    return text

def _normalize_text_preserve_links(text: str) -> str:
    """Standardize text while preserving important HTML tags like links."""
    text = html.unescape(text)  # Decode HTML entities like &amp;

    # 保留链接标签，移除其他HTML标签
    # 先保护链接标签
    text = re.sub(r'<a\s+([^>]*?)>', r'<a \1>', text)  # 标准化链接标签格式

    # 移除除了链接之外的其他HTML标签
    text = re.sub(r'<(?!/?a\b)[^>]+>', '', text)

    # 统一空白字符
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def _extract_content(html_content: str, rule: str) -> str:
    """Extracts content from HTML based on the provided rule (css, xpath, or regex)."""
    try:
        if rule.startswith('css:'):
            selector = rule[4:].strip()
            tree = lxml_html.fromstring(html_content)
            elements = tree.cssselect(selector)
            return "\n".join([_normalize_text(el.text_content()) for el in elements])
        elif rule.startswith('xpath:'):
            expression = rule[6:].strip()
            tree = lxml_html.fromstring(html_content)
            elements = tree.xpath(expression)
            # XPath can return strings or elements, handle both cases.
            result_parts = []
            for el in elements:
                if isinstance(el, str):
                    # XPath返回的字符串（如属性值）
                    result_parts.append(_normalize_text(el))
                else:
                    # XPath返回的元素，检查是否包含链接
                    element_html = lxml_html.tostring(el, encoding='unicode')
                    if '<a ' in element_html:
                        # 包含链接，保留HTML结构
                        result_parts.append(_normalize_text_preserve_links(element_html))
                    else:
                        # 不包含链接，正常处理
                        result_parts.append(_normalize_text(el.text_content()))
            return "\n".join(result_parts)
        elif rule.startswith('regex:'):
            pattern = rule[6:].strip()
            # For regex, we search against the raw HTML, not normalized text
            matches = re.findall(pattern, html_content, re.DOTALL)
            # We still normalize the final extracted strings
            return "\n".join([_normalize_text(match) for match in matches])
        else:
            logger.warning(f"Unknown rule format: {rule}. Returning full page text.")
            tree = lxml_html.fromstring(html_content)
            return _normalize_text(tree.text_content())
    except etree.ParserError as e:
        logger.error(f"Failed to parse HTML content: {e}. Falling back to regex on raw text.")
        # Fallback for broken HTML that lxml can't parse
        return _normalize_text(html_content)

async def fetch_page_content(task: Task) -> str:
    """仅获取页面内容，用于AI模板预览，不执行完整监控流程"""
    logger.info(f"[{task.name}] Fetching page content for AI preview...")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            logger.info(f"[{task.name}] Loading page: {task.url}")
            await page.goto(str(task.url), wait_until='domcontentloaded', timeout=30000)

            # 等待JavaScript渲染完成
            await page.wait_for_timeout(3000)

            html_content = await page.content()
            await browser.close()

        logger.info(f"[{task.name}] Extracting content with rule: {task.rule}")
        content = await _extract_content(html_content, task.rule)

        logger.info(f"[{task.name}] Successfully fetched content ({len(content)} characters)")
        return content

    except Exception as e:
        logger.error(f"[{task.name}] Failed to fetch page content: {e}")
        raise

async def run_task(task: Task):
    """The main execution function for a single monitoring task."""
    logger.info(f"[{task.name}] Starting task...")
    
    for attempt in range(MAX_RETRIES):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                
                logger.info(f"[{task.name}] Loading page: {task.url}")
                # 参考元素提取器的成功做法
                await page.goto(str(task.url), wait_until='domcontentloaded', timeout=30000)

                # 等待JavaScript渲染完成（参考selector.py的做法）
                await page.wait_for_timeout(3000)

                html_content = await page.content()
                
                screenshot_path: Optional[str] = None
                if task.screenshot:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    path = SCREENSHOTS_DIR / f"{task.name.replace(' ', '_')}_{ts}.png"
                    await page.screenshot(path=path, full_page=True)
                    screenshot_path = str(path)
                    logger.info(f"[{task.name}] Screenshot saved to {screenshot_path}")

                await browser.close()

            logger.info(f"[{task.name}] Extracting content with rule: {task.rule}")
            new_content = await _extract_content(html_content, task.rule)
            
            old_content = storage.get_last_result(task.name)

            if old_content is None:
                logger.info(f"[{task.name}] First run. Initializing baseline.")
                storage.save_result(task.name, new_content)
                return

            if new_content != old_content:
                logger.warning(f"[{task.name}] Change detected! Sending notification.")

                # Create a summary of changes (fallback for non-AI notifications)
                summary_old = (old_content[:200] + '...') if len(old_content) > 200 else old_content
                summary_new = (new_content[:200] + '...') if len(new_content) > 200 else new_content

                # Prepare template context
                screenshot_filename = Path(screenshot_path).name if screenshot_path else None
                screenshot_url = f"http://127.0.0.1:8000/screenshots/{quote(screenshot_filename)}" if screenshot_filename else None

                template_context = {
                    "task_name": task.name,
                    "url": str(task.url),
                    "old_summary": summary_old,
                    "new_summary": summary_new,
                    "screenshot_url": screenshot_url or None,
                    "screenshot_path": screenshot_path or "未启用"
                }

                # AI智能通知处理
                if task.ai_analysis_enabled:
                    logger.info(f"[{task.name}] Using AI-powered intelligent notification")

                    # 使用保存的AI提取规则进行字段提取
                    if task.ai_extraction_rules:
                        logger.info(f"[{task.name}] Using saved AI extraction rules")
                        from app.services.ai_notifier import NotificationAnalysis

                        # 创建一个临时的分析结果对象，只包含提取规则
                        temp_analysis = NotificationAnalysis(
                            title="",
                            content="",
                            summary="",
                            extraction_rules=task.ai_extraction_rules
                        )

                        # 使用智能解析器提取结构化数据
                        content_parser = get_content_parser()
                        extracted_fields = content_parser.extract_fields(temp_analysis, old_content, new_content)

                        # 将提取的字段添加到模板上下文
                        template_context.update(extracted_fields)
                        logger.info(f"[{task.name}] Extracted {len(extracted_fields)} intelligent fields: {list(extracted_fields.keys())}")
                    else:
                        logger.warning(f"[{task.name}] AI analysis enabled but no extraction rules found")
                else:
                    logger.info(f"[{task.name}] Using traditional notification template")

                try:
                    message = ""

                    # 检查是否启用AI智能通知但没有自定义模板
                    if task.ai_analysis_enabled and (not task.notification_template or task.notification_template in settings.notification_presets):
                        # AI智能通知启用但没有使用过生成AI模板预览，显示空白
                        logger.info(f"[{task.name}] AI notification enabled but no custom template found, skipping notification")
                        return

                    # 使用模板生成通知（AI生成的模板或传统模板）
                    # 1. User-defined template (包括AI生成的模板)
                    if task.notification_template and task.notification_template not in settings.notification_presets:
                        template_to_use = task.notification_template
                    # 2. Preset template (仅当未启用AI智能通知时)
                    else:
                        preset_key = task.notification_template or 'default'
                        template_to_use = settings.notification_presets.get(preset_key)

                    if template_to_use:
                        try:
                            jinja_template = Template(template_to_use)
                            message = jinja_template.render(**template_context)
                        except Exception as e:
                            logger.error(f"Error rendering Jinja2 template for task '{task.name}': {e}")
                            # Failsafe message
                            message = f"Task '{task.name}' has changed. URL: {task.url}"
                    else:
                        # This part should ideally not be reached if 'default' preset is always available
                        logger.warning("No notification template found. Using hardcoded failsafe template.")
                        message = f"Task '{task.name}' has changed. URL: {task.url}"

                    # 发送通知
                    await notifier.send_notification(task, message, screenshot_path)

                    storage.save_result(task.name, new_content)
                except Exception as e:
                    logger.error(f"Error processing task {task.name}: {e}")
            else:
                logger.info(f"[{task.name}] No change detected. No action needed.")

            return # Success, exit retry loop

        except PlaywrightTimeoutError:
            logger.error(f"[{task.name}] Page load timed out on attempt {attempt + 1}/{MAX_RETRIES}.")
        except Exception as e:
            logger.error(f"[{task.name}] An unexpected error occurred on attempt {attempt + 1}/{MAX_RETRIES}: {e}", exc_info=True)

        if attempt < MAX_RETRIES - 1:
            logger.info(f"[{task.name}] Retrying in {RETRY_DELAY_SECONDS} seconds...")
            await asyncio.sleep(RETRY_DELAY_SECONDS)
    
    logger.error(f"[{task.name}] Task failed after {MAX_RETRIES} attempts.") 