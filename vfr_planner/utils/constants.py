"""
Constantes pour VFR Planner
"""

# Constantes de navigation
EARTH_RADIUS_KM = 6371.0
EARTH_RADIUS_NM = 3440.065  # Rayon terrestre en milles nautiques
NM_TO_KM = 1.852
KM_TO_NM = 1.0 / 1.852
NM_TO_FEET = 6076.12
FEET_TO_NM = 1.0 / 6076.12

# Constantes de temps
HOURS_TO_MINUTES = 60
MINUTES_TO_HOURS = 1.0 / 60
SECONDS_TO_MINUTES = 1.0 / 60
MINUTES_TO_SECONDS = 60

# Constantes de carburant
GALLONS_TO_LITERS = 3.78541
LITERS_TO_GALLONS = 1.0 / 3.78541
POUNDS_TO_KG = 0.453592
KG_TO_POUNDS = 1.0 / 0.453592

# Constantes météorologiques
STANDARD_PRESSURE_HPA = 1013.25
STANDARD_PRESSURE_INHG = 29.92
STANDARD_TEMPERATURE_C = 15.0
STANDARD_TEMPERATURE_F = 59.0
LAPSE_RATE_C_PER_FOOT = 0.00198  # Gradient thermique standard

# Conversions de vitesse
KN_TO_MPH = 1.15078
MPH_TO_KN = 1.0 / 1.15078
KN_TO_KMH = 1.852
KMH_TO_KN = 1.0 / 1.852
MS_TO_KN = 1.943844
KN_TO_MS = 1.0 / 1.943844

# Conversions d'angles
DEG_TO_RAD = 0.017453292519943295
RAD_TO_DEG = 57.29577951308232

# Limites VFR (conditions météo minimales)
VFR_MIN_VISIBILITY_KM = 5.0  # Visibilité minimale en km
VFR_MIN_VISIBILITY_SM = 3.0  # Visibilité minimale en statute miles
VFR_MIN_CEILING_FEET = 1000  # Plafond minimal en pieds
VFR_MIN_CLOUD_CLEARANCE_FEET = 500  # Distance minimale des nuages

# Constantes d'aérodromes
AIRPORT_TYPES = [
    'large_airport',
    'medium_airport',
    'small_airport',
    'heliport',
    'seaplane_base',
    'balloonport',
    'closed'
]

AIRPORT_TYPE_LABELS = {
    'large_airport': 'Grand aéroport',
    'medium_airport': 'Aéroport moyen',
    'small_airport': 'Petit aéroport',
    'heliport': 'Héliport',
    'seaplane_base': 'Base d\'hydravions',
    'balloonport': 'Aéroport de ballons',
    'closed': 'Fermé'
}

# Codes de pays prioritaires
PRIORITY_COUNTRIES = ['CA', 'US', 'FR', 'GB', 'DE', 'AU']

COUNTRY_NAMES = {
    'CA': 'Canada',
    'US': 'États-Unis',
    'FR': 'France',
    'GB': 'Royaume-Uni',
    'DE': 'Allemagne',
    'AU': 'Australie'
}

# Fuseaux horaires
COMMON_TIMEZONES = {
    'EST': 'America/New_York',
    'CST': 'America/Chicago',
    'MST': 'America/Denver',
    'PST': 'America/Los_Angeles',
    'AST': 'America/Halifax',
    'UTC': 'UTC',
    'GMT': 'GMT'
}

# Paramètres par défaut d'aéronefs
DEFAULT_AIRCRAFT_PARAMS = {
    'cruise_speed': 110,  # knots
    'fuel_burn': 7.5,     # GPH
    'fuel_capacity': 40,   # gallons
    'reserve_fuel': 45,    # minutes
    'climb_rate': 500,     # feet per minute
    'descent_rate': 500,   # feet per minute
    'service_ceiling': 12500  # feet
}

# Paramètres de vol par défaut
DEFAULT_FLIGHT_PARAMS = {
    'departure_time': '10:00',
    'cruise_altitude': 3500,  # feet
    'passengers': 1,
    'baggage_weight': 0,      # pounds
    'reserve_time': 45        # minutes
}

# URLs et API
DEFAULT_WEATHER_API = 'tomorrow.io'
WEATHER_API_ENDPOINTS = {
    'tomorrow.io': 'https://api.tomorrow.io/v4/weather/forecast',
    'openweather': 'https://api.openweathermap.org/data/2.5/weather'
}

# Formats de fichiers supportés
SUPPORTED_EXPORT_FORMATS = [
    '.xlsx',  # Excel
    '.pdf',   # PDF
    '.csv',   # CSV
    '.json',  # JSON
    '.kml',   # Google Earth
    '.gpx'    # GPS Exchange
]

SUPPORTED_IMPORT_FORMATS = [
    '.csv',   # CSV d'aéroports
    '.json',  # Projets VFR
    '.vfr',   # Projets VFR natifs
    '.xlsx'   # Excel
]

