import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Basic English Stopwords
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
    'can', 'cannot', 'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for',
    'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him',
    'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me', 'more',
    'most', 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our',
    'ours', 'ourselves', 'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some', 'such', 'than',
    'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this',
    'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what',
    'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'with', 'would', 'you', 'your', 'yours'
}

def preprocess_text(text):
    """Clean and tokenize text for vectorization."""
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove URLs, email addresses, and phone numbers
    text = re.sub(r'http\S+|www\S+|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
    # Remove special characters and numbers
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    # Remove extra spaces
    tokens = text.split()
    # Filter stopwords and short tokens
    cleaned_tokens = [word for word in tokens if word not in STOP_WORDS and len(word) > 1]
    return " ".join(cleaned_tokens)

def calculate_tfidf_similarity(jd_text, resume_text):
    """
    Compute cosine similarity between Job Description and Resume using TF-IDF.
    Returns score as a percentage between 0 and 100.
    """
    clean_jd = preprocess_text(jd_text)
    clean_resume = preprocess_text(resume_text)
    
    if not clean_jd or not clean_resume:
        return 0.0
        
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        tfidf_matrix = vectorizer.fit_transform([clean_jd, clean_resume])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(np.round(similarity * 100, 2))
    except Exception as e:
        print(f"Error computing TF-IDF similarity: {e}")
        return 0.0

def evaluate_skill_coverage(required_skills, candidate_skills, preferred_skills=None):
    """
    Evaluate candidate skill coverage against job posting required and preferred skills.
    Returns:
      - score (0-100)
      - matched_skills list
      - missing_skills list
    """
    if not required_skills:
        return 100.0, candidate_skills, []
        
    req_set = {s.strip().lower() for s in required_skills if s.strip()}
    cand_set = {s.strip().lower() for s in candidate_skills if s.strip()}
    pref_set = {s.strip().lower() for s in (preferred_skills or []) if s.strip()}
    
    matched = []
    missing = []
    
    for req in required_skills:
        req_clean = req.strip().lower()
        # Direct match or partial match
        if any(req_clean == cand or req_clean in cand or cand in req_clean for cand in cand_set):
            matched.append(req.strip())
        else:
            missing.append(req.strip())
            
    # Calculate base score based on required skills matched
    base_match_ratio = len(matched) / len(req_set) if req_set else 1.0
    score = base_match_ratio * 100.0
    
    # Bonus points for matching preferred skills (up to +15%)
    if pref_set:
        pref_matched_count = sum(1 for p in pref_set if any(p == cand or p in cand or cand in p for cand in cand_set))
        bonus = (pref_matched_count / len(pref_set)) * 15.0
        score = min(100.0, score + bonus)
        
    return round(score, 1), matched, missing
