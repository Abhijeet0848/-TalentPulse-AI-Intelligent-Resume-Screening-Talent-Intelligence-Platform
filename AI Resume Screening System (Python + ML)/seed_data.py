import os
import json
from reportlab.pdfgen import canvas

from database import db, JobPosting, Candidate, ScreeningResult
from ml_engine.parser import parse_full_resume
from ml_engine.classifier import classifier_instance
from ml_engine.ranker import evaluate_candidate_for_job

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")

SAMPLE_JOBS = [
    {
        "title": "Senior Python Backend Engineer",
        "department": "Engineering",
        "required_skills": "Python, Django, FastAPI, PostgreSQL, REST API, Docker, Git, Microservices",
        "preferred_skills": "Redis, AWS, Kubernetes, Celery, CI/CD",
        "min_experience_years": 4.0,
        "required_education": "Bachelor's",
        "description": "We are seeking an experienced Senior Python Backend Engineer to build scalable microservices and RESTful APIs. You will work with FastAPI, PostgreSQL, Docker, and AWS. Candidates should have a strong grasp of clean code, database optimization, and asynchronous processing."
    },
    {
        "title": "Lead Data Scientist & AI Specialist",
        "department": "Data & AI",
        "required_skills": "Python, Machine Learning, TensorFlow, PyTorch, Scikit-Learn, Pandas, NLP, SQL",
        "preferred_skills": "BERT, LLM, Computer Vision, Docker, Tableau, Spark",
        "min_experience_years": 5.0,
        "required_education": "Master's",
        "description": "Looking for a Data Scientist with deep expertise in Natural Language Processing and Machine Learning models. You will train custom classification algorithms, fine-tune transformer models, clean unstructured datasets, and deploy ML models into production environment."
    },
    {
        "title": "DevOps & Cloud Infrastructure Specialist",
        "department": "Infrastructure",
        "required_skills": "AWS, Docker, Kubernetes, Terraform, CI/CD, Linux, Shell, Git",
        "preferred_skills": "Ansible, Python, Jenkins, Prometheus, Grafana",
        "min_experience_years": 3.0,
        "required_education": "Bachelor's",
        "description": "Join our infrastructure team to manage Kubernetes clusters, automate deployment pipelines with CI/CD and Terraform, and monitor multi-cloud systems on AWS. Experience in container security and Linux systems administration is highly valued."
    },
    {
        "title": "Senior Product Manager",
        "department": "Product",
        "required_skills": "Product Management, Agile, Scrum, Jira, Roadmapping, Stakeholder Management, User Stories",
        "preferred_skills": "SQL, A/B Testing, Data Analysis, Wireframing",
        "min_experience_years": 4.0,
        "required_education": "Bachelor's",
        "description": "Driven Senior Product Manager to lead cross-functional engineering and design teams. Responsible for product vision, feature prioritization, backlog grooming in Jira, user research, and data-driven iteration."
    }
]

