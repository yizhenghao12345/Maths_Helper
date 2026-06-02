import base64
import os
import io
import httpx
from ai_service import ai_service

async def extract_text_from_base64(base64_data: str, language: str = "zh-CN") -> str:
    """
    优先使用多模态大模型进行高精度 OCR 与几何解析，降级至本地 Tesseract OCR。
    """
    # 提取纯 base64 数据以备本地 OCR 降级使用
    raw_base64 = base64_data
    if "," in base64_data:
        raw_base64 = base64_data.split(",")[1]

    # 1. 尝试使用多模态大模型进行高精度识别
    try:
        # 优先读取 OCR 专属环境变量，如果不存在则使用全局 AI 服务配置
        ocr_provider = os.getenv("OCR_PROVIDER") or ai_service.provider
        ocr_api_key = os.getenv("OCR_API_KEY") or ai_service.api_key
        ocr_base_url = os.getenv("OCR_BASE_URL") or ai_service.base_url
        
        # 智能匹配支持的多模态模型
        ocr_model = os.getenv("OCR_MODEL")
        if not ocr_model:
            if ocr_provider == "minimax":
                ocr_model = "MiniMax-M3"
            elif ocr_provider == "openai":
                ocr_model = "gpt-4o-mini"
            elif ocr_provider == "qwen":
                ocr_model = "qwen-vl-max"
            else:
                ocr_model = ai_service.model  # 降级使用全局模型配置

        # 校验是否具备调用多模态大模型的 API Key，且该提供商属于我们支持的 OpenAI 兼容多模态格式
        if ocr_api_key and ocr_provider in ["minimax", "openai", "qwen", "custom"]:
            text = await _multimodal_ocr(
                base64_data=base64_data,
                provider=ocr_provider,
                api_key=ocr_api_key,
                base_url=ocr_base_url,
                model=ocr_model,
                language=language
            )
            if text:
                return text
    except Exception as e:
        print(f"大模型多模态 OCR 解析失败: {e}，尝试降级到本地 Tesseract OCR。")

    # 2. 降级为本地 Tesseract OCR
    try:
        image_bytes = base64.b64decode(raw_base64)
        return _simple_ocr(image_bytes)
    except Exception as e:
        return f"降级本地 OCR 失败: {str(e)}"


async def _multimodal_ocr(base64_data: str, provider: str, api_key: str, base_url: str, model: str, language: str = "zh-CN") -> str:
    """
    通过多模态模型解析题目与几何图象
    """
    if not base64_data.startswith("data:image"):
        # 默认假设是 png 图片，补齐头部
        base64_data = f"data:image/png;base64,{base64_data}"

    if language == "en-US":
        prompt = (
            "You are a high-precision math problem recognition assistant specialized in Chinese and English math textbook problems.\n"
            "Follow these steps strictly:\n\n"
            "【Step 1 — Recognize the problem text】\n"
            "Read all text visible in the image (including text below or beside the figure). "
            "Output it verbatim, using LaTeX syntax for all math expressions (e.g., $AD=DE=EC$, $S_{\\triangle ABC}=1$).\n\n"
            "【Step 2 — Describe the geometric figure (if present)】\n"
            "If there is a geometric diagram, describe it in the following order:\n"
            "  a. Figure type (e.g., triangle, quadrilateral) and its vertex labels (e.g., △ABC with A at top, B at bottom-left, C at bottom-right).\n"
            "  b. All labeled interior/boundary points and their locations (e.g., 'D and E lie on AC, dividing it into three equal parts AD=DE=EC').\n"
            "  c. All line segments or rays drawn inside the figure and the intersection points they create (e.g., 'BD and AG intersect at M; BE and AF intersect at N').\n"
            "  d. Any shaded, colored, or highlighted regions and their boundary vertices (e.g., 'Quadrilateral MGFN is shaded in blue').\n"
            "  e. Any known numerical values shown in or around the figure.\n\n"
            "【Step 3 — State the question】\n"
            "Clearly state what is being asked (e.g., 'Find the area of the shaded region').\n\n"
            "Output format: combine all three steps into one coherent problem statement. "
            "Do NOT include section headers in the output. Do NOT add any opening remarks or extra explanation."
        )
    else:
        prompt = (
            "你是一个高精度的数学题目识别助手，专门处理中小学及竞赛数学题目（含文字题干与几何图形）。\n"
            "请按以下步骤严格执行：\n\n"
            "【第一步 — 识别题目文字】\n"
            "读取图片中所有可见文字（包括图形下方或旁边的文字说明），原文转录。\n"
            "所有数学符号与公式请使用 LaTeX 语法输出，例如 $AD=DE=EC$、$S_{\\triangle ABC}=1$。\n\n"
            "【第二步 — 描述几何图形（如有）】\n"
            "若图中存在几何图形，请按如下顺序描述：\n"
            "  a. 图形类型及各顶点标注与位置（例如：△ABC，A 在顶部，B 在左下，C 在右下）。\n"
            "  b. 图形内部或边上的所有标注点及其位置关系（例如：D、E 在 AC 上，将 AC 三等分，满足 $AD=DE=EC$）。\n"
            "  c. 图形内部所有线段/射线的连接关系及其交点（例如：连接 BD 和 BE，连接 AG 和 AF；BE 与 AG 交于点 M，BE 与 AF 交于点 N）。\n"
            "  d. 图中标有颜色（阴影、填充）的区域及其顶点（例如：四边形 MGFN 为蓝色阴影区域）。\n"
            "  e. 图中或图旁标注的任何已知数值。\n\n"
            "【第三步 — 明确求解目标】\n"
            "清晰说明题目要求解什么（例如：求阴影部分的面积）。\n\n"
            "输出格式：将以上三步合并为一段连贯的题目描述，直接输出，不要在输出中包含步骤标题，也不要加任何开场白或解释说明。"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 构造 OpenAI 标准多模态 payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_data
                        }
                    }
                ]
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2000
    }

    url = f"{base_url}/chat/completions"
    async with httpx.AsyncClient(timeout=35.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


def _simple_ocr(image_bytes: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        return text.strip()
    except ImportError:
        return "未安装OCR依赖。请运行: pip install pytesseract Pillow，并安装Tesseract-OCR引擎。"
    except Exception as e:
        return f"OCR识别失败: {str(e)}"
