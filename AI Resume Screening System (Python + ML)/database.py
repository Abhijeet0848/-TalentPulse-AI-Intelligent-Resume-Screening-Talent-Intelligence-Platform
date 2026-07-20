from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='Recruiter')  # Recruiter, HR Manager, Admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

class JobPosting(db.Model):
    __tablename__ = 'job_postings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100), default='Engineering')
    required_skills = db.Column(db.Text, nullable=False)
    preferred_skills = db.Column(db.Text, default='')
    min_experience_years = db.Column(db.Float, default=0.0)
    required_education = db.Column(db.String(100), default='Bachelor\'s')
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    results = db.relationship('ScreeningResult', backref='job', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'department': self.department,
            'required_skills': [s.strip() for s in self.required_skills.split(',') if s.strip()],
            'preferred_skills': [s.strip() for s in self.preferred_skills.split(',') if s.strip()],
            'min_experience_years': self.min_experience_years,
            'required_education': self.required_education,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

class Candidate(db.Model):
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), default='')
    phone = db.Column(db.String(50), default='')
    linkedin = db.Column(db.String(255), default='')
    github = db.Column(db.String(255), default='')
    experience_years = db.Column(db.Float, default=0.0)
    education_level = db.Column(db.String(100), default='Bachelor\'s')
    parsed_skills = db.Column(db.Text, default='')
    raw_text = db.Column(db.Text, default='')
    file_path = db.Column(db.String(300), default='')
    file_name = db.Column(db.String(150), default='')
    predicted_category = db.Column(db.String(100), default='General')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    results = db.relationship('ScreeningResult', backref='candidate', lazy=True, cascade='all, delete-orphan')

    def get_skills_list(self):
        try:
            return json.loads(self.parsed_skills) if self.parsed_skills else []
        except Exception:
            return [s.strip() for s in self.parsed_skills.split(',') if s.strip()]

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'linkedin': self.linkedin,
            'github': self.github,
            'experience_years': self.experience_years,
            'education_level': self.education_level,
            'parsed_skills': self.get_skills_list(),
            'file_name': self.file_name,
            'predicted_category': self.predicted_category,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

class ScreeningResult(db.Model):
    __tablename__ = 'screening_results'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_postings.id'), nullable=False)
    
    overall_score = db.Column(db.Float, nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    skill_score = db.Column(db.Float, nullable=False)
    experience_score = db.Column(db.Float, nullable=False)
    education_score = db.Column(db.Float, nullable=False)
    
    matched_skills = db.Column(db.Text, default='[]')
    missing_skills = db.Column(db.Text, default='[]')
    status = db.Column(db.String(50), default='New')
    ai_recommendation = db.Column(db.String(100), default='Moderate Match')
    ai_feedback = db.Column(db.Text, default='')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'job_id': self.job_id,
            'candidate_name': self.candidate.full_name if self.candidate else 'Unknown',
            'job_title': self.job.title if self.job else 'Unknown',
            'overall_score': round(self.overall_score, 1),
            'similarity_score': round(self.similarity_score, 1),
            'skill_score': round(self.skill_score, 1),
            'experience_score': round(self.experience_score, 1),
            'education_score': round(self.education_score, 1),
            'matched_skills': json.loads(self.matched_skills) if self.matched_skills else [],
            'missing_skills': json.loads(self.missing_skills) if self.missing_skills else [],
            'status': self.status,
            'ai_recommendation': self.ai_recommendation,
            'ai_feedback': self.ai_feedback,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M')
        }
