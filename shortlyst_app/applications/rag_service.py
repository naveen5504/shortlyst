import json
import re
from typing import List, Dict, Any, Optional
import numpy as np
from applications.ollama_service import embed, embed_batch, chat

CHUNK_SIZE = 512
CHUNK_OVERLAP = 128

def chunk_text(text: str) -> List[str]:
    """Split text into overlapping character chunks."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= CHUNK_SIZE:
        return [cleaned] if cleaned else []
    
    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + CHUNK_SIZE, len(cleaned))
        chunks.append(cleaned[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))

def calculate_semantic_score(jd_embedding: List[float], chunk_embeddings: List[List[float]], top_k: int = 3) -> float:
    """Average cosine similarity across top-k best matching chunks."""
    if not chunk_embeddings or not jd_embedding:
        return 0.0
    similarities = [cosine_similarity(jd_embedding, c_emb) for c_emb in chunk_embeddings]
    similarities.sort(reverse=True)
    k = min(top_k, len(similarities))
    return float(sum(similarities[:k]) / k)

def llm_analyze_candidate(jd_text: str, resume_text: str, filename: str, chat_model: Optional[str] = None) -> Dict[str, Any]:
    """Execute LLM prompt to extract structured reasoning and score."""
    clean_name = re.sub(r"\.[a-zA-Z0-9]+$", "", filename)
    prompt = f"""You are an expert technical recruiter and hiring manager.
Analyze the candidate resume against the Job Description.

CRITICAL INSTRUCTIONS:
- Return ONLY a valid JSON object. No markdown, no commentary.
- The JSON must have EXACTLY these fields:
{{
  "candidateName": "Full name from resume, or '{clean_name}' if not found",
  "llmScore": <integer 0-100 representing overall fit>,
  "keyStrengths": ["strength 1", "strength 2", "strength 3"],
  "keyGaps": ["gap 1", "gap 2", "gap 3"]
}}
- llmScore: 80-100 = excellent fit, 50-79 = moderate, 0-49 = poor fit
- keyStrengths: 2-3 concise phrases about why this candidate is a good match
- keyGaps: 2-3 concise phrases about what is missing or weak

=== JOB DESCRIPTION ===
{jd_text[:3000]}

=== CANDIDATE RESUME ({filename}) ===
{resume_text[:4000]}

Return ONLY the JSON object:"""

    try:
        raw_response = chat(prompt, temperature=0.2, response_format="json", model=chat_model)
        match = re.search(r"\{[\s\S]*\}", raw_response)
        if match:
            parsed = json.loads(match.group(0))
            return {
                "candidateName": parsed.get("candidateName") or clean_name,
                "llmScore": max(0, min(100, int(parsed.get("llmScore", 50)))),
                "keyStrengths": parsed.get("keyStrengths", [])[:3],
                "keyGaps": parsed.get("keyGaps", [])[:3]
            }
    except Exception as e:
        print(f"LLM analysis warning for {filename}: {e}")

    return {
        "candidateName": clean_name,
        "llmScore": 50,
        "keyStrengths": ["Resume parsed and reviewed"],
        "keyGaps": ["Detailed automated evaluation limited"]
    }

def analyze_candidates_pipeline(
    jd_text: str,
    resumes: List[Dict[str, str]],
    chat_model: Optional[str] = None,
    embed_model: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Execute full RAG pipeline with selectable Ollama chat and embedding models."""
    if not jd_text.strip() or not resumes:
        return []

    # 1. Embed Job Description
    jd_embedding = embed(jd_text, model=embed_model)

    # 2. Chunk & Embed each resume
    results: List[Dict[str, Any]] = []

    for item in resumes:
        filename = item.get("fileName", "resume.pdf")
        text = item.get("text", "")

        chunks = chunk_text(text)
        chunk_embeddings = embed_batch(chunks, model=embed_model) if chunks else []

        # 3. Semantic similarity (60% weight)
        raw_semantic = calculate_semantic_score(jd_embedding, chunk_embeddings)

        # 4. LLM reasoning (40% weight)
        llm_data = llm_analyze_candidate(jd_text, text, filename, chat_model=chat_model)

        # 5. Hybrid combined score
        semantic_pct = raw_semantic * 100.0
        combined = int(round((semantic_pct * 0.6) + (llm_data["llmScore"] * 0.4)))
        match_score = max(0, min(100, combined))

        if match_score >= 80:
            recommendation = "Strong Fit"
        elif match_score >= 50:
            recommendation = "Moderate Fit"
        else:
            recommendation = "Not Fit"

        results.append({
            "candidateName": llm_data["candidateName"],
            "fileName": filename,
            "matchScore": match_score,
            "semanticScore": round(semantic_pct, 1),
            "llmScore": llm_data["llmScore"],
            "keyStrengths": llm_data["keyStrengths"],
            "keyGaps": llm_data["keyGaps"],
            "recommendation": recommendation
        })

    # 6. Sort descending by score
    results.sort(key=lambda x: x["matchScore"], reverse=True)
    return results
