import os
import io
import csv
import json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, session, send_file
from werkzeug.utils import secure_filename

from database import db, User, JobPosting, Candidate, ScreeningResult
from ml_engine.parser import parse_full_resume
from ml_engine.classifier import classifier_instance
from ml_engine.ranker import evaluate_candidate_for_job

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai_resume_screener_secret_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'screener.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOADS_DIR

db.init_app(app)

def init_db_and_seed():
    """Initialize database tables safely."""
    with app.app_context():
        db.create_all()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'Admin':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        selected_role = request.form.get('role', 'Recruiter')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            user.role = selected_role
            db.session.commit()

            session['user_id'] = user.id
            session['user_name'] = user.full_name
            session['user_email'] = user.email
            session['user_role'] = selected_role
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password.')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', 'Recruiter')

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email address is already registered.')

        new_user = User(
            full_name=full_name,
            email=email,
            role=role if role in ['Candidate', 'Recruiter', 'HR Manager', 'Admin'] else 'Recruiter'
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['user_name'] = new_user.full_name
        session['user_email'] = new_user.email
        session['user_role'] = new_user.role

        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/admin/users')
@admin_required
def admin_users():
    user_list = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', active_page='admin_users', users=[u.to_dict() for u in user_list])

@app.route('/admin/users/<int:user_id>/role', methods=['POST'])
@admin_required
def update_user_role(user_id):
    u = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['Candidate', 'Recruiter', 'HR Manager', 'Admin']:
        u.role = new_role
        db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id != session.get('user_id'):
        u = User.query.get_or_404(user_id)
        db.session.delete(u)
        db.session.commit()
    return redirect(url_for('admin_users'))

@app.route('/dashboard')
@login_required
def dashboard():
    total_candidates = Candidate.query.count()
    total_jobs = JobPosting.query.count()
    shortlisted_count = ScreeningResult.query.filter_by(status='Shortlisted').count()
    interview_count = ScreeningResult.query.filter_by(status='Interview').count()
    
    avg_score_res = db.session.query(db.func.avg(ScreeningResult.overall_score)).scalar()
    avg_score = round(avg_score_res, 1) if avg_score_res else 0.0

    results_all = ScreeningResult.query.order_by(ScreeningResult.overall_score.desc()).all()
    recent_dicts = [r.to_dict() for r in results_all]

    candidates = Candidate.query.all()
    category_counts = {}
    skill_counts = {}

    for c in candidates:
        cat = c.predicted_category or 'General'
        category_counts[cat] = category_counts.get(cat, 0) + 1
        
        try:
            skills = json.loads(c.parsed_skills or '[]')
            for s in skills:
                skill_counts[s] = skill_counts.get(s, 0) + 1
        except Exception:
            pass

    sorted_skills = dict(sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:8])

    kanban_stages = {
        'Applied': [r for r in recent_dicts if r['status'] == 'New'],
        'Shortlisted': [r for r in recent_dicts if r['status'] == 'Shortlisted'],
        'Interview': [r for r in recent_dicts if r['status'] == 'Interview'],
        'Rejected': [r for r in recent_dicts if r['status'] == 'Rejected']
    }

    return render_template(
        'index.html',
        active_page='dashboard',
        stats={
            'total_candidates': total_candidates,
            'total_jobs': total_jobs,
            'shortlisted_count': shortlisted_count,
            'interview_count': interview_count,
            'avg_score': avg_score
        },
        recent_results=recent_dicts,
        category_counts=category_counts,
        top_skills=sorted_skills,
        kanban_stages=kanban_stages
    )

@app.route('/jobs')
@login_required
def jobs():
    if session.get('user_role') not in ['Recruiter', 'HR Manager', 'Admin']:
        return redirect(url_for('screen'))
    job_list = JobPosting.query.order_by(JobPosting.created_at.desc()).all()
    return render_template('jobs.html', active_page='jobs', jobs=[j.to_dict() for j in job_list])

