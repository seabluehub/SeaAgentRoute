import httpx
import asyncio
from typing import Dict, Any, Optional
from config.models import get_model_config, MODEL_CONFIG
from datetime import datetime, timedelta


class HealthService:
    def __init__(self):
        self._health_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timeout = 60  # 缓存60秒
        self._client = httpx.AsyncClient(timeout=10)
    
    async def check_model_health(self, model_name: str) -> Dict[str, Any]:
        """检查指定模型的健康状态"""
        # 检查缓存
        if model_name in self._health_cache:
            cached_data = self._health_cache[model_name]
            cached_time = cached_data.get('timestamp')
            if cached_time and (datetime.now() - cached_time).total_seconds() < self._cache_timeout:
                return cached_data
        
        model_config = get_model_config(model_name)
        if not model_config:
            result = {
                'status': 'error',
                'message': f'Model {model_name} not found',
                'timestamp': datetime.now()
            }
        else:
            try:
                # 构建健康检查URL
                health_url = f"{model_config.base_url}/health" if model_config.base_url.endswith('/v1') else f"{model_config.base_url}/v1/health"
                
                headers = {}
                if model_config.auth_header:
                    headers["Authorization"] = model_config.auth_header
                
                # 发送健康检查请求
                response = await self._client.get(health_url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    result = {
                        'status': 'healthy',
                        'model': model_name,
                        'base_url': model_config.base_url,
                        'response_time': response.elapsed.total_seconds() * 1000,
                        'timestamp': datetime.now()
                    }
                else:
                    result = {
                        'status': 'unhealthy',
                        'model': model_name,
                        'base_url': model_config.base_url,
                        'status_code': response.status_code,
                        'message': response.text[:100],
                        'timestamp': datetime.now()
                    }
            except Exception as e:
                result = {
                    'status': 'unhealthy',
                    'model': model_name,
                    'base_url': model_config.base_url,
                    'message': str(e)[:100],
                    'timestamp': datetime.now()
                }
        
        # 更新缓存
        self._health_cache[model_name] = result
        return result
    
    async def check_all_models_health(self) -> Dict[str, Dict[str, Any]]:
        """检查所有模型的健康状态"""
        tasks = [self.check_model_health(model_name) for model_name in MODEL_CONFIG.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_status = {}
        for model_name, result in zip(MODEL_CONFIG.keys(), results):
            if isinstance(result, Exception):
                health_status[model_name] = {
                    'status': 'error',
                    'message': str(result)[:100],
                    'timestamp': datetime.now()
                }
            else:
                health_status[model_name] = result
        
        return health_status
    
    async def close(self):
        """关闭HTTP客户端"""
        await self._client.aclose()


# 全局健康检查服务实例
health_service = HealthService()


async def get_health_service() -> HealthService:
    """获取健康检查服务实例"""
    return health_service
