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

# 3. 登录 GHCR（拉取私有镜像需要）
echo "<YOUR_GITHUB_PAT>" | docker login ghcr.io -u <GITHUB_USERNAME> --password-stdin
```

## 配置 AI 密钥（在服务器上操作）

`docker-compose.yml` 中已内置 DeepSeek v4 Flash 默认配置（provider、base_url、model），**只需在服务器上配置 `AI_API_KEY`**。

```bash
# SSH 登录服务器后，在各环境目录下创建 .env 文件

# Dev 环境
cat > /opt/app/dev/.env << 'EOF'
AI_API_KEY=sk-your-deepseek-api-key-here
CONSOLE_PASSWORD=your-console-password
EOF

# Prod 环境
cat > /opt/app/prod/.env << 'EOF'
AI_API_KEY=sk-your-deepseek-api-key-here
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

## GitHub Secrets 配置

部署只需要以下基础设施相关的 Secrets（AI 密钥已改为服务器本地管理）：

| Secret 名称 | 说明 | 示例值 |
|---|---|---|
| `VPS_HOST` | 服务器 IP | `124.222.206.30` |
| `VPS_USER` | SSH 用户名 | `ubuntu` |
| `VPS_PORT` | SSH 端口 | `22` |
| `VPS_SSH_KEY` | SSH 私钥（完整 PEM 内容） | `-----BEGIN RSA PRIVATE KEY-----...` |
| `VPS_APP_DIR_DEV` | dev 环境目录 | `/opt/app/dev` |
| `VPS_APP_DIR_PROD` | prod 环境目录 | `/opt/app/prod` |

> ~~`AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL` 已从 GitHub Secrets 移除，改为服务器本地 `.env` 管理。~~

## 自动化部署流程

```
开发者推送代码到 dev/main 分支
  ↓
GitHub Actions 构建 Docker 镜像
  ↓
推送镜像到 GHCR（标签: :dev 或 :main）
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

## 故障排查

| 现象 | 排查 |
|------|------|
| 容器不健康 | `docker logs maths-helper-prod` 查看日志 |
| AI 不工作 | 检查服务器 `.env` 中 `AI_API_KEY` 是否正确；`curl http://localhost/api/health` 查看 `ai_enabled` |
| 数据丢失 | 确认 `data/` 目录存在且有写权限；`docker compose config` 确认 volume 挂载 |
| 镜像拉取失败 | 服务器需先 `docker login ghcr.io`；确认 PAT 有 `read:packages` 权限 |
| 密钥泄露 | 密钥仅在服务器 `.env` 中，不经过 GitHub；修改后重启容器即可 |
