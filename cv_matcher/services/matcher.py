from utils import extract_keywords, extract_skills_with_ia, compute_tfidf_similarity

def hybrid_match(offer_text, cv_text, skill_list):
    semantic_score, _ = compute_tfidf_similarity(offer_text, cv_text)
    offer_skills = set(extract_keywords(offer_text, skill_list))
    cv_skills_basic = set(extract_keywords(cv_text, skill_list))
    cv_skills_ia = set(extract_skills_with_ia(cv_text))

    cv_skills = cv_skills_basic.union(cv_skills_ia)
    common_skills = offer_skills.intersection(cv_skills)
    missing_skills = offer_skills.difference(cv_skills)

    # Score basé uniquement sur compétences extraites par les mots-clés de la liste
    keyword_score = len(common_skills) / len(offer_skills) if offer_skills else 0

    # Score IA = proportion compétences IA détectées parmi celles de l'offre
    ia_raw_score = len(offer_skills.intersection(cv_skills_ia)) / len(offer_skills) if offer_skills else 0
    ia_score = ia_raw_score if ia_raw_score > 0 else 0.1  

    # Score final = moyenne pondérée
    final_score = (semantic_score + keyword_score + ia_score) / 3

    return {
        "semantic_score": semantic_score,
        "keyword_score": keyword_score,
        "ia_score": ia_score,
        "final_score": final_score,
        "common_skills": common_skills,
        "missing_skills": missing_skills,
        "basic_skills": cv_skills_basic,
        "ia_skills": cv_skills_ia,
    }
