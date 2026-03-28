from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
import httpx

from config.settings import settings
from config.models import get_model_config, MODEL_CONFIG
from services.proxy import forward_request

app = FastAPI(title="AI Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_key(authorization: Optional[str] = Header(None)) -> bool:
    if not authorization:
        return False
    if not authorization.startswith("Bearer "):
        return False
    api_key = authorization[7:]
    return api_key in settings.gateway_api_keys


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "available_models": list(MODEL_CONFIG.keys())
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: Request, authorization: Optional[str] = Header(None)):
    if not verify_api_key(authorization):
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
    
    try:
        result = await forward_request(payload, model_config, stream)
        
        if stream:
            return StreamingResponse(
                result,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            return JSONResponse(content=result)
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.gateway_host,
        port=settings.gateway_port,
        reload=True
    )
