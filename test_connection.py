import httpx
import asyncio
import json

async def test_lm_studio():
    print("Testing LM Studio connection...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:1234/v1/models")
            print(f"✅ LM Studio Status: {response.status_code}")
            print(f"Models available: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return True
    except Exception as e:
        print(f"❌ LM Studio Error: {e}")
        return False

async def test_health_endpoint():
    print("\nTesting AI Gateway health endpoint...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8000/health")
            print(f"✅ Gateway Health Status: {response.status_code}")
            print(f"Health info: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            return True
    except Exception as e:
        print(f"❌ Gateway Error: {e}")
        return False

async def test_local_model():
    print("\nTesting local LM Studio model via gateway...")
    try:
        payload = {
            "model": "local-qwen",
            "messages": [{"role": "user", "content": "你好，请简单介绍一下自己"}],
            "max_tokens": 100
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                "http://localhost:8000/v1/chat/completions",
                headers={"Authorization": "Bearer test-key-123"},
                json=payload
            )
            print(f"✅ Local Model Status: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
    except Exception as e:
        print(f"❌ Local Model Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_glm_model():
    print("\nTesting GLM model via gateway...")
    try:
        payload = {
            "model": "glm-4-flash",
            "messages": [{"role": "user", "content": "你好，请简单介绍一下自己"}],
            "max_tokens": 100
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8000/v1/chat/completions",
                headers={"Authorization": "Bearer test-key-123"},
                json=payload
            )
            print(f"✅ GLM Model Status: {response.status_code}")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
    except Exception as e:
        print(f"❌ GLM Model Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stream_local():
    print("\nTesting STREAMING local LM Studio model via gateway...")
    try:
        payload = {
            "model": "local-qwen",
            "messages": [{"role": "user", "content": "请用100字讲一个有趣的小故事"}],
            "stream": True,
            "max_tokens": 200
        }
        print("Streaming response:")
        print("-" * 50)
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                "http://localhost:8000/v1/chat/completions",
                headers={"Authorization": "Bearer test-key-123"},
                json=payload
            ) as response:
                print(f"✅ Stream Status: {response.status_code}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print("-" * 50)
                full_content = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                                    full_content += content
                        except Exception:
                            pass
                print("\n" + "-" * 50)
                print(f"\n✅ Streaming complete! Full response length: {len(full_content)} chars")
                return True
    except Exception as e:
        print(f"\n❌ Streaming Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stream_glm():
    print("\nTesting STREAMING GLM model via gateway...")
    try:
        payload = {
            "model": "glm-4-flash",
            "messages": [{"role": "user", "content": "请用100字讲一个有趣的小故事"}],
            "stream": True,
            "max_tokens": 200
        }
        print("Streaming response:")
        print("-" * 50)
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "http://localhost:8000/v1/chat/completions",
                headers={"Authorization": "Bearer test-key-123"},
                json=payload
            ) as response:
                print(f"✅ Stream Status: {response.status_code}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print("-" * 50)
                full_content = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                                    full_content += content
                        except Exception:
                            pass
                print("\n" + "-" * 50)
                print(f"\n✅ Streaming complete! Full response length: {len(full_content)} chars")
                return True
    except Exception as e:
        print(f"\n❌ Streaming Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "lm":
            asyncio.run(test_lm_studio())
        elif sys.argv[1] == "health":
            asyncio.run(test_health_endpoint())
        elif sys.argv[1] == "local":
            asyncio.run(test_local_model())
        elif sys.argv[1] == "glm":
            asyncio.run(test_glm_model())
        elif sys.argv[1] == "stream-local":
            asyncio.run(test_stream_local())
        elif sys.argv[1] == "stream-glm":
            asyncio.run(test_stream_glm())
    else:
        print("Usage: python test_connection.py [lm|health|local|glm|stream-local|stream-glm]")
