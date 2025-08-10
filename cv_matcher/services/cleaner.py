import re
import unicodedata
from langdetect import detect

def clean_text(text: str) -> str:
    #Normaliser les caractères
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    #Mettre en minuscules
    text = text.lower()
    #Remplacer les retours à la ligne, tabulations, multiples espaces par un espace simple
    text = re.sub(r'\s+', ' ', text)
    #Supprimer les caractères spéciaux sauf lettres, chiffres et espaces
    text = re.sub(r'[^a-z0-9\s]', '', text)
    #Supprimer les espaces au début et fin
    text = text.strip()
    
    return text


def extract_emails(text: str) -> list:
    # Extraction d’emails 
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    return emails

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "unknown"

