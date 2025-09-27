#!/bin/bash

# 財經理財智能系統部署腳本
# 使用方式: ./deploy.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}
PROJECT_NAME="finance-agents"

echo "🚀 開始部署財經理財智能系統 (環境: $ENVIRONMENT)"
echo "=" ×50

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ 錯誤: Docker 未安裝或不在 PATH 中"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ 錯誤: Docker Compose 未安裝或不在 PATH 中"
    exit 1
fi

# 建立必要目錄
echo "📁 建立必要目錄..."
mkdir -p logs
mkdir -p chroma_db
mkdir -p ssl
mkdir -p data

# 設定權限
chmod 755 logs chroma_db data

# 選擇部署配置
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "🏭 生產環境部署"
    COMPOSE_FILE="docker-compose.prod.yml"

    # 檢查必要的環境變數
    if [ -z "$POSTGRES_PASSWORD" ]; then
        echo "❌ 錯誤: 生產環境需要設定 POSTGRES_PASSWORD 環境變數"
        echo "   export POSTGRES_PASSWORD=your-secure-password"
        exit 1
    fi

    # 檢查 SSL 憑證
    if [ ! -f "ssl/fullchain.pem" ] || [ ! -f "ssl/privkey.pem" ]; then
        echo "⚠️  警告: SSL 憑證不存在於 ssl/ 目錄"
        echo "   請確保已放置有效的 SSL 憑證"
    fi

else
    echo "🔧 開發環境部署"
    COMPOSE_FILE="docker-compose.yml"
fi

# 停止現有容器
echo "🛑 停止現有容器..."
docker-compose -f $COMPOSE_FILE down --remove-orphans || true

# 建立 Docker 映像
echo "🏗️  建立 Docker 映像..."
docker-compose -f $COMPOSE_FILE build --no-cache

# 啟動服務
echo "▶️  啟動服務..."
docker-compose -f $COMPOSE_FILE up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 30

# 健康檢查
echo "🏥 執行健康檢查..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "✅ 服務健康檢查通過"
        break
    else
        echo "⏳ 等待服務啟動... (嘗試 $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ 健康檢查失敗，服務可能未正常啟動"
    echo "📋 查看服務日誌:"
    docker-compose -f $COMPOSE_FILE logs --tail=50
    exit 1
fi

# 顯示部署狀態
echo ""
echo "🎉 部署完成！"
echo ""
echo "📊 服務狀態:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "🔗 服務端點:"
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "  • API 服務: https://finance-agents.com"
    echo "  • API 文檔: https://finance-agents.com/docs"
    echo "  • 健康檢查: https://finance-agents.com/health"
else
    echo "  • API 服務: http://localhost:8000"
    echo "  • API 文檔: http://localhost:8000/docs"
    echo "  • 健康檢查: http://localhost:8000/health"
fi

echo ""
echo "📋 有用的指令:"
echo "  • 查看日誌: docker-compose -f $COMPOSE_FILE logs -f"
echo "  • 停止服務: docker-compose -f $COMPOSE_FILE down"
echo "  • 重啟服務: docker-compose -f $COMPOSE_FILE restart"
echo "  • 查看指標: curl http://localhost:8000/stats"

# 載入範例資料（僅開發環境）
if [ "$ENVIRONMENT" = "dev" ]; then
    echo ""
    echo "📋 載入範例資料..."
    docker-compose exec finance-api python integrate_real_cnyes_data.py || true
fi

echo ""
echo "✨ 部署完成！系統已準備就緒。"