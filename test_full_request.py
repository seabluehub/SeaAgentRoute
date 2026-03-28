import httpx
import asyncio

async def test_full_request():
    async with httpx.AsyncClient() as client:
        # 测试完整的聊天请求
        print("Testing full chat completion request...")
        payload = {
            "model": "local-qwen",
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "stream": False
        }
        
        headers = {
            "Authorization": "Bearer test-key-123"
        }
        
        try:
            response = await client.post(
                "http://localhost:8000/v1/chat/completions",
                json=payload,
                headers=headers
            )
            print(f"Chat completion status code: {response.status_code}")
            if response.status_code == 200:
                print("Response received successfully")
                print("Response content:")
                print(response.json())
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        # 测试指标端点，看看请求指标是否被记录
        print("\nTesting metrics endpoint after chat request...")
        metrics_response = await client.get("http://localhost:8000/metrics")
        print("Metrics response (filtering for request-related metrics):")
        for line in metrics_response.text.split('\n'):
            if any(keyword in line for keyword in [
                'ai_gateway_requests_total',
                'ai_gateway_request_duration_seconds',
                'ai_gateway_active_requests'
            ]) and not line.startswith('#'):
                print(line)

if __name__ == "__main__":
    asyncio.run(test_full_request())