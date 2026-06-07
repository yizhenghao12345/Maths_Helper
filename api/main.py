import asyncio
import base64
import io
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile, Form
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
from ocr_service import extract_text_from_base64, get_ocr_full_config, log_ocr_upload_rejection
from ai_service import ai_service
from console_routes import router as console_router
import db


IMAGE_SIGNATURES = (
    ("image/jpeg", (b"\xff\xd8\xff",)),
    ("image/png", (b"\x89PNG\r\n\x1a\n",)),
    ("image/gif", (b"GIF87a", b"GIF89a")),
    ("image/webp", (b"RIFF",)),
)
OCR_IMAGE_MAX_EDGE = 2200
OCR_IMAGE_MAX_BYTES = 3 * 1024 * 1024
OCR_IMAGE_QUALITIES = (88, 82, 76, 70)


def _detect_image_media_type(image_bytes: bytes, content_type: str | None) -> str | None:
    normalized_content_type = (content_type or "").split(";", 1)[0].strip().lower()
    if normalized_content_type.startswith("image/"):
        return normalized_content_type

    for media_type, signatures in IMAGE_SIGNATURES:
        if media_type == "image/webp":
            if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
                return media_type
            continue
        if any(image_bytes.startswith(signature) for signature in signatures):
            return media_type

    return None


def _prepare_ocr_image(image_bytes: bytes, media_type: str) -> tuple[bytes, str]:
    try:
        from PIL import Image, ImageOps

        with Image.open(io.BytesIO(image_bytes)) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail((OCR_IMAGE_MAX_EDGE, OCR_IMAGE_MAX_EDGE), Image.Resampling.LANCZOS)

            if image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", image.size, "white")
                alpha = image.getchannel("A" if image.mode == "RGBA" else "a")
                background.paste(image.convert("RGBA"), mask=alpha)
                image = background
            else:
                image = image.convert("RGB")

            best_bytes = image_bytes
            for quality in OCR_IMAGE_QUALITIES:
                output = io.BytesIO()
                image.save(output, format="JPEG", quality=quality, optimize=True)
                normalized = output.getvalue()
                best_bytes = normalized
                if len(normalized) <= OCR_IMAGE_MAX_BYTES:
                    break

            return best_bytes, "image/jpeg"
    except Exception as e:
        print(f"OCR 图片预处理失败，使用原图继续: {e}", flush=True)
        return image_bytes, media_type


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

app = FastAPI(title="Math Thinking Trainer API", version="0.1.5", lifespan=lifespan)

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
    ocr_config = get_ocr_full_config()
    return {
        "status": "ok",
        "version": "0.1.5",
        "ai_enabled": ai_service.enabled,
        "ai_provider": ai_service.provider if ai_service.enabled else None,
        "ai_model": ai_service.model if ai_service.enabled else None,
        "ai_fast_model": ai_service.fast_model if ai_service.enabled else None,
        "ai_slow_model": ai_service.slow_model if ai_service.enabled else None,
        "ocr_enabled": ocr_config["enabled"],
        "ocr_provider": ocr_config["provider"],
        "ocr_model": ocr_config["model"] if ocr_config["enabled"] else "Tesseract",
    }


@app.get("/copyright")
async def get_copyright_public():
    val = db.get_config("copyright")
    return {"copyright": val or ""}


@app.post("/ocr/recognize")
async def recognize_image(
    file: UploadFile = File(...),
    language: str = Form("zh-CN"),
):
    image_bytes = await file.read()
    if not image_bytes:
        log_ocr_upload_rejection(
            reason="图片文件为空",
            language=language,
            content_type=file.content_type,
            filename=file.filename,
        )
        raise HTTPException(status_code=400, detail="图片文件为空")

    media_type = _detect_image_media_type(image_bytes, file.content_type)
    if not media_type:
        log_ocr_upload_rejection(
            reason="不支持的图片格式",
            language=language,
            content_type=file.content_type,
            filename=file.filename,
            file_size=len(image_bytes),
        )
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG、GIF 或 WebP 图片")

    original_size = len(image_bytes)
    original_media_type = media_type
    image_bytes, media_type = _prepare_ocr_image(image_bytes, media_type)
    print(
        (
            "OCR 图片预处理: "
            f"filename={file.filename or '-'} "
            f"media_type={original_media_type}->{media_type} "
            f"size={original_size}->{len(image_bytes)}"
        ),
        flush=True,
    )
    base64_data = f"data:{media_type};base64,{base64.b64encode(image_bytes).decode()}"
    result = await extract_text_from_base64(base64_data, language)
    # 只返回识别的文本内容
    return {"text": result.get("text", "")}
