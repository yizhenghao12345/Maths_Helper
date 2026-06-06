import base64
import io
import os
import re
import time
import uuid

import httpx

from ai_service import ai_service
import db


OCR_LOG_PREVIEW_LIMIT = 200


def _log_ocr_event(
    *,
    method: str,
    provider: str,
    model: str,
    language: str,
    duration_ms: int,
    success: bool,
    request_id: str,
    response_text: str = "",
    error_message: str = "",
):
    response_summary = (response_text or "")[:OCR_LOG_PREVIEW_LIMIT]
    error_summary = (error_message or "")[:500]
    status = "成功" if success else "失败"
    print(
        (
            f"OCR{status}: request_id={request_id} method={method} "
            f"provider={provider or '-'} model={model or '-'} "
            f"language={language} duration_ms={duration_ms} "
            f"text_length={len(response_text or '')}"
            + (f" error={error_summary}" if error_summary else "")
        ),
        flush=True,
    )

    try:
        db.add_ai_log(
            session_id=None,
            provider=provider or "ocr",
            model=model or "-",
            method=method,
            used_parsed_problem=False,
            parsed_problem_title=None,
            request_summary=f"request_id={request_id}; language={language}",
            response_summary=response_summary,
            duration_ms=duration_ms,
            success=success,
            error_message=error_summary,
        )
    except Exception:
        pass


def log_ocr_upload_rejection(
    *,
    reason: str,
    language: str,
    content_type: str | None = None,
    filename: str | None = None,
    file_size: int | None = None,
):
    request_id = uuid.uuid4().hex[:8]
    detail = (
        f"filename={filename or '-'}; content_type={content_type or '-'}; "
        f"file_size={file_size if file_size is not None else '-'}"
    )
    _log_ocr_event(
        method="ocr:upload",
        provider="upload",
        model="-",
        language=language,
        duration_ms=0,
        success=False,
        request_id=request_id,
        error_message=f"{reason}; {detail}",
    )


# ---------------------------------------------------------------------------
# 公共入口
# ---------------------------------------------------------------------------

async def extract_text_from_base64(
    base64_data: str,
    language: str = "zh-CN",
) -> dict:
    """
    识别图片中的数学题目文字。
    AI 路径（MiniMax-M3 / GPT-4o / qwen-vl 等）：高精度多模态识别。
    降级路径（Tesseract）：本地 OCR。
    返回格式：{"text": str, "model_used": str}
    """
    raw_base64 = base64_data
    if "," in base64_data:
        raw_base64 = base64_data.split(",")[1]

    request_id = uuid.uuid4().hex[:8]

    # 1. 优先使用多模态大模型
    try:
        multimodal_start = time.time()
        ocr_provider = os.getenv("OCR_PROVIDER") or ai_service.provider
        ocr_api_key = os.getenv("OCR_API_KEY") or ai_service.api_key
        ocr_base_url = os.getenv("OCR_BASE_URL") or ai_service.base_url

        ocr_model = os.getenv("OCR_MODEL")
        if not ocr_model:
            if ocr_provider == "minimax":
                ocr_model = "MiniMax-M3"
            elif ocr_provider == "openai":
                ocr_model = "gpt-4o-mini"
            elif ocr_provider == "qwen":
                ocr_model = "qwen-vl-max"
            else:
                ocr_model = ai_service.model

        if ocr_api_key and ocr_provider in ["minimax", "openai", "qwen", "custom"]:
            text = await _multimodal_ocr(
                base64_data=base64_data,
                api_key=ocr_api_key,
                base_url=ocr_base_url,
                model=ocr_model,
                language=language,
            )
            if text:
                _log_ocr_event(
                    method="ocr:multimodal",
                    provider=ocr_provider,
                    model=ocr_model,
                    language=language,
                    duration_ms=int((time.time() - multimodal_start) * 1000),
                    success=True,
                    request_id=request_id,
                    response_text=text,
                )
                return {"text": text, "model_used": ocr_model}
            _log_ocr_event(
                method="ocr:multimodal",
                provider=ocr_provider,
                model=ocr_model,
                language=language,
                duration_ms=int((time.time() - multimodal_start) * 1000),
                success=False,
                request_id=request_id,
                error_message="多模态 OCR 返回空文本，降级到 Tesseract",
            )
        else:
            reason = "未配置 OCR_API_KEY" if not ocr_api_key else f"不支持的 OCR_PROVIDER: {ocr_provider}"
            _log_ocr_event(
                method="ocr:multimodal",
                provider=ocr_provider,
                model=ocr_model,
                language=language,
                duration_ms=int((time.time() - multimodal_start) * 1000),
                success=False,
                request_id=request_id,
                error_message=f"{reason}，降级到 Tesseract",
            )
    except Exception as e:
        _log_ocr_event(
            method="ocr:multimodal",
            provider=locals().get("ocr_provider", "unknown"),
            model=locals().get("ocr_model", "unknown"),
            language=language,
            duration_ms=int((time.time() - multimodal_start) * 1000),
            success=False,
            request_id=request_id,
            error_message=f"{e}，降级到本地 Tesseract",
        )

    # 2. 降级：本地 Tesseract OCR
    tesseract_start = time.time()
    try:
        image_bytes = base64.b64decode(raw_base64)
        text = _simple_ocr(image_bytes)
        success = bool(text) and not text.startswith(("OCR 识别失败:", "未安装 OCR 依赖。"))
        _log_ocr_event(
            method="ocr:tesseract",
            provider="tesseract",
            model="Tesseract",
            language=language,
            duration_ms=int((time.time() - tesseract_start) * 1000),
            success=success,
            request_id=request_id,
            response_text=text if success else "",
            error_message="" if success else text or "Tesseract 返回空文本",
        )
        return {"text": text, "model_used": "Tesseract"}
    except Exception as e:
        _log_ocr_event(
            method="ocr:tesseract",
            provider="tesseract",
            model="Tesseract",
            language=language,
            duration_ms=int((time.time() - tesseract_start) * 1000),
            success=False,
            request_id=request_id,
            error_message=str(e),
        )
        return {"text": f"OCR 失败: {str(e)}", "model_used": "Tesseract"}


