import hashlib
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Define the base directory for storage relative to this file's location
STORAGE_DIR = Path(__file__).parent.parent.parent / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

def _get_storage_path(task_name: str) -> Path:
    """
    Generates a safe and unique file path for a given task name.
    Uses a SHA256 hash to create a consistent, filesystem-safe filename.
    """
    # Hash the task name to create a unique and safe filename
    safe_filename = hashlib.sha256(task_name.encode('utf-8')).hexdigest()
    storage_path = STORAGE_DIR / f"{safe_filename}.txt"
    logger.debug(f"Storage path for task '{task_name}': {storage_path}")
    return storage_path

def get_last_result(task_name: str) -> Optional[str]:
    """
    Retrieves the last saved result for a specific task.
    Returns the content as a string, or None if it doesn't exist.
    """
    storage_path = _get_storage_path(task_name)
    logger.debug(f"[{task_name}] Checking storage file: {storage_path}")

    if not storage_path.exists():
        logger.debug(f"[{task_name}] Storage file does not exist")
        return None

    try:
        # 获取文件修改时间
        import os
        from datetime import datetime
        mod_time = datetime.fromtimestamp(os.path.getmtime(storage_path))

        with open(storage_path, 'r', encoding='utf-8') as f:
            content = f.read()

            # 计算内容哈希用于追踪
            import hashlib
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]

            # 提取版本号用于调试
            version_match = None
            if "V15.1.1." in content:
                import re
                match = re.search(r'V15\.1\.1\.(\d+)', content)
                if match:
                    version_match = f"V15.1.1.{match.group(1)}"

            logger.info(f"[{task_name}] 📖 READ storage - Size: {len(content)}, Hash: {content_hash}, Modified: {mod_time.strftime('%H:%M:%S')}, Version: {version_match}")
            return content
    except IOError as e:
        # Handle potential read errors
        logger.error(f"[{task_name}] Error reading storage file: {e}")
        return None

def save_result(task_name: str, content: str):
    """
    Saves the current result for a specific task to its storage file.
    """
    storage_path = _get_storage_path(task_name)
    try:
        # 计算内容哈希用于追踪
        import hashlib
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]

        # 提取版本号用于调试
        version_match = None
        if "V15.1.1." in content:
            import re
            match = re.search(r'V15\.1\.1\.(\d+)', content)
            if match:
                version_match = f"V15.1.1.{match.group(1)}"

        # 记录写入前的状态
        old_exists = storage_path.exists()
        old_version = None
        if old_exists:
            try:
                with open(storage_path, 'r', encoding='utf-8') as f:
                    old_content = f.read()
                    if "V15.1.1." in old_content:
                        old_match = re.search(r'V15\.1\.1\.(\d+)', old_content)
                        if old_match:
                            old_version = f"V15.1.1.{old_match.group(1)}"
            except:
                pass

        with open(storage_path, 'w', encoding='utf-8') as f:
            f.write(content)

        from datetime import datetime
        current_time = datetime.now().strftime('%H:%M:%S')

        logger.warning(f"[{task_name}] 💾 SAVE storage - Size: {len(content)}, Hash: {content_hash}, Time: {current_time}, Old Version: {old_version} → New Version: {version_match}")

    except IOError as e:
        # Handle potential write errors
        logger.error(f"[{task_name}] Error saving result to storage: {e}")

def has_baseline(task_name: str) -> bool:
    """
    Checks if a baseline exists for the given task.
    This is a more explicit way to check for first run status.
    """
    storage_path = _get_storage_path(task_name)
    exists = storage_path.exists() and storage_path.stat().st_size > 0
    logger.debug(f"[{task_name}] Baseline exists: {exists}")
    return exists