@app.route('/api/generate_jd', methods=['POST'])
@login_required
def generate_jd():
    if session.get('user_role') not in ['Recruiter', 'HR Manager', 'Admin']:
        return jsonify({'success': False, 'error': 'Candidates cannot create job postings'}), 403
    data = request.get_json()
    role_title = data.get('role_title', 'MERN Stack Developer').strip()

    if 'mern' in role_title.lower():
        jd = {
            'title': 'Senior MERN Stack Engineer',
            'department': 'Engineering',
            'min_experience_years': 3.0,
            'required_education': "Bachelor's",
            'required_skills': 'MongoDB, Express.js, React, Node.js, JavaScript, REST API, Git',
            'preferred_skills': 'TypeScript, Redux, Docker, AWS, TailwindCSS, Jest',
            'salary_range': '₹ 14 – 22 LPA ($90K - $125K)',
            'description': 'We are seeking a talented Senior MERN Stack Engineer to design, build, and deploy high-performance web applications using MongoDB, Express, React, and Node.js.'
        }
    elif 'data' in role_title.lower() or 'ai' in role_title.lower():
        jd = {
            'title': 'Lead Data Scientist & AI Specialist',
            'department': 'Data Science & AI',
            'min_experience_years': 4.0,
            'required_education': "Master's",
            'required_skills': 'Python, PyTorch, TensorFlow, Scikit-Learn, Pandas, NLP, SQL',
            'preferred_skills': 'BERT, Transformers, Docker, MLOps, Tableau, AWS',
            'salary_range': '₹ 18 – 28 LPA ($120K - $160K)',
            'description': 'Lead end-to-end machine learning model development, Natural Language Processing pipelines, vector embeddings, and predictive intelligence.'
        }
    else:
        jd = {
            'title': f"Senior {role_title}",
            'department': 'Product Engineering',
            'min_experience_years': 3.0,
            'required_education': "Bachelor's",
            'required_skills': f"{role_title}, Python, SQL, REST API, Docker, Git",
            'preferred_skills': 'AWS, CI/CD, Microservices, Kubernetes',
            'salary_range': '₹ 12 – 18 LPA ($85K - $115K)',
            'description': f"Develop scalable microservices, optimize performance, and collaborate with product teams for {role_title} role."
        }

    return jsonify({'success': True, 'jd': jd})

# 8. AI Text Rewrite API
@app.route('/api/ai_rewrite_jd', methods=['POST'])
@login_required
def ai_rewrite_jd():
    data = request.get_json()
    text = data.get('text', '')
    rewritten = f"Architect, develop, test, and maintain high-throughput enterprise systems for '{text}', adhering to strict clean-code principles, automated CI/CD testing, and cross-functional team collaboration."
    return jsonify({'success': True, 'rewritten': rewritten})

@app.route('/jobs/create', methods=['POST'])
@login_required
def create_job():
    if session.get('user_role') not in ['Recruiter', 'HR Manager', 'Admin']:
        return redirect(url_for('screen'))
    title = request.form.get('title')
    department = request.form.get('department', 'Engineering')
    min_exp = float(request.form.get('min_experience_years', 0))
    req_edu = request.form.get('required_education', "Bachelor's")
    req_skills = request.form.get('required_skills', '')
    pref_skills = request.form.get('preferred_skills', '')
    description = request.form.get('description', '')

    new_job = JobPosting(
        title=title,
        department=department,
        min_experience_years=min_exp,
        required_education=req_edu,
        required_skills=req_skills,
        preferred_skills=pref_skills,
        description=description
    )
    db.session.add(new_job)
    db.session.commit()
    return redirect(url_for('jobs'))

@app.route('/screen')
@login_required
def screen():
    job_list = JobPosting.query.order_by(JobPosting.created_at.desc()).all()
    selected_job_id = request.args.get('job_id', type=int)
    if not selected_job_id and job_list:
        selected_job_id = job_list[0].id

    return render_template(
        'screen.html',
        active_page='screen',
        jobs=[j.to_dict() for j in job_list],
        selected_job_id=selected_job_id
    )

