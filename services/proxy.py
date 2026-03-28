import httpx
from typing import Dict, Any, Union, AsyncGenerator
from config.models import ModelConfig


async def forward_request(
    payload: Dict[str, Any],
    config: ModelConfig,
    stream: bool = False
) -> Union[Dict[str, Any], AsyncGenerator[bytes, None]]:
    headers = {}
    if config.auth_header:
        headers["Authorization"] = config.auth_header
    headers["Content-Type"] = "application/json"
    
    modified_payload = payload.copy()
    modified_payload["model"] = config.target_model
    
    url = f"{config.base_url}/chat/completions"
    
    if stream:
        async def stream_generator():
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    json=modified_payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
        return stream_generator()
    else:
        async with httpx.AsyncClient(timeout=config.timeout) as client:
            response = await client.post(
                url,
                json=modified_payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            if "model" in result:
                result["model"] = payload["model"]
            return result
