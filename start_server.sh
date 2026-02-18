#!/bin/bash
set -a
source .env
set +a
exec uv run uvicorn server.app:app --reload --host 0.0.0.0 --port 8000 --reload-dir server --reload-dir mlflow_demo
