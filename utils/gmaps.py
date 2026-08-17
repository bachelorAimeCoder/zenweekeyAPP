import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

import requests

def get_distance_between_addresses(origin_str, destination_str):
    """
    Calcule la distance entre une origine et une destination
    en utilisant la nouvelle API Google Routes (computeRoutes).
    Retourne la distance en kilomètres.
    """
    if not API_KEY:
        return 0.0

    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "routes.distanceMeters",
    }
    
    payload = {
        "origin": {
            "address": origin_str
        },
        "destination": {
            "address": destination_str
        },
        "travelMode": "DRIVE"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            routes = data.get("routes", [])
            if routes:
                meters = routes[0].get("distanceMeters", 0)
                return meters / 1000.0
            else:
                raise Exception("Aucun itinéraire trouvé entre ces deux points.")
        else:
            try:
                error_data = response.json()
                msg = error_data.get('error', {}).get('message', 'Erreur inconnue')
            except:
                msg = response.text
            raise Exception(f"Erreur API Routes ({response.status_code}): {msg}")
            
    except Exception as e:
        print(f"Erreur API Google Routes: {e}")
        raise e
    
    return 0.0

def calculate_total_trip_distance(addresses_list):
    """
    Prend une liste d'adresses textuelles et calcule la distance totale
    du parcours en passant d'une adresse à l'autre.
    """
    total_km = 0.0
    if len(addresses_list) < 2:
        return total_km
        
    for i in range(len(addresses_list) - 1):
        origin = addresses_list[i]
        destination = addresses_list[i+1]
        dist = get_distance_between_addresses(origin, destination)
        total_km += dist
        
    return total_km
