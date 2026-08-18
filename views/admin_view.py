import streamlit as st
import pandas as pd
import database
import auth
from datetime import datetime

def render_admin_dashboard():
    tabs = st.tabs(["Suivi des Trajets", "Gestion des Utilisateurs", "Gestion des Adresses"])
    
    with tabs[0]:
        render_trips_tracking()
        
    with tabs[1]:
        render_user_management()
        
    with tabs[2]:
        render_address_management()

def render_trips_tracking():
    st.header("Suivi des trajets")
    
    trips = database.get_all_trips()
    if not trips:
        st.info("Aucun trajet enregistré pour le moment.")
        return
        
    df = pd.DataFrame(trips, columns=['ID', 'Date', 'Total KM', 'Fille', 'Nb Étapes', 'Itinéraire', 'Statut', 'Heures'])
    # Convert 'Date' column to datetime where possible for filtering
    df['DateObj'] = pd.to_datetime(df['Date'], errors='coerce')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        # Get unique users
        users = ["Tous"] + list(df['Fille'].unique())
        selected_user = st.selectbox("Filtrer par fille", users)
    
    with col2:
        # Extract unique months (YYYY-MM)
        months = ["Tous"] + list(df['DateObj'].dt.strftime('%Y-%m').dropna().unique())
        selected_month = st.selectbox("Filtrer par mois", months)
        
    with col3:
        selected_date = st.date_input("Ou par jour précis", value=None)
        
    # Apply filters
    filtered_df = df.copy()
    if selected_user != "Tous":
        filtered_df = filtered_df[filtered_df['Fille'] == selected_user]
    if selected_month != "Tous":
        filtered_df = filtered_df[filtered_df['DateObj'].dt.strftime('%Y-%m') == selected_month]
    if selected_date:
        filtered_df = filtered_df[filtered_df['DateObj'].dt.date == selected_date]
        
    # Formatage de la date en français pour l'affichage
    display_df = filtered_df[['Date', 'Total KM', 'Fille', 'Statut', 'Heures', 'Nb Étapes', 'Itinéraire']].copy()
    months = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    
    def format_date_french(date_str):
        try:
            dt = pd.to_datetime(date_str)
            return f"{dt.day} {months[dt.month - 1]} {dt.year}"
        except:
            return date_str
            
    display_df['Date'] = display_df['Date'].apply(format_date_french)

    st.dataframe(
        display_df, 
        width='stretch', 
        hide_index=True
    )
    
    total_km = filtered_df['Total KM'].sum()
    total_hours = filtered_df['Heures'].sum()
    
    mc1, mc2 = st.columns(2)
    mc1.metric(label="Total Kilomètres (Filtre Actuel)", value=f"{total_km:.2f} km")
    mc2.metric(label="Total Heures (Filtre Actuel)", value=f"{total_hours:.2f} h")
    
    st.markdown("---")
    st.subheader("Exporter en PDF")
    
    date_filter_str = str(selected_date) if selected_date else "Tous"
    try:
        pdf_bytes = pdf_export.generate_pdf(display_df, total_km, total_hours, selected_user, selected_month, date_filter_str)
        st.download_button(
            label="Télécharger le rapport PDF",
            data=pdf_bytes,
            file_name=f"rapport_conciergerie_{datetime.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            type="primary"
        )
    except Exception as e:
        st.error(f"Impossible de générer le PDF : {str(e)}")

def render_user_management():
    st.header("Gestion des utilisateurs")
    
    # Création d'utilisateur
    with st.expander("Créer un nouvel utilisateur"):
        with st.form("new_user_form"):
            new_username = st.text_input("Nom d'utilisateur")
            new_password = st.text_input("Mot de passe", type="password")
            new_role = st.selectbox("Rôle", ["User", "Admin"])
            submit_user = st.form_submit_button("Créer", type="primary")
            
            if submit_user:
                if new_username and new_password:
                    hashed_pw = auth.hash_password(new_password)
                    if database.create_user(new_username, hashed_pw, new_role):
                        st.success(f"Utilisateur {new_username} créé avec succès !")
                        st.rerun()
                    else:
                        st.error("Ce nom d'utilisateur existe déjà.")
                else:
                    st.warning("Veuillez remplir tous les champs.")

    # Liste et suppression des utilisateurs
    st.subheader("Liste des utilisateurs")
    users = database.get_all_users()
    for user in users:
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"**{user['username']}** ({user['role']})")
        if user['username'] != st.session_state.user['username']: # Ne pas se supprimer soi-même
            if col2.button("Supprimer", key=f"del_user_{user['id']}"):
                database.delete_user(user['id'])
                st.success("Utilisateur supprimé.")
                st.rerun()

def render_address_management():
    st.header("Gestion des adresses")
    
    with st.expander("Ajouter une adresse"):
        with st.form("new_address_form"):
            ref = st.text_input("Référence (ex: Local, Nom client)")
            city = st.text_input("Ville")
            address = st.text_input("Adresse complète")
            submit_addr = st.form_submit_button("Ajouter", type="primary")
            
            if submit_addr:
                if ref and city and address:
                    database.create_address(ref, city, address)
                    st.success("Adresse ajoutée !")
                    st.rerun()
                else:
                    st.warning("Veuillez remplir tous les champs.")
                    
    st.subheader("Liste des adresses")
    addresses = database.get_all_addresses()
    if addresses:
        df_addr = pd.DataFrame(addresses, columns=['ID', 'Référence', 'Ville', 'Adresse'])
        st.dataframe(
            df_addr[['Référence', 'Ville', 'Adresse']], 
            width='stretch', 
            hide_index=True
        )
        
        # Option pour supprimer
        del_col1, del_col2 = st.columns([1, 2])
        with del_col1:
            addr_to_delete = st.selectbox("Adresse à supprimer (par ID)", [""] + list(df_addr['ID']))
            if st.button("Supprimer l'adresse"):
                if addr_to_delete:
                    database.delete_address(addr_to_delete)
                    st.success("Adresse supprimée.")
                    st.rerun()
