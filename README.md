# 数学思维训练助手 v0.1.4

[English Documentation](./README_EN.md)

> 一个通过可视化、互动式引导，帮助学生看清数学思考过程的训练工具。

在线体验： [Dev（开发）](https://maths-dev.m1in.com) ｜ [Prod（生产）](https://maths.m1in.com)

## 创意来源

在AI时代，学生依赖搜题软件，导致"一看就懂，一做就错"的情况频繁发生，而学生自身却缺乏真正的解题思维。本项目旨在通过可视化、互动式引导，让学生看清思考过程，从根源上训练数学逻辑能力。

## v0.1.4 更新亮点

- 🧠 **MiniMax-M3 多模态 OCR** - 新增几何图形与公式识别支持，提供降级保障
- 🔀 **苏格拉底提问三重升级** - A+B+C 三种提问策略组合
- ⚙️ **动态步数统计** - session 总步数实时计算，更准确展示进度

## v0.1.3 更新亮点

- 🤖 **三合一 AI 流程** - OCR + 解析 + 首题一次调用完成，减少等待
- 🧹 **MiniMax-M3 优化** - 过滤 `<think>` 推理块，优化几何图形、阴影区域与多语言支持
- 📦 **JS Bundle 路由级拆分** - 优化加载性能，移除 Trae 徽章

## v0.1.2 更新亮点

- 📱 **移动端适配** - 全面响应式布局优化，支持手机、平板等移动设备访问

## v0.0.4 更新亮点

- 🌐 **完整国际化** - 支持中文（简体）和英文两种语言
- 🔀 **一键切换** - 右上角语言切换按钮，实时切换界面语言
- 🎨 **i18n 架构** - 基于 React Context 的轻量级翻译系统

## 核心功能

- **思维可视化** - 将解题过程拆解为多个思维节点，以图形化方式呈现
- **苏格拉底式提问** - 通过引导式提问，培养学生独立思考能力
- **探索式学习** - 允许学生走弯路，顺着用户的思路生成节点，错误时温和回退提示
- **图片识别** - 支持上传题目图片，自动识别文字内容（Tesseract OCR）
- **AI 智能辅助** - 接入大模型 API（支持 OpenAI / 通义千问 / 文心一言），实现智能题目解析和动态提问
- **多题型支持** - 支持方程求解、几何证明、通用数学题等多种题型

### 思维导图说明

| 节点类型 | 图标 | 颜色 | 含义 |
|----------|------|------|------|
| 题目节点 | 📋 | 蓝色 | 初始题目展示 |
| 正确步骤 | ✓ | 绿色 | 用户选择正确答案后的思考路径 |
| 探索节点 | ? | 橙色 | 用户选择错误答案时的探索尝试 |
| 死胡同 | ⚠️ | 红色 | 连续错误后触发回退提示 |

**设计理念**: 不预设"正确分析路径"，只显示题目。用户的每一次思考都会被记录在图上——无论对错。

## 技术栈

### 前端
- React 18 + TypeScript
- Vite 构建工具
- ReactFlow 思维导图可视化
- Zustand 状态管理
- TailwindCSS 样式
- Lucide 图标库
- **i18n 国际化** (React Context + 翻译文件)

### 后端
- Python FastAPI (异步)
- Tesseract OCR (图片文字识别)
- httpx (HTTP 客户端)
- 会话管理 (30分钟超时自动清理)

### AI 支持 (可选)

| 提供商 | 模型示例 | 说明 |
|--------|----------|------|
| OpenAI | gpt-3.5-turbo, gpt-4, gpt-4o | 需要 API Key |
| 通义千问 | qwen-plus, qwen-max | 需要 DashScope API Key |
| 文心一言 | ernie-bot-4, ernie-bot-turbo | 需要 Baidu Access Token |

> 不配置 AI 也可运行，系统会使用内置的默认逻辑作为降级方案。

## 快速开始

### 前置要求
- Node.js 18+ 和 npm
- Python 3.10+
- [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) (用于图片识别，可选)

### 安装

1. **克隆项目**
```bash
git clone <repository-url>
cd Math_Helper
```

2. **安装前端依赖**
```bash
npm install
```

3. **安装后端依赖**
```bash
pip install -r api/requirements.txt
```

4. **配置环境变量 (AI 功能)**

   复制环境变量模板并编辑：

   ```bash
   cp .env.example .env
   ```

   编辑 `.env` 文件，填入你的 API 配置：

   ```env
   # 选择AI提供商: openai, qwen(通义千问), baidu(文心一言)
   AI_PROVIDER=qwen

   # API密钥
   AI_API_KEY=your-api-key-here

   # API基础URL (可选，留空使用默认值)
   # OpenAI: https://api.openai.com/v1
   # 通义千问: https://dashscope.aliyuncs.com/compatible-mode/v1
   # 文心一言: https://aip.baidubce.com
   AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

   # 模型名称 (可选)
   AI_MODEL=qwen-plus
   ```

5. **安装 Tesseract-OCR** (可选，用于图片识别功能)
   - Windows: 从 [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki) 下载安装
   - 将 Tesseract 添加到系统环境变量 PATH

### 运行

1. **启动后端服务**
```bash
python api/server.py
```
后端运行在 http://localhost:8000

2. **启动前端开发服务器**
```bash
npm run dev
```
前端运行在 http://localhost:5173

3. **验证 AI 状态**
```bash
curl http://localhost:8000/health
# 返回: {"status":"ok","version":"0.1.4","ai_enabled":true,"ai_provider":"qwen"}
```

## 项目结构

```
Math_Helper/
├── api/                          # Python FastAPI 后端
│   ├── server.py                 # 服务器入口 + 路由定义
│   ├── models.py                 # Pydantic 数据模型
│   ├── session_store.py          # 会话存储管理 (含过期清理)
│   ├── problem_parser.py         # 题目解析 (仅返回题目节点)
│   ├── question_generator.py     # 苏格拉底式提问生成器 (探索+回退机制)
│   ├── ai_service.py             # 大模型 API 服务 (OpenAI/Qwen/Baidu)
│   ├── ocr_service.py            # OCR 图片文字识别服务
│   └── requirements.txt          # Python 依赖
├── src/                          # React 前端
│   ├── api/index.ts              # API 调用封装
│   ├── i18n/                     # 国际化模块 (新增)
│   │   ├── I18nContext.tsx       # 语言上下文 (React Context)
│   │   ├── zh-CN.ts              # 中文翻译
│   │   └── en-US.ts              # 英文翻译
│   ├── store/useStore.ts         # Zustand 状态管理
│   ├── types/index.ts            # TypeScript 类型定义
│   ├── components/
│   │   ├── DeductionFlow.tsx     # ReactFlow 思维节点图 (6种节点样式)
│   │   └── QuestionPanel.tsx     # 提问交互面板 (支持回退提示)
│   └── pages/
│       ├── Home.tsx              # 主页 (含语言切换按钮)
│       ├── ProblemInput.tsx      # 题目输入页 (支持图片上传+OCR识别)
│       └── Deduction.tsx         # 思维推演页
├── .env.example                  # 环境变量模板
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 使用场景

- **课后练习** - 学生独立完成作业，培养自主解题能力
- **教师辅导** - 可视化思维过程，帮助教师讲解解题思路
- **家庭学习** - 家长可辅助孩子进行思维训练
- **国际学生** - 支持中英文切换，适合不同语言环境

## 使用流程

1. 访问主页 → 点击"开始使用"
2. 输入数学题目或上传图片（自动 OCR 识别）
3. 点击"开始推演"
4. 左侧显示**只有题目节点**的思维导图
5. 右侧面板出现第一个引导问题
6. 选择答案后：
   - ✅ **正确** → 绿色节点加入导图，进入下一步
   - ❓ **错误** → 橙色探索节点加入导图，继续追问
   - ⚠️ **连续错误** → 红色死胡同节点 + 回退提示，重新提问
7. 完成所有步骤后查看完整解题回顾

## 语言切换

在主页右上角点击语言按钮即可切换界面语言：
- 中文界面 → 按钮显示 `EN`
- 英文界面 → 按钮显示 `中文`

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/problem/submit` | POST | 提交题目，返回初始节点（仅题目） |
| `/question/answer` | POST | 提交答案，获取反馈和新节点 |
| `/ocr/recognize` | POST | 上传图片，返回识别文字 |
| `/health` | GET | 健康检查（含 AI 状态） |

## 自动部署（GitHub Actions + 腾讯云 CCR + Docker Compose）

> push `dev` 或 `main` 分支即可自动构建镜像并部署到腾讯云 VPS 的对应环境。

### 架构

```
本地 Trae / Claude Code / Codex
        ↓  git push origin dev / main
GitHub Actions 自动构建 Docker 镜像
        ↓
推送到腾讯云 CCR 个人版镜像仓库（ccr.ccs.tencentyun.com）
        ↓  Watchtower 自动检测 / SSH 手动
腾讯云 VPS 拉取新镜像并重启容器
        ↓
dev 环境  → https://maths-dev.m1in.com  (dev 分支)
prod 环境 → https://maths.m1in.com      (main 分支)
```

### 访问二维码

| 环境 | 地址 | 二维码 |
|------|------|--------|
| Dev（开发） | https://maths-dev.m1in.com | ![Dev 访问二维码](https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=https%3A%2F%2Fmaths-dev.m1in.com) |
| Prod（生产） | https://maths.m1in.com | ![Prod 访问二维码](https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=https%3A%2F%2Fmaths.m1in.com) |

镜像内 **nginx 托管前端静态文件 + 反向代理 `/api/` 到 uvicorn:8000**（去掉 `/api` 前缀），完整复刻本地开发时 Vite 的代理行为，前后端代码零改动。

### 双环境策略

| 环境 | 分支 | 端口 | 镜像标签 | 容器名 | 数据目录 |
|------|------|------|---------|--------|---------|
| Dev  | `dev` | 18080 | `:dev` | maths-helper-dev | `/data/server/maths-dev/data/` |
| Prod | `main` | 28080 | `:main` | maths-helper-prod | `/data/server/maths-prod/data/` |

两个环境同机隔离，各自持有独立的 `.env`、SQLite 数据卷（持久化，重部署不丢失）。

### VPS 一次性准备

```bash
# 创建双环境目录
sudo mkdir -p /data/server/{maths-dev,maths-prod}
sudo chown -R $USER:$USER /data/server

# 登录腾讯云 CCR（拉取镜像需要）
echo "<YOUR_PASSWORD>" | docker login ccr.ccs.tencentyun.com -u <YOUR_USERNAME> --password-stdin
```

> `.env` 文件无需手动创建 — GitHub Actions 部署时自动从 Secrets 生成。

### GitHub Secrets 配置

在仓库 **Settings → Secrets and variables → Actions** 中配置：

| Secret | 说明 | 示例值 |
|--------|------|--------|
| `VPS_HOST` | 腾讯云服务器公网 IP | `124.222.206.30` |
| `VPS_USER` | SSH 用户 | `ubuntu` |
| `VPS_PORT` | SSH 端口 | `22` |
| `VPS_SSH_KEY` | SSH 私钥全文 | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `VPS_APP_DIR_DEV` | dev 环境目录 | `/data/server/maths-dev` |
| `VPS_APP_DIR_PROD` | prod 环境目录 | `/data/server/maths-prod` |
| `TENCENT_REGISTRY_USERNAME` | 腾讯云 CCR 用户名 | `24220712` |
| `TENCENT_REGISTRY_PASSWORD` | 腾讯云 CCR 密码 | （对应密码） |
| `CONSOLE_PASSWORD` | 管理控制台密码 | 自定义强密码 |

> AI 密钥（`AI_API_KEY`）在服务器本地 `.env` 管理，不经过 GitHub。部署 SSH 仅在配置了 `VPS_HOST` 时执行，否则依赖 Watchtower 自动更新。

### 本地验证镜像

```bash
docker build -t maths-helper:test .
docker run --rm -p 18080:80 --env-file ./.env.example maths-helper:test
# 浏览器打开 http://localhost:18080 确认前端加载
curl http://localhost:18080/api/health
```

### 相关文件

| 文件 | 说明 |
|------|------|
| `Dockerfile` | 多阶段构建：node 构建前端 + python 运行时 + nginx + tesseract + curl |
| `nginx.conf` | 静态托管 + `/api/` 反代到 :8000 + SPA 回退 |
| `docker-entrypoint.sh` | 容器启动脚本（uvicorn + nginx） |
| `docker-compose.dev.yml` | dev 环境编排（`:dev` 镜像 + 18080:80 + 数据卷 + 健康检查） |
| `docker-compose.prod.yml` | prod 环境编排（`:main` 镜像 + 28080:80 + 数据卷 + 健康检查） |
| `.github/workflows/deploy.yml` | GitHub Actions CI/CD 工作流（双环境） |
| `deploy/README.md` | 服务器初始化与故障排查详细指南 |
| `.env.example` | 环境变量模板（AI / 控制台密码 / CORS） |

## 许可证

本项目仅供教育和学习使用。
