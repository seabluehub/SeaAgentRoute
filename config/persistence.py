import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from config.settings import settings

DATA_DIR = Path(__file__).parent.parent / "data"
CONFIG_FILE = DATA_DIR / "gateway_config.json"


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Dict[str, Any]:
    ensure_data_dir()
    if not CONFIG_FILE.exists():
        return get_default_config()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return get_default_config()


def save_config(config: Dict[str, Any]) -> bool:
    ensure_data_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_default_config() -> Dict[str, Any]:
    return {
        "api_keys": settings.gateway_api_keys,
        "models": {
            "gpt-4o": {
                "base_url": "https://api.siliconflow.cn/v1",
                "auth_header": f"Bearer {settings.silicon_api_key}",
                "target_model": "Qwen/Qwen2.5-72B-Instruct",
                "max_tokens": 4096,
                "supports_stream": True,
                "timeout": 60
            },
            "deepseek-r1": {
                "base_url": "https://api.deepseek.com/v1",
                "auth_header": f"Bearer {settings.deepseek_api_key}",
                "target_model": "deepseek-reasoner",
                "max_tokens": 8192,
                "supports_stream": True,
                "timeout": 60
            },
            "glm-4": {
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
                "auth_header": f"Bearer {settings.zhipu_api_key}",
                "target_model": "glm-4",
                "max_tokens": 8192,
                "supports_stream": True,
                "timeout": 60
            },
            "glm-4-flash": {
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
                "auth_header": f"Bearer {settings.zhipu_api_key}",
                "target_model": "glm-4-flash",
                "max_tokens": 8192,
                "supports_stream": True,
                "timeout": 60
            },
            "local-qwen": {
                "base_url": "http://localhost:1234/v1",
                "auth_header": "",
                "target_model": "ignored",
                "max_tokens": 2048,
                "supports_stream": True,
                "timeout": 300
            }
        }
    }


def get_model_configs() -> Dict[str, Any]:
    config = load_config()
    return config.get("models", {})


def save_model_configs(model_configs: Dict[str, Any]) -> bool:
    config = load_config()
    config["models"] = model_configs
    return save_config(config)


def get_api_keys() -> List[str]:
    config = load_config()
    return config.get("api_keys", [])


def save_api_keys(api_keys: List[str]) -> bool:
    config = load_config()
    config["api_keys"] = api_keys
    return save_config(config)


def update_runtime_config():
    from config import models as config_models
    from config.models import ModelConfig
    config = load_config()
    new_model_configs = {}
    for name, model_data in config.get("models", {}).items():
        new_model_configs[name] = ModelConfig(**model_data)
    config_models.MODEL_CONFIG = new_model_configs
