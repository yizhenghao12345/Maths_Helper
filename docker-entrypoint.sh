#!/usr/bin/env bash
set -e

# 启动后端 FastAPI（后台运行）
cd /app/api
uvicorn server:app --host 127.0.0.1 --port 8000 &

# 前台启动 nginx（保持容器运行）
nginx -g 'daemon off;'
