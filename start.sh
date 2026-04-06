#!/bin/bash

# LLM 投资分析平台 - 快速启动脚本

set -e

echo "🦞 LLM 投资分析平台 - 快速启动"
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
    echo "⚠️  请编辑 backend/.env 文件，填入必要的配置"
    echo ""
    read -p "是否继续启动？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 启动服务
echo "🚀 启动服务..."
docker-compose up -d

# 等待服务就绪
echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 健康检查
echo "🔍 检查服务状态..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务正常"
else
    echo "⚠️  后端服务可能还未完全启动，请稍后检查"
fi

echo ""
echo "================================"
echo "🎉 服务启动成功！"
echo ""
echo "📱 访问地址："
echo "   前端界面：http://localhost:3000"
echo "   后端 API：http://localhost:8000"
echo "   飞书 Bot：http://localhost:8001 (需单独配置)"
echo ""
echo "📊 查看日志："
echo "   docker-compose logs -f"
echo ""
echo "🛑 停止服务："
echo "   docker-compose down"
echo "================================"
