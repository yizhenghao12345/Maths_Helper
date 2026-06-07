import base64
import io
import os
import re
import time
import uuid

import httpx

from ai_service import ai_service, mask_api_key
import db


OCR_DEFAULT_PROVIDER = "minimax"
OCR_DEFAULT_BASE_URL = "https://api.minimaxi.com/v1"
OCR_DEFAULT_MODELS = {
    "minimax": "MiniMax-M3",
    "openai": "gpt-4o-mini",
    "qwen": "qwen-vl-max",
}
OCR_UI_NOISE_PATTERNS = (
    r"^\d{1,2}:\d{2}$",
    r"^\d+\s*(字|chars?)$",
    r"^https?://",
    r"^[\w.-]+\.(com|cn|net|org)",
    r"AI数学思维动态推演器",
    r"maths-dev",
    r"返回首页",
    r"输入题目",
    r"输入你要解决的数学题目",
    r"系统将为你生成",
    r"识别图片文字",
    r"上传图片",
    r"识别模型",
    r"开始推演",
    r"MiniMax",
    r"Tesseract",
    r"Recognition model",
    r"Upload Image",
    r"Start Deduction",
)
OCR_PROBLEM_START_PATTERN = re.compile(
    r"(^|\n)\s*(?:\d+\s*[.．、]|[（(]?\d+[）)]|如图|已知|求|证明|计算|解|设|若|在\s*[$\\]?(?:triangle|△)|In\s+)",
    re.IGNORECASE,
)


def _get_stored_config(key: str) -> str | None:
    try:
        value = db.get_config(key)
    except Exception:
        return None
    return value if value is not None else None


def _resolve_ocr_model(provider: str, stored_model: str | None = None) -> str:
    if stored_model:
        return stored_model
    return OCR_DEFAULT_MODELS.get(provider, ai_service.model)


def get_ocr_full_config() -> dict:
    provider = (
        _get_stored_config("ocr_provider")
        or os.getenv("OCR_PROVIDER")
        or OCR_DEFAULT_PROVIDER
    ).lower()
    api_key = _get_stored_config("ocr_api_key")
    if api_key is None:
        api_key = os.getenv("OCR_API_KEY", "")
    base_url = (
        _get_stored_config("ocr_base_url")
        or os.getenv("OCR_BASE_URL")
        or OCR_DEFAULT_BASE_URL
    )
    model = _resolve_ocr_model(
        provider,
        _get_stored_config("ocr_model") or os.getenv("OCR_MODEL"),
    )
    return {
        "provider": provider,
        "model": model,
        "api_key_masked": mask_api_key(api_key),
        "base_url": base_url,
        "enabled": bool(api_key),
    }


def get_ocr_runtime_config() -> dict:
    config = get_ocr_full_config()
    api_key = _get_stored_config("ocr_api_key")
    if api_key is None:
        api_key = os.getenv("OCR_API_KEY", "")
    return {**config, "api_key": api_key}


def _create_ocr_test_image_base64() -> str:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (240, 90), "white")
    draw = ImageDraw.Draw(image)
    draw.text((36, 28), "2 + 5 = 7", fill="black")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")


