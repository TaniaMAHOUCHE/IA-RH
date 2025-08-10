import json
import re

def load_skills(filepath="data/keywords.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        skills = json.load(f)
    return set(skill.lower() for skill in skills)

skills_set = load_skills()

def extract_skills(text, skills_set=skills_set):
    text = text.lower()
    found_skills = set()
    for skill in skills_set:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text):
            found_skills.add(skill)
    return list(found_skills)
