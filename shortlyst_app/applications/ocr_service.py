import io
import re
from typing import BinaryIO, Union
import numpy as np
from PIL import Image
from pypdf import PdfReader
from rapidocr_onnxruntime import RapidOCR

_ocr_engine = None

def get_ocr_engine() -> RapidOCR:
    """Lazy initialize RapidOCR engine."""
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = RapidOCR()
    return _ocr_engine

def extract_text_from_image(image_source: Union[bytes, BinaryIO, Image.Image]) -> str:
    """Extract plain text from an image using RapidOCR."""
    try:
        ocr = get_ocr_engine()
        if isinstance(image_source, Image.Image):
            img_arr = np.array(image_source.convert("RGB"))
        elif isinstance(image_source, bytes):
            img = Image.open(io.BytesIO(image_source)).convert("RGB")
            img_arr = np.array(img)
        else:
            img = Image.open(image_source).convert("RGB")
            img_arr = np.array(img)

        result, _ = ocr(img_arr)
        if not result:
            return ""

        extracted_lines = [line[1] for line in result if len(line) > 1 and line[1]]
        text = "\n".join(extracted_lines)
        return normalize_text(text)
    except Exception as e:
        print(f"Image OCR error: {e}")
        return ""

def extract_text_from_pdf_with_ocr(source: Union[bytes, BinaryIO]) -> str:
    """Extract text from PDF, falling back to OCR if scanned or image-based."""
    try:
        raw_bytes = source.read() if hasattr(source, "read") else source
        if hasattr(source, "seek"):
            source.seek(0)

        reader = PdfReader(io.BytesIO(raw_bytes))
        extracted_pages = [page.extract_text() or "" for page in reader.pages]
        combined = "\n".join(extracted_pages).strip()

        # If PDF has ample selectable text, return it
        if len(combined) >= 50:
            return normalize_text(combined)

        # Scanned PDF fallback: perform OCR on embedded images across pages
        ocr_lines = []
        for page in reader.pages:
            for img_file in page.images:
                img_text = extract_text_from_image(img_file.data)
                if img_text:
                    ocr_lines.append(img_text)

        if ocr_lines:
            return normalize_text("\n\n".join(ocr_lines))

        return normalize_text(combined)
    except Exception as e:
        print(f"PDF OCR extraction error: {e}")
        return ""

def extract_text_from_file(source: Union[bytes, BinaryIO], filename: str) -> str:
    """Universal text extractor supporting PDF, PNG, JPG, JPEG, WEBP, BMP."""
    fn = filename.lower()
    raw_bytes = source.read() if hasattr(source, "read") else source
    if hasattr(source, "seek"):
        source.seek(0)

    if fn.endswith(".pdf"):
        return extract_text_from_pdf_with_ocr(raw_bytes)
    elif fn.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")):
        return extract_text_from_image(raw_bytes)
    return ""

def normalize_text(text: str) -> str:
    """Clean extra spaces and carriage returns."""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()
