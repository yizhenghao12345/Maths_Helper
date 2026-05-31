# Codex AI 协作说明

本项目的完整 AI 协作说明统一维护在 [AGENTS.md](./AGENTS.md)，请阅读并严格遵循。

## 重要：Git 分支策略（必须遵守）

- **禁止直接在 `main` 分支上开发或提交代码。**
- 所有代码修改必须在 `dev` 分支上进行，通过 PR 合并到 `main`。
- 如果当前在 `main` 分支，必须先执行 `git checkout dev` 切换到 `dev` 分支再开始工作。
- 提交代码前请先确认当前分支：`git branch --show-current`。
