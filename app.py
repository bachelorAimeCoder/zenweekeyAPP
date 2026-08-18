import streamlit as st
import database
import auth
from views.admin_view import render_admin_dashboard
from views.user_view import render_user_dashboard

st.set_page_config(page_title="App de Conciergerie", page_icon="🧹", layout="wide")

# Injection de CSS pour forcer le jaune sur le bandeau du haut
st.markdown("""
    <style>
        header[data-testid="stHeader"] {
            background-color: #D5B646;
            border-bottom: 2px solid #1F1F1F;
        }
        /* Fond jaune clair pour toutes les cases de saisie (texte, date, select) */
        [data-baseweb="select"] > div,
        [data-baseweb="select"] > div > div,
        [data-baseweb="base-input"],
        [data-baseweb="base-input"] > input,
        [data-baseweb="input"],
        [data-baseweb="input"] > input {
            background-color: #fcf9e8 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Initialisation de la base de données
def init():
    database.init_db()

def render_login():
    st.title("Connexion")
    
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        if st.form_submit_button("Se connecter", type="primary"):
            user = auth.authenticate_user(username, password)
            if user:
                st.session_state.user = user
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error("Identifiants incorrects.")

def main():
    if "db_initialized" not in st.session_state:
        init()
        st.session_state.db_initialized = True

    if "user" not in st.session_state:
        render_login()
    else:
        # Main routing based on role
        if st.session_state.user['role'] == 'Admin':
            col1, col2 = st.columns([8, 2])
            with col1:
                st.title("Tableau de bord Administrateur")
            with col2:
                st.markdown(f"👤 **{st.session_state.user['username']}** ({st.session_state.user['role']})")
                if st.button("Se déconnecter", type="primary", use_container_width=True):
                    del st.session_state.user
                    st.rerun()
            render_admin_dashboard()
        else:
            col1, col2 = st.columns([8, 2])
            with col1:
                st.title(f"Bienvenue, {st.session_state.user['username']}")
            with col2:
                st.markdown(f"👤 **{st.session_state.user['username']}** ({st.session_state.user['role']})")
                if st.button("Se déconnecter", use_container_width=True):
                    del st.session_state.user
                    st.rerun()
            render_user_dashboard()

if __name__ == "__main__":
    main()
