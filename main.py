from fastapi import FastAPI, Request, HTTPException, Header, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, AsyncGenerator
from pathlib import Path
import httpx
import time
import uuid
import psutil

from config.settings import settings
from config.models import get_model_config, MODEL_CONFIG
from services.proxy import forward_request
from services.auth import auth_service
from services.quota import async_quota_service
from services.logger import async_logger_service
from services.admin import router as admin_router
from services.health import health_service
from services.metrics import metrics_service

app = FastAPI(title="AI Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(admin_router)


@app.get("/admin")
async def admin_page():
    admin_html = TEMPLATES_DIR / "admin.html"
    if admin_html.exists():
        return FileResponse(str(admin_html))
    raise HTTPException(status_code=404, detail="Admin page not found")


@app.get("/health")
async def health_check():
    redis_status = "connected" if (async_quota_service and async_logger_service and async_logger_service.logger_service.enabled) else "disconnected"
    
    # 检查所有模型的健康状态
    models_health = await health_service.check_all_models_health()
    
    # 统计健康模型数量
    healthy_count = sum(1 for status in models_health.values() if status.get('status') == 'healthy')
    total_count = len(models_health)
    
    return {
        "status": "ok",
        "version": "1.0.0",
        "redis_status": redis_status,
        "available_models": list(MODEL_CONFIG.keys()),
        "models_health": models_health,
        "health_summary": {
            "healthy": healthy_count,
            "total": total_count,
            "status": "healthy" if healthy_count == total_count else "degraded" if healthy_count > 0 else "unhealthy"
        }
    }


@app.get("/health/models/{model_name}")
async def check_model_health(model_name: str):
    """检查指定模型的健康状态"""
    health_status = await health_service.check_model_health(model_name)
    # 更新模型健康状态指标
    healthy = health_status.get('status') == 'healthy'
    metrics_service.set_model_health(model_name, healthy)
    return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus 指标端点"""
    # 更新内存使用指标
    process = psutil.Process()
    memory_usage = process.memory_info().rss
    metrics_service.set_memory_usage(memory_usage)
    
    # 生成并返回指标
    metrics_data = metrics_service.generate_metrics()
    return Response(content=metrics_data, media_type="text/plain")


async def log_and_deduct(
    api_key: str,
    model_name: str,
    payload: Dict[str, Any],
    request_id: str,
    response_payload: Optional[Dict[str, Any]],
    success: bool,
    error: Optional[str],
    latency_ms: float
):
    await async_logger_service.log_request(api_key, model_name, payload, request_id)
    await async_logger_service.log_response(
        api_key, model_name, response_payload, request_id, success, error, latency_ms
    )
    if success and response_payload and async_quota_service:
        usage = response_payload.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)
        if total_tokens > 0:
            await async_quota_service.deduct_quota(api_key, model_name, total_tokens)


async def stream_wrapper(
    generator: AsyncGenerator[bytes, None],
    background_tasks: BackgroundTasks,
    api_key: str,
    model_name: str,
    payload: Dict[str, Any],
    request_id: str,
    start_time: float
):
    try:
        async for chunk in generator:
            yield chunk
        
        latency_seconds = time.time() - start_time
        latency_ms = latency_seconds * 1000
        
        # 记录指标
        metrics_service.increment_request_count(model_name, api_key, 200, "POST")
        metrics_service.observe_request_latency(model_name, 200, latency_seconds)
        
        # 减少活跃请求数
        metrics_service.dec_active_requests(model_name)
        
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, True, None, latency_ms
        )
    except Exception as e:
        latency_seconds = time.time() - start_time
        latency_ms = latency_seconds * 1000
        
        # 记录指标
        metrics_service.increment_request_count(model_name, api_key, 500, "POST")
        metrics_service.observe_request_latency(model_name, 500, latency_seconds)
        metrics_service.increment_error_count(model_name, "stream_error")
        
        # 减少活跃请求数
        metrics_service.dec_active_requests(model_name)
        
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, False, str(e), latency_ms
        )
        raise


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    is_valid, api_key = auth_service.verify_api_key(authorization)
    if not is_valid:
        metrics_service.increment_request_count("unknown", "unknown", 401, "POST")
        metrics_service.increment_error_count("unknown", "unauthorized")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        payload = await request.json()
    except Exception:
        metrics_service.increment_request_count("unknown", api_key, 400, "POST")
        metrics_service.increment_error_count("unknown", "invalid_json")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    model_name = payload.get("model")
    if not model_name:
        metrics_service.increment_request_count("unknown", api_key, 400, "POST")
        metrics_service.increment_error_count("unknown", "missing_model")
        raise HTTPException(status_code=400, detail="Model parameter is required")
    
    model_config = get_model_config(model_name)
    if not model_config:
        metrics_service.increment_request_count(model_name, api_key, 400, "POST")
        metrics_service.increment_error_count(model_name, "unknown_model")
        raise HTTPException(status_code=400, detail=f"Unknown model: {model_name}")
    
    stream = payload.get("stream", False)
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # 增加活跃请求数
    metrics_service.inc_active_requests(model_name)
    
    try:
        result = await forward_request(payload, model_config, stream)
        
        if stream:
            return StreamingResponse(
                stream_wrapper(
                    result, background_tasks, api_key, model_name, payload, request_id, start_time
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "X-Request-ID": request_id
                }
            )
        else:
            latency_seconds = time.time() - start_time
            latency_ms = latency_seconds * 1000
            
            # 记录指标
            metrics_service.increment_request_count(model_name, api_key, 200, "POST")
            metrics_service.observe_request_latency(model_name, 200, latency_seconds)
            
            background_tasks.add_task(
                log_and_deduct,
                api_key, model_name, payload, request_id,
                result, True, None, latency_ms
            )
            
            # 减少活跃请求数
            metrics_service.dec_active_requests(model_name)
            
            response = JSONResponse(content=result)
            response.headers["X-Request-ID"] = request_id
            return response
    
    except httpx.HTTPStatusError as e:
        latency_seconds = time.time() - start_time
        latency_ms = latency_seconds * 1000
        
        # 记录指标
        metrics_service.increment_request_count(model_name, api_key, e.response.status_code, "POST")
        metrics_service.observe_request_latency(model_name, e.response.status_code, latency_seconds)
        metrics_service.increment_error_count(model_name, "http_status_error")
        
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, False, str(e), latency_ms
        )
        
        # 减少活跃请求数
        metrics_service.dec_active_requests(model_name)
        
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.TimeoutException:
        latency_seconds = time.time() - start_time
        latency_ms = latency_seconds * 1000
        
        # 记录指标
        metrics_service.increment_request_count(model_name, api_key, 504, "POST")
        metrics_service.observe_request_latency(model_name, 504, latency_seconds)
        metrics_service.increment_error_count(model_name, "timeout")
        
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, False, "Request timeout", latency_ms
        )
        
        # 减少活跃请求数
        metrics_service.dec_active_requests(model_name)
        
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.RequestError as e:
        latency_seconds = time.time() - start_time
        latency_ms = latency_seconds * 1000
        
        # 记录指标
        metrics_service.increment_request_count(model_name, api_key, 502, "POST")
        metrics_service.observe_request_latency(model_name, 502, latency_seconds)
        metrics_service.increment_error_count(model_name, "upstream_error")
        
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, False, f"Upstream error: {str(e)}", latency_ms
        )
        
        # 减少活跃请求数
        metrics_service.dec_active_requests(model_name)
        
        raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")
    except Exception as e:
        latency_seconds = time.time() - start_time
        latency_ms = latency_seconds * 1000
        
        # 记录指标
        metrics_service.increment_request_count(model_name, api_key, 500, "POST")
        metrics_service.observe_request_latency(model_name, 500, latency_seconds)
        metrics_service.increment_error_count(model_name, "internal_error")
        
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, False, f"Internal server error: {str(e)}", latency_ms
        )
        
        # 减少活跃请求数
        metrics_service.dec_active_requests(model_name)
        
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.gateway_host,
        port=settings.gateway_port,
        reload=True
    )
