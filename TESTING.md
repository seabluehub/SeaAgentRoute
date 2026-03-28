# AI Gateway 测试指南

## 📋 测试概览

本项目包含完整的单元测试和集成测试，用于验证 AI 网关的各项功能。

## ✅ 当前测试状态

**所有 20 个测试已通过！**

### 测试覆盖模块：

1. **认证服务 (test_auth.py) - 8 个测试
2. **代理服务集成 (test_proxy.py) - 10 个测试
3. **服务单元测试 (test_services.py) - 2 个测试

## 🚀 快速开始

### 1. 安装测试依赖

```bash
pip install pytest pytest-asyncio
```

### 2. 运行所有测试

```bash
python -m pytest tests/ -v
```

### 3. 运行特定模块测试

```bash
# 只运行认证测试
python -m pytest tests/test_auth.py -v

# 只运行代理测试
python -m pytest tests/test_proxy.py -v

# 运行特定测试用例
python -m pytest tests/test_proxy.py::test_chat_completions_success -v
```

## 📊 测试用例详解

### 认证服务测试 (test_auth.py)

| 测试用例 | 功能描述 |
|----------|----------|
| test_auth_service_init | 验证 AuthService 初始化正确 |
| test_verify_api_key_valid | 验证有效 API Key 返回 true |
| test_verify_api_key_invalid | 验证无效 API Key 返回 false |
| test_verify_api_key_no_bearer | 验证缺少 Bearer 前缀的 API Key |
| test_verify_api_key_none | 验证 null/空值处理 |
| test_add_api_key | 验证添加新 API Key |
| test_remove_api_key | 验证移除 API Key |
| test_remove_nonexistent_api_key | 验证移除不存在的 API Key |

### 代理集成测试 (test_proxy.py)

| 测试用例 | 功能描述 |
|----------|----------|
| test_health_endpoint | 验证健康检查端点正常 |
| test_chat_completions_unauthorized | 验证无认证返回 401 |
| test_chat_completions_invalid_json | 验证无效 JSON 返回 400 |
| test_chat_completions_missing_model | 验证缺少 model 字段返回 400 |
| test_chat_completions_unknown_model | 验证未知模型返回 400 |
| test_chat_completions_success | 验证成功的聊天完成请求 |
| test_chat_completions_stream | 验证流式响应功能 |
| test_chat_completions_http_error | 验证上游 HTTP 错误处理 |
| test_chat_completions_timeout | 验证请求超时处理 |
| test_chat_completions_upstream_error | 验证上游连接错误处理 |

### 服务单元测试 (test_services.py)

| 测试用例 | 功能描述 |
|----------|----------|
| test_forward_request_non_stream | 验证非流式转发逻辑 |
| test_forward_request_stream | 验证流式转发逻辑 |

## 🔍 测试技巧

### 查看测试覆盖率

```bash
# 安装 coverage.py
pip install coverage

# 运行带覆盖率的测试
coverage run -m pytest tests/
coverage report
coverage html  # 生成 HTML 报告
```

### 过滤测试

```bash
# 按关键字搜索测试
python -m pytest tests/ -k "stream" -v

# 只运行失败的测试
python -m pytest tests/ --lf
```

## 🛠️ 常见问题

**Q: 测试失败怎么办？**

A: 首先确保所有依赖已安装，并检查是否有环境变量问题。所有测试都是独立运行，不需要真实的 Redis 或外部 API 连接，因为我们使用了 mock。

**Q: 如何添加新测试？**

A: 在 `tests/` 目录下创建新的测试文件，以 `test_` 开头，使用 pytest 语法编写测试用例。

**Q: 测试如何处理异步函数？**

A: 使用 `@pytest.mark.asyncio` 装饰器，并在测试文件顶部导入 `AsyncMock。


## 📝 集成测试指南

除了单元测试外，你也可以使用 curl 进行真实的集成测试。更多详情请查看 README.md 中的测试示例。
