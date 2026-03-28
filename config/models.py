from typing import Optional, Dict, Any
from pydantic import BaseModel
from config.settings import settings


class ModelConfig(BaseModel):
    base_url: str
    auth_header: str
    target_model: str
    max_tokens: int
    supports_stream: bool
    timeout: int = 60


MODEL_CONFIG: Dict[str, ModelConfig] = {
    "gpt-4o": ModelConfig(
        base_url="https://api.siliconflow.cn/v1",
        auth_header=f"Bearer {settings.silicon_api_key}",
        target_model="Qwen/Qwen2.5-72B-Instruct",
        max_tokens=4096,
        supports_stream=True
    ),
    "deepseek-r1": ModelConfig(
        base_url="https://api.deepseek.com/v1",
        auth_header=f"Bearer {settings.deepseek_api_key}",
        target_model="deepseek-reasoner",
        max_tokens=8192,
        supports_stream=True
    ),
    "glm-4": ModelConfig(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        auth_header=f"Bearer {settings.zhipu_api_key}",
        target_model="glm-4",
        max_tokens=8192,
        supports_stream=True
    ),
    "glm-4-flash": ModelConfig(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        auth_header=f"Bearer {settings.zhipu_api_key}",
        target_model="glm-4-flash",
        max_tokens=8192,
        supports_stream=True
    ),
    "local-qwen": ModelConfig(
        base_url="http://localhost:1234/v1",
        auth_header="",
        target_model="ignored",
        max_tokens=2048,
        supports_stream=True,
        timeout=300
    )
}


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    return MODEL_CONFIG.get(model_name)
