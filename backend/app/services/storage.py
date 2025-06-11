import hashlib
import os
from pathlib import Path
from typing import Optional

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
    return STORAGE_DIR / f"{safe_filename}.txt"

def get_last_result(task_name: str) -> Optional[str]:
    """
    Retrieves the last saved result for a specific task.
    Returns the content as a string, or None if it doesn't exist.
    """
    storage_path = _get_storage_path(task_name)
    if not storage_path.exists():
        return None
    
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError:
        # Handle potential read errors
        return None

def save_result(task_name: str, content: str):
    """
    Saves the current result for a specific task to its storage file.
    """
    storage_path = _get_storage_path(task_name)
    try:
        with open(storage_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except IOError as e:
        # Handle potential write errors, e.g., by logging them
        print(f"Error saving result for task '{task_name}': {e}") 