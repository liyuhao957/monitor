import httpx
from typing import Optional
import logging
import mimetypes

from app.core.config import Task, Notification, settings

# Configure basic logging
logger = logging.getLogger(__name__)

async def _send_telegram_message(config: Notification, message: str, screenshot_path: Optional[str], task_name: str, custom_title: Optional[str] = None):
    """Sends a message and an optional photo to Telegram."""
    if not config.telegram.enabled or not config.telegram.bot_token or not config.telegram.chat_id:
        return

    bot_token = config.telegram.bot_token
    chat_id = config.telegram.chat_id
    
    # In monitor.py, the link is now part of the message. We should remove it for Telegram caption.
    message_for_telegram = message.split("\n\n---")[0]
    
    # Prepend title if available
    title = custom_title or f"{task_name} 内容变更"
    final_message = f"**{title}**\n\n{message_for_telegram}"

    async with httpx.AsyncClient() as client:
        try:
            # Send screenshot if available
            if screenshot_path:
                url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                with open(screenshot_path, 'rb') as f:
                    files = {'photo': f}
                    data = {'chat_id': chat_id, 'caption': final_message, 'parse_mode': 'Markdown'}
                    res = await client.post(url, files=files, data=data)
                    res.raise_for_status()
            else: # Send text message
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {'chat_id': chat_id, 'text': final_message, 'parse_mode': 'Markdown'}
                res = await client.post(url, json=payload)
                res.raise_for_status()

            logger.info(f"Successfully sent notification to Telegram for chat_id: {chat_id}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send Telegram notification. Status: {e.response.status_code}, Response: {e.response.text}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending Telegram notification: {e}")


async def _upload_feishu_image(image_path: str) -> Optional[str]:
    """Uploads an image to Feishu and returns the image_key."""
    upload_url = "https://open.feishu.cn/open-apis/im/v1/images"
    
    try:
        with open(image_path, 'rb') as f:
            image_content = f.read()
            
        file_name = image_path.split('/')[-1]
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        files = {
            'image': (file_name, image_content, mime_type)
        }
        form_data = {'image_type': 'message'}
        
        # We need a tenant_access_token to upload images. This is a complex topic.
        # For now, we will just log a warning that this part is not fully implemented.
        # A full implementation requires managing app_id/app_secret and token lifecycle.
        logger.warning("Feishu image upload requires tenant_access_token, which is not implemented. Skipping image upload.")
        # In a real app, you would get the token and make the request:
        # headers = {'Authorization': f'Bearer {tenant_access_token}'}
        # async with httpx.AsyncClient() as client:
        #     res = await client.post(upload_url, files=files, data=form_data, headers=headers)
        #     res.raise_for_status()
        #     data = res.json()
        #     if data.get("code") == 0:
        #         return data.get("data", {}).get("image_key")
        #     else:
        #         logging.error(f"Failed to upload image to Feishu: {data.get('msg')}")
        return None
    except Exception as e:
        logger.error(f"Error uploading image to Feishu: {e}")
        return None

async def _send_feishu_message(config: Notification, message: str, screenshot_path: Optional[str], task_name: str, custom_title: Optional[str] = None):
    """Sends a rich text message to Feishu, with an image if available."""
    if not config.feishu.enabled or not config.feishu.webhook:
        return

    webhook_url = str(config.feishu.webhook)
    
    # The message already contains the HTTP link, so we send it as is.
    card_elements = [{
        "tag": "div",
        "text": {
            "content": message,
            "tag": "lark_md"
        }
    }]
    
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {
                    "content": custom_title or "📈 网页监控告警",
                    "tag": "plain_text"
                }
            },
            "elements": card_elements
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(webhook_url, json=payload)
            res.raise_for_status()
            if res.json().get("StatusCode") != 0:
                 logger.error(f"Feishu API returned an error: {res.text}")
            else:
                logger.info(f"Successfully sent notification to Feishu.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send Feishu notification. Status: {e.response.status_code}, Response: {e.response.text}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending Feishu notification: {e}")


async def send_notification(task: Task, message: str, screenshot_path: Optional[str] = None):
    """
    Sends notifications based on the task's configuration, falling back to global settings.
    """
    # Use task-specific notification settings if they exist, otherwise use global default
    notification_config = task.notification or settings.default_notification

    # Send to Telegram
    if notification_config.telegram.enabled:
        await _send_telegram_message(notification_config, message, screenshot_path, task.name, task.notification_title)

    # Send to Feishu
    if notification_config.feishu.enabled:
        await _send_feishu_message(notification_config, message, screenshot_path, task.name, task.notification_title)