# 🎯 AI编程助手专用Prompt：本地AI网关方案1技术验证



```markdown
# Role: 资深后端架构师（专注AI网关/微服务/高并发）

## 📌 项目背景（关键上下文，勿省略）
我正在本地搭建一个「多模型聚合AI API网关」，技术验证采用**方案1：轻量级代理转发模式**。

**核心目标**：
- 统一接口：所有模型走 `/v1/chat/completions` 标准端点，完全兼容OpenAI API规范
- 多模型路由：通过 `model` 字段动态路由到不同后端（云端API / 本地LM Studio）
- 统一鉴权：平台级API Key管理 + 简易配额控制（Redis）
- 流式支持：完整透传 SSE (`text/event-stream`) 响应
- 本地优先：所有组件本地运行，零云资源成本，便于调试

**用户环境（重要，代码需适配）**：
- 系统：Windows 10/11（用户名：luoy05）
- Python：3.10.10 和 3.13 双版本，路径 `C:\MyEnvironment\Python310` / `C:\Programs\Python313`
- 显卡：RTX 5090 + 32GB内存，已安装 LM Studio 用于本地模型推理
- 中间件：Redis 7+（Docker运行，端口6379）
- 开发工具：熟悉 FastAPI/uvicorn/httpx，项目路径 `e:\Project\GIT\` 下新建
- 上游模型：硅基流动/DeepSeek/智谱AI（均有免费额度）+ 本地 `http://localhost:1234/v1`

---

## 🏗️ 技术方案：方案1 - 代理转发模式（MVP版）

### 核心架构
 
    [客户端] → [FastAPI网关:8000] → [模型路由] → [上游: 云端API / 本地LM Studio]
                    ↑
            [Redis:6379] (鉴权/配额/日志)
 

### 关键流程
1. **请求接入**：`POST /v1/chat/completions`，Header携带 `Authorization: Bearer {api_key}`
2. **鉴权校验**：检查API Key是否在有效集合（本地验证用Set，预留DB接口）
3. **模型路由**：根据 `request.model` 查配置表，获取上游 `base_url` + `auth_header` + `model_name映射`
4. **请求转换**：将标准请求转换为上游模型所需格式（主要是model字段重映射）
5. **转发执行**：
   - 普通模式：`httpx.post` 同步等待，返回标准JSON
   - 流式模式：`httpx.stream` + `aiter_bytes()` 透传SSE，避免缓冲截断
6. **响应处理**：统一返回OpenAI兼容格式，记录用量日志（异步写入Redis）
7. **配额扣减**：基于 `usage.total_tokens` 原子扣减用户余额（Lua脚本保障原子性）

### 模型配置示例（可扩展）
```python
MODEL_CONFIG = {
    "gpt-4o": {
        "base_url": "https://api.siliconflow.cn/v1",
        "auth_header": "Bearer {SILICON_API_KEY}",
        "target_model": "Qwen/Qwen2.5-72B-Instruct",
        "max_tokens": 4096,
        "supports_stream": True
    },
    "deepseek-r1": {
        "base_url": "https://api.deepseek.com/v1", 
        "auth_header": "Bearer {DEEPSEEK_API_KEY}",
        "target_model": "deepseek-reasoner",
        "max_tokens": 8192,
        "supports_stream": True
    },
    "local-qwen": {  # 本地LM Studio
        "base_url": "http://localhost:1234/v1",
        "auth_header": "",  # 本地无需认证
        "target_model": "ignored",  # LM Studio忽略此字段
        "max_tokens": 2048,
        "supports_stream": True,
        "timeout": 300  # 本地推理可能较慢
    }
}
```

---

