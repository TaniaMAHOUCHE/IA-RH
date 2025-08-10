from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
import torch

class SkillMatcher:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(stop_words='french')
        self.sent_transformer = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.tfidf_fitted = False

    def fit_tfidf(self, documents):
        self.tfidf_vectorizer.fit(documents)
        self.tfidf_fitted = True

    def tfidf_similarity(self, text1, text2):
        if not self.tfidf_fitted:
            raise ValueError("TF-IDF vectorizer not fitted yet")
        vecs = self.tfidf_vectorizer.transform([text1, text2])
        sim = cosine_similarity(vecs[0], vecs[1])[0][0]
        return sim

    def embedding_similarity(self, text1, text2):
        emb1 = self.sent_transformer.encode(text1, convert_to_tensor=True)
        emb2 = self.sent_transformer.encode(text2, convert_to_tensor=True)
        return util.pytorch_cos_sim(emb1, emb2).item()

    def compute_similarity(self, text1, text2):
        try:
            sim_tfidf = self.tfidf_similarity(text1, text2)
        except Exception:
            sim_tfidf = 0
        sim_emb = self.embedding_similarity(text1, text2)
        final_score = 0.4 * sim_tfidf + 0.6 * sim_emb
        return round(final_score, 3)
