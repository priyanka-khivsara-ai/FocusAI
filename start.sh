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

# 4. (Optional) Start Cloudflare Tunnel
TUNNEL_PID=""
if [[ "$1" == "--tunnel" || "$1" == "-t" ]]; then
    # Run cloudflared and write output to a temporary log to extract the URL
    cloudflared tunnel --url http://localhost:3000 > tunnel.log 2>&1 &
    TUNNEL_PID=$!
    
    echo -n "🌍 Waiting for Cloudflare Tunnel to initialize (this can take up to 10 seconds)"
    TUNNEL_URL=""
    for i in {1..20}; do
        TUNNEL_URL=$(grep -o 'https://.*\.trycloudflare\.com' tunnel.log | tail -n 1)
        if [ -n "$TUNNEL_URL" ]; then
            echo " Done!"
            break
        fi
        sleep 1
        echo -n "."
    done
    
    if [ -z "$TUNNEL_URL" ]; then
        echo -e "\n⚠️ Cloudflare Tunnel took too long to start. It may still be booting up in the background."
    fi
fi

echo ""
echo "✅ Everything is running!"
echo "➡️  Frontend (Local): http://localhost:3000"
echo "➡️  Backend API:      http://localhost:8000"
if [ -n "$TUNNEL_URL" ]; then
    echo "🌍 Public Link:       $TUNNEL_URL"
    echo "   (Open this on your phone/external device)"
else
    echo "ℹ️  Tip: To test on your phone over the internet, run: ./start.sh --tunnel"
fi
echo "Press [CTRL+C] to stop all services."

# Trap CTRL+C (SIGINT) and kill background processes
trap "echo '🛑 Stopping all services...'; kill $BACKEND_PID; kill $FRONTEND_PID; [ -n \"$TUNNEL_PID\" ] && kill $TUNNEL_PID; docker-compose stop; rm -f tunnel.log; exit" SIGINT SIGTERM

# Wait indefinitely to keep the script running and trap active
wait