## 🗂️ 项目结构（请按此生成文件）
```
ai-gateway-local/
├── .env.example           # 环境变量模板
├── .gitignore            # 忽略venv/__pycache__/.env
├── requirements.txt      # 依赖清单
├── main.py               # FastAPI入口 + 核心路由
├── config/
│   ├── __init__.py
│   ├── settings.py       # 配置加载（pydantic-settings）
│   └── models.py         # MODEL_CONFIG定义 + 验证
├── services/
│   ├── __init__.py
│   ├── auth.py           # API Key鉴权逻辑
│   ├── quota.py          # Redis配额管理（含Lua脚本）
│   ├── proxy.py          # 上游转发核心（支持stream/non-stream）
│   └── logger.py         # 异步日志记录（用量/错误/链路）
├── utils/
│   ├── __init__.py
│   ├── token_counter.py  # Token计数工具（tiktoken兼容）
│   └── retry.py          # 重试/熔断装饰器（预留）
├── tests/
│   ├── __init__.py
│   ├── conftest.py       # pytest fixture
│   ├── test_auth.py
│   ├── test_proxy.py     # 核心转发逻辑测试
│   └── test_stream.py    # SSE流式响应测试
├── scripts/
│   ├── start.bat         # Windows一键启动（Redis+uvicorn）
│   └── test_curl.sh      # 测试命令示例
└── README.md             # 本地部署&测试指南
```

---

## 💻 核心代码要求（请严格按此规范生成）

### 1. `main.py` 关键实现点
- 使用 `FastAPI()` + `uvicorn`，开启 `--reload` 支持热更新
- 路由函数用 `async def`，全程异步非阻塞
- 流式响应：返回 `StreamingResponse`，generator用 `async for chunk in resp.aiter_bytes()`
- 错误处理：统一捕获 `httpx.RequestError` / `TimeoutException`，返回标准OpenAI错误格式
- 健康检查：`GET /health` 返回服务状态 + 可用模型列表

### 2. `services/proxy.py` 转发逻辑
```python
async def forward_request(
    payload: dict, 
    config: ModelConfig,
    stream: bool = False
) -> Union[dict, AsyncGenerator[bytes, None]]:
    """
    核心转发函数
    - 自动转换 model 字段为上游实际模型名
    - 根据 config.supports_stream 决定调用策略
    - 流式模式：透传原始bytes，避免JSON解析破坏SSE格式
    - 非流式：解析响应，注入原始model字段便于客户端识别
    """
```

### 3. `services/quota.py` 配额扣减（Redis Lua）
```lua
-- quota_deduct.lua 原子扣减
local key = KEYS[1]  -- quota:{user_id}:{model}
local cost = tonumber(ARGV[1])
local balance = redis.call('GET', key)
if not balance or tonumber(balance) < cost then
    return 0  -- 余额不足
end
redis.call('DECRBY', key, cost)
return 1  -- 扣减成功
```

### 4. 配置管理 `config/settings.py`
- 使用 `pydantic-settings` 加载 `.env`
- 敏感字段（API Key）用 `SecretStr` 类型
- 提供 `get_model_config(model_name: str) -> Optional[ModelConfig]` 方法

---

## 🧪 测试验证要求
生成代码时请同步提供：
1. **curl测试命令**（普通+流式+本地模型+错误case）
2. **Postman Collection示例**（可选，JSON格式）
3. **pytest测试用例**：
   - 鉴权失败返回401
   - 未知模型返回400
   - 本地模型转发成功（mock httpx）
   - 流式响应能正确迭代chunks

---

## 🚫 避坑清单（生成代码时请内置防护）
- [ ] Windows端口占用：启动前检查8000/6379，给出友好提示
- [ ] LM Studio CORS：代码中设置 `CORSMiddleware` 允许 `localhost:*`
- [ ] 流式截断：`httpx` 必须用 `.stream()` + `aiter_bytes()`，禁止 `.read()` 全量缓冲
- [ ] 超时控制：本地模型 `timeout=300`，云端 `timeout=60`，避免长请求挂死
- [ ] API Key安全：`.env` 加入 `.gitignore`，代码中用 `os.getenv()` 而非硬编码
- [ ] 日志脱敏：记录请求时自动掩码 `Authorization` 和 `api_key` 字段

