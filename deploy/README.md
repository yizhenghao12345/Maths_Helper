# 部署指南

> 生产服务器 4C4G Ubuntu，Docker 部署，dev/main 双环境同机运行。

## 目录结构（服务器端）

```
/opt/app/
├── dev/                  # dev 环境
│   ├── docker-compose.yml   # ← docker-compose.dev.yml
│   ├── .env                 # ← 由 GitHub Actions 自动生成
│   └── data/                # SQLite 持久化（自动创建）
└── prod/                 # prod 环境
    ├── docker-compose.yml   # ← docker-compose.prod.yml
    ├── .env                 # ← 由 GitHub Actions 自动生成
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

## GitHub Secrets 配置

在仓库 **Settings → Secrets and variables → Actions** 中配置以下 Secrets：

| Secret 名称 | 说明 | 示例值 |
|---|---|---|
| `VPS_HOST` | 服务器 IP | `124.222.206.30` |
| `VPS_USER` | SSH 用户名 | `ubuntu` |
| `VPS_PORT` | SSH 端口 | `22` |
| `VPS_SSH_KEY` | SSH 私钥（完整 PEM 内容） | `-----BEGIN RSA PRIVATE KEY-----...` |
| `VPS_APP_DIR_DEV` | dev 环境目录 | `/opt/app/dev` |
| `VPS_APP_DIR_PROD` | prod 环境目录 | `/opt/app/prod` |
| `AI_API_KEY` | AI 服务密钥 | `sk-...` |
| `AI_BASE_URL` | AI 服务端点 | `https://ahbb.m1in.com/v1` |
| `AI_MODEL` | 默认 AI 模型 | `deepseek-v4-flash` |
| `CONSOLE_PASSWORD` | 管理控制台密码 | 自定义强密码 |

> **安全提醒**：`AI_API_KEY`、`VPS_SSH_KEY`、`CONSOLE_PASSWORD` 属高危凭证，切勿写入代码或 `.env.deploy` 以外的明文文件。`.env.deploy` 已被 `.gitignore` 排除，仅作为本地备忘。

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
用 GitHub Secrets 生成 .env
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
```

## 故障排查

| 现象 | 排查 |
|------|------|
| 容器不健康 | `docker logs maths-helper-prod` 查看日志 |
| AI 不工作 | 检查 `.env` 中 `AI_API_KEY` / `AI_BASE_URL` 是否正确；`curl http://localhost/api/health` 查看 `ai_enabled` |
| 数据丢失 | 确认 `data/` 目录存在且有写权限；`docker compose config` 确认 volume 挂载 |
| 镜像拉取失败 | 服务器需先 `docker login ghcr.io`；确认 PAT 有 `read:packages` 权限 |
