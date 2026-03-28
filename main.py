from fastapi import FastAPI, Request, HTTPException, Header, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, AsyncGenerator
import httpx
import time
import uuid

from config.settings import settings
from config.models import get_model_config, MODEL_CONFIG
from services.proxy import forward_request
from services.auth import auth_service
from services.quota import async_quota_service
from services.logger import async_logger_service

app = FastAPI(title="AI Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    redis_status = "connected" if (async_quota_service and async_logger_service.logger_service.enabled) else "disconnected"
    return {
        "status": "ok",
        "version": "1.0.0",
        "redis_status": redis_status,
        "available_models": list(MODEL_CONFIG.keys())
    }


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
        
        latency_ms = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, True, None, latency_ms
        )
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
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
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    model_name = payload.get("model")
    if not model_name:
        raise HTTPException(status_code=400, detail="Model parameter is required")
    
    model_config = get_model_config(model_name)
    if not model_config:
        raise HTTPException(status_code=400, detail=f"Unknown model: {model_name}")
    
    stream = payload.get("stream", False)
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
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
            latency_ms = (time.time() - start_time) * 1000
            background_tasks.add_task(
                log_and_deduct,
                api_key, model_name, payload, request_id,
                result, True, None, latency_ms
            )
            response = JSONResponse(content=result)
            response.headers["X-Request-ID"] = request_id
            return response
    
    except httpx.HTTPStatusError as e:
        latency_ms = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, False, str(e), latency_ms
        )
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.TimeoutException:
        latency_ms = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, False, "Request timeout", latency_ms
        )
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.RequestError as e:
        latency_ms = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, False, f"Upstream error: {str(e)}", latency_ms
        )
        raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        background_tasks.add_task(
            log_and_deduct,
            api_key, model_name, payload, request_id,
            None, False, f"Internal server error: {str(e)}", latency_ms
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.gateway_host,
        port=settings.gateway_port,
        reload=True
    )
