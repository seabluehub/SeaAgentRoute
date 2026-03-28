# AI Gateway - 本地多模型聚合网关

轻量级 AI API 网关，统一接口访问多个云端和本地 AI 模型。

## 功能特性

- 统一接口：完全兼容 OpenAI API 规范
- 多模型路由：支持云端 API（硅基流动、DeepSeek、智谱等）和本地 LM Studio
- 流式支持：完整透传 SSE (`text/event-stream`) 响应
- 统一鉴权：平台级 API Key 管理
- 配额管理：基于 Redis 的原子配额扣减（Lua 脚本）
- 请求日志：异步记录请求和响应到 Redis List
- 零云依赖：所有组件本地运行

## 快速开始

### 5分钟验证指南

#### 1. 环境准备

确保已安装：
- Python 3.10+
- Redis 7+（用于配额和日志）
- LM Studio（可选，用于本地模型）

**启动 Redis（Docker）：**
```bash
docker run -d -p 6379:6379 --name redis-gateway redis:7-alpine
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填入真实 API Keys：

```bash
copy .env.example .env
```

编辑 `.env` 文件：
```env
SILICON_API_KEY=your_silicon_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
ZHIPU_API_KEY=your_zhipu_api_key_here

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

GATEWAY_API_KEYS=test-key-123,test-key-456
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8000
```

#### 4. 设置用户配额（可选）

使用 Python 设置初始配额：
```python
from services.quota import quota_service
quota_service.set_quota("test-key-123", "gpt-4o", 100000)
```

#### 5. 启动服务

**Windows 一键启动：**
```bash
scripts\start.bat
```

**或手动启动：**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 6. 验证服务

**健康检查（包含 Redis 状态）：**
```bash
curl http://localhost:8000/health
```

**测试普通请求（使用测试 API Key）：**
```bash
curl -X POST http://localhost:8000/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer test-key-123" ^
  -d "{\"model\": \"gpt-4o\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}], \"stream\": false}"
```

**测试流式请求：**
```bash
curl -X POST http://localhost:8000/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer test-key-123" ^
  -d "{\"model\": \"gpt-4o\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello\"}], \"stream\": true}"
```

## 测试

### 运行 pytest 测试

```bash
pip install pytest httpx
pytest tests/ -v
```

## 项目结构

```
ai-gateway-local/
├── .env.example           # 环境变量模板
├── .gitignore            # Git 忽略文件
├── requirements.txt      # Python 依赖
├── main.py               # FastAPI 入口
├── config/
│   ├── __init__.py
│   ├── settings.py       # 配置加载
│   └── models.py         # 模型配置
├── services/
│   ├── __init__.py
│   ├── auth.py           # API Key 鉴权
│   ├── quota.py          # Redis 配额管理
│   ├── logger.py         # 异步日志记录
│   └── proxy.py          # 上游转发核心
├── utils/
│   └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # pytest fixtures
│   ├── test_auth.py      # 鉴权测试
│   └── test_proxy.py     # 代理转发测试
└── scripts/
    └── start.bat         # Windows 启动脚本
```

## 可用模型

- `gpt-4o` - 硅基流动 Qwen2.5-72B
- `deepseek-r1` - DeepSeek Reasoner
- `glm-4` - 智谱 GLM-4
- `glm-4-flash` - 智谱 GLM-4 Flash
- `local-qwen` - 本地 LM Studio 模型

## Redis 数据结构

### 配额 Key
```
quota:{api_key}:{model} -> String (剩余 token 数量)
```

### 日志 Key
```
logs:requests -> List (请求日志，保留最近 10000 条)
logs:responses -> List (响应日志，保留最近 10000 条)
```

### 查看日志示例
```bash
redis-cli LRANGE logs:requests -10 -1
redis-cli LRANGE logs:responses -10 -1
```

## 常见问题

### 端口被占用
修改 `.env` 中的 `GATEWAY_PORT` 或关闭占用 8000 端口的程序。

### LM Studio 连接失败
确保 LM Studio 已启动并监听 `http://localhost:1234`。

### Redis 连接失败
确保 Redis 服务已启动，检查 `.env` 中的 Redis 配置是否正确。如不需要配额和日志功能，服务仍可正常运行。

### 配额扣减不生效
确保已为用户设置初始配额：
```python
from services.quota import quota_service
quota_service.set_quota("test-key-123", "gpt-4o", 100000)
```

### 如何添加新的 API Key
编辑 `.env` 中的 `GATEWAY_API_KEYS`，用逗号分隔多个 key，重启服务生效。

## 开发路线

- Phase 1 ✅ - 基础框架
- Phase 2 ✅ - 鉴权/配额/日志（当前）
- Phase 3 🔜 - 高级功能
