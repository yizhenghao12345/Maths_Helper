# 部署指南

> 生产服务器 4C4G Ubuntu，Docker 部署，dev/main 双环境同机运行。

## 目录结构（服务器端）

```
/opt/app/
├── dev/                  # dev 环境
│   ├── docker-compose.yml   # ← docker-compose.dev.yml（由 GitHub Actions 自动上传）
│   ├── .env                 # ← 服务器本地维护，包含 AI 密钥等敏感配置
│   └── data/                # SQLite 持久化（自动创建）
└── prod/                 # prod 环境
    ├── docker-compose.yml   # ← docker-compose.prod.yml（由 GitHub Actions 自动上传）
    ├── .env                 # ← 服务器本地维护，包含 AI 密钥等敏感配置
    └── data/                # SQLite 持久化（自动创建）
```

| 环境 | 端口 | 镜像标签 | 容器名 | 触发分支 |
|------|------|---------|--------|---------|
| Dev  | 18080 | `:dev` | maths-helper-dev | `dev` |
| Prod | 80    | `:main` | maths-helper-prod | `main` |

## 服务器初始化（一次性）

```bash
# 1. 创建环境目录
ssh ubuntu@<YOUR_VPS>
sudo mkdir -p /opt/app/{dev,prod}
sudo chown -R $USER:$USER /opt/app

# 2. 安装 Docker（如未安装）
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# 重新登录使 docker 组生效

# 3. 登录腾讯云 CCR（拉取镜像需要）
echo "<YOUR_PASSWORD>" | docker login ccr.ccs.tencentyun.com -u <YOUR_USERNAME> --password-stdin
```

## 配置 AI 密钥（在服务器上操作）

`docker-compose.yml` 中已内置默认模型配置：

- AI：DeepSeek v4 Flash（`AI_PROVIDER`/`AI_BASE_URL`/`AI_MODEL`）
- OCR：MiniMax-M3（`OCR_PROVIDER`/`OCR_BASE_URL`/`OCR_MODEL`）

服务器上只需配置对应的 Key（不配 OCR key 会自动降级到本地 Tesseract）。

```bash
# SSH 登录服务器后，在各环境目录下创建 .env 文件

# Dev 环境
cat > /opt/app/dev/.env << 'EOF'
AI_API_KEY=sk-your-deepseek-api-key-here
OCR_API_KEY=sk-your-minimax-api-key-here
CONSOLE_PASSWORD=your-console-password
EOF

# Prod 环境
cat > /opt/app/prod/.env << 'EOF'
AI_API_KEY=sk-your-deepseek-api-key-here
OCR_API_KEY=sk-your-minimax-api-key-here
CONSOLE_PASSWORD=your-console-password
EOF
```

> **说明**：
> - `AI_PROVIDER`、`AI_BASE_URL`、`AI_MODEL` 已在 docker-compose 的 `environment` 中预设为 DeepSeek，`.env` 中无需重复配置。
> - 如需切换 AI 提供商，在 `.env` 中覆盖对应变量即可（`.env` 优先级高于 `environment`）。
> - **部署流程不会覆盖服务器上的 `.env` 文件**，密钥仅在服务器本地维护，无需通过 GitHub 管理。

### 默认 AI 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AI_PROVIDER` | `deepseek` | AI 提供商 |
| `AI_BASE_URL` | `https://api.deepseek.com/v1` | API 端点 |
| `AI_MODEL` | `deepseek-v4-flash` | 模型名称（免费额度） |
| `AI_API_KEY` | （无默认值） | **必须在服务器 .env 中配置** |

### 默认 OCR 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OCR_PROVIDER` | `minimax` | OCR 提供商 |
| `OCR_BASE_URL` | `https://api.minimaxi.com/v1` | API 端点 |
| `OCR_MODEL` | `MiniMax-M3` | 多模态 OCR 模型 |
| `OCR_API_KEY` | （无默认值） | 可选：不配置则降级到本地 Tesseract |

## GitHub Secrets 配置