# ---------------------------------------------------------------------------
# 多模态大模型识别（纯文本输出，不要求 JSON）
# ---------------------------------------------------------------------------

async def _multimodal_ocr(
    base64_data: str,
    api_key: str,
    base_url: str,
    model: str,
    language: str = "zh-CN",
) -> str:
    """
    调用多模态模型，只做一件事：识别图片中的数学题目，返回纯文字。
    不要求 JSON 格式，避免推理模型因 JSON 约束输出异常。
    """
    if not base64_data.startswith("data:image"):
        base64_data = f"data:image/png;base64,{base64_data}"

    if language == "en-US":
        prompt = (
            "You are a high-precision math problem recognition assistant.\n"
            "Your ONLY task: read all text from this math problem image and output it faithfully.\n\n"
            "Rules:\n"
            "1. Transcribe all visible text exactly, including text below or beside any figure.\n"
            "2. Use LaTeX for every math symbol and formula (e.g. $AD=DE=EC$, $S_{\\triangle ABC}=1$).\n"
            "3. If there is a geometric figure, briefly describe it AFTER the problem text:\n"
            "   - Shape type and vertex labels with positions.\n"
            "   - Key interior/boundary points and how they divide the sides.\n"
            "   - Which line segments are drawn and any labeled intersection points.\n"
            "   - Any shaded or colored region and its vertices.\n"
            "4. Output ONLY the problem text (and figure description if present).\n"
            "   Do NOT add any explanation, solution steps, or opening remarks."
        )
    else:
        prompt = (
            "你是一个高精度的数学题目识别助手。\n"
            "你唯一的任务：读取图片中的数学题目，原文输出。\n\n"
            "规则：\n"
            "1. 原文转录图片中所有可见文字，包括图形下方或旁边的说明文字。\n"
            "2. 所有数学符号和公式使用 LaTeX 语法（如 $AD=DE=EC$、$S_{\\triangle ABC}=1$）。\n"
            "3. 如果图中有几何图形，请在题目文字之后简要描述：\n"
            "   - 图形类型和各顶点标注与位置。\n"
            "   - 图形内部或边上的关键标注点及位置关系。\n"
            "   - 图中连接了哪些线段，以及标注的交点。\n"
            "   - 有颜色或阴影的区域及其顶点。\n"
            "4. 只输出题目内容（及几何描述），不要加任何前言、解题过程或解释。"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": base64_data}},
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1500,
    }

    url = f"{base_url}/chat/completions"
    async with httpx.AsyncClient(timeout=40.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"]

    return _clean_response(raw)


# ---------------------------------------------------------------------------
# 文本清洗
# ---------------------------------------------------------------------------

def _clean_response(raw: str) -> str:
    """
    清洗模型输出：
    - 剥离 <think>...</think> 推理块（适用于 MiniMax-M3 / DeepSeek-R1 等推理模型）
    - 去除 markdown 代码块标记
    """
    # 1. 去掉 <think>...</think>（贪婪，含跨行）
    text = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.IGNORECASE)
    # 2. 去掉 markdown 代码块包裹
    text = re.sub(r"```[^\n]*\n?", "", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Tesseract 本地 OCR（降级）
# ---------------------------------------------------------------------------

def _simple_ocr(image_bytes: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")
        return text.strip()
    except ImportError:
        return "未安装 OCR 依赖。请运行: pip install pytesseract Pillow，并安装 Tesseract-OCR 引擎。"
    except Exception as e:
        return f"OCR 识别失败: {str(e)}"
