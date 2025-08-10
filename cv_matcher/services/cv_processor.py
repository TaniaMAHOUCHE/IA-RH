import spacy
from langdetect import detect
from services.cleaner import clean_text, extract_emails
from utils import extract_skills_with_ia

# Chargement du modèle anglais de spaCy (en_cv_info_extr)
try:
    nlp_en = spacy.load("en_cv_info_extr")
except Exception as e:
    print("Erreur lors du chargement du modèle anglais :", e)
    nlp_en = None

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "unknown"

def process_cv_french(text: str):
    # On traite le CV en français via CamemBERT/NER
    cleaned = clean_text(text)
    ner_entities = extract_skills_with_ia(cleaned)
    return {
        "lang": "fr",
        "entities": ner_entities
    }

def process_cv_english(text: str):
    # On traite le CV anglais via en_cv_info_extr et spaCy
    if not nlp_en:
        return {"error": "Modèle anglais non disponible."}
    doc = nlp_en(text)

    entities_by_label = {}
    for ent in doc.ents:
        key = ent.label_
        entities_by_label.setdefault(key, []).append(ent.text)
    return {
        "lang": "en",
        "entities": entities_by_label
    }

def process_cv(text: str, lang_choice: str = "auto"):
    # On choisit la pipeline selon la langue détectée ou choisie 
    if lang_choice == "auto":
        lang = detect_language(text)
    else:
        lang = lang_choice

    if lang == "fr":
        return process_cv_french(text)
    elif lang == "en":
        return process_cv_english(text)
    else:
        return {"error": f"Langue '{lang}' non supportée."}
