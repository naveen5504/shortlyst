import json
from flask import render_template, request, jsonify, redirect, url_for
from app import app, db
from models.models import JobPosting, CandidateResult
from applications.ocr_service import extract_text_from_file
from applications.ollama_service import check_health, OLLAMA_BASE_URL, CHAT_MODEL, EMBED_MODEL
from applications.rag_service import analyze_candidates_pipeline

ALLOWED_EXTENSIONS = ('.pdf', '.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff')

def is_allowed_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

@app.route('/')
def home():
    """Render Shortlyst landing page."""
    return render_template('landing.html')

@app.route('/workspace')
@app.route('/analyze', methods=['GET'])
def workspace():
    """Render Shortlyst screening workspace."""
    return render_template('workspace.html')

@app.route('/health')
def health():
    """General healthcheck."""
    return jsonify({"status": "ok", "message": "Shortlyst Python RAG API is operational"})

@app.route('/api/health/llm')
def llm_health():
    """Ollama connectivity and models status."""
    health_data = check_health()
    status_code = 200 if health_data["ok"] else 503
    return jsonify({
        "ollama": "connected" if health_data["ok"] else "unreachable",
        "baseUrl": OLLAMA_BASE_URL,
        "chatModel": CHAT_MODEL,
        "embedModel": EMBED_MODEL,
        "availableModels": health_data.get("models", []),
        "error": health_data.get("error")
    }), status_code

@app.route('/api/upload-jd', methods=['POST'])
def upload_jd():
    """Accepts either jdFile (PDF/Image with OCR) or jdText. Returns parsed jdText."""
    jd_text = ""
    if 'jdFile' in request.files and request.files['jdFile'].filename:
        file = request.files['jdFile']
        if not is_allowed_file(file.filename):
            return jsonify({"error": "Unsupported file format. Upload PDF, PNG, JPG, or WEBP."}), 400
        jd_text = extract_text_from_file(file.stream, file.filename)
    elif request.form.get('jdText'):
        jd_text = request.form.get('jdText')
    elif request.is_json and request.json.get('jdText'):
        jd_text = request.json.get('jdText')
    else:
        return jsonify({"error": "Provide either jdFile (PDF/Image) or jdText"}), 400

    if not jd_text or not jd_text.strip():
        return jsonify({"error": "Failed to extract text from job description. Ensure the document or image is readable."}), 422

    return jsonify({"jdText": jd_text.strip()})

@app.route('/api/upload-resumes', methods=['POST'])
def upload_resumes():
    """Accepts multi-file PDF or image resumes with OCR. Returns summary."""
    files = request.files.getlist('resumes')
    if not files:
        return jsonify({"error": "No resume files uploaded"}), 400

    summaries = []
    for f in files:
        if f.filename and is_allowed_file(f.filename):
            text = extract_text_from_file(f.stream, f.filename)
            summaries.append({"fileName": f.filename, "textLength": len(text)})

    return jsonify({"resumes": summaries, "count": len(summaries)})

@app.route('/api/analyze', methods=['POST'])
@app.route('/analyze', methods=['POST'])
def analyze():
    """Main RAG screening endpoint. Supports PDF & Image OCR for JD & resumes."""
    try:
        jd_text = request.form.get('jdText', '')
        if 'jdFile' in request.files and request.files['jdFile'].filename:
            jd_file = request.files['jdFile']
            if is_allowed_file(jd_file.filename):
                jd_text = extract_text_from_file(jd_file.stream, jd_file.filename)

        if not jd_text.strip():
            return jsonify({"error": "Job description is required (jdText or jdFile PDF/Image)"}), 400

        files = request.files.getlist('resumes')
        if not files:
            return jsonify({"error": "At least one candidate resume (PDF or image) is required"}), 400

        resume_payload = []
        for f in files:
            if f.filename and is_allowed_file(f.filename):
                extracted = extract_text_from_file(f.stream, f.filename)
                resume_payload.append({
                    "fileName": f.filename,
                    "text": extracted
                })

        if not resume_payload:
            return jsonify({"error": "No readable PDF or image resumes found"}), 400

        # Run RAG Pipeline with selected or default models
        chat_model = request.form.get('chatModel') or None
        embed_model = request.form.get('embedModel') or None
        candidates = analyze_candidates_pipeline(jd_text, resume_payload, chat_model=chat_model, embed_model=embed_model)

        # Persist to SQLite
        job_title = request.form.get('jobTitle') or "Candidate Screening"
        job = JobPosting(title=job_title, jd_text=jd_text)
        db.session.add(job)
        db.session.flush()

        for c in candidates:
            result = CandidateResult(
                job_id=job.id,
                candidate_name=c["candidateName"],
                file_name=c["fileName"],
                match_score=c["matchScore"],
                semantic_score=c["semanticScore"],
                llm_score=c["llmScore"],
                recommendation=c["recommendation"],
                strengths_json=json.dumps(c.get("keyStrengths", [])),
                gaps_json=json.dumps(c.get("keyGaps", []))
            )
            db.session.add(result)
        db.session.commit()

        return jsonify({
            "screeningId": job.id,
            "redirectUrl": f"/results/{job.id}",
            "candidates": candidates,
            "count": len(candidates)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/results/<int:job_id>')
def view_results(job_id):
    """Dedicated results dashboard page for a specific screening."""
    job = JobPosting.query.get_or_404(job_id)
    raw_results = CandidateResult.query.filter_by(job_id=job.id).order_by(CandidateResult.match_score.desc()).all()

    candidates = []
    for r in raw_results:
        candidates.append({
            "candidateName": r.candidate_name,
            "fileName": r.file_name,
            "matchScore": r.match_score,
            "semanticScore": r.semantic_score,
            "llmScore": r.llm_score,
            "recommendation": r.recommendation,
            "keyStrengths": json.loads(r.strengths_json or "[]"),
            "keyGaps": json.loads(r.gaps_json or "[]"),
            "createdAt": r.created_at.strftime('%Y-%m-%d %H:%M')
        })

    total = len(candidates)
    strong_count = sum(1 for c in candidates if c["recommendation"] == "Strong Fit")
    avg_score = round(sum(c["matchScore"] for c in candidates) / total) if total > 0 else 0
    top_candidate = candidates[0]["candidateName"] if total > 0 else "-"

    stats = {
        "total": total,
        "strongCount": strong_count,
        "avgScore": avg_score,
        "topCandidate": top_candidate
    }

    return render_template(
        'results.html',
        job=job,
        candidates=candidates,
        stats=stats
    )

@app.route('/results')
def latest_results():
    """Redirect to the most recent screening or home if empty."""
    latest_job = JobPosting.query.order_by(JobPosting.id.desc()).first()
    if latest_job:
        return redirect(url_for('view_results', job_id=latest_job.id))
    return redirect(url_for('home'))
