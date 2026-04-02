# TikTok跨境电商全自动运营系统

基于多AI Agent协同架构的TikTok Shop跨境电商全链路无人化智能运营系统。MVP阶段聚焦核心业务闭环：1688选品 → AI素材处理 → 智能定价 → TikTok上架 → 订单履约 → 智能客服 → 财务核算。

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Alembic |
| Agent | LangGraph / LangChain / GPT-4o |
| 数据库 | PostgreSQL 15 / Redis 7 / MinIO |
| 消息队列 | RabbitMQ |
| 爬虫 | Scrapy / Playwright |
| 前端 | Vue 3 / TypeScript / Element Plus / Pinia |
| 容器 | Docker / Docker Compose |
| CI/CD | GitHub Actions |

## 项目结构

```
├── backend/          # FastAPI后端服务
├── agent/            # LangGraph Agent编排服务
├── scraper/          # Scrapy爬虫服务
├── frontend/         # Vue3管理后台
├── docs/             # 项目文档
├── infra/            # 基础设施配置
└── docker-compose.yml
```

## 快速开始

### 前置条件

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 启动开发环境

```bash
# 1. 克隆项目
git clone <repo-url> && cd project_code

# 2. 启动基础设施（PostgreSQL, Redis, MinIO, RabbitMQ）
make dev-up

# 3. 安装后端依赖并运行迁移
make backend-install
make backend-migrate

# 4. 安装前端依赖
make frontend-install

# 5. 启动后端服务
make backend-run

# 6. 启动前端服务（新终端）
make frontend-run
```

访问 http://localhost:3000 进入管理后台，http://localhost:8000/docs 查看API文档。

## 常用命令

```bash
make help          # 查看所有命令
make test          # 运行测试
make lint          # 代码检查
make format        # 代码格式化
make dev-down      # 停止所有服务
```

## 文档

- [详细需求说明书](./TikTok跨境电商全自动运营系统-详细需求说明书V1.0.md)
- [MVP开发计划](./MVP详细开发计划-6周分阶段执行方案.md)
- [Agent协同配置](./开发团队多Agent协同配置完整文档.md)
- [验收标准](./附录A-验收标准与测试方案.md)
- [风险评估](./附录B-风险评估与应急预案.md)