SAMPLE_RESUMES_TEXT = [
    {
        "filename": "alex_morgan_python_dev.pdf",
        "name": "Alex Morgan",
        "email": "alex.morgan@example.com",
        "phone": "+1 (555) 234-5678",
        "linkedin": "https://linkedin.com/in/alexmorgan-dev",
        "github": "https://github.com/alexmorgan-python",
        "title": "Senior Python Engineer",
        "summary": "Results-driven Senior Python Engineer with 6 years of experience building high-throughput REST APIs and microservices. Expert in FastAPI, Django, PostgreSQL, Docker, Redis, and AWS.",
        "skills": ["Python", "FastAPI", "Django", "PostgreSQL", "REST API", "Docker", "Git", "Microservices", "Redis", "AWS", "Linux", "CI/CD", "Unit Testing"],
        "experience": [
            "Senior Backend Engineer - TechCorp Solutions (2021 - Present)\nArchitected high-performance FastAPI microservices handling 50k requests/min.\nOptimized PostgreSQL query indexing, reducing database load by 35%.\nDeployed containerized applications with Docker and AWS ECS.",
            "Python Developer - Innovate Labs (2018 - 2021)\nBuilt RESTful web APIs using Django and Celery for async task queues.\nImplemented OAuth2 authentication and Redis caching layer."
        ],
        "education": "B.S. in Computer Science - University of Tech (2018)"
    },
    {
        "filename": "sarah_connor_data_scientist.pdf",
        "name": "Sarah Connor",
        "email": "sarah.connor@example.com",
        "phone": "+1 (555) 987-6543",
        "linkedin": "https://linkedin.com/in/sarah-connor-ds",
        "github": "https://github.com/sarah-ds-ai",
        "title": "Senior Data Scientist & ML Engineer",
        "summary": "Data Scientist with 5 years of experience specializing in Machine Learning, Natural Language Processing (NLP), PyTorch, Scikit-Learn, and Deep Learning model deployment.",
        "skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-Learn", "Pandas", "NLP", "SQL", "BERT", "LLM", "Data Analysis", "Tableau", "FastAPI"],
        "experience": [
            "Lead AI Researcher - Neural Insights Inc. (2021 - Present)\nFine-tuned BERT and LLM transformer models for sentiment classification with 94% accuracy.\nEngineered NLP feature extraction pipelines processing millions of document records.\nBuilt ML deployment service using FastAPI and Docker on AWS.",
            "Data Scientist - Analytics Hub (2019 - 2021)\nDeveloped predictive customer churn models using Scikit-Learn RandomForest and XGBoost.\nPerformed SQL data transformations and built automated Tableau executive dashboards."
        ],
        "education": "M.S. in Data Science & Artificial Intelligence - State University (2019)"
    },
    {
        "filename": "david_chen_devops.pdf",
        "name": "David Chen",
        "email": "david.chen@example.com",
        "phone": "+1 (555) 456-7890",
        "linkedin": "https://linkedin.com/in/davidchen-devops",
        "github": "https://github.com/davidchen-infra",
        "title": "DevOps & Cloud Specialist",
        "summary": "Certified AWS Solutions Architect and DevOps Specialist with 4 years of hands-on experience in Kubernetes, Terraform, Docker, Linux, and GitHub Actions CI/CD pipelines.",
        "skills": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux", "Shell", "Git", "Ansible", "Jenkins", "Python", "Prometheus", "Grafana"],
        "experience": [
            "DevOps Engineer - CloudScale Systems (2022 - Present)\nAutomated AWS cloud infrastructure provisioning using Terraform and Ansible.\nManaged multi-node Kubernetes clusters and configured Helm deployment charts.\nBuilt automated GitHub Actions CI/CD pipelines reducing deployment time by 60%.",
            "Systems Administrator - DataNet (2020 - 2022)\nMaintained Linux production servers, configured Nginx reverse proxies and SSL certificates.\nWrote Bash shell scripts for server health monitoring and backup automation."
        ],
        "education": "B.S. in Computer Information Systems - City College (2020)"
    },
    {
        "filename": "emily_watson_product.pdf",
        "name": "Emily Watson",
        "email": "emily.watson@example.com",
        "phone": "+1 (555) 321-7654",
        "linkedin": "https://linkedin.com/in/emilywatson-pm",
        "github": "https://github.com/emilywatson",
        "title": "Senior Product Manager",
        "summary": "User-focused Senior Product Manager with 5 years of experience leading cross-functional software teams, driving product strategy, Agile Scrum, Jira backlog refinement, and customer analytics.",
        "skills": ["Product Management", "Agile", "Scrum", "Jira", "Roadmapping", "Stakeholder Management", "User Stories", "SQL", "A/B Testing", "Data Analysis", "Wireframing"],
        "experience": [
            "Senior Product Manager - SaaSify (2021 - Present)\nDefined product roadmap for flagship enterprise SaaS product generating $12M ARR.\nLed Agile Scrum team of 8 engineers and 2 UX designers using Jira.\nConducted user interviews and A/B tests to improve onboarding conversion by 28%.",
            "Associate Product Manager - Digital Media Corp (2019 - 2021)\nWrote detailed technical user stories, acceptance criteria, and wireframes."
        ],
        "education": "B.A. in Business & Technology - Metro University (2019)"
    },
    {
        "filename": "michael_scott_junior_dev.pdf",
        "name": "Michael Scott",
        "email": "michael.scott@example.com",
        "phone": "+1 (555) 777-8899",
        "linkedin": "https://linkedin.com/in/michaelscott-dev",
        "github": "https://github.com/mscott-code",
        "title": "Junior Web Developer",
        "summary": "Enthusiastic Junior Developer with 1 year of internship experience in HTML, CSS, JavaScript, Basic Python, and Git version control.",
        "skills": ["HTML", "CSS", "JavaScript", "Python", "Git", "Bootstrap", "SQL"],
        "experience": [
            "Frontend Web Intern - PaperTech Inc. (2023 - 2024)\nDesigned landing pages using HTML, CSS, JavaScript, and Bootstrap.\nAssisted senior developers with Git commits and minor bug fixes."
        ],
        "education": "Associate Degree in Web Development - Community College (2023)"
    }
]

