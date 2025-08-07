#!/bin/bash

set -e


# source .env and .env.local if they exist
if [ -f ".env" ]; then
  echo "Loading .env"
  export $(grep -v '^#' .env | xargs)
fi
if [ -f ".env.local" ]; then
  echo "Loading .env.local"
  export $(grep -v '^#' .env.local | xargs)
fi

# Set UVICORN_PORT with default value of 8000
UVICORN_PORT=${UVICORN_PORT:-8000}

# if [ ! -z "$DATABRICKS_CONFIG_PROFILE" ]; then
#   databricks auth login --profile $DATABRICKS_CONFIG_PROFILE
# else
#   databricks auth login
# fi

uv run python -m scripts.make_fastapi_client

pushd client && BROWSER=none bun run dev | cat && popd &
pid[2]=$!

uv run uvicorn server.app:app --reload --host 0.0.0.0 --port $UVICORN_PORT --reload-dir server --reload-dir mlflow_demo &
pid[1]=$!

uv run watchmedo auto-restart \
  --patterns="*.py" \
  --debounce-interval=1 \
  --no-restart-on-command-exit \
  --recursive \
  --directory=server \
  uv -- run python -m scripts.make_fastapi_client &
pid[0]=$!

# sleep 2 && open "http://localhost:$UVICORN_PORT"

# Enhanced cleanup function
cleanup() {
  echo "Shutting down all processes..."

  # Kill tracked process IDs
  pkill -P $$

  # Kill anything running on port $UVICORN_PORT (uvicorn server)
  echo "Killing processes on port $UVICORN_PORT..."
  lsof -ti:$UVICORN_PORT | xargs kill -TERM 2>/dev/null || true

  # Kill anything running on port 3000 (client dev server)
  echo "Killing processes on port 3000..."
  lsof -ti:3000 | xargs kill -TERM 2>/dev/null || true

  # Also kill any remaining child processes
  pkill -P $$ 2>/dev/null || true

  # Wait a moment for graceful shutdown
  sleep 2

  # Force kill anything still on ports
  echo "Force killing remaining processes on ports..."
  lsof -ti:$UVICORN_PORT | xargs kill -9 2>/dev/null || true
  lsof -ti:3000 | xargs kill -9 2>/dev/null || true

  echo "Cleanup complete"
  exit 0
}

# When control+c is pressed, run cleanup function
trap cleanup INT TERM EXIT
wait
