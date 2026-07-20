import json
from ml_engine.nlp import calculate_tfidf_similarity, evaluate_skill_coverage

DEGREE_HIERARCHY = {
    "Ph.D.": 4,
    "Master's": 3,
    "Bachelor's": 2,
    "Associate/Diploma": 1,
    "High School": 0
}

def calculate_experience_score(cand_years, min_required_years):
    """Calculate experience match percentage."""
    if min_required_years <= 0:
        return 100.0
    if cand_years >= min_required_years:
        # Full score + slight bonus for senior experience up to 100
        return 100.0
    else:
        return round((cand_years / min_required_years) * 100.0, 1)

def calculate_education_score(cand_edu, req_edu):
    """Calculate education level alignment percentage."""
    cand_level = DEGREE_HIERARCHY.get(cand_edu, 2)
    req_level = DEGREE_HIERARCHY.get(req_edu, 2)
    
    if cand_level >= req_level:
        return 100.0
    elif cand_level == req_level - 1:
        return 75.0
    else:
        return 50.0

def generate_ai_feedback(overall_score, matched_skills, missing_skills, exp_years, req_exp_years, similarity_score):
    """Generate human-readable AI analysis feedback for candidate profile."""
    feedback_parts = []
    
    # Recommendation summary
    if overall_score >= 75:
        feedback_parts.append("🌟 **Strong Match**: Candidate demonstrates high alignment with key job requirements.")
    elif overall_score >= 55:
        feedback_parts.append("⚖️ **Moderate Match**: Candidate meets essential qualifications with a few skill or experience gaps.")
    else:
        feedback_parts.append("⚠️ **Low Match**: Candidate significantly falls short of required skills or experience level.")

    # Skill match comments
    if matched_skills:
        feedback_parts.append(f"✅ **Key Skill Matches**: {', '.join(matched_skills[:6])}.")
    if missing_skills:
        feedback_parts.append(f"❌ **Missing Critical Skills**: {', '.join(missing_skills[:6])}.")

    # Experience feedback
    if exp_years >= req_exp_years:
        feedback_parts.append(f"📈 **Experience**: Has {exp_years} yrs of experience (meets requirement of {req_exp_years} yrs).")
    else:
        feedback_parts.append(f"📉 **Experience Gap**: Candidate has {exp_years} yrs (job requires {req_exp_years} yrs).")

    # Semantic similarity comment
    feedback_parts.append(f"🔍 **Semantic Relevance**: {similarity_score}% contextual similarity to job description.")

    return "\n".join(feedback_parts)

def evaluate_candidate_for_job(candidate_data, job_data):
    """
    Perform multi-factor candidate ranking against a job posting.
    Returns dictionary with all scores, skill breakdowns, recommendation, and feedback.
    """
    jd_text = job_data.get('description', '') + " " + " ".join(job_data.get('required_skills', []))
    resume_text = candidate_data.get('raw_text', '') + " " + " ".join(candidate_data.get('parsed_skills', []))
    
    # 1. Similarity Score (40%)
    similarity_score = calculate_tfidf_similarity(jd_text, resume_text)
    
    # 2. Skill Coverage Score (30%)
    req_skills = job_data.get('required_skills', [])
    pref_skills = job_data.get('preferred_skills', [])
    cand_skills = candidate_data.get('parsed_skills', [])
    
    skill_score, matched_skills, missing_skills = evaluate_skill_coverage(
        required_skills=req_skills,
        candidate_skills=cand_skills,
        preferred_skills=pref_skills
    )
    
    # 3. Experience Score (20%)
    cand_exp = candidate_data.get('experience_years', 0.0)
    req_exp = job_data.get('min_experience_years', 0.0)
    exp_score = calculate_experience_score(cand_exp, req_exp)
    
    # 4. Education Score (10%)
    cand_edu = candidate_data.get('education_level', "Bachelor's")
    req_edu = job_data.get('required_education', "Bachelor's")
    edu_score = calculate_education_score(cand_edu, req_edu)
    
    # Weighted Overall Score
    overall_score = round(
        (0.40 * similarity_score) +
        (0.30 * skill_score) +
        (0.20 * exp_score) +
        (0.10 * edu_score),
        1
    )
    
    # Determine AI recommendation level
    if overall_score >= 75.0:
        recommendation = "Strong Match"
    elif overall_score >= 55.0:
        recommendation = "Moderate Match"
    else:
        recommendation = "Low Match"
        
    ai_feedback = generate_ai_feedback(
        overall_score=overall_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        exp_years=cand_exp,
        req_exp_years=req_exp,
        similarity_score=similarity_score
    )
    
    return {
        "overall_score": overall_score,
        "similarity_score": similarity_score,
        "skill_score": skill_score,
        "experience_score": exp_score,
        "education_score": edu_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "ai_recommendation": recommendation,
        "ai_feedback": ai_feedback
    }
