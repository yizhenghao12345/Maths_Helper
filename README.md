# 数学思维训练助手 v0.0.1

[English Documentation](./README_EN.md)

> 一个通过可视化、互动式引导，帮助学生看清数学思考过程的训练工具。

## 创意来源

在AI时代，学生依赖搜题软件，导致"一看就懂，一做就错"的情况频繁发生，而学生自身却缺乏真正的解题思维。本项目旨在通过可视化、互动式引导，让学生看清思考过程，从根源上训练数学逻辑能力。

## 核心功能

- **思维可视化** - 将解题过程拆解为多个思维节点，以图形化方式呈现
- **苏格拉底式提问** - 通过引导式提问，培养学生独立思考能力
- **错误纠偏** - 选择错误答案时，AI会温和提示原因并允许重新思考
- **图片识别** - 支持上传题目图片，自动识别文字内容
- **多题型支持** - 支持方程求解、几何证明、通用数学题等多种题型

## 技术栈

### 前端
- React 18 + TypeScript
- Vite 构建工具
- ReactFlow 思维导图可视化
- Zustand 状态管理
- TailwindCSS 样式
- Lucide 图标库

### 后端
- Python FastAPI
- Tesseract OCR (图片文字识别)
- 会话管理 (支持30分钟超时自动清理)

## 快速开始

### 前置要求
- Node.js 18+ 和 npm
- Python 3.10+
- [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) (用于图片识别)

### 安装

1. **安装前端依赖**
```bash
npm install
```

2. **安装后端依赖**
```bash
pip install -r api/requirements.txt
```

3. **安装 Tesseract-OCR** (可选，用于图片识别功能)
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

## 项目结构

```
Math_Helper/
├── api/                          # Python FastAPI 后端
│   ├── server.py                 # 服务器入口
│   ├── models.py                 # 数据模型定义
│   ├── session_store.py          # 会话存储管理
│   ├── problem_parser.py         # 题目解析和思维节点生成
│   ├── question_generator.py     # 苏格拉底式提问生成器
│   ├── ocr_service.py            # OCR图片文字识别服务
│   └── requirements.txt          # Python 依赖
├── src/                          # React 前端
│   ├── api/index.ts              # API 调用封装
│   ├── store/useStore.ts         # Zustand 状态管理
│   ├── types/index.ts            # TypeScript 类型定义
│   ├── components/
│   │   ├── DeductionFlow.tsx     # ReactFlow 思维节点图
│   │   └── QuestionPanel.tsx     # 提问交互面板
│   └── pages/
│       ├── Home.tsx              # 主页
│       ├── ProblemInput.tsx      # 题目输入页（支持图片上传）
│       └── Deduction.tsx         # 思维推演页
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 使用场景

- **课后练习** - 学生独立完成作业，培养自主解题能力
- **教师辅导** - 可视化思维过程，帮助教师讲解解题思路
- **家庭学习** - 家长可辅助孩子进行思维训练

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/problem/submit` | POST | 提交题目，生成思维节点 |
| `/question/answer` | POST | 提交答案，获取反馈 |
| `/ocr/recognize` | POST | 上传图片识别文字 |
| `/health` | GET | 健康检查 |

## 许可证

本项目仅供教育和学习使用。
