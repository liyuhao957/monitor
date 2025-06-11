import os
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml
import json
from pydantic import BaseModel, Field, HttpUrl, TypeAdapter

# --- Pydantic Models for Configuration ---

class TelegramNotification(BaseModel):
    enabled: bool = False
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None

class FeishuNotification(BaseModel):
    enabled: bool = False
    webhook: Optional[HttpUrl] = None

class Notification(BaseModel):
    enabled: bool = True
    telegram: TelegramNotification = TelegramNotification()
    feishu: FeishuNotification = FeishuNotification()

class Task(BaseModel):
    name: str
    url: HttpUrl
    frequency: str
    rule: str
    enabled: bool = True
    screenshot: bool = False
    notification_title: Optional[str] = None
    notification: Optional[Notification] = None
    notification_template: Optional[str] = None
    storage_strategy: str = "file"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Task 1",
                    "url": "https://example.com/task1",
                    "cron": "* * * * *",
                    "rules": ["rule1", "rule2"],
                    "enabled": True,
                    "screenshot": False,
                    "notifications": []
                },
                {
                    "name": "Task 2",
                    "url": "https://example.com/task2",
                    "cron": "* * * * *",
                    "rules": ["rule3"],
                    "enabled": True,
                    "screenshot": True,
                    "notifications": []
                }
            ]
        }
    }

class Settings(BaseModel):
    default_notification: Notification = Field(default_factory=Notification)
    tasks: List[Task] = []
    notification_presets: Optional[Dict[str, str]] = None


# --- Configuration Loading and Saving Logic ---

def save_config(settings_obj: Settings, config_path: Path):
    """Saves the settings object back to a YAML file."""
    # Pydantic v2 recommends using model_dump_json then loading it back
    # to ensure all custom types are correctly serialized to basic types.
    # We then dump this pure dictionary to YAML.
    # https://docs.pydantic.dev/latest/concepts/serialization/#json
    
    # Step 1: Serialize the Pydantic model to a JSON string.
    # This correctly handles types like HttpUrl, converting them to strings.
    json_str = settings_obj.model_dump_json(indent=2)
    
    # Step 2: Parse the JSON string back into a standard Python dictionary.
    config_data = json.loads(json_str)
    
    # Step 3: Dump the clean Python dictionary to the YAML file.
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, allow_unicode=True, sort_keys=False, indent=2)

def load_config(config_path: Path) -> Settings:
    """Loads configuration from a YAML file and validates it with Pydantic."""
    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    return Settings(**config_data)

def get_config_path() -> Path:
    """
    Determines the configuration file path.
    Priority:
    1. MONITOR_CONFIG environment variable
    2. `config.yaml` in the project root
    """
    if config_env_path := os.getenv("MONITOR_CONFIG"):
        return Path(config_env_path)
    
    # Assumes the script is run from the project root
    project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "config.yaml"

# --- Global Settings Object ---

try:
    config_file_path = get_config_path()
    settings = load_config(config_file_path)
except FileNotFoundError as e:
    print(f"Error: {e}")
    # Create a default empty settings object to avoid crashing on import
    settings = Settings() 