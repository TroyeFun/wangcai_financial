#!/bin/bash

# ============================================================
# LLM 投资分析平台 - 一键部署脚本
# ============================================================

set -e

echo "🦞 LLM 投资分析平台 - 一键部署"
echo "================================"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 进入项目目录
cd "$(dirname "$0")"

# 检查环境变量文件
if [ ! -f "backend/.env" ]; then
    echo "⚙️  创建环境变量文件..."
    cp backend/.env.example backend/.env
    echo ""
    echo "⚠️  请编辑 backend/.env 文件，填入必要的配置："
    echo "   - AIHUBMIX_API_KEY（推荐）或 DEEPSEEK_API_KEY"
    echo "   - FEISHU_APP_ID 和 FEISHU_APP_SECRET（如需飞书 Bot）"
    echo "   - FINNHUB_API_KEY（如需美股数据）"
    echo ""
    echo "按 Enter 继续，或 Ctrl+C 退出..."
    read
fi

# 清理旧容器
echo "🧹 清理旧容器..."
docker-compose down -v 2>/dev/null || true

# 构建镜像
echo "🔨 构建 Docker 镜像..."
docker-compose build --no-cache

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务就绪
echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 健康检查
echo "🔍 检查服务状态..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务正常"
else
    echo "⚠️  后端服务可能还未完全启动，请稍后检查"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 前端服务正常"
else
    echo "⚠️  前端服务可能还未完全启动"
fi

echo ""
echo "================================"
echo "🎉 部署完成！"
echo ""
echo "📱 访问地址："
echo "   🌐 前端界面：http://localhost:3000"
echo "   🔧 后端 API：http://localhost:8000"
echo "   📊 API 文档：http://localhost:8000/docs"
echo "   🤖 飞书 Bot：http://localhost:8001"
echo ""
echo "📋 常用命令："
echo "   查看日志：docker-compose logs -f"
echo "   停止服务：docker-compose down"
echo "   重启服务：docker-compose restart"
echo "================================"
