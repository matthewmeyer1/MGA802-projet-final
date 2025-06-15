import math

mport math
import pandas as pd

# ------------------------
# Fonction utilitaire : calcul distance Haversine entre deux points (en nautiques)
# ------------------------
def haversine(lat1, lon1, lat2, lon2):
    """
    Calcule la distance entre deux points (lat, lon) en nautiques.
    Entrée en degrés décimaux.
    """
    R = 6371.0  # Rayon terrestre en km
    deg2rad = math.pi / 180
    dlat = (lat2 - lat1) * deg2rad
    dlon = (lon2 - lon1) * deg2rad
    a = math.sin(dlat/2)**2 + math.cos(lat1*deg2rad) * math.cos(lat2*deg2rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_km = R * c
    return distance_km / 1.852  # conversion km -> nautiques

# ------------------------
# Exemple : liste des waypoints du trajet prévu (données utilisateur ou calculées)
# ------------------------
trajet_waypoints = [
    {"name": "WP1", "lat": 50.6333, "lon": -113.9333},  # exemple : EBLG
    {"name": "WP2", "lat": 50.6833, "lon": -113.7833},  # exemple : EBLG-ECHO
    {"name": "WP3", "lat": 50.4833, "lon": -113.9167},  # exemple : EBSP
]

# ------------------------
# Exemple : base de données d'aérodromes extraits du CFS (données internes)
# ------------------------
# Remplace ceci par l'import réel des données extraites depuis ton script précédent
df_aerodromes = pd.DataFrame([
    {"Aérodrome": "CEF4", "Latitude": 51.2639, "Longitude": -113.9344},
    {"Aérodrome": "CAM4", "Latitude": 52.3458, "Longitude": -114.6672},
    {"Aérodrome": "CYMM", "Latitude": 56.6539, "Longitude": -111.2228},
    {"Aérodrome": "CEP3", "Latitude": 54.0970, "Longitude": -114.4389},
    {"Aérodrome": "CYBA", "Latitude": 51.2, "Longitude": -115.5333},
])

# ------------------------
# Recherche d’aéroports alternatifs dans un rayon donné (ex: 50 NM) autour du trajet
# ------------------------
RAYON_NM = 50  # Rayon de recherche en nautiques
alternatifs = []

for wp in trajet_waypoints:
    for _, row in df_aerodromes.iterrows():
        dist = haversine(wp["lat"], wp["lon"], row["Latitude"], row["Longitude"])
        if dist <= RAYON_NM:
            alternatifs.append({
                "Waypoint": wp["name"],
                "Aérodrome": row["Aérodrome"],
                "Lat": row["Latitude"],
                "Lon": row["Longitude"],
                "Distance_NM": round(dist, 2)
            })

# Résultat final : tableau des aéroports proches de chaque segment
df_alternatifs = pd.DataFrame(alternatifs)
from ace_tools import display_dataframe_to_user
display_dataframe_to_user("Aéroports alternatifs proches du trajet", df_alternatifs)
