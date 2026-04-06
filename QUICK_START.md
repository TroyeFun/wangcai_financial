# 🦞 快速预览指南

## 方式一：本地运行（推荐）

### 1. 安装 Node.js

如果还没安装，访问 https://nodejs.org/ 下载安装（建议 v18+）

### 2. 进入前端目录

```bash
cd investment-analysis/frontend
```

### 3. 安装依赖

```bash
npm install
```

### 4. 启动开发服务器

```bash
npm run dev
```

### 5. 打开浏览器

访问 http://localhost:3000

---

## 方式二：直接用 Docker

```bash
cd investment-analysis
./start.sh
```

然后访问 http://localhost:3000

---

## 🎯 可以试的功能

1. **快捷示例** - 点击预设问题直接看效果
   - "现在适合买入 A 股吗？" → 触发四维综合分析
   - "分析一下当前宏观环境" → 只看宏观分析
   - "沪深 300 估值如何？" → 只看估值分析

2. **Tab 切换** - 查看不同维度的分析
   - 全部：显示所有 Agent 的分析
   - 宏观/估值/资金/情绪：单独查看

3. **综合评分** - 自动计算四个维度的平均分，给出建议

4. **风控建议** - 根据综合评分给出仓位建议

---

## 📱 界面预览

- 顶部：大标题 + 输入框
- 中间：综合评分卡片（蓝色渐变）
- 下方：各个 Agent 的分析卡片（带数据表格）
- 底部：风控经理建议（黄色警告框）

---

## ⚠️ 注意事项

- 当前是 **Mock 数据演示版**，数据是写死的
- Week 2 会接入真实数据（AkShare、Finnhub 等）
- 后端 API 已写好，配置好环境变量即可启用

---

**设计文档**: https://www.feishu.cn/docx/R5KXdLd1doGKKdxMXJ4cJIhynbd