@app.route('/api/duplicate_check', methods=['POST'])
@login_required
def duplicate_check():
    data = request.get_json()
    filename = data.get('filename')
    existing = Candidate.query.filter_by(file_name=filename).first()
    if existing:
        return jsonify({'duplicate': True, 'candidate_name': existing.full_name, 'uploaded_at': str(existing.created_at)})
    return jsonify({'duplicate': False})

@app.route('/screen/upload', methods=['POST'])
@login_required
def upload_resume():
    job_id = request.form.get('job_id', type=int)
    job = JobPosting.query.get_or_404(job_id)
    files = request.files.getlist('resume_files')

    if not files or files[0].filename == '':
        return redirect(url_for('screen', job_id=job_id))

    for file in files:
        if file:
            filename = secure_filename(file.filename)
            saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(saved_path)

            parsed = parse_full_resume(saved_path)
            predicted_cat, conf, _ = classifier_instance.predict(parsed['raw_text'])

            candidate = Candidate(
                full_name=parsed['full_name'],
                email=parsed['email'],
                phone=parsed['phone'],
                linkedin=parsed['linkedin'],
                github=parsed['github'],
                experience_years=parsed['experience_years'],
                education_level=parsed['education_level'],
                parsed_skills=json.dumps(parsed['parsed_skills']),
                raw_text=parsed['raw_text'],
                file_path=saved_path,
                file_name=filename,
                predicted_category=predicted_cat
            )
            db.session.add(candidate)
            db.session.commit()

            result_eval = evaluate_candidate_for_job(candidate.to_dict(), job.to_dict())
            status = 'Shortlisted' if result_eval['overall_score'] >= 75 else ('Interview' if result_eval['overall_score'] >= 60 else 'New')

            screening_result = ScreeningResult(
                candidate_id=candidate.id,
                job_id=job.id,
                overall_score=result_eval['overall_score'],
                similarity_score=result_eval['similarity_score'],
                skill_score=result_eval['skill_score'],
                experience_score=result_eval['experience_score'],
                education_score=result_eval['education_score'],
                matched_skills=json.dumps(result_eval['matched_skills']),
                missing_skills=json.dumps(result_eval['missing_skills']),
                status=status,
                ai_recommendation=result_eval['ai_recommendation'],
                ai_feedback=result_eval['ai_feedback']
            )
            db.session.add(screening_result)

    db.session.commit()
    return redirect(url_for('leaderboard'))

@app.route('/leaderboard')
@login_required
def leaderboard():
    results = ScreeningResult.query.order_by(ScreeningResult.overall_score.desc()).all()
    return render_template('leaderboard.html', active_page='leaderboard', results=[r.to_dict() for r in results])

@app.route('/uploads/<filename>')
@login_required
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@app.route('/candidate/<int:result_id>')
@login_required
def candidate_detail(result_id):
    res = ScreeningResult.query.get_or_404(result_id)
    cand = Candidate.query.get_or_404(res.candidate_id)
    return render_template('candidate.html', active_page='leaderboard', result=res.to_dict(), candidate=cand.to_dict())

@app.route('/api/candidate/<int:result_id>/notes', methods=['POST'])
@login_required
def save_notes(result_id):
    res = ScreeningResult.query.get_or_404(result_id)
    data = request.get_json()
    notes = data.get('notes', '')
    res.ai_feedback = notes
    db.session.commit()
    return jsonify({'success': True, 'notes': notes})

@app.route('/compare')
@login_required
def compare_candidates():
    c1_id = request.args.get('c1', type=int)
    c2_id = request.args.get('c2', type=int)
    
    results = ScreeningResult.query.order_by(ScreeningResult.overall_score.desc()).all()
    results_dicts = [r.to_dict() for r in results]

    c1 = ScreeningResult.query.get(c1_id).to_dict() if c1_id else (results_dicts[0] if len(results_dicts) > 0 else None)
    c2 = ScreeningResult.query.get(c2_id).to_dict() if c2_id else (results_dicts[1] if len(results_dicts) > 1 else None)

    winner = None
    if c1 and c2:
        winner = c1 if c1['overall_score'] >= c2['overall_score'] else c2

    return render_template('compare.html', active_page='leaderboard', c1=c1, c2=c2, winner=winner, candidates=results_dicts)

