from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import uuid

from models import (
    SubmitProblemRequest,
    SubmitProblemResponse,
    QuestionRequest,
    QuestionResponse,
)
from session_store import session_store
from problem_parser import parse_problem
from question_generator import generate_question
from console_routes import router as console_router
import db


async def cleanup_sessions():
    while True:
        await asyncio.sleep(300)
        session_store.cleanup_expired()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    task = asyncio.create_task(cleanup_sessions())
    yield
    task.cancel()

app = FastAPI(title="Math Thinking Trainer API", version="0.0.4", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(console_router)


@app.post("/problem/submit", response_model=SubmitProblemResponse)
async def submit_problem(request: SubmitProblemRequest):
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    nodes, edges = parse_problem(request.problem)

    session = session_store.create_session(session_id, request.problem)
    session.nodes = nodes
    session.edges = edges
    session.save()

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
    return {"status": "ok", "version": "0.0.4"}