async def test_ocr_connection(
    *,
    provider: str,
    api_key: str,
    base_url: str,
    model: str,
    language: str = "zh-CN",
) -> dict:
    provider = (provider or "").lower().strip()
    api_key = (api_key or "").strip()
    base_url = (base_url or "").rstrip("/")
    model = (model or "").strip()
    request_id = uuid.uuid4().hex[:8]
    started_at = time.time()

    if not provider or not model or not base_url:
        return {"success": False, "message": "OCR供应商、模型和基础URL不能为空"}
    if not api_key:
        return {"success": False, "message": "OCR API密钥不能为空"}
    if provider not in ["minimax", "openai", "qwen", "custom"]:
        return {"success": False, "message": f"不支持的 OCR_PROVIDER: {provider}"}

    try:
        image_base64 = _create_ocr_test_image_base64()
        text = await _multimodal_ocr(
            base64_data=image_base64,
            api_key=api_key,
            base_url=base_url,
            model=model,
            language=language,
        )
        normalized = re.sub(r"\s+", "", text or "")
        success = all(part in normalized for part in ("2", "5", "7"))
        message = "OCR连接成功，模型返回有效图片识别结果" if success else "OCR连接成功，但未识别出预期测试内容"
        _log_ocr_event(
            method="ocr:test_multimodal",
            provider=provider,
            model=model,
            language=language,
            duration_ms=int((time.time() - started_at) * 1000),
            success=success,
            request_id=request_id,
            response_text=text,
            error_message="" if success else message,
        )
        return {"success": success, "message": message, "response_preview": text[:100]}
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text[:500] if e.response is not None else str(e)
        message = f"HTTP {e.response.status_code}: {error_detail}" if e.response is not None else str(e)
        _log_ocr_event(
            method="ocr:test_multimodal",
            provider=provider,
            model=model,
            language=language,
            duration_ms=int((time.time() - started_at) * 1000),
            success=False,
            request_id=request_id,
            error_message=message,
        )
        return {"success": False, "message": message}
    except Exception as e:
        _log_ocr_event(
            method="ocr:test_multimodal",
            provider=provider,
            model=model,
            language=language,
            duration_ms=int((time.time() - started_at) * 1000),
            success=False,
            request_id=request_id,
            error_message=str(e),
        )
        return {"success": False, "message": str(e)}


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
    response_summary = response_text or ""
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
        ocr_config = get_ocr_runtime_config()
        ocr_provider = ocr_config["provider"]
        ocr_api_key = ocr_config["api_key"]
        ocr_base_url = ocr_config["base_url"]
        ocr_model = ocr_config["model"]

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
        cleaned_text = _extract_primary_problem_text(text)
        success = bool(text) and not text.startswith(("OCR 识别失败:", "未安装 OCR 依赖。"))
        _log_ocr_event(
            method="ocr:tesseract",
            provider="tesseract",
            model="Tesseract",
            language=language,
            duration_ms=int((time.time() - tesseract_start) * 1000),
            success=success,
            request_id=request_id,
            response_text=cleaned_text if success else "",
            error_message="" if success else text or "Tesseract 返回空文本",
        )
        return {"text": cleaned_text if success else text, "model_used": "Tesseract"}
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
            "Your ONLY task: extract the main math problem area from the image.\n\n"
            "Rules:\n"
            "1. Keep only the primary math problem statement. If the image is a phone/web screenshot, ignore status bars, app titles, URLs, buttons, upload controls, OCR model labels, word counts, and any surrounding UI text.\n"
            "2. A single main problem may contain a shared stem plus multiple subquestions such as (1)(2), ①②, I/II, or a/b. Keep all subquestions that belong to that same main problem.\n"
            "3. If multiple unrelated problems or repeated OCR text blocks are visible, choose the clearest and most prominent actual math problem area only.\n"
            "4. Preserve the original problem numbering and subquestion numbering when visible.\n"
            "5. Transcribe the problem text faithfully, including text below or beside any figure.\n"
            "6. Use LaTeX for every math symbol and formula (e.g. $AD=DE=EC$, $S_{\\triangle ABC}=1$).\n"
            "7. If there is a geometric figure, briefly describe it AFTER the problem text:\n"
            "   - Shape type and vertex labels with positions.\n"
            "   - Key interior/boundary points and how they divide the sides.\n"
            "   - Which line segments are drawn and any labeled intersection points.\n"
            "   - Any shaded or colored region and its vertices.\n"
            "8. Output ONLY the selected main problem and its own subquestions (and figure description if needed).\n"
            "   Do NOT add any explanation, solution steps, opening remarks, or UI text."
        )
    else:
        prompt = (
            "你是一个高精度的数学题目识别助手。\n"
            "你唯一的任务：从图片中提取最主要的数学题目区域。\n\n"
            "规则：\n"
            "1. 只保留核心题目内容。如果图片是手机/网页截图，请忽略状态栏、应用标题、网址、按钮、上传控件、识别模型、字数统计、页面说明等 UI 文案。\n"
            "2. 一个主题目可以包含公共题干和多个小问，例如（1）（2）、①②、I/II、a/b。只要属于同一大题，就必须完整保留这些小问。\n"
            "3. 如果图片里有多个互不相关的题目，或同一题目被页面重复展示，只选择最清晰、最主要的实际题目区域。\n"
            "4. 保留原题号和小问编号；不要把同一大题的小问误删。\n"
            "5. 原文转录题干文字，包括图形下方或旁边与题目相关的说明文字。\n"
            "6. 所有数学符号和公式使用 LaTeX 语法（如 $AD=DE=EC$、$S_{\\triangle ABC}=1$）。\n"
            "7. 如果图中有几何图形，请在题目文字之后简要描述：\n"
            "   - 图形类型和各顶点标注与位置。\n"
            "   - 图形内部或边上的关键标注点及位置关系。\n"
            "   - 图中连接了哪些线段，以及标注的交点。\n"
            "   - 有颜色或阴影的区域及其顶点。\n"
            "8. 只输出选中的主题目及其所属小问（必要时附简短图形描述），不要加前言、解题过程、解释或 UI 文案。"
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
    return _extract_primary_problem_text(text)


def _is_ocr_ui_noise(line: str) -> bool:
    normalized = line.strip()
    if not normalized:
        return True
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in OCR_UI_NOISE_PATTERNS)


def _extract_primary_problem_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if not _is_ocr_ui_noise(line)]
    cleaned = "\n".join(lines).strip()
    if not cleaned:
        return text.strip()

    match = OCR_PROBLEM_START_PATTERN.search(cleaned)
    if match:
        cleaned = cleaned[match.start():].strip()

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


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
