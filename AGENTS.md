# AGENTS.md

本文件为所有 AI Coding 工具（Claude Code / Codex / Trae / GLM 等）共用的 AI 协作说明。
`CLAUDE.md` 通过引用本文件复用内容，请勿维护多份。

> **项目事实（功能介绍、技术栈、项目结构、API 接口、节点类型等）统一维护在 [README.md](./README.md)，本文件不重复。**
> AI 工具应关注 README 的以下章节：创意来源、核心功能、技术栈、快速开始、项目结构、API 接口。

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

## 约定与规范

- **Git 提交信息**：使用中文，简洁明了，避免复杂词汇；并带上版本名，例如 `feat(v0.0.4): ...`（见 `.trae/rules/git-commit-message.md`）。
- **国际化**：所有面向用户的文案需同时维护 `src/i18n/zh-CN.ts` 和 `src/i18n/en-US.ts`，不要硬编码中文。
- **类型检查**：提交前运行 `npm run check` 和 `npm run lint` 保证通过。
- **AI 降级**：后端涉及 AI 的功能必须保留无 Key 时的默认逻辑分支，确保不配置 AI 也能运行。
- 详细产品需求与架构见 `.trae/documents/PRD.md` 与 `.trae/documents/Technical_Architecture.md`。
