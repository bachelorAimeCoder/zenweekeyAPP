import streamlit as st
import pandas as pd
import database
import auth
from datetime import datetime
from utils import pdf_export

def render_admin_dashboard():
    # ==== ALERTES JOURS MANQUANTS ====
    users = database.get_all_users()
    today = datetime.today().date()
    from datetime import date
    
    missing_alerts = []
    for u in users:
        if u['role'] == 'User':
            recorded = database.get_recorded_dates(u['id'])
            missing_for_u = []
            for i in range(1, today.day):
                d = date(today.year, today.month, i)
                if str(d) not in recorded:
                    missing_for_u.append(f"{i:02d}/{today.month:02d}")
            if missing_for_u:
                missing_alerts.append(f"**{u['username']}** : {', '.join(missing_for_u)}")
                
    if missing_alerts:
        col_space, col_alert = st.columns([8, 2])
        with col_alert:
            with st.popover(f"🚨 {len(missing_alerts)} Alerte(s)"):
                st.markdown("**Jours non déclarés ce mois-ci :**")
                for alert in missing_alerts:
                    st.markdown(alert)
    # ==================================

    tabs = st.tabs(["Suivi des salariés", "Gestion des Utilisateurs", "Gestion des Adresses"])
    
    with tabs[0]:
        render_trips_tracking()
        
    with tabs[1]:
        render_user_management()
        
    with tabs[2]:
        render_address_management()

def render_trips_tracking():
    st.header("Suivi des salariés")
    
    trips = database.get_all_trips()
    if not trips:
        st.info("Aucun trajet enregistré pour le moment.")
        return
        
    df = pd.DataFrame(trips, columns=['ID', 'Date', 'Total KM', 'Fille', 'Nom', 'Nb Étapes', 'Itinéraire', 'Statut', 'Heures'])
    df['Nom_Famille'] = df['Nom'].fillna('')
    df['Fille_Complet'] = df.apply(lambda r: f"{r['Fille']} {r['Nom_Famille']}".strip(), axis=1)
    
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
        
    # Capture accounting dataframe isolated from specific date/user filters
    accounting_df = filtered_df.copy()
    accounting_df['Fille'] = accounting_df['Fille_Complet']
    
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
            
    def format_hours_str(val):
        if pd.isna(val) or val is None: return "0h"
        h = int(val)
        m = int(round((val - h) * 60))
        if m == 0: return f"{h}h"
        return f"{h}h{m:02d}"
            
    # Application du Decimal Rounding Half-Up exact
    def format_km(val):
        from decimal import Decimal, ROUND_HALF_UP
        if pd.isna(val) or val is None: return "0.0"
        try:
            return f"{Decimal(str(val)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP):.1f}"
        except:
            return f"{val:.1f}"

    ui_df = display_df.copy()
    ui_df['Date'] = ui_df['Date'].apply(format_date_french)
    ui_df['Heures'] = ui_df['Heures'].apply(format_hours_str)
    ui_df['Total KM'] = ui_df['Total KM'].apply(format_km)

    st.dataframe(
        ui_df, 
        width='stretch', 
        hide_index=True
    )
    
    total_km = filtered_df['Total KM'].sum()
    total_hours = filtered_df['Heures'].sum()
    
    mc1, mc2 = st.columns(2)
    mc1.metric(label="Total Kilomètres (Filtre Actuel)", value=f"{format_km(total_km)} km")
    mc2.metric(label="Total Heures (Filtre Actuel)", value=format_hours_str(total_hours))
    
    st.markdown("---")
    st.subheader("Exporter en PDF")
    
    date_filter_str = str(selected_date) if selected_date else "Tous"
    
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        st.markdown("**Récépissé Complet (selon les filtres actuels)**")
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
            st.error(f"Erreur PDF : {str(e)}")
            
    with col_dl2:
        st.markdown("**Fiches Comptables (une fiche / salarié / mois)**")
        if accounting_df.empty:
            st.warning("Aucune donnée enregistrée.")
        else:
            try:
                zip_bytes = pdf_export.generate_accounting_zip(accounting_df, selected_month)
                st.download_button(
                    label=f"📦 Télécharger ZIP ({len(accounting_df['Fille'].unique())} Fiches)",
                    data=zip_bytes,
                    file_name=f"Fiches_Comptables_{selected_month}.zip",
                    mime="application/zip",
                    type="secondary"
                )
            except Exception as e:
                st.error(f"Erreur ZIP : {str(e)}")

def render_user_management():
    st.header("Gestion des utilisateurs")
    
    # Création d'utilisateur
    with st.expander("Créer un nouvel utilisateur"):
        with st.form("new_user_form"):
            new_username = st.text_input("Nom d'utilisateur (Prénom)")
            new_last_name = st.text_input("Nom de famille", help="Utile pour la fiche comptable")
            new_password = st.text_input("Mot de passe", type="password")
            new_role = st.selectbox("Rôle", ["User", "Admin"])
            submit_user = st.form_submit_button("Créer", type="primary")
            
            if submit_user:
                if new_username and new_password:
                    hashed_pw = auth.hash_password(new_password)
                    if database.create_user(new_username, hashed_pw, new_role, new_last_name):
                        st.success(f"Utilisateur {new_username} créé avec succès !")
                        st.rerun()
                    else:
                        st.error("Ce nom d'utilisateur existe déjà.")
                else:
                    st.warning("Veuillez remplir tous les champs obligatoires.")
                    
    # Liste et suppression des utilisateurs
    st.subheader("Liste des utilisateurs")
    users = database.get_all_users()
    for user in users:
        col1, col2, col3 = st.columns([3, 1, 1])
        # sqlite3.Row doesn't have .get(), so we check keys or access directly since last_name is in SELECT
        ln = user['last_name'] if user['last_name'] else ''
        full_name = f"{user['username']} {ln}".strip()
        col1.write(f"**{full_name}** ({user['role']})")
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
            options = [""] + df_addr.to_dict('records')
            addr_to_delete = st.selectbox(
                "Adresse à supprimer (par référence)", 
                options,
                format_func=lambda x: x['Référence'] if isinstance(x, dict) else str(x)
            )
            if st.button("Supprimer l'adresse"):
                if addr_to_delete:
                    database.delete_address(addr_to_delete['ID'])
                    st.success("Adresse supprimée.")
                    st.rerun()
