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
        # Check status for non-work days
        try:
            statut = existing_trip['status']
        except:
            statut = "Travail"
            
        if statut == "Travail":
            st.success(f"Vous avez déjà enregistré une journée de travail pour cette date ({existing_trip['total_km']:.1f} km).")
        else:
            st.success(f"Vous avez déjà déclaré cette date comme étant : **{statut}**.")
            
        st.info("Vous ne pouvez enregistrer qu'une seule activité par jour.")
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
        def format_hours_str(val):
            h = int(val)
            m = int(round((val - h) * 60))
            if m == 0: return f"{h}h"
            return f"{h}h{m:02d}"
            
        hours_options = [i / 12.0 for i in range(0, 24 * 12 + 1)]
        hours_worked = st.selectbox(
            "Nombre d'heures travaillées", 
            options=hours_options, 
            format_func=format_hours_str, 
            index=0
        )
        st.markdown("<p style='color: #e06666; font-size: 0.85em; margin-top: -10px; margin-bottom: 20px;'><i>* Pour rappel, une pause de 20 minutes est obligatoire pour six heures de travail consécutives.</i></p>", unsafe_allow_html=True)
        
        st.subheader("Itinéraire")
        st.info("🚗 **Note:** Pour tenir compte des temps de stationnement et d'accès, un forfait automatique de **300 mètres (0.3 km) est ajouté au total pour chaque étape** renseignée.")
        
        # Dynamically determine the number of step fields to show
        # Streamlit saves selectbox values in st.session_state based on their keys
        num_fields = 1
        for i in range(25):
            key = f"step_{i}"
            if key in st.session_state and st.session_state[key] is not None:
                num_fields = i + 2
                
        steps = []
        for i in range(num_fields):
            label = f"Étape {i+1}"
            step_selection = st.selectbox(
                label, 
                addr_options, 
                key=f"step_{i}", 
                index=None, 
                placeholder="Sélectionnez une adresse..."
            )
            if step_selection is not None:
                steps.append(step_selection)
            
        st.markdown("---")
        if st.button("Enregistrer la journée", type="primary"):
            if len(steps) < 2:
                st.warning("Veuillez saisir au moins deux étapes (un point de départ et une destination).")
            else:
                with st.spinner("Calcul des distances..."):
                    # Préparer la liste des adresses textuelles pour Google Maps
                    full_addresses = [f"{addr_mapping[s]['address']}, {addr_mapping[s]['city']}, France" for s in steps]
                    
                    try:
                        total_km_raw = gmaps.calculate_total_trip_distance(full_addresses)
                        
                        # Bonus stationnement / accès : 300m par étape
                        total_km_raw += len(steps) * 0.3
                        
                        from decimal import Decimal, ROUND_HALF_UP
                        try:
                            total_km = float(Decimal(str(total_km_raw)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))
                        except:
                            total_km = float(total_km_raw)
                        
                        # Sauvegarder en BDD
                        step_ids = [addr_mapping[s]['id'] for s in steps]
                        database.save_trip(st.session_state.user['id'], date_str, total_km, step_ids, status=day_status, hours=hours_worked)
                        
                        st.success(f"Journée enregistrée avec succès ! Kilométrage total calculé : {total_km:.1f} km")
                        
                        # Clean up dynamic keys
                        for key in list(st.session_state.keys()):
                            if key.startswith("step_"):
                                del st.session_state[key]
                                
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
