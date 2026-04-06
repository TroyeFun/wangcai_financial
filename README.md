# LLM-Native 投资分析平台

一个面向小圈子（5-20 人）的 LLM-Native 投资分析平台，核心目标是消除个人投资者与机构投资者之间的信息差。

## 🎯 产品定位

- **目标用户**：5-20 人的投资小圈子，具备一定投资经验
- **资产覆盖**：A 股、港股、美股、债券、期货、加密货币、基金、黄金
- **分析重心**：宏观基本面 + 行业/指数投资，极少个股分析
- **核心价值**：用 AI 模拟机构级分析流程，让个人投资者获得专业分析能力

## 🚀 快速开始

### 环境要求

- Docker & Docker Compose
- Python 3.10+
- Node.js 18+

### 1. 克隆项目

```bash
git clone <repo-url>
cd investment-analysis
```

### 2. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 API Keys
```

### 3. 启动服务

```bash
docker compose up -d
```

若在国内网络下 **Docker Hub 超时** 或 **镜像加速仍失败**，请使用仓库内 **`.env.compose`** 指定直连镜像仓库（见 [docs/DOCKER_CN.md](docs/DOCKER_CN.md)）：

```bash
cp .env.compose.example .env.compose
docker compose --env-file .env.compose up -d --build
```

服务启动后：
- 后端 API：http://localhost:8000
- 前端界面：http://localhost:3000
- 飞书 Bot：需单独部署（见下文）

### 4. 健康检查

```bash
curl http://localhost:8000/health
```

## 📁 项目结构

```
investment-analysis/
├── backend/                 # 后端服务（FastAPI）
│   ├── agents/             # AI Agent 实现
│   │   ├── base_agent.py   # Agent 基类
│   │   ├── macro_analyst.py # 宏观分析师
│   │   └── ...
│   ├── data/               # 数据层
│   │   ├── providers/      # 数据源 Provider
│   │   │   ├── akshare.py  # AkShare（主力）
│   │   │   └── ...
│   │   ├── cache.py        # 缓存管理
│   │   └── scheduler.py    # 数据采集调度
│   ├── router/             # 对话路由
│   │   └── intent.py       # 意图识别
│   ├── api/                # FastAPI 路由
│   │   └── main.py         # 主入口
│   └── config/             # 配置管理
├── frontend/               # 前端（React + TailwindCSS）
├── feishu-bot/            # 飞书 Bot 服务
└── docker-compose.yml     # Docker 编排
```

## 🔧 核心功能

### 1. 六维 Agent 矩阵

| Agent | 职责 | 核心指标 |
|-------|------|----------|
| 宏观 Analyst | 宏观经济分析 | GDP/CPI/PMI、利率汇率 |
| 估值 Analyst | 资产估值分析 | PE/PB/PS、DCF/DDM |
| 资金流 Tracker | 资金流向追踪 | 北向资金、两融余额 |
| 情绪 Analyst | 市场情绪分析 | 恐贪指数、VIX |
| 行业 Analyst | 行业轮动分析 | 产业链、景气度 |
| 风控 Manager | 风险管理 | VaR、回撤、仓位建议 |

### 2. 四维分析框架

- **基本面**（40%）：GDP、PMI、CPI、企业盈利
- **资金面**（20%）：北向资金、两融余额、央行操作
- **情绪面**（15%）：恐贪指数、VIX、换手率
- **信息面**（25%）：政策文件、行业数据、舆情

### 3. 多模型路由

- **DeepSeek V4**：中国市场分析（性价比极高）
- **GPT-4o**：美股、全球市场分析
- **DeepSeek R1**：复杂推理（多因子分析、套利策略）

## 🔧 LLM 配置详解

### AIHubMix（推荐国内用户）

**官网**：https://aihubmix.com

AIHubMix 是国内的 AI API 聚合平台，提供统一接口调用多种大模型，适合国内用户使用。

**优势**：
- 🌏 国内直连，无需魔法
- 💰 价格低（DeepSeek V3 约 ¥1/百万 tokens）
- 🤖 支持多种模型（DeepSeek、GPT、Qwen、Yi 等）
- 📊 统一计费

**配置步骤**：

1. **注册账号**：访问 https://aihubmix.com 注册

2. **获取 API Key**：在控制台获取 API Key

3. **配置环境变量**：
   ```bash
   # backend/.env
   AIHUBMIX_API_KEY=your_api_key_here
   
   # 可选，自定义端点（不填用官方默认）
   # AIHUBMIX_BASE_URL=https://api.aihubmix.com/v1
   ```

4. **支持的模型**（填入配置文件即可）：
   | 模型别名 | 说明 | 价格（¥/M tokens） |
   |---------|------|-------------------|
   | `deepseek-chat` | DeepSeek V3，性价比最高 | 输入 1 / 输出 2 |
   | `deepseek-reasoner` | DeepSeek R1，复杂推理 | 输入 4 / 输出 16 |
   | `gpt-4o` | GPT-4o，英文分析强 | 输入 15 / 输出 60 |
   | `gpt-4o-mini` | GPT-4o Mini，便宜快速 | 输入 1.5 / 输出 6 |
   | `qwen-plus` | 通义千问 Plus | 输入 2 / 输出 6 |
   | `yi-large` | 零一万物 | 输入 3 / 输出 9 |

5. **验证配置**：
   ```bash
   curl -X POST http://localhost:8000/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"query": "你好"}'
   ```

### 其他 LLM 配置方案

#### DeepSeek 官方

```bash
# backend/.env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

