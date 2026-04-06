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
docker-compose up -d
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
3. 配置 Webhook 地址
4. 填写 `.env` 中的飞书配置项

### 可用命令

| 命令 | 功能 |
|------|------|
| `/宏观` | 宏观经济概览 |
| `/估值` | 市场/行业估值 |
| `/资金` | 资金流向 |
| `/情绪` | 市场情绪 |
| `/分析` | 综合四维分析 |
| `/预警` | 查看/设置预警 |

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
- [ ] **Week 3**: Agent 完善
  - 估值 Analyst
  - 资金流 Tracker
  - 情绪 Analyst
- [ ] **Week 4**: 前端 MVP
  - 图表可视化
  - 历史记录
  - 四维评分雷达图

### Phase 2: Agent 矩阵（Week 5-8）
- [ ] 6 个 Agent 完整上线
- [ ] 四维评分系统
- [ ] 飞书 Bot + 早晚报推送

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
