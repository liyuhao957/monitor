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

class ApiSettings(BaseModel):
    # DeepSeek 配置
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-reasoner"

    # OpenAI 配置
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.oaipro.com/v1"
    openai_model: str = "claude-sonnet-4-20250514"

    # 选择使用的 AI 服务提供商: "deepseek" 或 "openai"
    ai_provider: str = "openai"

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
    # notification_template removed - only using AI-generated Python code
    storage_strategy: str = "file"
    ai_analysis_enabled: bool = False
    ai_description: Optional[str] = None
    ai_extraction_rules: Optional[Dict[str, str]] = None  # AI生成的字段提取规则
    ai_formatter_code: Optional[str] = None  # AI生成的Python格式化代码

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
    api_settings: Optional[ApiSettings] = Field(default_factory=ApiSettings)
    default_notification: Notification = Field(default_factory=Notification)
    tasks: List[Task] = []
    # notification_presets removed - only using AI-generated Python code


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
        yaml.dump(config_data, f, allow_unicode=True, sort_keys=False, indent=2, width=float('inf'))

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
    
    # 修复配置路径问题：始终使用项目根目录的config.yaml
    # 无论从哪个目录运行，都能找到正确的配置文件
    current_file = Path(__file__).resolve()  # 获取绝对路径
    
    # 从当前文件向上查找，直到找到包含config.yaml的目录
    # config.py 位于 backend/app/core/config.py
    # 所以向上3级就是项目根目录
    project_root = current_file.parent.parent.parent.parent
    config_path = project_root / "config.yaml"
    
    # 如果根目录的config.yaml不存在，尝试backend目录
    if not config_path.exists():
        backend_config = current_file.parent.parent.parent / "config.yaml"
        if backend_config.exists():
            # 如果只有backend/config.yaml存在，使用它但发出警告
            print(f"警告：使用backend目录的config.yaml: {backend_config}")
            print(f"建议：将配置文件移动到项目根目录: {config_path}")
            return backend_config
    
    return config_path

# --- Global Settings Object ---

try:
    config_file_path = get_config_path()
    settings = load_config(config_file_path)
except FileNotFoundError as e:
    print(f"Error: {e}")
    # Create a default empty settings object to avoid crashing on import
    settings = Settings() 