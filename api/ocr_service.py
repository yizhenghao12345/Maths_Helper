import base64
import json
import os
import io
import re
import httpx
from ai_service import ai_service


async def extract_text_from_base64(
    base64_data: str,
    language: str = "zh-CN",
) -> dict:
    """
    优先使用多模态大模型进行高精度 OCR 与几何解析。
    AI 路径：一次调用同时返回
      - text: 完整题目文字描述（用于填入文本框）
      - parsed_problem: 结构化题目分析（可供 /problem/submit 直接使用）
      - first_question: 第一道苏格拉底引导题（含选项、反馈）
    降级路径（Tesseract）：仅返回 text，parsed_problem/first_question 为 None。
    """
    raw_base64 = base64_data
    if "," in base64_data:
        raw_base64 = base64_data.split(",")[1]

    # 1. 尝试使用多模态大模型进行高精度识别
    try:
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
            result = await _multimodal_ocr_full(
                base64_data=base64_data,
                api_key=ocr_api_key,
                base_url=ocr_base_url,
                model=ocr_model,
                language=language,
            )
            if result.get("text"):
                return result
    except Exception as e:
        print(f"大模型多模态 OCR 解析失败: {e}，尝试降级到本地 Tesseract OCR。")

    # 2. 降级为本地 Tesseract OCR（仅返回文字）
    try:
        image_bytes = base64.b64decode(raw_base64)
        text = _simple_ocr(image_bytes)
        return {"text": text, "parsed_problem": None, "first_question": None}
    except Exception as e:
        return {"text": f"降级本地 OCR 失败: {str(e)}", "parsed_problem": None, "first_question": None}


async def _multimodal_ocr_full(
    base64_data: str,
    api_key: str,
    base_url: str,
    model: str,
    language: str = "zh-CN",
) -> dict:
    """
    通过多模态模型一次完成：
      1. 识别图片中的题目文字（text）
      2. 结构化解析题目（parsed_problem）
      3. 生成第一道苏格拉底引导问题（first_question）
    返回格式：{"text": str, "parsed_problem": dict | None, "first_question": dict | None}
    """
    if not base64_data.startswith("data:image"):
        base64_data = f"data:image/png;base64,{base64_data}"

    if language == "en-US":
        prompt = (
            "You are a high-precision math problem recognition and analysis assistant.\n"
            "Given the math problem image, complete ALL THREE tasks in ONE response and return ONLY a single JSON object.\n\n"
            "【Task 1 — Recognize problem text】\n"
            "Read all visible text (including text below/beside the figure). "
            "Use LaTeX for all math expressions (e.g., $AD=DE=EC$, $S_{\\triangle ABC}=1$).\n"
            "If a geometric figure is present, describe it after the text:\n"
            "  a. Figure type and vertex labels with positions (e.g., △ABC, A at top, B at bottom-left, C at bottom-right).\n"
            "  b. All labeled interior/boundary points and their location relationships.\n"
            "  c. All drawn line segments and the intersection points they create.\n"
            "  d. Any shaded/colored regions and their boundary vertices.\n\n"
            "【Task 2 — Structured problem analysis】\n"
            "Analyze the recognized problem and fill the parsed_problem fields.\n\n"
            "【Task 3 — First Socratic question】\n"
            "Generate ONE guiding question to help the student start thinking (Socratic method, step 1). "
            "Provide 2-4 options (A/B/C/D), all plausible. One is optimal; others are common misconceptions. "
            "Never reveal the answer directly.\n\n"
            "Return ONLY this JSON (no markdown, no extra text):\n"
            "{\n"
            '  "text": "Full problem text with geometric description",\n'
            '  "parsed_problem": {\n'
            '    "problem_type": "equation|geometry|general|algebra|function",\n'
            '    "title": "Short problem title",\n'
            '    "known_conditions": ["condition 1", "condition 2"],\n'
            '    "goal": "What to find",\n'
            '    "key_concepts": ["concept 1", "concept 2"],\n'
            '    "suggested_steps": ["step 1", "step 2", "step 3"]\n'
            "  },\n"
            '  "first_question": {\n'
            '    "question": "Guiding question",\n'
            '    "options": ["A. ...", "B. ...", "C. ..."],\n'
            '    "correct_index": 0,\n'
            '    "success_feedback": "Encouraging feedback",\n'
            '    "error_feedback": "Gentle hint for wrong choice",\n'
            '    "explanation": "Brief explanation"\n'
            "  }\n"
            "}"
        )
    else:
        prompt = (
            "你是一个高精度的数学题目识别与分析助手，专门处理中小学及竞赛数学题目。\n"
            "请对图片中的数学题目一次性完成以下三项任务，仅返回一个 JSON 对象。\n\n"
            "【任务一 — 识别题目文字】\n"
            "读取图片中所有可见文字（含图形下方或旁边的说明），使用 LaTeX 语法输出数学符号（如 $AD=DE=EC$、$S_{\\triangle ABC}=1$）。\n"
            "若图中存在几何图形，请在文字之后按顺序描述：\n"
            "  a. 图形类型及各顶点标注与位置（如：△ABC，A 在顶部，B 在左下，C 在右下）。\n"
            "  b. 图形内部或边上的所有标注点及位置关系（如：D、E 在 AC 上将其三等分，满足 $AD=DE=EC$）。\n"
            "  c. 图形内部所有线段的连接关系及其产生的交点（如：BD 与 AG 交于 M，BE 与 AF 交于 N）。\n"
            "  d. 图中标有颜色或阴影的区域及其顶点（如：蓝色阴影区域为四边形 MGFN）。\n\n"
            "【任务二 — 结构化题目解析】\n"
            "分析识别出的题目，填写 parsed_problem 各字段。\n\n"
            "【任务三 — 生成第一道苏格拉底引导问题】\n"
            "基于题目生成一道引导学生开始思考的问题（苏格拉底式，第一步）。\n"
            "提供 2-4 个选项（A/B/C/D），所有选项都是合理的思考方向：一个最优，其余反映常见思维误区。\n"
            "禁止直接给出答案或解题步骤。\n\n"
            "仅返回以下 JSON（不要 markdown 代码块，不要多余文字）：\n"
            "{\n"
            '  "text": "完整题目文字（含几何图形描述）",\n'
            '  "parsed_problem": {\n'
            '    "problem_type": "equation|geometry|general|algebra|function",\n'
            '    "title": "题目简短标题",\n'
            '    "known_conditions": ["已知条件1", "已知条件2"],\n'
            '    "goal": "求解目标",\n'
            '    "key_concepts": ["知识点1", "知识点2"],\n'
            '    "suggested_steps": ["步骤1", "步骤2", "步骤3"]\n'
            "  },\n"
            '  "first_question": {\n'
            '    "question": "引导性问题",\n'
            '    "options": ["A. ...", "B. ...", "C. ..."],\n'
            '    "correct_index": 0,\n'
            '    "success_feedback": "选择正确时的鼓励性反馈",\n'
            '    "error_feedback": "选择错误时的温和提示",\n'
            '    "explanation": "这一步的简短说明"\n'
            "  }\n"
            "}"
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
                    {
                        "type": "image_url",
                        "image_url": {"url": base64_data},
                    },
                ],
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2500,
    }

    url = f"{base_url}/chat/completions"
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"].strip()

    return _parse_ocr_response(raw)


