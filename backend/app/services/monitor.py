import asyncio
import logging
import re
import html
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import quote

from lxml import etree, html as lxml_html
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from app.core.config import Task, settings
from app.services import storage, notifier

from app.services.content_parser import get_content_parser
from app.services.code_executor import execute_notification_formatter
# Jinja2 removed - only using AI-generated Python code

# Configure logging
logger = logging.getLogger(__name__)

# Define base directories
SCREENSHOTS_DIR = Path(__file__).parent.parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 30

# Global task execution lock to prevent concurrent task execution
_task_execution_lock = asyncio.Lock()

# Separate lock for AI preview to avoid conflicts with scheduled tasks
_ai_preview_lock = asyncio.Lock()

# Anti-duplicate notification cache
# Format: {task_name: {content_hash: timestamp}}
_notification_cache: Dict[str, Dict[str, datetime]] = {}
NOTIFICATION_COOLDOWN_MINUTES = 5  # Prevent duplicate notifications within 5 minutes

def _should_send_notification(task_name: str, content: str) -> bool:
    """
    Check if we should send a notification based on content and timing.
    Prevents duplicate notifications within the cooldown period.
    """
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    current_time = datetime.now()

    # Initialize task cache if not exists
    if task_name not in _notification_cache:
        _notification_cache[task_name] = {}

    task_cache = _notification_cache[task_name]

    # Check if we've sent this exact content recently
    if content_hash in task_cache:
        last_sent = task_cache[content_hash]
        time_diff = current_time - last_sent
        if time_diff.total_seconds() < NOTIFICATION_COOLDOWN_MINUTES * 60:
            logger.info(f"[{task_name}] Duplicate notification suppressed (sent {time_diff.total_seconds():.0f}s ago)")
            return False

    # Clean up old entries (older than cooldown period)
    cutoff_time = current_time - timedelta(minutes=NOTIFICATION_COOLDOWN_MINUTES * 2)
    task_cache = {h: t for h, t in task_cache.items() if t > cutoff_time}
    _notification_cache[task_name] = task_cache

    # Record this notification
    task_cache[content_hash] = current_time
    return True

async def _extract_content(html_content: str, rule: str) -> str:
    """Extracts HTML content based on the provided rule (css, xpath, or regex), preserving HTML structure."""
    try:
        if rule.startswith('css:'):
            selector = rule[4:].strip()
            tree = lxml_html.fromstring(html_content)
            elements = tree.cssselect(selector)
            return "\n".join([lxml_html.tostring(el, encoding='unicode', method='html') for el in elements])
        elif rule.startswith('xpath:'):
            expression = rule[6:].strip()
            tree = lxml_html.fromstring(html_content)
            elements = tree.xpath(expression)
            # XPath can return strings or elements, handle both cases.
            result_parts = []
            for el in elements:
                if isinstance(el, str):
                    # XPath返回的字符串（如属性值），直接使用
                    result_parts.append(el)
                else:
                    # XPath返回的元素，保留HTML结构
                    result_parts.append(lxml_html.tostring(el, encoding='unicode', method='html'))
            return "\n".join(result_parts)
        elif rule.startswith('regex:'):
            pattern = rule[6:].strip()
            # For regex, we search against the raw HTML
            matches = re.findall(pattern, html_content, re.DOTALL)
            return "\n".join(matches)
        else:
            logger.warning(f"Unknown rule format: {rule}. Returning full page HTML.")
            return html_content
    except etree.ParserError as e:
        logger.error(f"Failed to parse HTML content: {e}. Returning raw content.")
        return html_content

async def fetch_page_content(task: Task) -> str:
    """仅获取页面内容，用于AI模板预览，不执行完整监控流程"""
    logger.debug(f"[{task.name}] Waiting for AI preview lock...")

    try:
        # Use separate lock for AI preview to avoid conflicts with scheduled tasks
        async with asyncio.timeout(60):  # 60 second timeout for AI preview (longer than monitoring)
            async with _ai_preview_lock:
                logger.info(f"[{task.name}] Fetching page content for AI preview (acquired AI preview lock)...")
                return await _fetch_page_content_internal(task)
    except asyncio.TimeoutError:
        logger.error(f"[{task.name}] Failed to acquire AI preview lock within 60 seconds")
        raise
    finally:
        logger.debug(f"[{task.name}] Released AI preview lock")

async def _fetch_page_content_internal(task: Task) -> str:
    """Internal page content fetching function."""
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
    logger.debug(f"[{task.name}] Waiting for execution lock...")

    try:
        # Use asyncio.wait_for to add timeout to lock acquisition
        async with asyncio.timeout(30):  # 30 second timeout for lock acquisition
            async with _task_execution_lock:
                logger.info(f"[{task.name}] Starting task (acquired execution lock)...")
                return await _run_task_internal(task)
    except asyncio.TimeoutError:
        logger.error(f"[{task.name}] Failed to acquire execution lock within 30 seconds")
        raise
    finally:
        logger.debug(f"[{task.name}] Released execution lock")

