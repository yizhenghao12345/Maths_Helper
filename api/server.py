import sys
sys.path.append('.')

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uuid
import base64
import os
from dotenv import load_dotenv

load_dotenv()

from models import (
    SubmitProblemRequest,
    SubmitProblemResponse,
    QuestionRequest,
    QuestionResponse,
)
from session_store import session_store
from problem_parser import parse_problem
from question_generator import generate_question
from ocr_service import extract_text_from_base64
from ai_service import ai_service

app = FastAPI(title="Math Thinking Trainer API", version="0.0.4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/problem/submit", response_model=SubmitProblemResponse)
async def submit_problem(request: SubmitProblemRequest):
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    nodes, edges = await parse_problem(request.problem)

    session = session_store.create_session(session_id, request.problem)
    session.nodes = nodes
    session.edges = edges

    return SubmitProblemResponse(
        sessionId=session_id, initialNodes=nodes, initialEdges=edges
    )


@app.post("/question/answer", response_model=QuestionResponse)
async def answer_question(request: QuestionRequest):
    session = session_store.get_session(request.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    response = await generate_question(session, request.userAnswer, request.currentNodeId)

    if response.nextNodes:
        session.nodes.extend(response.nextNodes)
    if response.nextEdges:
        session.edges.extend(response.nextEdges)

    return response


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "0.0.4",
        "ai_enabled": ai_service.enabled,
        "ai_provider": ai_service.provider if ai_service.enabled else None,
    }


@app.post("/ocr/recognize")
async def recognize_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    image_bytes = await file.read()
    base64_data = f"data:{file.content_type};base64,{base64.b64encode(image_bytes).decode()}"
    text = extract_text_from_base64(base64_data)

    return {"text": text}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
