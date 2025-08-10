import fitz
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline

# Nettoyage simple du texte 
def clean_text(text):
    return re.sub(r"[^a-zA-ZÀ-ÿ0-9\s]", " ", text).lower()

# Extraction texte PDF 
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Extraction mots-clés basés sur la liste de compétences
def extract_keywords(text, skill_list=None):
    text_clean = clean_text(text)
    if skill_list:
        return [skill for skill in skill_list if skill.lower() in text_clean]
    else:
        return list(set(text_clean.split()))

# Initialisation du pipeline NER avec CamemBERT français
ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple", device=-1)

# Extraction des compétences avec l'IA 
def extract_skills_with_ia(text):
    cleaned_text = clean_text(text)
    entities = ner_pipeline(cleaned_text)
    skills = set()
    valid_labels = ['MISC', 'ORG', 'PER']
    for ent in entities:
        if ent['entity_group'] in valid_labels:
            word = ent['word'].lower().strip()
            skills.add(word)
    return list(skills)

# Calcul similarité TF-IDF entre 2 textes
def compute_tfidf_similarity(text1, text2):
    vect = TfidfVectorizer(stop_words=None)
    tfidf = vect.fit_transform([text1, text2])
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return score, None
