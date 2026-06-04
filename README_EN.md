# Math Thinking Trainer v0.1.4

[中文文档](./README.md)

> A training tool that helps students see the mathematical thinking process through visual and interactive guidance.

Live Demo: [Dev](https://maths-dev.m1in.com) ｜ [Prod](https://maths.m1in.com)

<img alt="Prod QR Code" src="https://api.qrserver.com/v1/create-qr-code/?size=140x140&data=https%3A%2F%2Fmaths.m1in.com" width="140" />

## What You Get

- **See the thinking**: visualize the solution process as a step-by-step mind map
- **Guided reasoning**: Socratic questions lead students to the key ideas
- **Safe exploration**: wrong attempts are recorded and gently guided back when needed

## Origin

In the AI era, students rely heavily on problem-solving apps, leading to the frequent "understand at a glance, fail when solving" phenomenon. Students lack genuine problem-solving thinking. This project aims to visualize and interactively guide students through the thinking process, training mathematical logical abilities from the ground up.

## v0.1.4 Highlights

- 🧠 **MiniMax-M3 Multimodal OCR** - Added geometry and formula recognition support with fallback guarantee
- 🔀 **Socratic Questioning Triple Upgrade** - A+B+C question strategy combinations
- ⚙️ **Dynamic Step Counting** - Session total steps calculated in real-time for more accurate progress display

<details>
<summary>Highlights from Previous Versions</summary>

## v0.1.3 Highlights

- 🤖 **3-in-1 AI Pipeline** - OCR + parsing + first question completed in one API call, reducing wait time
- 🧹 **MiniMax-M3 Optimization** - Filters `<think>` reasoning blocks, improves geometry shapes, shadow areas and multi-language support
- 📦 **JS Bundle Route-Level Splitting** - Optimized loading performance, removed Trae badge

## v0.1.2 Highlights

- 📱 **Mobile Adaptation** - Fully responsive layout optimization, supporting mobile phones and tablets

## v0.0.4 Highlights

- 🌐 **Full Internationalization** - Supports both Simplified Chinese and English
- 🔀 **One-Click Switching** - Language toggle button in the top-right corner for instant switching
- 🎨 **i18n Architecture** - Lightweight translation system based on React Context

</details>

## Core Features

- **Visual Thinking Map** - Breaks down problem-solving into multiple thinking nodes, presented graphically
- **Socratic Questioning** - Guides students to think independently through guided questions
- **Exploration-Based Learning** - Allows students to take wrong turns with gentle guidance when mistakes happen
- **Image Recognition** - Upload problem images for automatic text recognition (Tesseract OCR)
- **AI Smart Assistance** - Integrates LLM APIs (DeepSeek / MiniMax / OpenAI / Qwen / Baidu ERNIE) for intelligent parsing and dynamic questioning
- **Multi-Problem Support** - Supports equations, geometry proofs, general math problems, and more

### Mind Map Guide

| Node Type | Icon | Color | Meaning |
|-----------|------|-------|---------|
| Problem | 📋 | Blue | Initial problem display |
| Correct Step | ✓ | Green | User's correct thinking path |
| Exploration | ? | Orange | User's wrong answer exploration |
| Dead End | ⚠️ | Red | Consecutive errors trigger retreat |

**Design Philosophy**: No preset "correct analysis path", only the problem is shown. Every thinking attempt by the user is recorded on the map — right or wrong.

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite build tool
- ReactFlow for mind map visualization
- Zustand state management
- TailwindCSS styling
- Lucide icon library
- **i18n Internationalization** (React Context + translation files)

### Backend
- Python FastAPI (async)
- Tesseract OCR (image text recognition)
- httpx (HTTP client)
- Session management (30-min auto cleanup)

### AI Support (Optional)

| Provider | Model Example | Notes |
|----------|---------------|-------|
| DeepSeek | deepseek-v4-flash, deepseek-reasoner | Requires API Key |
| MiniMax | MiniMax-M3 | Requires API Key |
| OpenAI | gpt-3.5-turbo, gpt-4, gpt-4o | Requires API Key |
| Qwen | qwen-plus, qwen-max | Requires DashScope API Key |
| ERNIE | ernie-bot-4, ernie-bot-turbo | Requires Baidu Access Token |

> The app runs without AI configuration, using built-in default logic as a fallback.

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) (optional, for image recognition)

### Installation

1. **Clone the repository**
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

