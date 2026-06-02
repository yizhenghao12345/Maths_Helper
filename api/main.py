import asyncio
import base64
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

_MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_MAIN_DIR, '..', '.env'))

from models import (
    SubmitProblemRequest,
    SubmitProblemResponse,
    QuestionRequest,
    QuestionResponse,
)
from session_store import session_store
from problem_parser import parse_problem
from question_generator import generate_question, _get_questions_for_problem, _get_total_steps
from ocr_service import extract_text_from_base64
from ai_service import ai_service
from console_routes import router as console_router
import db


async def cleanup_sessions():
    while True:
        await asyncio.sleep(300)
        session_store.cleanup_expired()


async def _parse_problem_in_background(session):
    try:
        session.parsed_problem = await ai_service.parse_problem(
            session.problem,
            session_id=session.session_id,
        )
        session.save()
        return session.parsed_problem
    except Exception as e:
        print(f"AI后台解析题目失败，继续使用快模型追问: {e}")
        return None
    finally:
        session.parsed_problem_task = None


def _start_background_parse(session):
    if not ai_service.enabled or session.parsed_problem is not None:
        return

    task = getattr(session, "parsed_problem_task", None)
    if task is not None and not task.done():
        return

    session.parsed_problem_task = asyncio.create_task(_parse_problem_in_background(session))


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    ai_service.load_persisted_config()
    task = asyncio.create_task(cleanup_sessions())
    yield
    task.cancel()

app = FastAPI(title="Math Thinking Trainer API", version="0.1.3", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:545"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(console_router)


@app.post("/problem/submit", response_model=SubmitProblemResponse)
async def submit_problem(request: SubmitProblemRequest):
    language = request.language or "zh-CN"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    nodes, edges = await parse_problem(request.problem, language)

    session = session_store.create_session(session_id, request.problem, language)
    session.nodes = nodes
    session.edges = edges

    first_question = None
    first_options = None
    current_question_data = None

    if ai_service.enabled:
        _start_background_parse(session)

        try:
            question_data = await ai_service.generate_socratic_question(
                problem=request.problem,
                history=[],
                current_step=0,
                total_steps=_get_total_steps(session),
                language=language,
                session_id=session_id,
            )
            current_question_data = question_data
            first_question = question_data.get("question")
            first_options = question_data.get("options")
        except Exception as e:
            print(f"AI生成首题失败，使用默认逻辑: {e}")

    if not first_question:
        default_questions = _get_questions_for_problem(request.problem, language)
        if default_questions:
            current_question_data = default_questions[0]
            first_question = default_questions[0]["question"]
            first_options = default_questions[0]["options"]

    session.current_question_data = current_question_data

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

    if request.language:
        session.language = request.language

    history_len_before = len(getattr(session, "question_history", []))
    response = await generate_question(
        session,
        request.userAnswer,
        request.currentNodeId,
        request.currentQuestion,
        request.currentOptions,
    )

    if response.nextNodes:
        session.nodes.extend(response.nextNodes)
    if response.nextEdges:
        session.edges.extend(response.nextEdges)
    session.is_completed = response.isCompleted

    if hasattr(session, 'question_history') and len(session.question_history) > history_len_before:
        latest_entries = session.question_history[history_len_before:]
        step = max(session.current_step, 1)
        for latest in latest_entries:
            db.add_question_history(
                session_id=session.session_id,
                question=latest.get("question", ""),
                answer=latest.get("answer", ""),
                selected_option=latest.get("selected_option", ""),
                feedback=latest.get("feedback", ""),
                is_correct=latest.get("is_correct", False),
                step=step,
            )

    session.save()

    return response


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "0.1.3",
        "ai_enabled": ai_service.enabled,
        "ai_provider": ai_service.provider if ai_service.enabled else None,
        "ai_model": ai_service.model if ai_service.enabled else None,
        "ai_fast_model": ai_service.fast_model if ai_service.enabled else None,
        "ai_slow_model": ai_service.slow_model if ai_service.enabled else None,
    }


@app.post("/ocr/recognize")
async def recognize_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    image_bytes = await file.read()
    base64_data = f"data:{file.content_type};base64,{base64.b64encode(image_bytes).decode()}"
    text = await extract_text_from_base64(base64_data)

    return {"text": text}
