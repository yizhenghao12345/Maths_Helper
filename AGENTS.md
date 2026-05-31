# AGENTS.md

本文件为所有 AI Coding 工具（Claude Code / Codex / Trae / GLM 等）共用的项目说明。
`CLAUDE.md` 通过引用本文件复用内容，请勿维护多份。

## 项目简介

数学思维训练助手 —— 通过可视化、互动式的苏格拉底式引导，帮助学生看清数学解题的思考过程，从根源训练数学逻辑能力。不预设"正确路径"，记录用户每一次思考（无论对错）。

## 技术栈

**前端**：React 18 + TypeScript · Vite 6 · ReactFlow (`@xyflow/react`) 思维导图 · Zustand 状态管理 · TailwindCSS 3 · react-router-dom 7 · lucide-react 图标 · React Context 国际化

**后端**：Python 3.10+ · FastAPI（异步）· pytesseract（OCR 图片识别）· httpx · python-dotenv · 内存会话管理（30 分钟超时清理）

**AI（可选）**：OpenAI / 通义千问(qwen) / 文心一言(baidu)，通过 `.env` 配置。不配置则降级为内置默认逻辑。

## 常用命令

```bash
# 前端
npm install            # 安装依赖
npm run dev            # 开发服务器 http://localhost:5173
npm run build          # tsc -b && vite build
npm run check          # tsc -b --noEmit 类型检查
npm run lint           # eslint .

# 后端（在仓库根目录运行）
pip install -r api/requirements.txt
python api/server.py   # 启动入口，运行在 http://localhost:8000
curl http://localhost:8000/health   # 健康检查（含 AI 状态）
```

> Vite dev server 已将 `/api` 代理到 `http://localhost:8000`（见 `vite.config.ts`，自动去掉 `/api` 前缀）。

## 项目结构

```
api/                       # Python FastAPI 后端
├── server.py              # 启动入口（加载 .env + OCR + AI，README 指定入口）
├── main.py                # 精简版 app（仅核心路由，无 OCR/AI）
├── models.py              # Pydantic 数据模型
├── session_store.py       # 会话存储（含过期清理）
├── problem_parser.py      # 题目解析（仅返回题目节点）
├── question_generator.py  # 苏格拉底式提问生成（探索 + 回退机制）
├── ai_service.py          # 大模型 API 服务 (OpenAI/Qwen/Baidu)
├── ocr_service.py         # OCR 图片文字识别
└── requirements.txt
src/                       # React 前端
├── api/index.ts           # API 调用封装
├── i18n/                  # 国际化：I18nContext.tsx / zh-CN.ts / en-US.ts
├── store/useStore.ts      # Zustand 状态管理
├── types/index.ts         # TypeScript 类型定义
├── components/            # DeductionFlow.tsx（节点图）/ QuestionPanel.tsx
└── pages/                 # Home.tsx / ProblemInput.tsx / Deduction.tsx
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/problem/submit` | POST | 提交题目，返回初始节点（仅题目） |
| `/question/answer` | POST | 提交答案，获取反馈和新节点 |
| `/ocr/recognize` | POST | 上传图片，返回识别文字 |
| `/health` | GET | 健康检查（含 AI 状态） |

## 思维节点类型

| 类型 | 颜色 | 含义 |
|------|------|------|
| 题目节点 | 蓝色 | 初始题目 |
| 正确步骤 | 绿色 | 用户答对后的思考路径 |
| 探索节点 | 橙色 | 用户答错时的探索尝试 |
| 死胡同 | 红色 | 连续错误触发回退提示 |

## 约定与规范

- **Git 提交信息**：使用中文，简洁明了，避免复杂词汇；并带上版本名，例如 `feat(v0.0.4): ...`（见 `.trae/rules/git-commit-message.md`）。
- **国际化**：所有面向用户的文案需同时维护 `src/i18n/zh-CN.ts` 和 `src/i18n/en-US.ts`，不要硬编码中文。
- **类型检查**：提交前运行 `npm run check` 和 `npm run lint` 保证通过。
- **AI 降级**：后端涉及 AI 的功能必须保留无 Key 时的默认逻辑分支，确保不配置 AI 也能运行。
- 详细产品需求与架构见 `.trae/documents/PRD.md` 与 `.trae/documents/Technical_Architecture.md`。
