import redis
import asyncio
import json
import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from config.settings import settings

# 配置 structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class LoggerService:
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True
            )
            self.redis_client.ping()
            self.enabled = True
        except Exception as e:
            logger.warning("Redis connection failed, logger disabled", error=str(e))
            self.redis_client = None
            self.enabled = False
    
    def _mask_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        masked = data.copy()
        if "Authorization" in masked:
            masked["Authorization"] = "Bearer ****"
        if "api_key" in masked:
            masked["api_key"] = "****"
        return masked
    
    def log_request(
        self,
        api_key: str,
        model: str,
        request_payload: Dict[str, Any],
        request_id: str
    ) -> None:
        # 结构化日志
        logger.info(
            "Request received",
            request_id=request_id,
            api_key=api_key[:8] + "****" if len(api_key) > 8 else "****",
            model=model,
            payload=self._mask_sensitive(request_payload)
        )
        
        # Redis 日志
        if not self.enabled:
            return
        try:
            log_entry = {
                "type": "request",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "api_key": api_key[:8] + "****" if len(api_key) > 8 else "****",
                "model": model,
                "payload": self._mask_sensitive(request_payload)
            }
            self.redis_client.rpush("logs:requests", json.dumps(log_entry))
            self.redis_client.ltrim("logs:requests", -10000, -1)
        except Exception as e:
            logger.error("Error logging request to Redis", error=str(e))
    
    def log_response(
        self,
        api_key: str,
        model: str,
        response_payload: Optional[Dict[str, Any]],
        request_id: str,
        success: bool = True,
        error: Optional[str] = None,
        latency_ms: float = 0.0
    ) -> None:
        # 结构化日志
        logger.info(
            "Response sent",
            request_id=request_id,
            api_key=api_key[:8] + "****" if len(api_key) > 8 else "****",
            model=model,
            success=success,
            error=error,
            latency_ms=latency_ms,
            usage=response_payload.get("usage") if response_payload else None
        )
        
        # Redis 日志
        if not self.enabled:
            return
        try:
            log_entry = {
                "type": "response",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "api_key": api_key[:8] + "****" if len(api_key) > 8 else "****",
                "model": model,
                "success": success,
                "error": error,
                "latency_ms": latency_ms,
                "usage": response_payload.get("usage") if response_payload else None
            }
            self.redis_client.rpush("logs:responses", json.dumps(log_entry))
            self.redis_client.ltrim("logs:responses", -10000, -1)
        except Exception as e:
            logger.error("Error logging response to Redis", error=str(e))


class AsyncLoggerService:
    def __init__(self, logger_service: LoggerService):
        self.logger_service = logger_service
        self.loop = asyncio.get_event_loop()
    
    async def log_request(
        self,
        api_key: str,
        model: str,
        request_payload: Dict[str, Any],
        request_id: str
    ) -> None:
        await self.loop.run_in_executor(
            None,
            self.logger_service.log_request,
            api_key,
            model,
            request_payload,
            request_id
        )
    
    async def log_response(
        self,
        api_key: str,
        model: str,
        response_payload: Optional[Dict[str, Any]],
        request_id: str,
        success: bool = True,
        error: Optional[str] = None,
        latency_ms: float = 0.0
    ) -> None:
        await self.loop.run_in_executor(
            None,
            self.logger_service.log_response,
            api_key,
            model,
            response_payload,
            request_id,
            success,
            error,
            latency_ms
        )


logger_service = LoggerService()
async_logger_service = AsyncLoggerService(logger_service)