async def _run_task_internal(task: Task):
    """Internal task execution function with retry logic."""
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

            # 处理多规则或单规则
            if task.rules and len(task.rules) > 0:
                # 多规则模式
                logger.info(f"[{task.name}] Extracting content with {len(task.rules)} rules")
                
                all_content = []
                for i, rule in enumerate(task.rules):
                    rule_content = await _extract_content(html_content, rule)
                    if rule_content:
                        all_content.append(f"=== 规则 {i+1}: {rule} ===\n{rule_content}")
                        logger.info(f"[{task.name}] Rule {i+1} extracted {len(rule_content)} characters")
                    else:
                        logger.warning(f"[{task.name}] Rule {i+1} extracted no content: {rule}")
                        all_content.append(f"=== 规则 {i+1}: {rule} ===\n[无内容]")
                
                new_content = "\n\n".join(all_content)
                logger.info(f"[{task.name}] Combined content from {len(task.rules)} rules: {len(new_content)} characters")
            else:
                # 单规则模式（向后兼容）
                logger.info(f"[{task.name}] Extracting content with rule: {task.rule}")
                new_content = await _extract_content(html_content, task.rule)

            # Enhanced storage state checking
            old_content = storage.get_last_result(task.name)
            has_baseline = storage.has_baseline(task.name)

            logger.debug(f"[{task.name}] Storage state - has_baseline: {has_baseline}, old_content length: {len(old_content) if old_content else 0}")

            if old_content is None or not has_baseline:
                logger.info(f"[{task.name}] First run or missing baseline. Initializing baseline.")
                storage.save_result(task.name, new_content)
                return

            if new_content != old_content:
                logger.warning(f"[{task.name}] Change detected! Sending notification.")
                logger.debug(f"[{task.name}] Content comparison - Old: {len(old_content)} chars, New: {len(new_content)} chars")

                # 提取版本号用于调试
                def extract_version(content):
                    if "V15.1.1." in content:
                        import re
                        match = re.search(r'V15\.1\.1\.(\d+)', content)
                        if match:
                            return f"V15.1.1.{match.group(1)}"
                    return "未找到"

                old_version = extract_version(old_content)
                new_version = extract_version(new_content)
                logger.warning(f"[{task.name}] 🔍 Version comparison - Storage: {old_version}, Website: {new_version}")

                # Log first 200 characters of both contents for debugging
                old_preview = (old_content[:200] + '...') if len(old_content) > 200 else old_content
                new_preview = (new_content[:200] + '...') if len(new_content) > 200 else new_content
                logger.debug(f"[{task.name}] Old content preview: {old_preview}")
                logger.debug(f"[{task.name}] New content preview: {new_preview}")

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
                    "screenshot_path": screenshot_path or "未启用",
                    # 通用时间变量
                    "now": datetime.now,  # 时间函数，可用于 now().strftime('%Y-%m-%d')
                    "current_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "current_date": datetime.now().strftime('%Y-%m-%d'),
                    "timestamp": int(datetime.now().timestamp())
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
                            summary="",
                            extraction_rules=task.ai_extraction_rules,
                            formatter_code=""  # 临时对象不需要格式化代码
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

                    # 检查是否启用AI智能通知但没有自定义代码
                    if task.ai_analysis_enabled and not task.ai_formatter_code:
                        # AI智能通知启用但没有AI代码，跳过通知
                        logger.info(f"[{task.name}] AI notification enabled but no AI formatter code found, skipping notification")
                        return

                    # 优先使用AI生成的Python代码
                    if task.ai_analysis_enabled and task.ai_formatter_code:
                        try:
                            logger.info(f"[{task.name}] Using AI-generated Python formatter code")

                            # 准备AI代码需要的数据：只传递提取的字段数据，不包含通用模板变量
                            ai_extracted_data = {}
                            if task.ai_extraction_rules:
                                # 从template_context中提取AI字段数据
                                for field_name in task.ai_extraction_rules.keys():
                                    if field_name in template_context:
                                        ai_extracted_data[field_name] = template_context[field_name]
                                logger.info(f"[{task.name}] Prepared AI data with {len(ai_extracted_data)} fields: {list(ai_extracted_data.keys())}")
                            else:
                                logger.warning(f"[{task.name}] No AI extraction rules found, using empty data")

                            message = execute_notification_formatter(
                                task.ai_formatter_code,
                                ai_extracted_data,  # 使用纯净的AI提取字段数据
                                {
                                    "name": task.name,
                                    "url": str(task.url),
                                    "current_time": template_context.get("current_time", ""),
                                    "screenshot_url": screenshot_url,
                                    "screenshot_path": screenshot_path
                                }
                            )
                        except Exception as e:
                            logger.error(f"Error executing AI formatter code for task '{task.name}': {e}")
                            # AI代码执行失败，直接抛出异常，中断任务
                            raise e
                    else:
                        # 没有AI代码，不发送任何通知
                        logger.warning(f"[{task.name}] No AI formatter code available, skipping notification.")
                        message = "" # 确保消息为空

                    # 如果消息为空则不发送
                    if not message:
                        return

                    # 防重复通知检查
                    if not _should_send_notification(task.name, new_content):
                        logger.info(f"[{task.name}] Notification suppressed due to duplicate content")
                        return

                    # 发送通知
                    await notifier.send_notification(task, message, screenshot_path)

                    # 保存新内容到存储（这会覆盖任何手动修改）
                    logger.warning(f"[{task.name}] 🔄 About to save website content to storage, this will overwrite any manual changes")
                    storage.save_result(task.name, new_content)
                    logger.warning(f"[{task.name}] ✅ Storage updated with website content")
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


# Jinja2 template rendering removed - only using AI-generated Python code