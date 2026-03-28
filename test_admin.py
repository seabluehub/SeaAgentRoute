import httpx
import asyncio
import json


async def test_admin_api():
    print("Testing Admin API...\n")
    
    async with httpx.AsyncClient() as client:
        # 测试获取模型列表
        print("1. Testing GET /admin/api/models...")
        try:
            response = await client.get("http://localhost:8000/admin/api/models")
            print(f"   Status: {response.status_code}")
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Models: {list(data.get('data', {}).keys())}")
            print("   ✅ Models API OK\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
        
        # 测试获取API Keys
        print("2. Testing GET /admin/api/api-keys...")
        try:
            response = await client.get("http://localhost:8000/admin/api/api-keys")
            print(f"   Status: {response.status_code}")
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   API Keys count: {len(data.get('data', []))}")
            print("   ✅ API Keys API OK\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
        
        # 测试获取完整配置
        print("3. Testing GET /admin/api/config...")
        try:
            response = await client.get("http://localhost:8000/admin/api/config")
            print(f"   Status: {response.status_code}")
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print("   ✅ Config API OK\n")
        except Exception as e:
            print(f"   ❌ Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(test_admin_api())
