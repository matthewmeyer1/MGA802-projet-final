import pandas as pd
from geopy.distance import geodesic


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
    {"Aerodrome": "CEF4", "Latitude": 51.2639, "Longitude": -113.9344},
    {"Aerodrome": "CAM4", "Latitude": 52.3458, "Longitude": -114.6672},
    {"Aerodrome": "CYMM", "Latitude": 51.2539, "Longitude": -113.6228},
    {"Aerodrome": "CEP3", "Latitude": 54.0970, "Longitude": -114.4389},
    {"Aerodrome": "CYBA", "Latitude": 51.2, "Longitude": -115.5333},
])

print(df_aerodromes)
# ------------------------
# Recherche d’aéroports alternatifs dans un rayon donné (ex: 50 NM) autour du trajet
# ------------------------
RAYON_NM = 50  # Rayon de recherche en nautiques
alternatifs = []

for wp in trajet_waypoints:
    for _, row in df_aerodromes.iterrows():
        print(row["Aerodrome"])
        dist = geodesic((wp["lat"], wp["lon"]), (row["Latitude"], row["Longitude"])).nm
        if dist <= RAYON_NM:
            print(row["Aerodrome"])
            alternatifs.append({
                "Waypoint": wp["name"],
                "Aérodrome": row["Aerodrome"],
                "Lat": row["Latitude"],
                "Lon": row["Longitude"],
                "Distance_NM": round(dist, 2)
            })

# Résultat final : tableau des aéroports proches de chaque segment
df_alternatifs = pd.DataFrame(alternatifs)
print(df_alternatifs)
