import logging
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict

from app.core.config import Notification, settings, save_config, get_config_path

logger = logging.getLogger(__name__)
router = APIRouter()

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