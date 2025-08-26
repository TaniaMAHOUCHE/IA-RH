from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher

class Matcher:
    def __init__(self):
        pass

    def fuzzy_match(self, word1, word2, threshold=0.8):
        ratio = SequenceMatcher(None, word1.lower(), word2.lower()).ratio()
        return ratio >= threshold

    def compute_skill_score(self, required_skills, extracted_skills):
        if not required_skills:
            return 0.0
        
        matched = 0
        for req in required_skills:
            for skill in extracted_skills:
                if self.fuzzy_match(req, skill):
                    matched += 1
                    break

        return (matched / len(required_skills)) * 100

    def compute_text_score(self, annonce_text, cv_text):
        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform([annonce_text, cv_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity * 100
        except Exception:
            return 0.0

    def compute_score(self, annonce_text, cv_text, required_skills=None, extracted_skills=None):
        required_skills = required_skills or []
        extracted_skills = extracted_skills or []

        text_score = self.compute_text_score(annonce_text, cv_text)
        skill_score = self.compute_skill_score(required_skills, extracted_skills)

        final_score = 0.7 * skill_score + 0.3 * text_score

        return {
            "text_score": round(text_score, 2),
            "skill_score": round(skill_score, 2),
            "final_score": round(final_score, 2)
        }
