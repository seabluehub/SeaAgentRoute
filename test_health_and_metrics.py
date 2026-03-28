import httpx
import asyncio

async def test_health_and_metrics():
    async with httpx.AsyncClient() as client:
        # 测试健康检查端点
        print("Testing health endpoint...")
        health_response = await client.get("http://localhost:8000/health")
        print(f"Health status code: {health_response.status_code}")
        print("Health response:")
        print(health_response.json())
        
        # 再次测试指标端点，看看模型健康状态是否被更新
        print("\nTesting metrics endpoint after health check...")
        metrics_response = await client.get("http://localhost:8000/metrics")
        print(f"Metrics status code: {metrics_response.status_code}")
        print("Metrics response (filtering for model health):")
        for line in metrics_response.text.split('\n'):
            if 'ai_gateway_model_health' in line:
                print(line)
        
        # 测试单个模型健康检查
        print("\nTesting individual model health check...")
        model_health_response = await client.get("http://localhost:8000/health/models/local-qwen")
        print(f"Model health status code: {model_health_response.status_code}")
        print("Model health response:")
        print(model_health_response.json())
        
        # 再次测试指标端点
        print("\nTesting metrics endpoint after model health check...")
        metrics_response = await client.get("http://localhost:8000/metrics")
        print("Metrics response (filtering for model health):")
        for line in metrics_response.text.split('\n'):
            if 'ai_gateway_model_health' in line:
                print(line)

if __name__ == "__main__":
    asyncio.run(test_health_and_metrics())