def generate_pdf_resume(resume_info):
    """Generate a clean fast PDF resume using ReportLab Canvas."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    pdf_path = os.path.join(UPLOADS_DIR, resume_info['filename'])
    
    c = canvas.Canvas(pdf_path)
    c.setFont("Helvetica-Bold", 16)
    y = 750
    c.drawString(50, y, resume_info['name'])
    
    c.setFont("Helvetica-Bold", 12)
    y -= 20
    c.drawString(50, y, resume_info['title'])
    
    c.setFont("Helvetica", 10)
    y -= 15
    c.drawString(50, y, f"Email: {resume_info['email']} | Phone: {resume_info['phone']} | {resume_info['linkedin']}")
    
    y -= 25
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "SUMMARY:")
    c.setFont("Helvetica", 9)
    y -= 15
    c.drawString(50, y, resume_info['summary'][:90])
    
    y -= 25
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "SKILLS:")
    c.setFont("Helvetica", 9)
    y -= 15
    c.drawString(50, y, ", ".join(resume_info['skills']))
    
    y -= 25
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "EXPERIENCE & EDUCATION:")
    c.setFont("Helvetica", 9)
    for exp in resume_info['experience']:
        for line in exp.split("\n"):
            y -= 12
            c.drawString(50, y, line[:90])
            
    y -= 20
    c.drawString(50, y, f"Education: {resume_info['education']}")
    
    c.save()
    return pdf_path

def seed_database_and_samples():
    """Populate database with sample jobs, create PDF resumes, parse & score them safely without locking SQLite."""
    ScreeningResult.query.delete()
    Candidate.query.delete()
    JobPosting.query.delete()
    db.session.commit()
    
    print("Seeding Job Postings...")
    job_objects = []
    for j_data in SAMPLE_JOBS:
        job = JobPosting(**j_data)
        db.session.add(job)
        job_objects.append(job)
    db.session.commit()

    print("Generating Sample PDF Resumes & Screening Candidates...")
    for r_info in SAMPLE_RESUMES_TEXT:
        pdf_path = generate_pdf_resume(r_info)
        parsed = parse_full_resume(pdf_path)
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
            file_path=pdf_path,
            file_name=r_info['filename'],
            predicted_category=predicted_cat
        )
        db.session.add(candidate)
        db.session.commit()

        for job in job_objects:
            job_dict = job.to_dict()
            cand_dict = candidate.to_dict()
            cand_dict['raw_text'] = parsed['raw_text']
            
            result_eval = evaluate_candidate_for_job(cand_dict, job_dict)
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
    print("Database seeding and PDF resume generation completed successfully!")
