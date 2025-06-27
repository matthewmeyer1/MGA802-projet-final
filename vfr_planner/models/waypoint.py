"""
Ce module contient la classe Waypoint.
Cette classe contient et calcule les données pour les waypoints.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import math


@dataclass
class Waypoint:
    """
    Modèle de données pour un point de navigation (waypoint).

    :param lat: Latitude en degrés décimaux
    :type lat: float
    :param lon: Longitude en degrés décimaux
    :type lon: float
    :param name: Nom/identifiant du waypoint, par défaut ""
    :type name: str
    :param alt: Altitude en pieds (optionnel), par défaut 0.0
    :type alt: float
    :param waypoint_type: Type du waypoint ('airport', 'custom', 'fix', etc.), par défaut "custom"
    :type waypoint_type: str
    :param info: Informations supplémentaires, par défaut None
    :type info: Optional[Dict[str, Any]]
    """

    lat: float  # Latitude en degrés décimaux
    lon: float  # Longitude en degrés décimaux
    name: str = ""  # Nom/identifiant du waypoint
    alt: float = 0.0  # Altitude en pieds (optionnel)
    waypoint_type: str = "custom"  # Type: 'airport', 'custom', 'fix', etc.
    info: Optional[Dict[str, Any]] = None  # Informations supplémentaires

    def __post_init__(self):
        """
        Validation après initialisation.

        :raises ValueError: Si latitude ou longitude sont hors limites valides.
        """
        if not (-90 <= self.lat <= 90):
            raise ValueError(f"Latitude invalide: {self.lat}. Doit être entre -90 et 90.")
        if not (-180 <= self.lon <= 180):
            raise ValueError(f"Longitude invalide: {self.lon}. Doit être entre -180 et 180.")

        # Initialiser info si None
        if self.info is None:
            self.info = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Waypoint':
        """
        Créer un Waypoint depuis un dictionnaire.

        :param data: Dictionnaire contenant les données du waypoint
        :type data: Dict[str, Any]
        :return: Instance Waypoint
        :rtype: Waypoint
        """
        return cls(
            lat=float(data['lat']),
            lon=float(data['lon']),
            name=data.get('name', ''),
            alt=float(data.get('alt', 0)),
            waypoint_type=data.get('type', 'custom'),
            info=data.get('info', {})
        )

    @classmethod
    def from_airport(cls, airport_data: Dict[str, Any]) -> 'Waypoint':
        """
        Créer un Waypoint depuis des données d'aéroport.

        :param airport_data: Données d'aéroport (lat, lon, icao, elevation, etc.)
        :type airport_data: Dict[str, Any]
        :return: Instance Waypoint de type 'airport'
        :rtype: Waypoint
        """
        return cls(
            lat=airport_data['lat'],
            lon=airport_data['lon'],
            name=airport_data.get('icao', airport_data.get('ident', 'UNKNOWN')),
            alt=airport_data.get('elevation', 0),
            waypoint_type='airport',
            info=airport_data
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertir le waypoint en dictionnaire.

        :return: Dictionnaire représentant le waypoint
        :rtype: Dict[str, Any]
        """
        return {
            'name': self.name,
            'lat': self.lat,
            'lon': self.lon,
            'alt': self.alt,
            'type': self.waypoint_type,
            'info': self.info
        }

    def distance_to(self, other: 'Waypoint') -> float:
        """
        Calculer la distance vers un autre waypoint (formule haversine).

        :param other: Autre waypoint cible
        :type other: Waypoint
        :return: Distance en milles nautiques
        :rtype: float
        """
        return self._haversine_distance(self.lat, self.lon, other.lat, other.lon)

    def bearing_to(self, other: 'Waypoint') -> float:
        """
        Calculer le cap (bearing) vers un autre waypoint.

        :param other: Autre waypoint cible
        :type other: Waypoint
        :return: Cap en degrés (0-360)
        :rtype: float
        """
        lat1_rad = math.radians(self.lat)
        lat2_rad = math.radians(other.lat)
        dlon_rad = math.radians(other.lon - self.lon)

        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))

        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)

        return (bearing_deg + 360) % 360

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculer la distance haversine entre deux points géographiques.

        :param lat1: Latitude du premier point en degrés décimaux
        :type lat1: float
        :param lon1: Longitude du premier point en degrés décimaux
        :type lon1: float
        :param lat2: Latitude du second point en degrés décimaux
        :type lat2: float
        :param lon2: Longitude du second point en degrés décimaux
        :type lon2: float
        :return: Distance entre les deux points en milles nautiques
        :rtype: float
        """
        R = 6371.0  # Rayon terrestre en km

        # Conversion en radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Différences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Formule haversine
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance_km = R * c
        return distance_km / 1.852  # Conversion km -> milles nautiques

    def get_display_name(self) -> str:
        """
        Obtenir le nom d'affichage du waypoint.

        :return: Nom ou coordonnées formatées
        :rtype: str
        """
        if self.name:
            return self.name
        else:
            return f"WP({self.lat:.4f}, {self.lon:.4f})"

    def get_coordinates_string(self, format_type: str = "decimal") -> str:
        """
        Obtenir les coordonnées sous forme de chaîne formatée.

        :param format_type: Format de sortie ('decimal', 'dms', 'dm')
        :type format_type: str
        :return: Chaîne formatée des coordonnées
        :rtype: str
        """
        if format_type == "decimal":
            return f"{self.lat:.6f}°N, {abs(self.lon):.6f}°W"
        elif format_type == "dms":
            return f"{self._to_dms(self.lat, 'lat')}, {self._to_dms(self.lon, 'lon')}"
        elif format_type == "dm":
            return f"{self._to_dm(self.lat, 'lat')}, {self._to_dm(self.lon, 'lon')}"
        else:
            return f"{self.lat:.6f}, {self.lon:.6f}"

    def _to_dms(self, coord: float, coord_type: str) -> str:
        """
        Convertir une coordonnée en degrés-minutes-secondes (DMS).

        :param coord: Coordonnée en degrés décimaux
        :type coord: float
        :param coord_type: 'lat' ou 'lon' pour déterminer l'hémisphère
        :type coord_type: str
        :return: Coordonnée en format DMS
        :rtype: str
        """
        is_positive = coord >= 0
        coord = abs(coord)

        degrees = int(coord)
        minutes_float = (coord - degrees) * 60
        minutes = int(minutes_float)
        seconds = (minutes_float - minutes) * 60

        if coord_type == 'lat':
            hemisphere = 'N' if is_positive else 'S'
        else:  # lon
            hemisphere = 'E' if is_positive else 'W'

        return f"{degrees:02d}°{minutes:02d}'{seconds:04.1f}\"{hemisphere}"

    def _to_dm(self, coord: float, coord_type: str) -> str:
        """
        Convertir une coordonnée en degrés-minutes (DM).

        :param coord: Coordonnée en degrés décimaux
        :type coord: float
        :param coord_type: 'lat' ou 'lon' pour déterminer l'hémisphère
        :type coord_type: str
        :return: Coordonnée en format DM
        :rtype: str
        """
        is_positive = coord >= 0
        coord = abs(coord)

        degrees = int(coord)
        minutes = (coord - degrees) * 60

        if coord_type == 'lat':
            hemisphere = 'N' if is_positive else 'S'
        else:  # lon
            hemisphere = 'E' if is_positive else 'W'

        return f"{degrees:02d}°{minutes:06.3f}'{hemisphere}"

    def is_airport(self) -> bool:
        """
        Vérifier si le waypoint est un aéroport.

        :return: True si c'est un aéroport, False sinon
        :rtype: bool
        """
        return self.waypoint_type == 'airport'

    def get_airport_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtenir les informations d'aéroport si disponibles.

        :return: Dictionnaire d'informations d'aéroport ou None
        :rtype: Optional[Dict[str, Any]]
        """
        if self.is_airport() and self.info:
            return self.info
        return None

    def __str__(self) -> str:
        """
        Représentation en chaîne.

        :return: Nom d'affichage et coordonnées
        :rtype: str
        """
        return f"{self.get_display_name()} ({self.lat:.4f}, {self.lon:.4f})"

    def __repr__(self) -> str:
        """
        Représentation officielle.

        :return: Chaîne descriptive du waypoint
        :rtype: str
        """
        return f"Waypoint(name='{self.name}', lat={self.lat}, lon={self.lon})"

    def __eq__(self, other) -> bool:
        """
        Comparaison d'égalité basée sur la proximité des coordonnées.

        :param other: Objet à comparer
        :type other: Any
        :return: True si égaux (tolérance 0.0001°), False sinon
        :rtype: bool
        """
        if not isinstance(other, Waypoint):
            return False

        lat_diff = abs(self.lat - other.lat)
        lon_diff = abs(self.lon - other.lon)

        return lat_diff < 0.0001 and lon_diff < 0.0001

    def __hash__(self) -> int:
        """
        Hash basé sur les coordonnées arrondies.

        :return: Valeur de hash
        :rtype: int
        """
        return hash((round(self.lat, 4), round(self.lon, 4)))