def _strip_think_tags(text: str) -> str:
    """
    移除模型输出中的 <think>...</think> 推理块。
    适用于 MiniMax-M3 / DeepSeek-R1 等带思维链的模型。
    """
    # 贪婪匹配：去掉所有 <think>...</think>（含跨行）
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    return text.strip()


def _parse_ocr_response(raw: str) -> dict:
    """
    解析多模态模型的 JSON 返回，健壮处理各种格式。
    始终保证返回 {"text": str, "parsed_problem": dict|None, "first_question": dict|None}。
    """
    # 1. 先剥离思维链 <think>...</think>
    text = _strip_think_tags(raw)

    # 2. 去除可能包裹的 markdown 代码块
    if "```" in text:
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            obj = json.loads(text[json_start:json_end])
            if isinstance(obj, dict) and obj.get("text"):
                # 对 text 字段也做一次思维链清洗（防止模型把 <think> 写进 JSON 内容）
                clean_text = _strip_think_tags(str(obj.get("text", "")))
                return {
                    "text": clean_text,
                    "parsed_problem": obj.get("parsed_problem") if isinstance(obj.get("parsed_problem"), dict) else None,
                    "first_question": obj.get("first_question") if isinstance(obj.get("first_question"), dict) else None,
                }
    except (json.JSONDecodeError, ValueError):
        pass

    # JSON 解析失败：将剥离思维链后的内容作为 text 返回
    return {"text": text, "parsed_problem": None, "first_question": None}


def _simple_ocr(image_bytes: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang="chi_sim+eng")
        return text.strip()
    except ImportError:
        return "未安装OCR依赖。请运行: pip install pytesseract Pillow，并安装Tesseract-OCR引擎。"
    except Exception as e:
        return f"OCR识别失败: {str(e)}"
