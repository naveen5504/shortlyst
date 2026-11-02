from datetime import datetime, timezone
from applications.extensions import db

def utc_now():
    return datetime.now(timezone.utc)

class JobPosting(db.Model):
    __tablename__ = 'job_postings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, default="Untitled Screening")
    jd_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    candidates = db.relationship('CandidateResult', backref='job', cascade='all, delete-orphan', lazy=True)

class CandidateResult(db.Model):
    __tablename__ = 'candidate_results'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    candidate_name = db.Column(db.String(255), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    match_score = db.Column(db.Integer, nullable=False)
    semantic_score = db.Column(db.Float, default=0.0)
    llm_score = db.Column(db.Integer, default=0)
    recommendation = db.Column(db.String(50), nullable=False)
    strengths_json = db.Column(db.Text, default="[]")
    gaps_json = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=utc_now)
