import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from ml_engine.nlp import preprocess_text

MODEL_PATH = os.path.join(os.path.dirname(__file__), "resume_classifier.pkl")

# Built-in synthetic corpus for initial ML training if no model exists
TRAINING_DATASET = [
    # Software Engineering
    ("Senior Python Backend Developer with experience in Django, Flask, FastAPI, PostgreSQL, REST APIs, Microservices, Docker, Redis, Git, and Unit Testing.", "Software Engineering"),
    ("Java Software Engineer skilled in Spring Boot, Hibernate, Microservices, Kafka, MySQL, Kubernetes, CI/CD, OOP design patterns, and AWS.", "Software Engineering"),
    ("Full Stack Developer proficient in React, Node.js, TypeScript, Express, MongoDB, GraphQL, System Design, REST APIs, and Docker.", "Software Engineering"),
    ("C++ Software Engineer specializing in low-latency systems, data structures, multithreading, Linux kernel, and algorithm optimization.", "Software Engineering"),
    
    # Data Science & AI
    ("Data Scientist with expertise in Machine Learning, Python, TensorFlow, PyTorch, Scikit-learn, Pandas, NLP, LLM, BERT, Feature Engineering, and SQL.", "Data Science & AI"),
    ("Machine Learning Engineer focused on computer vision, deep learning, PyTorch, OpenCV, CUDA, model deployment, FastAPI, and MLops.", "Data Science & AI"),
    ("AI Researcher and Data Analyst proficient in statistical analysis, R, Python, Matplotlib, Seaborn, Tableau, Hypothesis Testing, and predictive modeling.", "Data Science & AI"),
    ("Natural Language Processing Specialist building custom transformers, fine-tuning LLMs, text classification, vector databases, Hugging Face, and Python.", "Data Science & AI"),
    
    # DevOps & Cloud
    ("DevOps Specialist experienced in AWS, Terraform, Ansible, Docker, Kubernetes, Jenkins, GitHub Actions, Linux administration, and CI/CD pipelines.", "DevOps & Cloud"),
    ("Cloud Infrastructure Architect managing Azure, GCP, Terraform, Site Reliability Engineering (SRE), Prometheus, Grafana, and Bash scripting.", "DevOps & Cloud"),
    ("System Administrator skilled in Linux, Shell Scripting, Network Security, Docker, Nginx, Ansible, Cloud monitoring, and Disaster Recovery.", "DevOps & Cloud"),
    
    # Product Management
    ("Senior Product Manager leading cross-functional teams, roadmap planning, Agile Scrum, user stories, A/B testing, Jira, product analytics, and customer discovery.", "Product Management"),
    ("Technical Product Owner with strong background in software engineering, requirements gathering, stakeholder management, wireframing, and SQL analytics.", "Product Management"),
    
    # Frontend / UX Design
    ("Lead Frontend Engineer specializing in React.js, Next.js, Redux, HTML5, CSS3, Tailwind CSS, Webpack, Responsive Web Design, and accessibility.", "Frontend / UX Design"),
    ("UI/UX Designer and Frontend Developer skilled in Figma, Adobe XD, HTML/CSS, JavaScript, User Research, Prototyping, and Design Systems.", "Frontend / UX Design")
]

class ResumeClassifier:
    def __init__(self):
        self.pipeline = None
        self.categories = []
        self.load_or_train_model()

    def train(self, corpus=None):
        """Train the TF-IDF + Random Forest model pipeline."""
        if corpus is None:
            corpus = TRAINING_DATASET

        texts, labels = zip(*corpus)
        cleaned_texts = [preprocess_text(t) for t in texts]
        
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ('clf', RandomForestClassifier(n_estimators=20, random_state=42))
        ])
        
        self.pipeline.fit(cleaned_texts, labels)
        self.categories = list(self.pipeline.named_steps['clf'].classes_)
        
        # Save model
        try:
            with open(MODEL_PATH, 'wb') as f:
                pickle.dump(self.pipeline, f)
        except Exception as e:
            print(f"Failed to save trained classifier model: {e}")
            
        return len(texts), self.categories

    def load_or_train_model(self):
        """Load trained model from disk or train fresh instance."""
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, 'rb') as f:
                    self.pipeline = pickle.load(f)
                    self.categories = list(self.pipeline.named_steps['clf'].classes_)
                return
            except Exception as e:
                print(f"Error loading model, retraining: {e}")
                
        self.train()

    def predict(self, raw_text):
        """
        Predict job category for a given resume text.
        Returns:
          - top_category (str)
          - confidence (float 0-100)
          - probabilities (dict)
        """
        if not self.pipeline:
            self.load_or_train_model()

        clean_t = preprocess_text(raw_text)
        if not clean_t:
            return "General", 50.0, {}

        probs = self.pipeline.predict_proba([clean_t])[0]
        max_idx = np.argmax(probs)
        top_cat = self.categories[max_idx]
        confidence = float(np.round(probs[max_idx] * 100, 1))

        prob_dict = {cat: float(np.round(prob * 100, 1)) for cat, prob in zip(self.categories, probs)}
        return top_cat, confidence, prob_dict

# Global Classifier Instance
classifier_instance = ResumeClassifier()