# Fonctions utilitaires pour créer des waypoints

def create_waypoint_from_coordinates(lat: float, lon: float, name: str = "") -> Waypoint:
    """
    Créer un waypoint à partir de coordonnées décimales.

    :param lat: Latitude en degrés décimaux
    :type lat: float
    :param lon: Longitude en degrés décimaux
    :type lon: float
    :param name: Nom du waypoint, par défaut ""
    :type name: str
    :return: Instance Waypoint
    :rtype: Waypoint
    """
    return Waypoint(lat=lat, lon=lon, name=name)


def create_waypoint_from_dms(lat_dms: str, lon_dms: str, name: str = "") -> Waypoint:
    """
    Créer un waypoint à partir de coordonnées en format degrés-minutes-secondes (DMS).

    :param lat_dms: Latitude en format DMS (ex: "45°27'30\"N")
    :type lat_dms: str
    :param lon_dms: Longitude en format DMS (ex: "73°44'54\"W")
    :type lon_dms: str
    :param name: Nom du waypoint, par défaut ""
    :type name: str
    :return: Instance Waypoint
    :rtype: Waypoint
    """
    lat = _parse_dms(lat_dms)
    lon = _parse_dms(lon_dms)
    return Waypoint(lat=lat, lon=lon, name=name)


def _parse_dms(dms_str: str) -> float:
    """
    Parser une chaîne DMS en degrés décimaux.

    :param dms_str: Chaîne DMS (ex: "45°27'30\"N")
    :type dms_str: str
    :return: Valeur en degrés décimaux
    :rtype: float
    :raises ValueError: Si le format DMS est invalide
    """
    import re

    # Pattern pour extraire degrés, minutes, secondes et hémisphère
    pattern = r"(\d+)°(\d+)'([\d.]+)\"([NSEW])"
    match = re.match(pattern, dms_str.strip())

    if not match:
        raise ValueError(f"Format DMS invalide: {dms_str}")

    degrees = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))
    hemisphere = match.group(4)

    # Convertir en degrés décimaux
    decimal = degrees + minutes / 60 + seconds / 3600

    # Appliquer le signe selon l'hémisphère
    if hemisphere in ['S', 'W']:
        decimal = -decimal

    return decimal