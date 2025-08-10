import streamlit as st

def display_offers(offers):
    for offer in offers:
        offer_id = str(offer['_id'])
        st.markdown(f"### Offre : {offer.get('title', 'Sans titre')} (ID: {offer_id})")
        cvs = offer.get('selected_cvs', [])
        for cv in cvs:
            st.write(f"- {cv['cv_name']} (score: {cv.get('score', 'N/A')})")
        st.markdown("---")
