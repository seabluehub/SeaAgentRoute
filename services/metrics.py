from prometheus_client import Counter, Histogram, Gauge, Summary
from prometheus_client.exposition import generate_latest
from typing import Optional

# 请求计数指标
REQUEST_COUNT = Counter(
    'ai_gateway_requests_total',
    'Total number of requests',
    ['model', 'api_key', 'status', 'method']
)

# 响应时间直方图
REQUEST_LATENCY = Histogram(
    'ai_gateway_request_duration_seconds',
    'Request latency in seconds',
    ['model', 'status']
)

# 上游响应时间直方图
UPSTREAM_LATENCY = Histogram(
    'ai_gateway_upstream_duration_seconds',
    'Upstream request latency in seconds',
    ['model']
)

# 错误计数
ERROR_COUNT = Counter(
    'ai_gateway_errors_total',
    'Total number of errors',
    ['model', 'error_type']
)

# 配额使用情况
QUOTA_USAGE = Gauge(
    'ai_gateway_quota_usage',
    'Quota usage for API keys',
    ['api_key', 'model']
)

# 活跃请求数
ACTIVE_REQUESTS = Gauge(
    'ai_gateway_active_requests',
    'Number of active requests',
    ['model']
)

# 模型健康状态
MODEL_HEALTH = Gauge(
    'ai_gateway_model_health',
    'Model health status (1=healthy, 0=unhealthy)',
    ['model']
)

# 内存使用情况
MEMORY_USAGE = Gauge(
    'ai_gateway_memory_usage_bytes',
    'Memory usage in bytes'
)


class MetricsService:
    def __init__(self):
        pass
    
    def increment_request_count(self, model: str, api_key: str, status: int, method: str):
        """增加请求计数"""
        REQUEST_COUNT.labels(
            model=model,
            api_key=api_key[:8] + '****' if len(api_key) > 8 else '****',
            status=str(status),
            method=method
        ).inc()
    
    def observe_request_latency(self, model: str, status: int, latency_seconds: float):
        """观察请求延迟"""
        REQUEST_LATENCY.labels(
            model=model,
            status=str(status)
        ).observe(latency_seconds)
    
    def observe_upstream_latency(self, model: str, latency_seconds: float):
        """观察上游延迟"""
        UPSTREAM_LATENCY.labels(model=model).observe(latency_seconds)
    
    def increment_error_count(self, model: str, error_type: str):
        """增加错误计数"""
        ERROR_COUNT.labels(model=model, error_type=error_type).inc()
    
    def set_quota_usage(self, api_key: str, model: str, usage: int):
        """设置配额使用情况"""
        QUOTA_USAGE.labels(
            api_key=api_key[:8] + '****' if len(api_key) > 8 else '****',
            model=model
        ).set(usage)
    
    def set_model_health(self, model: str, healthy: bool):
        """设置模型健康状态"""
        MODEL_HEALTH.labels(model=model).set(1 if healthy else 0)
    
    def inc_active_requests(self, model: str):
        """增加活跃请求数"""
        ACTIVE_REQUESTS.labels(model=model).inc()
    
    def dec_active_requests(self, model: str):
        """减少活跃请求数"""
        ACTIVE_REQUESTS.labels(model=model).dec()
    
    def set_memory_usage(self, usage: int):
        """设置内存使用情况"""
        MEMORY_USAGE.set(usage)
    
    def generate_metrics(self):
        """生成指标数据"""
        return generate_latest()


metrics_service = MetricsService()