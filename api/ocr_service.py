import base64
import re


def extract_text_from_base64(base64_data: str) -> str:
    if "," in base64_data:
        base64_data = base64_data.split(",")[1]

    image_bytes = base64.b64decode(base64_data)

    text = _simple_ocr(image_bytes)
    return text


def _simple_ocr(image_bytes: bytes) -> str:
    try:
        from PIL import Image
        import pytesseract
        import io

        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang='chi_sim+eng')
        return text.strip()
    except ImportError:
        return "未安装OCR依赖。请运行: pip install pytesseract Pillow，并安装Tesseract-OCR引擎。"
    except Exception as e:
        return f"OCR识别失败: {str(e)}"
