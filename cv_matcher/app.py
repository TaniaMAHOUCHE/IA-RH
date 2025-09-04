import streamlit as st
from services.translation import Translator
from services.extraction import extract_cv_info
from services.matching import Matcher
from services.storage import MongoDB
from config import SCORE_THRESHOLD
from PyPDF2 import PdfReader

translator = Translator()
matcher = Matcher()
db = MongoDB()
st.set_page_config(page_title="CV Matcher", layout="wide")

with open("static/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Sidebar navigation
tabs = ["🏠 Accueil", "📋 Annonces", "📄 Dépôt CV", "🎯 Matching", "📊 Dashboard"]
page = st.sidebar.radio("Navigation", tabs)


def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text.strip()

# PAGE D'ACCUEIL
if page == "🏠 Accueil":
    st.title("Bienvenue sur CV Matcher")
    st.write("""
        Cette application vous permet de :
        - Gérer vos annonces d'emploi
        - Déposer et analyser des CVs
        - Effectuer le matching entre les CVs et les annonces
        - Consulter un tableau de bord avec les statistiques
    """)

# PAGE 1 : GESTION ANNONCES
elif page == "📋 Annonces":
    st.header("Gestion des annonces")
    titre = st.text_input("Titre du poste")
    service = st.text_input("Service")
    desc = st.text_area("Description (FR)")
    pdf_file = st.file_uploader("Importer un PDF pour l'annonce", type=["pdf"])
    
    if pdf_file:
        desc = read_pdf(pdf_file)
    
    if st.button("Créer annonce"):
        if not titre or not desc:
            st.warning("Le titre et la description sont obligatoires.")
        else:
            existing = [a for a in db.get_annonces() if a["titre"].lower() == titre.lower()]
            if existing:
                st.warning("Une annonce avec ce titre existe déjà.")
            else:
                desc_en = translator.translate(desc)
                infos_annonce = extract_cv_info(desc_en)
                annonce_skills = infos_annonce.get("HSKILL", [])

                annonce_id = db.add_annonce(titre, service, desc, desc_en, annonce_skills)
                st.success(f"Annonce '{titre}' créée")

    # Affichage des annonces
    st.subheader("Liste des annonces")
    annonces = db.get_annonces()
    for annonce in annonces:
        with st.expander(f"{annonce['titre']} - {annonce.get('service','')}"):
            st.write(annonce.get("description_fr", ""))
            if st.button(f"Supprimer annonce '{annonce['titre']}'", key=f"del_annonce_{annonce['_id']}"):
                db.delete_annonce(annonce["_id"])
                st.success(f"Annonce '{annonce['titre']}' supprimée ✅")
                st.experimental_rerun()

#PAGE 2 : DEPOT CV
elif page == "📄 Dépôt CV":
    st.header("Dépôt de CV")
    annonces = db.get_annonces()
    
    if not annonces:
        st.warning("Ajoutez d'abord une annonce.")
    else:
        annonce = st.selectbox("Sélectionner une annonce", annonces, format_func=lambda x: x['titre'])
        auto_threshold = st.slider("Seuil de sauvegarde automatique (%)", 0, 100, SCORE_THRESHOLD, 1)
        cv_files = st.file_uploader("Importer CVs (PDF)", type=["pdf"], accept_multiple_files=True)

        if st.button("Analyser"):
            if not cv_files:
                st.warning("Veuillez importer au moins un CV PDF.")
            else:
                st.session_state["cv_results"] = []
                for cv_file in cv_files:
                    cv_text = read_pdf(cv_file)
                    if not cv_text:
                        st.error(f"Le fichier {cv_file.name} est vide ou illisible.")
                        continue

                    existing_cvs = db.get_cvs_by_annonce(annonce["_id"])
                    if any(cv["filename"].lower() == cv_file.name.lower() for cv in existing_cvs):
                        st.warning(f"Le CV '{cv_file.name}' a déjà été enregistré.")
                        continue

                    cv_en = translator.translate(cv_text)
                    infos_cv = extract_cv_info(cv_en)
                    cv_skills = infos_cv.get("HSKILL", [])

                    scores = matcher.compute_score(
                        annonce["description_en"],
                        cv_en,
                        required_skills=annonce.get("skills", []),
                        extracted_skills=cv_skills
                    )

                    auto = scores["final_score"] >= auto_threshold

                    st.session_state["cv_results"].append({
                        "filename": cv_file.name,
                        "text": cv_text,
                        "text_en": cv_en,
                        "infos": infos_cv,
                        "scores": scores,
                        "auto": auto,
                    })

        if "cv_results" in st.session_state:
            for cv in st.session_state["cv_results"]:
                st.write(f"**{cv['filename']}** - Score final: {cv['scores']['final_score']}%")
                if cv["auto"]:
                    db.add_cv(annonce["_id"], cv["filename"], cv["text"], cv["text_en"],
                              cv["infos"], cv["scores"], True)
                    st.success(f"✅ CV '{cv['filename']}' enregistré automatiquement")
                else:
                    if st.button(f"Sauvegarder manuellement {cv['filename']}", key=f"save_{cv['filename']}"):
                        db.add_cv(annonce["_id"], cv["filename"], cv["text"], cv["text_en"],
                                  cv["infos"], cv["scores"], False)
                        st.success(f"CV '{cv['filename']}' sauvegardé manuellement")

#PAGE 3 : MATCHING
elif page == "🎯 Matching":
    st.header("Résultats de matching")
    annonces = db.get_annonces()
    search = st.text_input("Rechercher une annonce")
    if search:
        annonces = [a for a in annonces if search.lower() in a["titre"].lower()]
    
    if not annonces:
        st.info("Aucune annonce trouvée.")
    else:
        for annonce in annonces:
            with st.expander(f"{annonce['titre']} - {annonce.get('service','')}"):
                st.write(annonce.get("description_fr", ""))
                if st.button(f"Supprimer annonce '{annonce['titre']}'", key=f"del_match_annonce_{annonce['_id']}"):
                    db.delete_annonce(annonce["_id"])
                    st.success(f"Annonce '{annonce['titre']}' supprimée ✅")
                    st.experimental_rerun()

                cvs = db.get_cvs_by_annonce(annonce["_id"])
                if not cvs:
                    st.info("Aucun CV associé pour cette annonce.")
                else:
                    for cv in cvs:
                        statut = "Auto" if cv.get("auto_enregistre") else "Manuel"
                        st.write(f"{cv['filename']} - Score: {cv['score']['final_score']}% ({statut})")
                        if st.button(f"Supprimer CV '{cv['filename']}'", key=f"del_match_cv_{cv['_id']}"):
                            db.delete_cv(cv["_id"])
                            st.success(f"CV '{cv['filename']}' supprimé ✅")
                            st.experimental_rerun()

#PAGE 4 : DASHBOARD
elif page == "📊 Dashboard":
    st.header("Dashboard")
    st.metric("Annonces actives", len(db.get_annonces()))
    st.metric("CVs analysés", db.count_cvs())