# Configuration de l'interface
GUI_DEFAULTS = {
    'window_width': 1200,
    'window_height': 800,
    'min_width': 1000,
    'min_height': 600,
    'font_family': 'Arial',
    'font_size': 10
}

# Messages d'erreur standardisés
ERROR_MESSAGES = {
    'no_waypoints': "Au moins 2 waypoints sont requis pour créer un itinéraire",
    'no_aircraft': "Veuillez configurer les paramètres de l'aéronef",
    'invalid_coordinates': "Coordonnées invalides",
    'api_key_missing': "Clé API météo manquante",
    'api_error': "Erreur lors de l'appel API météo",
    'file_not_found': "Fichier non trouvé",
    'invalid_format': "Format de fichier non supporté",
    'calculation_error': "Erreur lors des calculs de navigation"
}

# Codes météorologiques Tomorrow.io
WEATHER_CODES = {
    1000: 'Dégagé',
    1100: 'Généralement dégagé',
    1101: 'Partiellement nuageux',
    1102: 'Généralement nuageux',
    1001: 'Nuageux',
    2000: 'Brouillard',
    2100: 'Brouillard léger',
    4000: 'Bruine',
    4001: 'Pluie',
    4200: 'Pluie légère',
    4201: 'Pluie forte',
    5000: 'Neige',
    5001: 'Grêle',
    6000: 'Verglas',
    7000: 'Vent fort',
    8000: 'Orage'
}

# Seuils d'alerte météo
WEATHER_ALERTS = {
    'wind_speed_high': 25,      # knots
    'wind_speed_severe': 35,    # knots
    'visibility_low': 5,        # km
    'visibility_poor': 3,       # km
    'precipitation_light': 1,   # mm/h
    'precipitation_heavy': 5,   # mm/h
    'cloud_cover_high': 75,     # %
    'cloud_cover_overcast': 90  # %
}

# Couleurs pour l'interface et cartes
COLORS = {
    'departure': '#28a745',    # Vert
    'destination': '#dc3545',  # Rouge
    'waypoint': '#007bff',     # Bleu
    'route': '#ffc107',        # Jaune/Orange
    'alternate': '#6c757d',    # Gris
    'danger': '#dc3545',       # Rouge
    'warning': '#ffc107',      # Orange
    'success': '#28a745',      # Vert
    'info': '#17a2b8'          # Cyan
}

# Icônes pour la carte
MAP_ICONS = {
    'departure': 'play',
    'destination': 'stop',
    'waypoint': 'info-sign',
    'airport': 'plane',
    'alternate': 'question-sign'
}

# Extensions de fichiers
FILE_EXTENSIONS = {
    'project': '.vfr',
    'excel': '.xlsx',
    'pdf': '.pdf',
    'csv': '.csv',
    'json': '.json',
    'map': '.html'
}

# Formats de coordonnées
COORDINATE_FORMATS = {
    'decimal': 'Degrés décimaux (45.4582)',
    'dms': 'Degrés-minutes-secondes (45°27\'30")',
    'dm': 'Degrés-minutes (45°27.500\')'
}

# Unités disponibles
UNITS = {
    'distance': ['NM', 'km', 'mi'],
    'speed': ['kn', 'km/h', 'mph'],
    'altitude': ['ft', 'm'],
    'fuel': ['gal', 'L'],
    'weight': ['lbs', 'kg'],
    'temperature': ['°C', '°F']
}

# Validation des données
VALIDATION_LIMITS = {
    'latitude': (-90, 90),
    'longitude': (-180, 180),
    'altitude': (0, 60000),      # feet
    'speed': (0, 500),           # knots
    'fuel_capacity': (0, 1000),  # gallons
    'fuel_burn': (0, 100),       # GPH
    'weight': (0, 50000)         # pounds
}

# Configuration par défaut pour les calculs
CALCULATION_DEFAULTS = {
    'magnetic_variation': -15.0,  # degrés (Est du Canada)
    'standard_atmosphere': True,
    'earth_model': 'spherical',
    'wind_interpolation': 'linear',
    'fuel_reserve_percent': 10    # % de réserve supplémentaire
}

# Messages de statut
STATUS_MESSAGES = {
    'ready': "Prêt - Configurez votre vol",
    'calculating': "Calcul en cours...",
    'complete': "Calculs terminés",
    'error': "Erreur détectée",
    'saving': "Sauvegarde en cours...",
    'loading': "Chargement..."
}

# Configuration des exports
EXPORT_SETTINGS = {
    'excel': {
        'font_size': 10,
        'header_color': '4472C4',
        'border_style': 'thin'
    },
    'pdf': {
        'page_size': 'letter',
        'font_family': 'Helvetica',
        'font_size': 10,
        'margins': 0.5  # inches
    }
}