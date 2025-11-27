#!/bin/bash
# Quick setup for SARVAI with Qdrant migration

set -e

echo "========================================="
echo "SARVAI Qdrant Migration Setup"
echo "========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose found"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.10+ first."
    exit 1
fi

PY_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PY_VERSION found"
echo ""

# Navigate to root
cd "$(dirname "$0")/.."

echo "Step 1: Stopping any running services..."
docker-compose down 2>/dev/null || true
echo "✓ Old services stopped"
echo ""

echo "Step 2: Starting services (PostgreSQL, Qdrant, MinIO)..."
docker-compose up -d
echo "✓ Services starting..."
echo ""

echo "Step 3: Waiting for services to be healthy..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U user &>/dev/null && \
       curl -s http://localhost:6333/health &>/dev/null; then
        echo "✓ All services healthy"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ Services failed to start. Check docker-compose logs"
        exit 1
    fi
    
    echo "  Waiting... ($i/30)"
    sleep 1
done
echo ""

echo "Step 4: Installing Python dependencies..."
cd backend
pip install -r requirements.txt > /dev/null
echo "✓ Dependencies installed"
echo ""

echo "Step 5: Running database migrations..."
alembic upgrade head > /dev/null
echo "✓ Migrations applied"
echo ""

echo "Step 6: Starting backend server..."
echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Services running:"
echo "  • PostgreSQL:       localhost:5432"
echo "  • Qdrant REST:      localhost:6333"
echo "  • Qdrant Dashboard: http://localhost:6333/dashboard"
echo "  • Qdrant gRPC:      localhost:6334"
echo "  • MinIO:            http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "Starting backend (press Ctrl+C to stop):"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
