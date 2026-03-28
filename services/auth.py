from typing import Optional, Tuple
from config.settings import settings


class AuthService:
    def __init__(self):
        self.valid_api_keys = set(settings.gateway_api_keys)
    
    def verify_api_key(self, authorization: Optional[str]) -> Tuple[bool, Optional[str]]:
        if not authorization:
            return False, None
        if not authorization.startswith("Bearer "):
            return False, None
        
        api_key = authorization[7:].strip()
        if api_key in self.valid_api_keys:
            return True, api_key
        return False, None
    
    def add_api_key(self, api_key: str) -> None:
        self.valid_api_keys.add(api_key)
    
    def remove_api_key(self, api_key: str) -> bool:
        if api_key in self.valid_api_keys:
            self.valid_api_keys.remove(api_key)
            return True
        return False


auth_service = AuthService()
