import httpx

async def test_metrics_endpoint():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/metrics")
            print(f"Status code: {response.status_code}")
            print("Metrics response:")
            print(response.text)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_metrics_endpoint())