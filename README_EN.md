# Math Thinking Trainer v0.0.1

[中文文档](./README.md)

> An interactive training tool that helps students visualize and understand mathematical thinking processes through exploration-based learning.

## Origin & Problem Solved

In the AI era, students rely heavily on problem-solving apps, leading to the frequent "understand when seeing, fail when doing" phenomenon. Students lack genuine problem-solving thinking skills. This project aims to help students see the thinking process through visualization and interactive guidance, training mathematical logical abilities from the ground up.

## Core Features

- **Visual Thinking** - Breaks down problem-solving into multiple thinking nodes, presented graphically
- **Socratic Questioning** - Cultivates independent thinking through guided questions
- **Exploration-Based Learning** - Allows students to take wrong turns; follows user's thought process, generates nodes for both correct and incorrect paths, with gentle retreat prompts on repeated errors
- **Image Recognition** - Supports uploading problem images with automatic text recognition (Tesseract OCR)
- **AI-Powered Assistance** - Integrates LLM APIs (OpenAI / Qwen / ERNIE Bot) for intelligent problem parsing and dynamic question generation
- **Multiple Problem Types** - Supports equation solving, geometry proofs, general math problems, and more

### Mind Map Node Types

| Type | Icon | Color | Meaning |
|------|------|-------|---------|
| Problem | 📋 | Blue | Initial problem display |
| Correct Step | ✓ | Green | User's correct thinking path |
| Exploration | ? | Orange | User's exploratory attempt when choosing wrong answer |
| Dead End | ⚠️ | Red | Retreat prompt after consecutive errors |

**Design Philosophy**: No pre-defined "correct analysis path" — only the problem node is shown initially. Every thought is recorded on the map, whether right or wrong.

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite build tool
- ReactFlow for mind map visualization
- Zustand for state management
- TailwindCSS for styling
- Lucide icon library

### Backend
- Python FastAPI (async)
- Tesseract OCR (image text recognition)
- httpx (HTTP client)
- Session management (30-minute timeout auto-cleanup)

### AI Support (Optional)

| Provider | Model Examples | Notes |
|----------|----------------|-------|
| OpenAI | gpt-3.5-turbo, gpt-4, gpt-4o | Requires API Key |
| Qwen (通义千问) | qwen-plus, qwen-max | Requires DashScope API Key |
| ERNIE Bot (文心一言) | ernie-bot-4, ernie-bot-turbo | Requires Baidu Access Token |

> The app works without AI configuration — it falls back to built-in default logic.

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) (for image recognition, optional)

### Installation

1. **Clone the project**
```bash
git clone <repository-url>
cd Math_Helper
```

2. **Install frontend dependencies**
```bash
npm install
```

3. **Install backend dependencies**
```bash
pip install -r api/requirements.txt
```

4. **Configure environment variables (for AI features)**

   Copy the template and edit:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your API configuration:

   ```env
   # Choose provider: openai, qwen, baidu
   AI_PROVIDER=qwen

   # API Key
   AI_API_KEY=your-api-key-here

   # Base URL (optional, leave empty for defaults)
   # OpenAI: https://api.openai.com/v1
   # Qwen: https://dashscope.aliyuncs.com/compatible-mode/v1
   # Baidu: https://aip.baidubce.com
   AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

   # Model name (optional)
   AI_MODEL=qwen-plus
   ```

5. **Install Tesseract-OCR** (optional, for image recognition)
   - Windows: Download from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add Tesseract to system PATH

### Running

1. **Start backend server**
```bash
python api/server.py
```
Backend runs at http://localhost:8000

2. **Start frontend dev server**
```bash
npm run dev
```
Frontend runs at http://localhost:5173

3. **Verify AI status**
```bash
curl http://localhost:8000/health
# Returns: {"status":"ok","version":"0.0.3","ai_enabled":true,"ai_provider":"qwen"}
```

## Project Structure

```
Math_Helper/
├── api/                          # Python FastAPI Backend
│   ├── server.py                 # Server entry point + route definitions
│   ├── models.py                 # Pydantic data models
│   ├── session_store.py          # Session storage (with expiry cleanup)
│   ├── problem_parser.py         # Problem parser (returns only problem node)
│   ├── question_generator.py     # Socratic question generator (exploration + retreat)
│   ├── ai_service.py             # LLM API service (OpenAI/Qwen/Baidu)
│   ├── ocr_service.py            # OCR image text recognition service
│   └── requirements.txt          # Python dependencies
├── src/                          # React Frontend
│   ├── api/index.ts              # API call wrapper
│   ├── store/useStore.ts         # Zustand state management
│   ├── types/index.ts            # TypeScript type definitions
│   ├── components/
│   │   ├── DeductionFlow.tsx     # ReactFlow mind map (6 node styles)
│   │   └── QuestionPanel.tsx     # Question interaction panel (with retreat support)
│   └── pages/
│       ├── Home.tsx              # Homepage
│       ├── ProblemInput.tsx      # Problem input page (with image upload + OCR)
│       └── Deduction.tsx         # Thinking deduction page
├── .env.example                  # Environment variable template
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Use Cases

- **After-class Practice** - Students complete homework independently, building autonomous problem-solving skills
- **Teacher Tutoring** - Visualizes thinking process to help teachers explain problem-solving approaches
- **Home Learning** - Parents can assist children with thinking training

## Usage Flow

1. Visit homepage → Click "Get Started"
2. Enter a math problem or upload an image (auto OCR recognition)
3. Click "Start Deduction"
4. Left side shows mind map with **only the problem node**
5. Right panel shows first guiding question
6. After selecting an answer:
   - ✅ **Correct** → Green node added to map, proceed to next step
   - ❓ **Wrong** → Orange exploration node added, continue questioning
   - ⚠️ **Consecutive errors** → Red dead-end node + retreat prompt, re-ask question
7. After completing all steps, view full solution review

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/problem/submit` | POST | Submit problem, return initial nodes (problem only) |
| `/question/answer` | POST | Submit answer, get feedback and new nodes |
| `/ocr/recognize` | POST | Upload image for text recognition |
| `/health` | GET | Health check (includes AI status) |

## License

This project is for educational and learning purposes only.
