# AI Gateway - 本地多模型聚合网关

轻量级 AI API 网关，统一接口访问多个云端和本地 AI 模型。

## 功能特性

- 统一接口：完全兼容 OpenAI API 规范
- 多模型路由：支持云端 API（硅基流动、DeepSeek 等）和本地 LM Studio
- 流式支持：完整透传 SSE (`text/event-stream`) 响应
- 统一鉴权：平台级 API Key 管理
- 零云依赖：所有组件本地运行

## 快速开始

### 5分钟验证指南

#### 1. 环境准备

确保已安装：
- Python 3.10+
- Redis 7+（可选，Phase 2 需要）
- LM Studio（可选，用于本地模型）

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
```

#### 4. 启动服务

**Windows 一键启动：**
```bash
scripts\start.bat
```

**或手动启动：**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 5. 验证服务

**健康检查：**
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
│   └── proxy.py          # 上游转发核心
├── utils/
│   └── __init__.py
├── tests/
│   └── __init__.py
└── scripts/
    └── start.bat         # Windows 启动脚本
```

## 可用模型

- `gpt-4o` - 硅基流动 Qwen2.5-72B
- `deepseek-r1` - DeepSeek Reasoner
- `local-qwen` - 本地 LM Studio 模型

## 常见问题

### 端口被占用
修改 `.env` 中的 `GATEWAY_PORT` 或关闭占用 8000 端口的程序。

### LM Studio 连接失败
确保 LM Studio 已启动并监听 `http://localhost:1234`。

### Redis 连接失败
Phase 1 暂不需要 Redis，可忽略相关错误。

## 开发路线

- Phase 1 ✅ - 基础框架（当前）
- Phase 2 ⏳ - 鉴权/配额/日志
- Phase 3 🔜 - 高级功能
