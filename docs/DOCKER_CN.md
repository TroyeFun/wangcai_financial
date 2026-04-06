# 国内网络下运行 Docker（Docker Hub 超时 / 镜像加速无效）

Daemon 里配置的「镜像加速」有时仍会把请求转到 `auth.docker.io`，在部分网络下会 **IPv6 超时** 或 **拉取失败**。更稳妥的方式是：**镜像名直接写成国内可拉取的仓库前缀**（不经过 Docker Hub 鉴权）。

本项目已支持通过 **`.env.compose`** 指定镜像地址与构建时用到的 PyPI/npm 源。

## 方式一：使用 `.env.compose`（推荐）

```bash
cd /path/to/wangcai_financial
cp .env.compose.example .env.compose
# 若 DaoCloud 拉不动，编辑 .env.compose 改用阿里云那组变量（文件内有注释）

docker compose --env-file .env.compose up -d --build
```

健康检查（与 README 一致）：

```bash
curl http://localhost:8000/health
```

访问：后端 http://localhost:8000 ，前端 http://localhost:3000 。

### 镜像前缀可替换

在 `.env.compose` 里四行 `*_IMAGE` 保持同一「源」即可，例如：

| 源 | 前缀示例 |
|----|----------|
| DaoCloud | `docker.m.daocloud.io/library/...` |
| 阿里云 | `registry.cn-hangzhou.aliyuncs.com/library/...` |

某一源失败时，整组换成另一源（postgres / redis / python / node 要一起换）。

## 方式二：只起数据库，本机跑前后端（镜像最少）

当 **python / node 基础镜像** 仍然拉不下来时，可只拉 **postgres + redis** 两个小镜像：

```bash
cp .env.compose.example .env.compose
docker compose --env-file .env.compose -f docker-compose.db-only.yml up -d
```

在 `backend/.env` 中改为连本机：

```env
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/investment_db
REDIS_URL=redis://127.0.0.1:6379/0
```

终端 1（Python 3.10+）：

```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

终端 2：

```bash
cd frontend
npm config set registry https://registry.npmmirror.com
npm install
npm run dev
```

## 方式三：完全不用 Docker

本机安装 PostgreSQL 15 + Redis 7（如 `brew install postgresql@15 redis`），创建库 `investment_db`，再按方式二的 `backend/.env` 与 `uvicorn` / `npm run dev` 启动即可。

## 说明

- `.env.compose` 只给 **Compose 替换镜像名和 build 参数**，**不要**把 `backend/.env` 里的 API Key 挪进去（除非你刻意统一管理）。
- 若公司网络拦截境外域名，请优先试 **阿里云 `registry.cn-hangzhou.aliyuncs.com/library/...`** 整组镜像名。
