import os
from typing import Dict, Any, List, Optional
import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
DEFAULT_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2")
DEFAULT_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = DEFAULT_CHAT_MODEL
EMBED_MODEL = DEFAULT_EMBED_MODEL

def check_health() -> Dict[str, Any]:
    """Verify Ollama reachability and list available models."""
    try:
        res = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if res.status_code == 200:
            data = res.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return {"ok": True, "models": models, "error": None}
        return {"ok": False, "models": [], "error": f"HTTP {res.status_code}: {res.text}"}
    except Exception as e:
        return {"ok": False, "models": [], "error": str(e)}

def embed(text: str, model: Optional[str] = None) -> List[float]:
    """Generate dense embedding vector for a single text string."""
    trimmed = text.strip()
    if not trimmed:
        return []
    url = f"{OLLAMA_BASE_URL}/api/embed"
    payload = {"model": model or DEFAULT_EMBED_MODEL, "input": trimmed}
    res = requests.post(url, json=payload, timeout=60)
    res.raise_for_status()
    data = res.json()
    embeddings = data.get("embeddings", [])
    if not embeddings:
        raise ValueError("Ollama returned empty embeddings")
    return embeddings[0]

def embed_batch(texts: List[str], model: Optional[str] = None) -> List[List[float]]:
    """Generate embeddings for multiple texts in batch."""
    cleaned = [t.strip() for t in texts if t.strip()]
    if not cleaned:
        return []
    url = f"{OLLAMA_BASE_URL}/api/embed"
    payload = {"model": model or DEFAULT_EMBED_MODEL, "input": cleaned}
    res = requests.post(url, json=payload, timeout=120)
    res.raise_for_status()
    data = res.json()
    embeddings = data.get("embeddings", [])
    if len(embeddings) != len(cleaned):
        raise ValueError(f"Expected {len(cleaned)} embeddings, received {len(embeddings)}")
    return embeddings

def chat(prompt: str, temperature: float = 0.2, response_format: Optional[str] = "json", model: Optional[str] = None) -> str:
    """Generate text completion from Ollama chat model."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload: Dict[str, Any] = {
        "model": model or DEFAULT_CHAT_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature}
    }
    if response_format:
        payload["format"] = response_format

    res = requests.post(url, json=payload, timeout=180)
    res.raise_for_status()
    data = res.json()
    return data.get("response", "")