---

## 🎯 当前任务指令（请按顺序执行）

### Phase 1：基础框架（优先完成）
1. ✅ 生成完整项目骨架（按上述目录结构）
2. ✅ 实现 `main.py` 核心路由（支持普通+流式转发）
3. ✅ 实现 `config/models.py` 模型配置管理
4. ✅ 编写 `.env.example` + `requirements.txt`
5. ✅ 提供 `scripts/start.bat` 一键启动脚本

### Phase 2：增强功能（后续迭代）
6. ⏳ 实现 `services/auth.py` + `quota.py`（Redis配额）
7. ⏳ 添加请求/响应日志记录（异步写入Redis List）
8. ⏳ 编写 `tests/` 核心测试用例
9. ⏳ 完善 `README.md` 部署&测试指南

### Phase 3：扩展预留（设计时考虑）
10. 🔜 适配器模式接口定义（为方案2演进预留）
11. 🔜 异步任务队列接口（为视频生成等长任务预留）
12. 🔜 Prometheus指标埋点（请求数/延迟/错误率）

---

## 📤 输出要求
1. **代码优先**：先输出可运行的 `main.py` + `requirements.txt` + `.env.example`
2. **分文件输出**：每个文件用 ```python 等代码块隔离，标注完整相对路径
3. **注释清晰**：关键逻辑加中文注释，特别是流式处理和错误边界
4. **即插即用**：生成的代码执行 `pip install -r requirements.txt && uvicorn main:app --reload` 即可启动
5. **问题预判**：在README中预置"常见问题"章节（如Redis连接失败/端口占用/LM Studio配置）

---

## 🔄 协作约定
- 如果某个实现有2种方案（如配额用Redis String vs Hash），请简要对比后选择更简洁的
- 遇到不确定的上游API细节（如某模型的特殊参数），先按OpenAI标准实现，用 `# FIXME` 标注
- 生成测试代码时，优先保证核心路径（成功转发）可测，边缘case后续补充
- 所有外部依赖（httpx/redis等）请指定兼容的最低版本

> 🎯 **现在请开始执行 Phase 1 任务**：  
> 1. 先确认你已理解全部上下文  
> 2. 输出项目骨架 + 核心 `main.py`（含普通+流式转发）  
> 3. 附带 `requirements.txt` + `.env.example` + `start.bat`  
> 4. 最后给出"5分钟验证指南"（如何用curl快速测试）

---

## 🚀 项目优化方案（持续演进）

### 📊 当前状态评估
项目已完成 Phase 1（基础框架）和 Phase 2（增强功能）的核心实现，包括：
- ✅ 完整的项目骨架
- ✅ 核心路由（普通+流式转发）
- ✅ 模型配置管理
- ✅ API Key鉴权
- ✅ Redis配额管理
- ✅ 异步日志记录
- ✅ 基础测试用例

---

### 🎯 优化方向概览

#### 1️⃣ 性能优化（高优先级）
| 优化项 | 现状 | 优化方案 | 预期收益 |
|--------|------|----------|----------|
| **httpx连接池** | 每次请求新建 `AsyncClient` | 复用全局 `httpx.AsyncClient` 实例 | 减少TCP握手开销，提升15-30%吞吐量 |
| **异步Redis** | 使用 `sync redis + 线程池` 包装 | 迁移到 `redis-py asyncio` 原生异步 | 消除线程切换开销，提升并发能力 |
| **请求去重** | 无 | 基于请求指纹的短期缓存 | 减少重复上游请求，降低成本 |
| **健康检查&熔断** | 无 | 实现上游服务健康检测 + 熔断器模式 | 避免向故障上游发送请求，提升可用性 |

