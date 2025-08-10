import streamlit as st
import json
from utils import extract_text_from_pdf, extract_keywords, compute_tfidf_similarity, extract_skills_with_ia
from services.matcher import hybrid_match
from ui_components import show_collapsible_badges, add_manual_selection_button
from services.db import save_offer_and_cvs, load_saved_offers, delete_offer, delete_cv_from_offer
from services.cv_processor import process_cv  

lang_map = {
    "fr": "Français",
    "en": "Anglais",
    "auto": "Détection automatique"
}

# Pour éviter de recharger et retraiter le fichier à chaque interaction
@st.cache_data

# Chargement des compétences depuis JSON
def load_skill_list():
    with open("data/keywords.json", "r", encoding="utf-8") as f:
        return [skill.lower() for skill in json.load(f)]

skill_list = load_skill_list()

def page_matcher():

    st.markdown("### 1. Titre de l'offre")
    offer_title = st.text_input("Titre de l'offre", max_chars=100)

    st.markdown("### 2. Offre d'emploi")
    offer_source = st.radio("Source :", ("Texte", "PDF"))
    offer_text = ""
    if offer_source == "Texte":
        offer_text = st.text_area("Collez le texte de l'offre")
    else:
        pdf_file = st.file_uploader("Uploader PDF", type="pdf")
        if pdf_file:
            offer_text = extract_text_from_pdf(pdf_file)
            st.text_area("Texte extrait", offer_text, height=150)

    st.markdown("### 3. Uploader CV(s) PDF")
    cvs = st.file_uploader("CVs", type="pdf", accept_multiple_files=True)

    lang_choice = st.selectbox("Langue du CV", ["Détection automatique", "Français", "Anglais"]) 
    seuil = st.slider("Seuil score sélection automatique", 0.0, 1.0, 0.3, 0.05)

    skill_list = load_skill_list() 

    selected_cvs = []

    if offer_text and cvs and offer_title.strip():
        st.markdown("### Résultats")

        for cv_file in cvs:
            cv_text = extract_text_from_pdf(cv_file)

            # Traitement CV multilingue
            cv_processing_result = process_cv(cv_text, lang_choice=lang_choice)
            lang_code = cv_processing_result.get("lang", "inconnue")
            st.write(f"Langue détectée : {lang_map.get(lang_code, lang_code)}")
            if "entities" in cv_processing_result:
                st.write("Entités extraites :", cv_processing_result["entities"])
            if "error" in cv_processing_result:
                st.error(cv_processing_result["error"])

            results = hybrid_match(offer_text, cv_text, skill_list)

            st.subheader(f"📄 CV: {cv_file.name}")
            st.write("**Résultat de l'analyse :**")
            st.write("Ce CV a obtenu un score global basé sur l'analyse des compétences extraites par mots-clés, l'analyse sémantique TF-IDF, et la reconnaissance par IA.")
            st.write(f"**Score final :** {results['final_score']:.3f}")

            if results['common_skills']:
                show_collapsible_badges(results['common_skills'], label="✅ Compétences communes")

            ia_only = set(results['ia_skills']) - set(results['common_skills'])
            if ia_only:
                show_collapsible_badges(list(ia_only), label="Compétences détectées par IA uniquement")

            keywords_only = set(results['basic_skills']) - set(results['common_skills'])
            if keywords_only:
                show_collapsible_badges(list(keywords_only), label="🔍 Compétences détectées par mots-clés uniquement")

            if add_manual_selection_button(cv_file.name):
                selected_cvs.append({
                    "cv_name": cv_file.name,
                    "cv_text": cv_text,
                    "score": results['final_score'],
                    "added_manually": True
                })
                st.success(f"CV {cv_file.name} ajouté manuellement.")

            if results['final_score'] >= seuil:
                selected_cvs.append({
                    "cv_name": cv_file.name,
                    "cv_text": cv_text,
                    "score": results['final_score'],
                    "added_manually": False
                })
                st.info(f"CV {cv_file.name} ajouté automatiquement (score >= seuil).")

        if selected_cvs:
            save_offer_and_cvs(offer_text, selected_cvs, offer_title)
            st.success("Offre et CVs enregistrés.")

    elif offer_text and not offer_title.strip():
        st.warning("Merci de saisir un titre d'offre.")

st.markdown("""
<style>
div[data-testid="stExpander"] div[role="button"] {
    background: #fff !important;
    color: #191919 !important;
    transition: background 0.3s, box-shadow 0.3s;
}

div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
    border-radius: 0 0 6px 6px;
}

div[data-testid="stExpander"] div[data-testid="stVerticalBlock"]:not([hidden]) ~ div[role="button"] {
    background: #fafafa !important;
    box-shadow: inset 0 -2px 0 rgba(0,0,0,0.08);
}

div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
    background-color: #9bb3c5 !important;
    color: #191919 !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    border-radius: 6px;
    padding: 10px;
}
/* Boutons "Supprimer cette offre"  */
button[kind="secondary"], 
button[kind="secondary"]:hover {
    color: black !important; 
    border-color: #d9534f !important; 
    background: #c94f4f !important;
}

/* Message "Aucune offre" */
.empty-message {
    background: #D9EDF7; 
    color: black; 
    padding: 10px; 
    border-radius: 5px; 
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

def page_cvs_selectionnes():
    st.subheader("Offres sauvegardées")
    offers = load_saved_offers()
    if not offers:
        st.markdown(
            '<div class="empty-message">Aucune offre enregistrée pour le moment.</div>',
            unsafe_allow_html=True
        )
        return

    for offer in offers:
        offer_id_str = str(offer["_id"])
        with st.expander(offer.get("title", "Offre sans titre")):
            st.write(f"**Titre de l'offre :** {offer.get('title', 'Offre sans titre')}")
            st.write("**Texte de l'offre :**")
            st.write(offer.get("offer_text", ""))

            if st.button("Supprimer cette offre", key=f"del_offer_{offer['_id']}"):
                delete_offer(offer['_id'])
                st.success("Offre supprimée.")
                st.write("Merci de recharger la page pour voir les changements.")
                st.stop()

            cvs = offer.get("selected_cvs", [])
            if cvs:
                st.write("**CVs associés :**")
                for cv in cvs:
                    cols = st.columns([0.9, 0.1])
                    with cols[0]:
                        st.write(f"- {cv['cv_name']} (score: {cv['score']:.3f})")
                    with cols[1]:
                        if st.button("✕", key=f"del_cv_{offer_id_str}_{cv['cv_name']}"):
                            delete_cv_from_offer(offer_id_str, cv['cv_name'])
                            st.success("CV supprimé.")
                            st.write("Merci de recharger la page pour voir les changements.")
                            st.stop()
            else:
                st.write("Aucun CV associé à cette offre.")


def main():
    st.set_page_config(page_title="Outil de présélection de CV avec IA", layout="wide")
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    st.title("Outil de présélection de CV avec IA")
    st.markdown("""
    <style>
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #9bb3c5;   
        padding-top: 36px !important;   
    }

    /* Boutons radio */
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 14px !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        background: #9bb3c5;
        padding: 8px 18px;
        border-radius: 18px;
        color: #765f36 !important;
        transition: all 0.15s;
        font-size: 1em;
    }
    section[data-testid="stSidebar"] .stRadio input:checked + div > label {
        background: #f3e5c6 !important;
        color: #333 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    menu = st.sidebar.radio("Menu",["Outil de présélection de CV", "CVs sélectionnés"])
    if menu == "Outil de présélection de CV":
        page_matcher()
    else:
        page_cvs_selectionnes()

if __name__ == "__main__":
    main()
