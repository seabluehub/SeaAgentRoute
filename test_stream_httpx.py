import httpx
import asyncio

async def test_streaming():
    url = "http://localhost:8000/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer test-key-123"
    }
    payload = {
        "model": "local-qwen",
        "messages": [{"role": "user", "content": "Hello, how are you?"}],
        "stream": True
    }

    print("Testing streaming response...")
    print("=" * 50)

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            url,
            headers=headers,
            json=payload
        ) as response:
            print(f"Status code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print("\nStreaming response:")
            print("-" * 50)
            
            async for chunk in response.aiter_bytes():
                if chunk:
                    print(chunk.decode('utf-8'), end='')
            print("\n" + "-" * 50)
            print("Streaming test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_streaming())
