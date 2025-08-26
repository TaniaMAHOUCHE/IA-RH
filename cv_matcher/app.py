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
tabs = ["Annonces", "Dépôt CV", "Matching", "Dashboard"]
page = st.sidebar.radio("Navigation", tabs)

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text.strip()

if page == "📋 Annonces":
    st.header("Gestion des annonces")
    titre = st.text_input("Titre du poste")
    service = st.text_input("Service")
    desc = st.text_area("Description (FR)")
    pdf_file = st.file_uploader("Ou importez un PDF pour l'annonce", type=["pdf"])
    
    if pdf_file:
        desc = read_pdf(pdf_file)
    
    if st.button("Créer annonce"):
        if not titre:
            st.warning("Le titre est obligatoire.")
        elif not desc:
            st.warning("Veuillez saisir une description ou importer un PDF.")
        else:
            # Vérification si l'annonce existe déjà
            existing = [a for a in db.get_annonces() if a["titre"].lower() == titre.lower()]
            if existing:
                st.warning("Une annonce avec ce titre existe déjà.")
            else:
                desc_en = translator.translate(desc)
                infos_annonce = extract_cv_info(desc_en)
                annonce_skills = infos_annonce.get("HSKILL", [])

                annonce_id = db.add_annonce(titre, service, desc, desc_en, annonce_skills)
                st.success(f"Annonce '{titre}' créée")

                with st.expander("Voir les informations extraites de l'annonce"):
                    st.json(infos_annonce)
elif page == "📄 Dépôt CV":
    st.header("Dépôt de CV")
    annonces = db.get_annonces()

    if not annonces:
        st.warning("Ajoutez d'abord une annonce.")
    else:
        annonce = st.selectbox(
            "Sélectionner une annonce", 
            annonces, 
            format_func=lambda x: x['titre']
        )

        annonce_skills = annonce.get("skills", [])

        auto_threshold = st.slider(
            "Seuil de sauvegarde automatique (%)",
            min_value=0, max_value=100,
            value=SCORE_THRESHOLD, step=1
        )

        cv_files = st.file_uploader(
            "Importer un ou plusieurs CV (PDF uniquement)", 
            type=["pdf"], accept_multiple_files=True
        )
        
        if st.button("Analyser"):
            if not cv_files:
                st.warning("Veuillez importer au moins un CV PDF.")
            else:
                for cv_file in cv_files:
                    cv_text = read_pdf(cv_file)
                    if not cv_text:
                        st.error(f"Le fichier {cv_file.name} est vide ou illisible.")
                        continue

                    # Vérifier si CV déjà enregistré pour cette annonce
                    existing_cvs = db.get_cvs_by_annonce(annonce["_id"])
                    if any(cv["filename"].lower() == cv_file.name.lower() for cv in existing_cvs):
                        st.warning(f"Le CV '{cv_file.name}' a déjà été enregistré pour cette annonce.")
                        continue

                    cv_en = translator.translate(cv_text)
                    infos_cv = extract_cv_info(cv_en)
                    cv_skills = infos_cv.get("HSKILL", [])

                    scores = matcher.compute_score(
                        annonce["description_en"],
                        cv_en,
                        required_skills=annonce_skills,
                        extracted_skills=cv_skills
                    )

                    auto = scores["final_score"] >= auto_threshold
                    st.write(f"**{cv_file.name}** - Score final: {scores['final_score']}%")

                    if auto:
                        db.add_cv(
                            annonce["_id"], cv_file.name, cv_text, cv_en, infos_cv, scores, True
                        )
                        st.success(f"✅ CV '{cv_file.name}' enregistré automatiquement")
                    else:
                        if st.button(f"Sauvegarder manuellement {cv_file.name}"):
                            db.add_cv(
                                annonce["_id"], cv_file.name, cv_text, cv_en, infos_cv, scores, False
                            )
                            st.success(f"CV '{cv_file.name}' sauvegardé manuellement")
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
            service = annonce.get("service", "")
            with st.expander(f"{annonce['titre']} - {service}"):

                st.subheader("Description de l'annonce")
                st.write(annonce.get("description_fr", ""))

                if st.button(f"Supprimer annonce '{annonce['titre']}'", key=f"del_annonce_{annonce['_id']}"):
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

                        if st.button(f"Supprimer CV '{cv['filename']}'", key=f"del_cv_{cv['_id']}"):
                            db.delete_cv(cv["_id"])
                            st.success(f"CV '{cv['filename']}' supprimé ✅")
                            st.experimental_rerun()
elif page == "📊 Dashboard":
    st.header("Dashboard")
    st.metric("Annonces actives", len(db.get_annonces()))
    st.metric("CVs analysés", db.count_cvs())
