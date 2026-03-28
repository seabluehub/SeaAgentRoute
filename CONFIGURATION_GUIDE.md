# 📖 AI网关配置和使用指南

## ✅ 回答你的两个问题

### 问题1：如何配置和使用自定义模型？

**是的，你可以直接使用 `http://localhost:8000/v1/chat/completions` 来配置自定义模型！**

#### 重要注意事项
- **正确的端点是**：`/v1/chat/completions`（不是 `/v1/chat`）
- 这是标准的 OpenAI 兼容 API 格式

---

## 📋 配置自定义模型步骤

### 步骤1：在 `.env` 文件中添加 API Key

编辑 `.env` 文件，添加你的 API Key：

```env
# 新增的模型服务商 API Key
MY_NEW_API_KEY=your_api_key_here
```

### 步骤2：在 `config/models.py` 中添加模型配置

编辑 `config/models.py`，在 `MODEL_CONFIG` 字典中添加新配置：

```python
MODEL_CONFIG: Dict[str, ModelConfig] = {
    # ... 现有配置 ...
    
    # 新增自定义模型
    "my-custom-model": ModelConfig(
        base_url="https://api.your-provider.com/v1",  # 服务商API地址
        auth_header=f"Bearer {settings.my_new_api_key}",  # 从.env读取API Key
        target_model="actual-model-name",  # 服务商的真实模型名
        max_tokens=4096,  # 最大token数
        supports_stream=True,  # 是否支持流式响应
        timeout=60  # 超时时间（秒）
    ),
}
```

### 步骤3：在 `config/settings.py` 中添加环境变量读取

编辑 `config/settings.py`，添加新的配置项：

```python
class Settings:
    def __init__(self):
        # ... 现有配置 ...
        
        # 新增的 API Key
        self.my_new_api_key: str = os.getenv("MY_NEW_API_KEY", "")
```

---

## 🚀 使用方法

### 基本调用格式

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key-123" \
  -d '{
    "model": "my-custom-model",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

### Python 示例

```python
import httpx
import asyncio

async def chat():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/chat/completions",
            headers={"Authorization": "Bearer test-key-123"},
            json={
                "model": "my-custom-model",
                "messages": [{"role": "user", "content": "你好"}]
            }
        )
        print(response.json())

asyncio.run(chat())
```

---

## 🔄 问题2：流式请求实现状态

### ✅ 流式响应已完整实现！

**流式功能特性：**
1. ✅ 完整的 SSE (Server-Sent Events) 支持
2. ✅ 使用 `httpx.stream()` + `aiter_bytes()` 透传，无缓冲截断
3. ✅ 正确的 `Content-Type: text/event-stream` 响应头
4. ✅ 支持 `Cache-Control: no-cache` 和其他必要头
5. ✅ 流式和非流式都可以通过 `stream` 参数切换

### 如何使用流式响应

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key-123" \
  -d '{
    "model": "local-qwen",
    "messages": [{"role": "user", "content": "讲个故事"}],
    "stream": true
  }'
```

### Python 流式示例

```python
import httpx
import asyncio
import json

async def stream_chat():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/v1/chat/completions",
            headers={"Authorization": "Bearer test-key-123"},
            json={
                "model": "glm-4-flash",
                "messages": [{"role": "user", "content": "讲个故事"}],
                "stream": True
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if "choices" in chunk:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                print(content, end="", flush=True)
                    except:
                        pass

asyncio.run(stream_chat())
```

---

## 📊 已配置的可用模型

| 模型名称 | 后端服务商 | 说明 |
|----------|------------|------|
| `gpt-4o` | 硅基流动 | Qwen2.5-72B |
| `deepseek-r1` | DeepSeek | deepseek-reasoner |
| `glm-4` | 智谱AI | glm-4 |
| `glm-4-flash` | 智谱AI | glm-4-flash (快速版) |
| `local-qwen` | LM Studio | 本地 qwen3.5-35b-a3b |

---

## 🔑 网关认证

**网关 API Key（在 .env 中配置）：**
```env
GATEWAY_API_KEYS=test-key-123,test-key-456
```

使用时在 Header 中传递：
```
Authorization: Bearer test-key-123
```

---

## 📝 完整请求参数

```json
{
  "model": "模型名称",
  "messages": [
    {"role": "system", "content": "系统提示"},
    {"role": "user", "content": "用户消息"},
    {"role": "assistant", "content": "助手回复"}
  ],
  "stream": false,
  "max_tokens": 1000,
  "temperature": 0.7,
  "top_p": 1.0
}
```

---

## 🛠️ 测试命令汇总

```bash
# 健康检查
python test_connection.py health

# 测试本地模型（非流式）
python test_connection.py local

# 测试本地模型（流式）
python test_connection.py stream-local

# 测试GLM模型（非流式）
python test_connection.py glm

# 测试GLM模型（流式）
python test_connection.py stream-glm

# 查看LM Studio可用模型
python test_connection.py lm
```
