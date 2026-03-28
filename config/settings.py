import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.silicon_api_key: str = os.getenv("SILICON_API_KEY", "")
        self.deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
        self.zhipu_api_key: str = os.getenv("ZHIPU_API_KEY", "")
        
        self.redis_host: str = os.getenv("REDIS_HOST", "localhost")
        self.redis_port: int = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db: int = int(os.getenv("REDIS_DB", 0))
        self.redis_password: Optional[str] = os.getenv("REDIS_PASSWORD", None)
        
        self.gateway_api_keys: List[str] = os.getenv("GATEWAY_API_KEYS", "test-key-123").split(",")
        self.gateway_host: str = os.getenv("GATEWAY_HOST", "0.0.0.0")
        self.gateway_port: int = int(os.getenv("GATEWAY_PORT", 8000))


settings = Settings()
