import redis
import asyncio
from typing import Optional
from config.settings import settings


QUOTA_DEDUCT_LUA = """
local key = KEYS[1]
local cost = tonumber(ARGV[1])
local balance = redis.call('GET', key)
if not balance then
    return 0
end
local balance_num = tonumber(balance)
if balance_num < cost then
    return 0
end
redis.call('DECRBY', key, cost)
return 1
"""


class QuotaService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )
        self.redis_client.ping()
    
    def get_quota_key(self, api_key: str, model: str) -> str:
        return f"quota:{api_key}:{model}"
    
    def get_quota(self, api_key: str, model: str) -> Optional[int]:
        key = self.get_quota_key(api_key, model)
        balance = self.redis_client.get(key)
        return int(balance) if balance is not None else None
    
    def set_quota(self, api_key: str, model: str, amount: int) -> None:
        key = self.get_quota_key(api_key, model)
        self.redis_client.set(key, amount)
    
    def deduct_quota(self, api_key: str, model: str, cost: int) -> bool:
        key = self.get_quota_key(api_key, model)
        result = self.redis_client.eval(
            QUOTA_DEDUCT_LUA,
            1,
            key,
            cost
        )
        return bool(result)
    
    def add_quota(self, api_key: str, model: str, amount: int) -> None:
        key = self.get_quota_key(api_key, model)
        self.redis_client.incrby(key, amount)


class AsyncQuotaService:
    def __init__(self, quota_service: QuotaService):
        self.quota_service = quota_service
        self.loop = asyncio.get_event_loop()
    
    async def get_quota(self, api_key: str, model: str) -> Optional[int]:
        return await self.loop.run_in_executor(
            None,
            self.quota_service.get_quota,
            api_key,
            model
        )
    
    async def set_quota(self, api_key: str, model: str, amount: int) -> None:
        await self.loop.run_in_executor(
            None,
            self.quota_service.set_quota,
            api_key,
            model,
            amount
        )
    
    async def deduct_quota(self, api_key: str, model: str, cost: int) -> bool:
        return await self.loop.run_in_executor(
            None,
            self.quota_service.deduct_quota,
            api_key,
            model,
            cost
        )
    
    async def add_quota(self, api_key: str, model: str, amount: int) -> None:
        await self.loop.run_in_executor(
            None,
            self.quota_service.add_quota,
            api_key,
            model,
            amount
        )


try:
    quota_service = QuotaService()
    async_quota_service = AsyncQuotaService(quota_service)
except Exception as e:
    print(f"Warning: Redis connection failed, quota service disabled: {e}")
    quota_service = None
    async_quota_service = None
