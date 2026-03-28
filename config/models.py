from typing import Optional, Dict, Any
from pydantic import BaseModel
from config.persistence import load_config


class ModelConfig(BaseModel):
    base_url: str
    auth_header: str
    target_model: str
    max_tokens: int
    supports_stream: bool
    timeout: int = 60


def _init_model_config():
    config = load_config()
    model_configs = {}
    for name, model_data in config.get("models", {}).items():
        model_configs[name] = ModelConfig(**model_data)
    return model_configs


MODEL_CONFIG: Dict[str, ModelConfig] = _init_model_config()


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    return MODEL_CONFIG.get(model_name)
