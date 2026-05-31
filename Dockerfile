# ---------- Stage 1: 构建前端静态文件 ----------
FROM node:20-slim AS frontend-build
WORKDIR /build

# 先复制依赖清单以利用层缓存
COPY package.json package-lock.json ./
RUN npm ci

# 复制源码并构建（产出 dist/）
COPY . .
RUN npm run build

# ---------- Stage 2: 运行时（nginx 托管前端 + uvicorn 跑后端）----------
FROM python:3.11-slim AS runtime

# nginx 反向代理 + tesseract OCR（含中文语言包）+ curl（容器健康检查用）
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        nginx \
        tesseract-ocr \
        tesseract-ocr-chi-sim \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装后端依赖
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

# 拷贝后端代码
COPY api/ /app/api/

# 拷贝前端构建产物到 nginx 静态目录
COPY --from=frontend-build /build/dist/ /usr/share/nginx/html/

# nginx 配置与启动脚本
# 删除 Debian nginx 自带的默认站点（listen 80 default_server，会抢占 /api/ 转发导致 404）
RUN rm -f /etc/nginx/sites-enabled/default
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

CMD ["/docker-entrypoint.sh"]
