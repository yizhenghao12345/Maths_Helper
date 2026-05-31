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
from console_routes import router as console_router
import db


app = FastAPI(title="Math Thinking Trainer API", version="0.0.4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(console_router)


@app.on_event("startup")
async def startup():
    db.init_db()


@app.post("/problem/submit", response_model=SubmitProblemResponse)
async def submit_problem(request: SubmitProblemRequest):
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    nodes, edges = await parse_problem(request.problem)

    session = session_store.create_session(session_id, request.problem)
    session.nodes = nodes
    session.edges = edges

    first_question = None
    first_options = None

    if ai_service.enabled:
        try:
            parsed = await ai_service.parse_problem(request.problem, session_id=session_id)
            session.parsed_problem = parsed
        except Exception as e:
            print(f"AI解析题目失败: {e}")

        try:
            question_data = await ai_service.generate_socratic_question(
                problem=request.problem,
                history=[],
                current_step=0,
                total_steps=3,
                parsed_problem=session.parsed_problem,
                session_id=session_id,
            )
            first_question = question_data.get("question")
            first_options = question_data.get("options")
        except Exception as e:
            print(f"AI生成首问失败，使用默认问题: {e}")

    if not first_question:
        first_question = "观察这道题，你认为第一步应该做什么?"
        first_options = [
            "A. 仔细分析已知条件",
            "B. 直接尝试计算",
            "C. 跳过分析",
            "D. 不做思考",
        ]

    session.save()

    return SubmitProblemResponse(
        sessionId=session_id,
        initialNodes=nodes,
        initialEdges=edges,
        firstQuestion=first_question,
        firstOptions=first_options,
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

    if hasattr(session, 'question_history') and session.question_history:
        latest = session.question_history[-1]
        db.add_question_history(
            session_id=session.session_id,
            question=latest.get("question", ""),
            answer=latest.get("answer", ""),
            selected_option=latest.get("selected_option", ""),
            feedback=latest.get("feedback", ""),
            is_correct=latest.get("is_correct", False),
            step=session.current_step,
        )

    session.save()

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
