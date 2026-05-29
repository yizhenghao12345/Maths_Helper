# 数学思维训练助手 v0.0.4

[English Documentation](./README_EN.md)

> 一个通过可视化、互动式引导，帮助学生看清数学思考过程的训练工具。

## 创意来源

在AI时代，学生依赖搜题软件，导致"一看就懂，一做就错"的情况频繁发生，而学生自身却缺乏真正的解题思维。本项目旨在通过可视化、互动式引导，让学生看清思考过程，从根源上训练数学逻辑能力。

## 核心功能

- **思维可视化** - 将解题过程拆解为多个思维节点，以图形化方式呈现
- **苏格拉底式提问** - 通过引导式提问，培养学生独立思考能力
- **探索式学习** - 允许学生走弯路，顺着用户的思路生成节点，错误时温和回退提示
- **图片识别** - 支持上传题目图片，自动识别文字内容（Tesseract OCR）
- **AI 智能辅助** - 接入大模型 API（支持 OpenAI / 通义千问 / 文心一言），实现智能题目解析和动态提问
- **多题型支持** - 支持方程求解、几何证明、通用数学题等多种题型

### 思维导图说明

| 节点类型 | 图标 | 颜色 | 含义             |
| ---- | -- | -- | -------------- |
| 题目节点 | 📋 | 蓝色 | 初始题目展示         |
| 正确步骤 | ✓  | 绿色 | 用户选择正确答案后的思考路径 |
| 探索节点 | ?  | 橙色 | 用户选择错误答案时的探索尝试 |
| 死胡同  | ⚠️ | 红色 | 连续错误后触发回退提示    |

**设计理念**: 不预设"正确分析路径"，只显示题目。用户的每一次思考都会被记录在图上——无论对错。

## 技术栈

### 前端

- React 18 + TypeScript
- Vite 构建工具
- ReactFlow 思维导图可视化
- Zustand 状态管理
- TailwindCSS 样式
- Lucide 图标库

### 后端

- Python FastAPI (异步)
- Tesseract OCR (图片文字识别)
- httpx (HTTP 客户端)
- 会话管理 (30分钟超时自动清理)

### AI 支持 (可选)

| 提供商    | 模型示例                         | 说明                    |
| ------ | ---------------------------- | --------------------- |
| OpenAI | gpt-3.5-turbo, gpt-4, gpt-4o | 需要 API Key            |
| 通义千问   | qwen-plus, qwen-max          | 需要 DashScope API Key  |
| 文心一言   | ernie-bot-4, ernie-bot-turbo | 需要 Baidu Access Token |

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

1. **安装前端依赖**

```bash
npm install
```

1. **安装后端依赖**

```bash
pip install -r api/requirements.txt
```

1. **配置环境变量 (AI 功能)**

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
2. **安装 Tesseract-OCR** (可选，用于图片识别功能)
   - Windows: 从 [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki) 下载安装
   - 将 Tesseract 添加到系统环境变量 PATH

### 运行

1. **启动后端服务**

```bash
python api/server.py
```

后端运行在 <http://localhost:8000>

1. **启动前端开发服务器**

```bash
npm run dev
```

前端运行在 <http://localhost:5173>

1. **验证 AI 状态**

```bash
curl http://localhost:8000/health
# 返回: {"status":"ok","version":"0.0.3","ai_enabled":true,"ai_provider":"qwen"}
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
│   ├── store/useStore.ts         # Zustand 状态管理
│   ├── types/index.ts            # TypeScript 类型定义
│   ├── components/
│   │   ├── DeductionFlow.tsx     # ReactFlow 思维节点图 (6种节点样式)
│   │   └── QuestionPanel.tsx     # 提问交互面板 (支持回退提示)
│   └── pages/
│       ├── Home.tsx              # 主页
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

## API 接口

| 接口                 | 方法   | 说明               |
| ------------------ | ---- | ---------------- |
| `/problem/submit`  | POST | 提交题目，返回初始节点（仅题目） |
| `/question/answer` | POST | 提交答案，获取反馈和新节点    |
| `/ocr/recognize`   | POST | 上传图片，返回识别文字      |
| `/health`          | GET  | 健康检查（含 AI 状态）    |

## 许可证

本项目仅供教育和学习使用。
