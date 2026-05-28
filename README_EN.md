# Math Thinking Trainer v0.0.1

[中文文档](./README.md)

> An interactive training tool that helps students visualize and understand mathematical thinking processes.

## Origin & Problem Solved

In the AI era, students rely heavily on problem-solving apps, leading to the frequent "understand when seeing, fail when doing" phenomenon. Students lack genuine problem-solving thinking skills. This project aims to help students see the thinking process through visualization and interactive guidance, training mathematical logical abilities from the ground up.

## Core Features

- **Visual Thinking** - Breaks down problem-solving into multiple thinking nodes, presented graphically
- **Socratic Questioning** - Cultivates independent thinking through guided questions
- **Error Correction** - When wrong answers are selected, AI gently prompts reasons and allows rethinking
- **Image Recognition** - Supports uploading problem images with automatic text recognition
- **Multiple Problem Types** - Supports equation solving, geometry proofs, general math problems, and more

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite build tool
- ReactFlow for mind map visualization
- Zustand for state management
- TailwindCSS for styling
- Lucide icon library

### Backend
- Python FastAPI
- Tesseract OCR (image text recognition)
- Session management (30-minute timeout auto-cleanup)

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) (for image recognition)

### Installation

1. **Install frontend dependencies**
```bash
npm install
```

2. **Install backend dependencies**
```bash
pip install -r api/requirements.txt
```

3. **Install Tesseract-OCR** (optional, for image recognition)
   - Windows: Download and install from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
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

## Project Structure

```
Math_Helper/
├── api/                          # Python FastAPI Backend
│   ├── server.py                 # Server entry point
│   ├── models.py                 # Data model definitions
│   ├── session_store.py          # Session storage management
│   ├── problem_parser.py         # Problem parsing and mind node generation
│   ├── question_generator.py     # Socratic question generator
│   ├── ocr_service.py            # OCR image text recognition service
│   └── requirements.txt          # Python dependencies
├── src/                          # React Frontend
│   ├── api/index.ts              # API call wrapper
│   ├── store/useStore.ts         # Zustand state management
│   ├── types/index.ts            # TypeScript type definitions
│   ├── components/
│   │   ├── DeductionFlow.tsx     # ReactFlow mind node graph
│   │   └── QuestionPanel.tsx     # Question interaction panel
│   └── pages/
│       ├── Home.tsx              # Homepage
│       ├── ProblemInput.tsx      # Problem input page (with image upload)
│       └── Deduction.tsx         # Thinking deduction page
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Use Cases

- **After-class Practice** - Students complete homework independently, building autonomous problem-solving skills
- **Teacher Tutoring** - Visualizes thinking process to help teachers explain problem-solving approaches
- **Home Learning** - Parents can assist children with thinking training

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/problem/submit` | POST | Submit problem, generate thinking nodes |
| `/question/answer` | POST | Submit answer, get feedback |
| `/ocr/recognize` | POST | Upload image for text recognition |
| `/health` | GET | Health check |

## License

This project is for educational and learning purposes only.
