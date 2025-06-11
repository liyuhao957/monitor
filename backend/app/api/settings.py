import logging
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
from pydantic import BaseModel

from app.core.config import Notification, settings, save_config, get_config_path

logger = logging.getLogger(__name__)
router = APIRouter()


class RuleInfo(BaseModel):
    id: str
    name: str
    description: str
    example: str
    needs_value: bool


@router.get("/rules", response_model=List[RuleInfo])
def get_extraction_rules():
    """Retrieve all available content extraction rules."""
    return [
        RuleInfo(
            id="css",
            name="CSS Selector",
            description="通过 CSS 选择器定位元素。这是最常用和最稳定的方式。",
            example="例如: h1.main-title 或 #product .price",
            needs_value=True
        ),
        RuleInfo(
            id="xpath",
            name="XPath",
            description="通过 XPath 表达式定位元素。功能强大，可以处理复杂的 HTML 结构。",
            example="例如: //div[@id='content']/p",
            needs_value=True
        ),
        RuleInfo(
            id="regex",
            name="Regex",
            description="通过正则表达式从原始 HTML 源码中提取内容。灵活但容易因页面结构改变而失效。",
            example='例如: "price":\\s*(\\d+\\.\\d{2})',
            needs_value=True
        ),
        RuleInfo(
            id="full_text",
            name="Full Text",
            description="提取整个页面去除 HTML 标签后的所有文本。当您关心任何文本变化时使用。",
            example="此模式无需填写规则值。",
            needs_value=False
        ),
    ]


@router.get("/notifications", response_model=Notification)
def get_notification_settings():
    """Retrieve the default notification settings."""
    return settings.default_notification

@router.put("/notifications", response_model=Notification)
def update_notification_settings(notification_config: Notification):
    """Update the default notification settings."""
    try:
        settings.default_notification = notification_config
        save_config(settings, get_config_path())
        logger.info("Successfully updated default notification settings.")
        return settings.default_notification
    except Exception as e:
        logger.error(f"Failed to save or apply notification settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save or apply settings.")

@router.get("/notifications/presets", response_model=Dict[str, str])
def get_notification_presets():
    """Retrieve all available notification template presets as a dict."""
    return settings.notification_presets or {} 