部署只需要以下基础设施相关的 Secrets（AI 密钥已改为服务器本地管理）：

| Secret 名称 | 说明 | 示例值 |
|---|---|---|
| `VPS_HOST` | 服务器 IP | `124.222.206.30` |
| `VPS_USER` | SSH 用户名 | `ubuntu` |
| `VPS_PORT` | SSH 端口 | `22` |
| `VPS_SSH_KEY` | SSH 私钥（完整 PEM 内容） | `-----BEGIN RSA PRIVATE KEY-----...` |
| `VPS_APP_DIR_DEV` | dev 环境目录 | `/data/server/maths-dev` |
| `VPS_APP_DIR_PROD` | prod 环境目录 | `/data/server/maths-prod` |
| `TENCENT_REGISTRY_USERNAME` | 腾讯云 CCR 用户名 | `24220712` |
| `TENCENT_REGISTRY_PASSWORD` | 腾讯云 CCR 密码 | （对应密码） |

> ~~`AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL` 已从 GitHub Secrets 移除，改为服务器本地 `.env` 管理。~~

## 自动化部署流程

```
开发者推送代码到 dev/main 分支
  ↓
GitHub Actions 构建 Docker 镜像
  ↓
推送镜像到腾讯云 CCR（标签: :dev 或 :main）
  ↓
SSH 连接服务器
  ↓
上传对应 docker-compose.yml
  ↓
保留服务器本地 .env（不覆盖）
  ↓
docker compose pull && up -d
```

## 手动操作

```bash
# 查看运行状态
docker ps                    # 两个容器应显示 healthy
docker compose -f /opt/app/prod/docker-compose.yml logs -f

# 手动重启
docker compose -f /opt/app/prod/docker-compose.yml restart

# 查看数据
ls -la /opt/app/prod/data/   # SQLite 数据库文件

# 更新 AI 密钥（修改后需重启容器生效）
vim /opt/app/prod/.env       # 编辑 AI_API_KEY
docker compose -f /opt/app/prod/docker-compose.yml up -d
```

## 自动更新（Watchtower）

两个环境的 `docker-compose.yml` 已集成 [Watchtower](https://containrrr.github.io/watchtower/)，每 5 分钟自动检查腾讯云 CCR 上是否有新镜像，发现新版本后自动拉取并重启容器。

| 环境 | Watchtower 容器 | 监控 scope | 检查间隔 |
|------|----------------|-----------|---------|
| Dev  | `watchtower-dev`  | `dev`  | 300s (5min) |
| Prod | `watchtower-prod` | `prod` | 300s (5min) |

- **scope 隔离**：通过 `--scope` 参数和容器 label，dev 的 Watchtower 只更新 dev 容器，prod 同理，互不干扰。
- **`--cleanup`**：更新后自动删除旧镜像，避免磁盘堆积。
- **开箱即用**：随 `docker compose up -d` 一起启动，无需额外配置。

```bash
# 查看 Watchtower 日志（确认更新是否触发）
docker logs watchtower-prod -f
docker logs watchtower-dev -f
```

> 如需调整检查间隔，修改 `docker-compose.yml` 中 `command: --interval 300` 的数值（单位：秒）。

## 故障排查

| 现象 | 排查 |
|------|------|
| 容器不健康 | `docker logs maths-helper-prod` 查看日志 |
| AI 不工作 | 检查服务器 `.env` 中 `AI_API_KEY` 是否正确；`curl http://localhost/api/health` 查看 `ai_enabled` |
| 数据丢失 | 确认 `data/` 目录存在且有写权限；`docker compose config` 确认 volume 挂载 |
| 镜像拉取失败 | 服务器需先 `docker login ccr.ccs.tencentyun.com`；确认账号密码正确 |
| 密钥泄露 | 密钥仅在服务器 `.env` 中，不经过 GitHub；修改后重启容器即可 |
| 自动更新未生效 | 检查 Watchtower 容器是否运行（`docker ps | grep watchtower`）；查看日志确认是否检测到新镜像 |
