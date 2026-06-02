import base64
import os
import io
import httpx
from ai_service import ai_service

async def extract_text_from_base64(base64_data: str) -> str:
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
                model=ocr_model
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


async def _multimodal_ocr(base64_data: str, provider: str, api_key: str, base_url: str, model: str) -> str:
    """
    通过多模态模型解析题目与几何图象
    """
    if not base64_data.startswith("data:image"):
        # 默认假设是 png 图片，补齐头部
        base64_data = f"data:image/png;base64,{base64_data}"

    prompt = (
        "你是一个高精度的数学题目识别助手。请识别并提取图片中的数学题目内容。\n"
        "要求：\n"
        "1. 请使用 LaTeX 语法输出所有的数学公式和符号（例如用 $...$ 或 $$...$$）。\n"
        "2. 如果图片中包含几何图形、函数图象等视觉元素，请在识别出文本题目的同时，用详尽、逻辑严密的文字描述图形中的几何结构、各线段之间的连接与位置关系、已知的长度、角度以及图象关键点坐标。\n"
        "3. 整理后的输出应能让一个看不见图片的盲人（或纯文本大模型）仅通过阅读你输出的文本，就能完全理解题目并正确解答该几何/数学题。\n"
        "4. 直接输出整理后的题目文本，不要包含任何多余的开场白或解释。"
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
        "max_tokens": 1500
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
