# Agent-RAG Production Demo

这个仓库现在同时包含两套入口：

- `server.main:app`
  面向生产化改造后的 FastAPI 服务，包含 JWT/RBAC、PostgreSQL/pgvector、LangGraph 工作流、RAG 检索与报告查询。
- `app.py`
  仅作为 Streamlit 演示 UI，调用本地 FastAPI 接口，不再直接执行 Agent。

## 已完成的生产化改造

- FastAPI API 层
- PostgreSQL + pgvector 存储层
- JWT 认证与最小 RBAC
- LangGraph 显式意图路由
- 报告查询权限流
- 文档离线入库与向量检索
- 引用来源返回
- 无答案时拒答
- 本地 Python 3.12 / PostgreSQL 17 仿真环境

## 本地环境

- Python：`G:\devTools\Python312\python.exe`
- PostgreSQL：`G:\devTools\PostgreSQL\17`
- 数据目录：`G:\devTools\PostgreSQL\data`
- 日志目录：`G:\devTools\PostgreSQL\logs`
- 数据库：`agent_rag`
- 应用用户：`agent_app`
- PostgreSQL 服务名：`postgresql-agent-rag`

## 安装与启动

### 1. 创建虚拟环境

```powershell
G:\devTools\Python312\python.exe -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 准备环境变量

复制 `.env.example` 为 `.env`，按需修改：

```env
DATABASE_URL=postgresql+psycopg://agent_app:AgentApp!2026@127.0.0.1:5432/agent_rag
JWT_SECRET_KEY=replace-this-local-dev-secret
AI_DASHSCOPE_API_KEY=
```

如果不提供 `AI_DASHSCOPE_API_KEY`，系统会使用本地哈希 embedding 和模板化生成兜底，仍可完成开发联调。

### 3. 启动 API

```powershell
.\.venv312\Scripts\python.exe -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```

首次启动会自动：

- 创建表结构
- 初始化权限、角色、用户
- 导入 `data/external/records.csv`
- 导入 `data/` 下的知识文件到 pgvector

### 4. 启动 Streamlit 演示 UI

```powershell
.\.venv312\Scripts\python.exe -m streamlit run app.py
```

## 默认账号

- 普通用户：`user1001 / user1001`
- 普通用户：`user1002 / user1002`
- 管理员：`admin / admin123`

默认权限：

- `user`：`kb:read`, `report:read:self`
- `admin`：`kb:read`, `report:read:self`, `report:read:any`, `admin:knowledge:write`

## API 概览

- `POST /auth/login`
- `POST /auth/refresh`
- `GET /me`
- `POST /chat`
- `GET /conversations/{thread_id}`
- `POST /reports/query`
- `POST /knowledge/ingest`
- `GET /health`
- `GET /ready`

## LangGraph 路由

- `intent_classifier`
- `policy_guard`
- `faq_rag`
- `report_fetch`
- `report_generate`
- `fallback`
- `handoff`

当前显式意图：

- `product_qa`
- `troubleshooting`
- `maintenance`
- `purchase_advice`
- `personal_report`
- `unknown`

## 测试

```powershell
.\.venv312\Scripts\python.exe -m pytest -p no:cacheprovider tests
```

## 说明

- 老的 `agent/`、`rag/`、`model/` 目录仍保留，便于对比原始 demo 与生产化实现。
- 当前没有接入 Redis，限流和会话黑名单是本地可替换实现。
- 若需要进一步收敛到真正生产环境，下一步建议补 Alembic 迁移脚本、Redis、对象存储和评测流水线。
