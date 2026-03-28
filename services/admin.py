from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from config.models import ModelConfig, MODEL_CONFIG
from config.persistence import (
    load_config,
    save_config,
    save_model_configs,
    save_api_keys,
    update_runtime_config
)
from services.auth import auth_service
from services.quota import async_quota_service

router = APIRouter(prefix="/admin/api", tags=["admin"])


class ModelConfigUpdate(BaseModel):
    base_url: str
    auth_header: str
    target_model: str
    max_tokens: int
    supports_stream: bool
    timeout: int = 60


@router.get("/config")
async def get_config():
    config = load_config()
    return {
        "success": True,
        "data": config
    }


@router.post("/config")
async def update_config(config: Dict[str, Any]):
    try:
        if save_config(config):
            update_runtime_config()
            auth_service.reload_api_keys()
            return {"success": True, "message": "Config updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save config")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models")
async def get_models():
    return {
        "success": True,
        "data": {name: model.model_dump() for name, model in MODEL_CONFIG.items()}
    }


@router.get("/models/{model_name}")
async def get_model(model_name: str):
    model = MODEL_CONFIG.get(model_name)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "success": True,
        "data": model.model_dump()
    }


@router.post("/models/{model_name}")
async def create_or_update_model(model_name: str, model_config: ModelConfigUpdate):
    try:
        config = load_config()
        models_dict = config.get("models", {})
        models_dict[model_name] = model_config.model_dump()
        config["models"] = models_dict
        if save_config(config):
            update_runtime_config()
            return {"success": True, "message": f"Model {model_name} updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save model config")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/models/{model_name}")
async def delete_model(model_name: str):
    if model_name not in MODEL_CONFIG:
        raise HTTPException(status_code=404, detail="Model not found")
    try:
        config = load_config()
        models_dict = config.get("models", {})
        if model_name in models_dict:
            del models_dict[model_name]
        config["models"] = models_dict
        if save_config(config):
            update_runtime_config()
            return {"success": True, "message": f"Model {model_name} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save model config")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api-keys")
async def get_api_keys():
    return {
        "success": True,
        "data": list(auth_service.valid_api_keys)
    }


@router.post("/api-keys")
async def add_api_key(api_key: str):
    try:
        keys = list(auth_service.valid_api_keys)
        if api_key not in keys:
            keys.append(api_key)
            if save_api_keys(keys):
                auth_service.reload_api_keys()
                return {"success": True, "message": "API key added successfully"}
        return {"success": True, "message": "API key already exists"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api-keys/{api_key}")
async def remove_api_key(api_key: str):
    try:
        keys = list(auth_service.valid_api_keys)
        if api_key in keys:
            keys.remove(api_key)
            if save_api_keys(keys):
                auth_service.reload_api_keys()
                return {"success": True, "message": "API key removed successfully"}
        raise HTTPException(status_code=404, detail="API key not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quota")
async def get_all_quota():
    """获取所有配额信息"""
    if not async_quota_service:
        raise HTTPException(status_code=503, detail="Quota service not available")
    
    try:
        api_keys = list(auth_service.valid_api_keys)
        models = list(MODEL_CONFIG.keys())
        quota_data = {}
        
        for api_key in api_keys:
            api_key_quotas = {}
            for model in models:
                quota = await async_quota_service.get_quota(api_key, model)
                if quota is not None:
                    api_key_quotas[model] = quota
            if api_key_quotas:
                quota_data[api_key] = api_key_quotas
        
        return {
            "success": True,
            "data": quota_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quota/{api_key}")
async def get_api_key_quota(api_key: str):
    """获取指定API Key的配额"""
    if not async_quota_service:
        raise HTTPException(status_code=503, detail="Quota service not available")
    
    if api_key not in auth_service.valid_api_keys:
        raise HTTPException(status_code=404, detail="API key not found")
    
    try:
        models = list(MODEL_CONFIG.keys())
        quota_data = {}
        
        for model in models:
            quota = await async_quota_service.get_quota(api_key, model)
            if quota is not None:
                quota_data[model] = quota
        
        return {
            "success": True,
            "data": quota_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quota/{api_key}/{model}")
async def get_model_quota(api_key: str, model: str):
    """获取指定API Key和模型的配额"""
    if not async_quota_service:
        raise HTTPException(status_code=503, detail="Quota service not available")
    
    if api_key not in auth_service.valid_api_keys:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if model not in MODEL_CONFIG:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        quota = await async_quota_service.get_quota(api_key, model)
        return {
            "success": True,
            "data": {
                "api_key": api_key,
                "model": model,
                "quota": quota
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class QuotaUpdate(BaseModel):
    amount: int


@router.post("/quota/{api_key}/{model}")
async def set_model_quota(api_key: str, model: str, quota_update: QuotaUpdate):
    """设置指定API Key和模型的配额"""
    if not async_quota_service:
        raise HTTPException(status_code=503, detail="Quota service not available")
    
    if api_key not in auth_service.valid_api_keys:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if model not in MODEL_CONFIG:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        await async_quota_service.set_quota(api_key, model, quota_update.amount)
        return {
            "success": True,
            "message": f"Quota for {api_key} on {model} set to {quota_update.amount}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quota/{api_key}/{model}/add")
async def add_model_quota(api_key: str, model: str, quota_update: QuotaUpdate):
    """增加指定API Key和模型的配额"""
    if not async_quota_service:
        raise HTTPException(status_code=503, detail="Quota service not available")
    
    if api_key not in auth_service.valid_api_keys:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if model not in MODEL_CONFIG:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        await async_quota_service.add_quota(api_key, model, quota_update.amount)
        return {
            "success": True,
            "message": f"Added {quota_update.amount} quota to {api_key} on {model}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
