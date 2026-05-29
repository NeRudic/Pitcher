#!/bin/bash
set -e

echo "=== Piano Performance Analyzer ==="

# Start uvicorn in the background
echo "[1/2] Starting backend on http://127.0.0.1:8000 ..."
python -m uvicorn main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
for i in $(seq 1 30); do
    if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" 2>/dev/null; then
        echo "  Backend is ready."
        break
    fi
    sleep 2
done

# Start nginx in the foreground (runs until the container stops)
echo "[2/2] Starting nginx on port 80 ..."
nginx -g "daemon off;" &
NGINX_PID=$!

# Forward signals to both processes
cleanup() {
    echo "Shutting down..."
    kill $NGINX_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    wait
    exit 0
}
trap cleanup SIGTERM SIGINT

# Wait for either process to exit
wait -n $NGINX_PID $BACKEND_PID
cleanup