#### OpenAI

```bash
# backend/.env
OPENAI_API_KEY=sk-xxxx
```

#### Azure OpenAI

```bash
# backend/.env
AZURE_API_KEY=your_azure_key
AZURE_BASE_URL=https://your-resource.openai.azure.com
AZURE_API_VERSION=2024-02-01
```

### 模型路由说明

配置文件中指定了默认使用的模型：

```bash
# 默认模型（用于中国市场分析）
DEFAULT_MODEL=deepseek-chat
CHINA_MODEL=deepseek-chat

# 美股/国际市场模型
US_MODEL=gpt-4o

# 复杂推理模型（用于套利策略等）
REASONING_MODEL=deepseek-reasoner
```

---

## 📊 API 使用示例

### 宏观分析

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query": "分析一下当前 A 股的宏观环境"}'
```

### 综合四维分析

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{"query": "现在适合买入 A 股吗？全面分析"}'
```

## 🤖 飞书 Bot 集成

### 配置步骤

1. 在飞书开放平台创建应用
2. 启用机器人权限
3. 配置事件订阅（Webhook 地址）
4. 填写 `.env` 中的飞书配置项

### 飞书 Bot 部署

```bash
cd feishu-bot
cp ../backend/.env.example .env
# 配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET

# 启动 Bot
python run.py

# 测试命令
python run.py --test        # 测试 Agent
python run.py --morning-report  # 生成早报
python run.py --alerts      # 检查预警
```

### 可用命令

| 命令 | 功能 |
|------|------|
| `/宏观 [国家]` | 宏观经济概览 |
| `/估值 [标的]` | 市场/行业估值 |
| `/资金 [类型]` | 资金流向 |
| `/情绪 [市场]` | 市场情绪 |
| `/分析 [标的]` | 综合四维分析 |
| `/预警 列表` | 查看预警设置 |
| `/早报` | 立即获取早报 |
| `/晚报` | 立即获取晚报 |

## 🛣️ MVP 路线图

### Phase 1: 数据基座（Week 1-4）
- [x] **Week 1**: 项目脚手架
  - 项目结构搭建（FastAPI + React + 飞书 Bot）
  - AI Agent 框架（ROLES Prompt 反幻觉）
  - AkShare Provider（基础版）
  - 意图识别路由
- [x] **Week 2**: 数据源扩展
  - Finnhub Provider（美股数据）
  - CoinGecko Provider（加密货币）
  - 数据调度器（定时采集）
  - 统一数据服务层
- [x] **Week 3**: Agent 完善
  - 估值 Analyst（PE/PB/PS 分位计算）
  - 资金流 Tracker（北向/两融追踪）
  - 情绪 Analyst（恐贪指数、VIX）
  - 风控 Manager（仓位建议、VaR、回撤）
  - API 集成所有 Agent
- [x] **Week 4**: 前端 MVP ✅
  - 四维评分可视化（渐变卡片）
  - 进度条评分展示
  - 风控建议面板
  - 深色主题 UI
  - 快捷示例

### Phase 2: Agent 矩阵（Week 5-6）
- [x] **Week 5-6**: 飞书 Bot + 异常预警 ✅
  - 飞书 Bot 完整版（命令系统）
  - 定时推送（早报 07:30、晚报 20:00）
  - 异常预警检查（每小时）
  - 多 Agent 协同分析
- [ ] **Week 7-8**: 飞书 Bot + 早晚报推送
  - 群组绑定配置
  - 预警推送到指定群
  - 前端集成实时推送

### Phase 3: 智能化（Week 9-12）
- [x] **Week 9**: 多 Agent 协同对话 ✅
  - Agent 协调器（四维综合分析）
  - 智能问题分类
  - 并行执行优化
- [x] **Week 10**: 异常预警系统 ✅
  - 预警配置管理
  - 早晚报生成
  - API 接口完善
- [x] **Week 11**: 个性化配置 ✅
  - 用户偏好管理
  - 市场/板块关注
  - 推送时间配置
- [x] **Week 12**: 历史分析向量检索 ✅
  - ChromaDB 集成
  - 相似分析检索
  - 统计分析

### Phase 3: 智能化（Week 9-12）
- [ ] 多 Agent 协同对话
- [ ] 异常预警系统
- [ ] 个性化配置
- [ ] 历史分析向量检索

## ⚙️ 技术栈

- **后端**：Python + FastAPI
- **前端**：React + TailwindCSS
- **数据库**：PostgreSQL
- **缓存**：Redis
- **向量库**：ChromaDB
- **LLM SDK**：LiteLLM
- **部署**：Docker Compose

## 📝 开发指南

### 添加新的 Agent

1. 在 `backend/agents/` 创建新文件，继承 `BaseAgent`
2. 实现 `analyze()` 方法
3. 在 `router/intent.py` 添加意图识别规则
4. 在 `api/main.py` 注册路由

### 添加新的数据源

1. 在 `backend/data/providers/` 创建新 Provider
2. 继承 `DataProvider` 基类
3. 实现数据获取方法
4. 在缓存层配置 TTL

## 📄 许可证

MIT License

---

**设计文档**：[查看详细设计文档](https://www.feishu.cn/docx/R5KXdLd1doGKKdxMXJ4cJIhynbd)
