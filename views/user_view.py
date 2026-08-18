import streamlit as st
from datetime import datetime
import database
from utils import gmaps

def render_user_dashboard():
    st.header("Saisie des trajets du jour")
    
    addresses = database.get_all_addresses()
    if not addresses:
        st.error("Aucune adresse n'est configurée dans la base de données. Contactez l'administrateur.")
        return
        
    # Formatting addresses for selection
    addr_options = [f"{a['reference']} - {a['address']} ({a['city']})" for a in addresses]
    addr_mapping = {f"{a['reference']} - {a['address']} ({a['city']})": a for a in addresses}

    # Calcul des jours manquants pour le mois en cours (jusqu'à la veille)
    today = datetime.today().date()
    recorded_dates = database.get_recorded_dates(st.session_state.user['id'])
    
    missing_days = []
    from datetime import timedelta, date
    for i in range(1, today.day):
        d = date(today.year, today.month, i)
        if str(d) not in recorded_dates:
            missing_days.append(f"{i:02d}/{today.month:02d}")
            
    if missing_days:
        st.error(f"⚠️ Certains jours n'ont pas été déclarés ! ({', '.join(missing_days)})")

    date_trip = st.date_input("Date du trajet", value=today)
    date_str = str(date_trip)
    
    # Check if a trip already exists for the selected date
    existing_trip = database.get_trip_by_user_and_date(st.session_state.user['id'], date_str)
    
    if existing_trip:
        st.success(f"Vous avez déjà enregistré un trajet pour cette date ({existing_trip['total_km']} km).")
        st.info("Vous ne pouvez enregistrer qu'une seule série de trajets par jour.")
        if st.button("Effacer le trajet de ce jour", type="primary"):
            database.delete_trip(existing_trip['id'])
            st.warning("Le trajet a été supprimé.")
            import time
            time.sleep(1)
            st.rerun()
        return

    # Statut de la journée
    status_options = [
        "Travail", 
        "Repos", 
        "Congé payé", 
        "Maladie avec justificatif", 
        "Absence sans justificatif"
    ]
    day_status = st.selectbox("Statut de la journée", status_options)

    if day_status == "Travail":
        hours_worked = st.number_input("Nombre d'heures travaillées", min_value=0.0, max_value=24.0, step=0.5, value=0.0)
        st.markdown("<p style='color: #e06666; font-size: 0.85em; margin-top: -10px; margin-bottom: 20px;'><i>* Pour rappel, une pause de 20 minutes est obligatoire pour six heures de travail consécutives.</i></p>", unsafe_allow_html=True)
        
        # Initialize steps in session state
        if "trip_steps" not in st.session_state:
            st.session_state.trip_steps = 1
        
        steps = []
        
        st.subheader("Itinéraire")
        for i in range(st.session_state.trip_steps):
            label = "Départ" if i == 0 else f"Étape {i}"
            step_selection = st.selectbox(
                label, 
                addr_options, 
                key=f"step_{i}", 
                index=None, 
                placeholder="Sélectionnez une adresse..."
            )
            steps.append(step_selection)
            
        if st.button("Ajouter une étape"):
            st.session_state.trip_steps += 1
            st.rerun()
            
        st.markdown("---")
        if st.button("Enregistrer la journée", type="primary"):
            if None in steps:
                st.warning("Erreur : Certaines étapes sont vides. Veuillez sélectionner une adresse pour chaque étape.")
            elif len(steps) < 2:
                st.warning("Veuillez saisir au moins un point de départ et une destination.")
            else:
                with st.spinner("Calcul des distances..."):
                    # Préparer la liste des adresses textuelles pour Google Maps
                    full_addresses = [f"{addr_mapping[s]['address']}, {addr_mapping[s]['city']}, France" for s in steps]
                    
                    try:
                        total_km = gmaps.calculate_total_trip_distance(full_addresses)
                        
                        # Sauvegarder en BDD
                        step_ids = [addr_mapping[s]['id'] for s in steps]
                        database.save_trip(st.session_state.user['id'], date_str, total_km, step_ids, status=day_status, hours=hours_worked)
                        
                        st.success(f"Journée enregistrée avec succès ! Kilométrage total calculé : {total_km:.2f} km")
                        
                        # Reset
                        st.session_state.trip_steps = 1
                        import time
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Impossible de calculer le kilométrage complet.")
                        st.error(f"Détails de l'erreur : {str(e)}")
    else:
        # Non-working day
        st.info(f"Vous avez sélectionné une journée de type : **{day_status}**.")
        if st.button("Enregistrer la journée", type="primary"):
            database.save_trip(st.session_state.user['id'], date_str, 0.0, [], status=day_status, hours=0.0)
            st.success(f"Journée de {day_status} enregistrée avec succès.")
            import time
            time.sleep(2)
            st.rerun()