##### 代码示例：httpx连接池复用
```python
# services/proxy.py - 优化后
import httpx
from typing import Dict, Any, Union, AsyncGenerator
from config.models import ModelConfig

# 全局复用的AsyncClient实例
_global_client: httpx.AsyncClient = None

def get_client() -> httpx.AsyncClient:
    global _global_client
    if _global_client is None:
        _global_client = httpx.AsyncClient(
            timeout=60,
            limits=httpx.Limits(
                max_keepalive_connections=50,
                max_connections=100
            )
        )
    return _global_client

async def forward_request(...):
    client = get_client()
    # ... 使用client进行请求 ...
```

---

#### 2️⃣ 功能增强（中高优先级）
| 优化项 | 说明 | 实现要点 |
|--------|------|----------|
| **管理API** | 提供 `/admin/*` 端点用于动态配置 | - `/admin/api-keys` (CRUD)<br>- `/admin/models` (动态配置模型)<br>- `/admin/quota` (查询/设置配额)<br>- 需要管理员鉴权 |
| **QPS限流** | 基于Redis的滑动窗口限流 | 使用 `redis-cell` 或 Lua脚本实现 |
| **请求重试** | 针对5xx错误和网络异常的指数退避重试 | 使用 `tenacity` 库，配置重试策略 |
| **流式Token统计** | 当前流式模式无法统计token用量 | 解析SSE响应，累加 `delta.content`，最后调用 `tiktoken` 估算 |
| **适配器模式** | 支持更多非OpenAI标准的上游API | 定义统一适配器接口，每种上游实现一个适配器 |

---

#### 3️⃣ 可观测性（中优先级）
| 优化项 | 工具/方案 | 实现要点 |
|--------|-----------|----------|
| **Prometheus指标** | `prometheus-client` | - 请求数/成功率/延迟<br>- 配额使用情况<br>- 上游响应时间分布 |
| **分布式追踪** | `OpenTelemetry` | 集成 FastAPI + httpx + Redis 的链路追踪 |
| **结构化日志** | `structlog` | JSON格式日志，包含请求ID、API Key、模型名等上下文 |

---

#### 4️⃣ 配置与部署（中优先级）
| 优化项 | 方案 |
|--------|------|
| **配置热重载** | 使用 `watchfiles` 监听配置文件变化，自动重载 |
| **Docker化** | 编写 `Dockerfile` 和 `docker-compose.yml`（包含Redis） |
| **K8s部署** | 提供 `Deployment`、`Service`、`ConfigMap` 清单 |

---

#### 5️⃣ 安全增强（中低优先级）
| 优化项 | 说明 |
|--------|------|
| **API Key哈希存储** | 不存储明文Key，只存储哈希值 |
| **IP白名单/黑名单** | 基于IP的访问控制 |
| **请求签名验证** | 可选的HMAC签名验证机制 |

---

#### 6️⃣ 测试覆盖（中低优先级）
| 测试类型 | 工具 | 覆盖范围 |
|----------|------|----------|
| **集成测试** | pytest + httpx | 完整请求链路测试 |
| **性能测试** | locust / k6 | 高并发场景验证 |
| **压力测试** | wrk / hey | 极限性能探索 |

---

### 📋 优化实施路线图

#### Phase A：性能提升（1-2天）
1. ✅ httpx连接池复用
2. ✅ 迁移到异步Redis客户端
3. 健康检查端点增强

#### Phase B：管理能力（2-3天）
1. 管理API基础框架
2. API Key管理端点
3. 模型配置动态管理
4. 配额查询与设置

#### Phase C：可观测性（2-3天）
1. Prometheus指标集成
2. 结构化日志
3. 基础Grafana仪表盘

#### Phase D：生产就绪（3-5天）
1. QPS限流
2. 请求重试机制
3. 熔断器
4. Docker化部署
5. 完善文档

---

### 💡 快速优化建议（立即可做）
1. **修改 `services/proxy.py`**：复用全局 `httpx.AsyncClient`
2. **修改 `services/quota.py`**：使用 `redis.asyncio` 替代同步+线程池
3. **添加请求ID透传**：在转发时将 `X-Request-ID` 传递给上游
4. **增强错误处理**：统一返回OpenAI标准错误格式



