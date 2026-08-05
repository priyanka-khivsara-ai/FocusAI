#!/bin/bash

echo "🚀 Starting FocusAI Local Development Environment..."

# 1. Start the Databases
echo "📦 Starting TimescaleDB and PostgreSQL via Docker..."
docker-compose up -d

# Wait a few seconds for DB to be ready
sleep 3

# 2. Start the Backend
echo "⚙️ Starting FastAPI Backend..."
cd backend
# Check if virtual environment exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "⚠️ Virtual environment '.venv' not found in backend directory. Please create it."
    exit 1
fi

# Run the backend in the background
python main.py &
BACKEND_PID=$!
cd ..

# 3. Start the Frontend
echo "🎨 Starting Next.js Frontend..."
cd frontend
# Run the frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Everything is running!"
echo "➡️  Frontend: http://localhost:3000"
echo "➡️  Backend API: http://localhost:8000"
echo "Press [CTRL+C] to stop all services."

# Trap CTRL+C (SIGINT) and kill background processes
trap "echo '🛑 Stopping all services...'; kill $BACKEND_PID; kill $FRONTEND_PID; docker-compose stop; exit" SIGINT SIGTERM

# Wait indefinitely to keep the script running and trap active
wait
