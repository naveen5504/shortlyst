import io
import re
from typing import BinaryIO, Union
from pypdf import PdfReader

def extract_text_from_pdf(source: Union[bytes, BinaryIO]) -> str:
    """Extract and normalize plain text from a PDF stream or bytes buffer."""
    try:
        stream = io.BytesIO(source) if isinstance(source, bytes) else source
        reader = PdfReader(stream)
        pages_text = [page.extract_text() or "" for page in reader.pages]
        combined = "\n".join(pages_text)
        
        # Normalize whitespace
        combined = re.sub(r"\r\n", "\n", combined)
        combined = re.sub(r"\n{3,}", "\n\n", combined)
        combined = re.sub(r" {2,}", " ", combined)
        return combined.strip()
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""
