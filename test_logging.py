import httpx
import asyncio

async def test_logging():
    async with httpx.AsyncClient() as client:
        # 测试健康检查端点，触发日志记录
        print("Testing health endpoint to trigger logging...")
        response = await client.get("http://localhost:8000/health")
        print(f"Health status code: {response.status_code}")
        
        # 测试一个错误请求，触发错误日志
        print("\nTesting error request to trigger error logging...")
        try:
            response = await client.post(
                "http://localhost:8000/v1/chat/completions",
                json={"model": "non-existent-model", "messages": [{"role": "user", "content": "Hello"}]},
                headers={"Authorization": "Bearer test-key-123"}
            )
            print(f"Error request status code: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\nCheck the server logs to see if structured logs are being generated.")

if __name__ == "__main__":
    asyncio.run(test_logging())