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

    date_trip = datetime.today().date()
    st.write(f"**Date du jour :** {date_trip.strftime('%A %d %B %Y')}") # Fixed date for today
    date_str = str(date_trip)
    
    # Check if a trip already exists for today
    existing_trip = database.get_trip_by_user_and_date(st.session_state.user['id'], date_str)
    
    if existing_trip:
        st.success(f"Vous avez déjà enregistré un trajet pour aujourd'hui ({existing_trip['total_km']} km).")
        st.info("Vous ne pouvez enregistrer qu'une seule série de trajets par jour.")
        if st.button("Effacer le trajet d'aujourd'hui", type="primary"):
            database.delete_trip(existing_trip['id'])
            st.warning("Le trajet a été supprimé.")
            import time
            time.sleep(1)
            st.rerun()
        return

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
    if st.button("Enregistrer l'itinéraire", type="primary"):
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
                    database.save_trip(st.session_state.user['id'], date_str, total_km, step_ids)
                    
                    st.success(f"Trajet enregistré avec succès ! Kilométrage total calculé : {total_km:.2f} km")
                    
                    # Reset
                    st.session_state.trip_steps = 1
                    import time
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Impossible de calculer le kilométrage complet.")
                    st.error(f"Détails de l'erreur : {str(e)}")
