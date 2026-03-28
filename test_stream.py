import requests
import json

# 测试流式响应
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

response = requests.post(url, headers=headers, json=payload, stream=True)

if response.status_code == 200:
    print(f"Status code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print("\nStreaming response:")
    print("-" * 50)
    
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:
            chunk_str = chunk.decode('utf-8')
            print(chunk_str, end='')
    print("\n" + "-" * 50)
    print("Streaming test completed successfully!")
else:
    print(f"Error: {response.status_code}")
    print(f"Response: {response.text}")
