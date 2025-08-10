import streamlit as st

def show_collapsible_badges(items, label="Compétences"):
    if items:
        with st.expander(f"{label} ({len(items)})"):
            st.markdown(
                f"""
                <div class="badges-container">
                {"".join(f'<span class="tag-badge">{item}</span>' for item in items)}
                </div>
                """, 
                unsafe_allow_html=True
            )

def add_manual_selection_button(cv_name):
    return st.button(f"Ajouter CV {cv_name} manuellement")