4. **Configure Environment Variables (AI Features)**

   Copy the environment variable template and edit:

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file with your API configuration:

   ```env
   # Choose AI provider: deepseek, minimax, openai, qwen, baidu
   AI_PROVIDER=deepseek

   # API Key
   AI_API_KEY=your-api-key-here

   # Base URL (optional, leave blank for defaults)
   # DeepSeek: https://api.deepseek.com/v1
   # MiniMax: https://api.minimaxi.com/v1
   # OpenAI: https://api.openai.com/v1
   # Qwen: https://dashscope.aliyuncs.com/compatible-mode/v1
   # Baidu: https://aip.baidubce.com
   AI_BASE_URL=https://api.deepseek.com/v1

   # Model name (optional)
   AI_MODEL=deepseek-v4-flash

   # OCR (optional, recommended: MiniMax-M3; without OCR_API_KEY it falls back to local Tesseract)
   OCR_PROVIDER=minimax
   OCR_API_KEY=your-ocr-api-key-here
   OCR_BASE_URL=https://api.minimaxi.com/v1
   OCR_MODEL=MiniMax-M3
   ```

5. **Install Tesseract-OCR** (optional, for image recognition)
   - Windows: Download from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add Tesseract to your system PATH

### Running

1. **Start the backend**
```bash
python api/server.py
```
Backend runs at http://localhost:8000

2. **Start the frontend dev server**
```bash
npm run dev
```
Frontend runs at http://localhost:5173

3. **Verify AI Status**
```bash
curl http://localhost:8000/health
# Returns: {"status":"ok","version":"0.1.4","ai_enabled":true,"ai_provider":"deepseek"}
```

## Project Structure

```
Math_Helper/
├── api/                          # Python FastAPI Backend
│   ├── server.py                 # Server entry + route definitions
│   ├── models.py                 # Pydantic data models
│   ├── session_store.py          # Session management (with expiry cleanup)
│   ├── problem_parser.py         # Problem parsing (returns only problem node)
│   ├── question_generator.py     # Socratic question generator (exploration + retreat)
│   ├── ai_service.py             # LLM API service (multi-provider + fallback)
│   ├── ocr_service.py            # OCR image text recognition
│   └── requirements.txt          # Python dependencies
├── src/                          # React Frontend
│   ├── api/index.ts              # API call wrappers
│   ├── i18n/                     # Internationalization module (new)
│   │   ├── I18nContext.tsx       # Language context (React Context)
│   │   ├── zh-CN.ts              # Chinese translations
│   │   └── en-US.ts              # English translations
│   ├── store/useStore.ts         # Zustand state management
│   ├── types/index.ts            # TypeScript type definitions
│   ├── components/
│   │   ├── DeductionFlow.tsx     # ReactFlow mind map (6 node styles)
│   │   └── QuestionPanel.tsx     # Question interaction panel (with retreat prompts)
│   └── pages/
│       ├── Home.tsx              # Homepage (with language toggle)
│       ├── ProblemInput.tsx      # Problem input page (with image upload + OCR)
│       └── Deduction.tsx         # Thinking deduction page
├── .env.example                  # Environment variable template
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Use Cases

- **After-School Practice** - Students complete homework independently, building problem-solving skills
- **Teacher Tutoring** - Visualizes thinking process to help teachers explain solutions
- **Home Learning** - Parents can assist children with thinking training
- **International Students** - Supports Chinese/English switching for different language environments

## Workflow

1. Visit homepage → Click "Get Started"
2. Enter a math problem or upload an image (auto OCR recognition)
3. Click "Start Deduction"
4. Left side shows the mind map with **only the problem node**
5. Right panel shows the first guiding question
6. After selecting an answer:
   - ✅ **Correct** → Green node added to map, proceed to next step
   - ❓ **Wrong** → Orange exploration node added, continue questioning
   - ⚠️ **Consecutive errors** → Red dead-end node + retreat prompt, re-ask question
7. After completing all steps, view the full solution review

## Language Switching

Click the language button in the top-right corner of the homepage:
- Chinese interface → Button shows `EN`
- English interface → Button shows `中文`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/problem/submit` | POST | Submit problem, return initial nodes (problem only) |
| `/question/answer` | POST | Submit answer, get feedback and new nodes |
| `/ocr/recognize` | POST | Upload image, return recognized text |
| `/health` | GET | Health check (including AI status) |

## Deployment (Auto)

- Environments: Dev https://maths-dev.m1in.com / Prod https://maths.m1in.com
- Auto deploy: pushing to `dev` / `main` triggers build & deploy
- Details: see [deploy/README.md](./deploy/README.md) (Chinese)

<details>
<summary>Dev/Prod QR Codes</summary>

| Environment | URL | QR Code |
|-------------|-----|--------|
| Dev | https://maths-dev.m1in.com | ![Dev QR Code](https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=https%3A%2F%2Fmaths-dev.m1in.com) |
| Prod | https://maths.m1in.com | ![Prod QR Code](https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=https%3A%2F%2Fmaths.m1in.com) |

</details>

## License

This project is for educational and learning purposes only.
