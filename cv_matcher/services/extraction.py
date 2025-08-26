import spacy

nlp = spacy.load("en_cv_info_extr")

def extract_cv_info(cv_text_en: str):
    doc = nlp(cv_text_en)
    extracted = {}
    for ent in doc.ents:
        label = ent.label_
        text = ent.text.strip()
        extracted.setdefault(label, []).append(text)
    return extracted
