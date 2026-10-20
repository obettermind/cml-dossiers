import os
import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="Rech-DOS", layout="centered")

st.markdown(
    """
    <div style="background-color:#FCD5B5; padding:10px; border-radius:5px; text-align:center; margin-bottom:20px;">
        <h2 style="color:#000000; margin:0;">Rech-DOS</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

def get_secret(nom):
    # Hugging Face fournit les secrets en variables d'environnement,
    # en local ils viennent de .streamlit/secrets.toml
    if nom in os.environ:
        return os.environ[nom]
    return st.secrets[nom]

# --- Mot de passe ---
if not st.session_state.get("ok"):
    mdp = st.text_input("Mot de passe :", type="password")
    if st.button("Entrer"):
        if mdp == get_secret("APP_PASSWORD"):
            st.session_state["ok"] = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")
    st.stop()

# --- Connexion Supabase ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(get_secret("SUPABASE_URL"), get_secret("SUPABASE_SERVICE_KEY"))

supabase = init_connection()

# --- Formulaire de recherche ---
st.subheader("🔍 Critères de recherche")

with st.form("recherche"):
    search_ref = st.text_input("N° REF :")
    search_tpi = st.text_input("Num Jurid-tpi :")
    search_cie = st.text_input("Nom Compagnie :")
    search_assure = st.text_input("ASSURE :")
    search_date = st.text_input("DATE-ACCID (AAAA-MM-JJ) :")
    search_ca = st.text_input("CA :")
    lancer = st.form_submit_button("Rechercher", use_container_width=True)

if lancer:
    query = supabase.table("dossiers").select("*").limit(200)
    filtres = False

    if search_ref.strip():
        query = query.eq("n_ref", search_ref.strip()); filtres = True
    if search_tpi.strip():
        query = query.ilike("tpi", f"%{search_tpi.strip()}%"); filtres = True
    if search_cie.strip():
        query = query.ilike("nom_compagnie", f"%{search_cie.strip()}%"); filtres = True
    if search_assure.strip():
        query = query.ilike("assure", f"%{search_assure.strip()}%"); filtres = True
    if search_date.strip():
        query = query.eq("date_accid", search_date.strip()); filtres = True
    if search_ca.strip():
        query = query.eq("ca", search_ca.strip()); filtres = True

    st.markdown("---")
    if not filtres:
        st.warning("Remplis au moins un critère.")
    else:
        try:
            data = query.execute().data
            if not data:
                st.warning("❌ Aucun dossier ne correspond à ces critères.")
            else:
                df = pd.DataFrame(data).rename(columns={
                    "n_ref": "N° REF", "nom_compagnie": "Nom Compagnie",
                    "ville": "Ville", "date_accid": "Date accident",
                    "assure": "Assuré", "tpi": "TPI", "ca": "CA",
                })
                if len(df) == 1:
                    st.success("🎯 Dossier unique trouvé !")
                    st.table(df.T)
                else:
                    st.info(f"📊 {len(df)} dossier(s) trouvé(s) :")
                    st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Erreur : {e}")