@app.route('/api/generate_questions/<int:result_id>')
@login_required
def generate_interview_questions(result_id):
    res = ScreeningResult.query.get_or_404(result_id)
    skills = res.to_dict().get('matched_skills', ['Python', 'SQL', 'Git'])
    
    questions = [
        f"1. Explain how you implemented {skills[0] if len(skills) > 0 else 'Python'} in your past key projects.",
        f"2. How do you handle scalability and error handling when deploying with {skills[1] if len(skills) > 1 else 'Docker'}?",
        f"3. Can you describe a challenge you faced with {skills[2] if len(skills) > 2 else 'PostgreSQL'} and how you optimized query performance?",
        "4. Describe your approach to code reviews, Git branching strategies, and CI/CD automated testing.",
        "5. How do you evaluate trade-offs between system architecture design and rapid project timelines?"
    ]
    
    return jsonify({'success': True, 'candidate_name': res.candidate.full_name, 'questions': questions})

@app.route('/api/ai_chat', methods=['POST'])
@login_required
def ai_chat():
    data = request.get_json()
    query = data.get('query', '').lower()
    
    if 'react' in query:
        res = "I found candidates with React skills in the talent pool: John Doe (98% match), Sarah Jenkins (92% match)."
    elif 'top' in query or 'best' in query:
        res = "Top candidate is John Doe for Senior Python Engineer with a 98.5% overall fit score."
    elif 'summarize' in query or 'john' in query:
        res = "John Doe is a Senior Full Stack Engineer with 5 years experience in Python, FastAPI, Docker, and PostgreSQL."
    elif 'salary' in query:
        res = "Market Salary Recommendation: ₹ 14 - 22 LPA ($90K - $125K) for Senior Full Stack/MERN engineers based on skills and location."
    else:
        res = f"TalentPulse AI Copilot: Processed query for '{query}'. Skill taxonomy and candidate match matrix are fully updated."
        
    return jsonify({'response': res})

@app.route('/api/screening/<int:result_id>/status', methods=['POST'])
@login_required
def update_status(result_id):
    res = ScreeningResult.query.get_or_404(result_id)
    data = request.get_json()
    new_status = data.get('status')
    if new_status in ['New', 'Shortlisted', 'Interview', 'Rejected']:
        res.status = new_status
        db.session.commit()
        return jsonify({'success': True, 'status': new_status})
    return jsonify({'success': False, 'error': 'Invalid status'}), 400

@app.route('/export/<format>')
@login_required
def export_results(format):
    results = ScreeningResult.query.order_by(ScreeningResult.overall_score.desc()).all()
    
    if format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Rank', 'Candidate Name', 'Target Job', 'Predicted Domain', 'Overall Fit Score %', 'Similarity %', 'Skill Score %', 'Experience Yrs', 'Recommendation', 'Status'])
        
        for idx, r in enumerate(results, 1):
            writer.writerow([
                idx, r.candidate.full_name if r.candidate else '',
                r.job.title if r.job else '',
                r.candidate.predicted_category if r.candidate else '',
                r.overall_score, r.similarity_score, r.skill_score,
                r.candidate.experience_years if r.candidate else 0,
                r.ai_recommendation, r.status
            ])
            
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=candidate_screening_rankings.csv"})
        
    elif format == 'json':
        data = [r.to_dict() for r in results]
        return jsonify(data)
        
    return redirect(url_for('leaderboard'))

@app.route('/analytics')
@login_required
def analytics():
    if session.get('user_role') not in ['HR Manager', 'Admin']:
        return redirect(url_for('dashboard'))
    return render_template('analytics.html', active_page='analytics')

@app.route('/retrain', methods=['POST'])
@admin_required
def retrain_model():
    classifier_instance.train()
    return redirect(url_for('analytics'))

@app.route('/reseed', methods=['POST'])
@admin_required
def reseed_db():
    from seed_data import seed_database_and_samples
    seed_database_and_samples()
    return redirect(url_for('leaderboard'))

if __name__ == '__main__':
    init_db_and_seed()
    print("Starting TalentPulse AI Screener Application on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
