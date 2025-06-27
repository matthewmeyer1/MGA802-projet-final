"""
Base de données d'aéroports pour la planification VFR
"""

import pandas as pd
import os
from typing import List, Dict, Optional


class AirportDatabase:
    """
    Gestionnaire de la base de données d'aéroports.

    Permet de charger une base CSV d'aéroports ou d'utiliser un jeu de secours.
    Gère le nettoyage, les filtres (pays, types, codes ICAO/IATA), et fournit une liste d’aéroports exploitables
    pour les opérations de planification de vol.
    """

    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialiser la base de données d'aéroports.

        Si aucun chemin CSV n'est fourni, plusieurs chemins par défaut sont essayés.

        :param csv_path: Chemin vers le fichier CSV d'aéroports (optionnel)
        :type csv_path: Optional[str]
        """
        # Chemins possibles pour le fichier CSV
        if csv_path is None:
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "airports.csv"),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "airports.csv"),
                "airports.csv"
            ]
            csv_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    csv_path = path
                    break

        self.csv_path = csv_path
        self.airports_df = None
        self.filtered_airports = None
        self.current_filters = {
            'countries': [],
            'types': [],
            'icao_only': False,
            'iata_only': False
        }

        self.load_airports()

    def load_airports(self):
        """
        Charger la base de données d'aéroports depuis un fichier CSV ou créer des données de secours.

        Cette méthode tente de lire les données CSV, puis applique un nettoyage et des filtres par défaut :
        - Pays : CA, US
        - Types : non filtrés
        - ICAO/IATA : non filtrés

        En cas d'erreur de chargement, un jeu de 9 aéroports standards est utilisé.
        """
        try:
            if self.csv_path and os.path.exists(self.csv_path):
                print(f"Chargement de la base de données: {self.csv_path}")
                self.airports_df = pd.read_csv(self.csv_path)
                self._clean_data()
                print(f"Base de données chargée: {len(self.airports_df)} aéroports")
            else:
                print("Fichier CSV non trouvé, utilisation des données de base")
                self._create_fallback_data()

            # Appliquer filtres par défaut
            self.current_filters = {
                'countries': ['CA', 'US'],
                'types': [],
                'icao_only': False,
                'iata_only': False
            }
            self.apply_filters()

        except Exception as e:
            print(f"Erreur lors du chargement: {e}")
            self._create_fallback_data()

    def _clean_data(self):
        """
        Nettoyer et normaliser les données brutes du fichier CSV.

        - Mise en majuscule et nettoyage des codes (ICAO, IATA, etc.)
        - Remplissage des valeurs manquantes dans les champs textes
        - Conversion des coordonnées en types numériques
        - Suppression des lignes sans coordonnées valides
        """
        # Nettoyer les codes
        for col in ['icao_code', 'iata_code', 'ident', 'local_code', 'gps_code']:
            if col in self.airports_df.columns:
                self.airports_df[col] = self.airports_df[col].fillna('').str.upper().str.strip()

        # Nettoyer les textes
        for col in ['name', 'municipality']:
            if col in self.airports_df.columns:
                self.airports_df[col] = self.airports_df[col].fillna('Unknown')

        # S'assurer que les coordonnées sont numériques
        for col in ['latitude_deg', 'longitude_deg']:
            if col in self.airports_df.columns:
                self.airports_df[col] = pd.to_numeric(self.airports_df[col], errors='coerce')

        # Supprimer les lignes avec coordonnées invalides
        self.airports_df = self.airports_df.dropna(subset=['latitude_deg', 'longitude_deg'])

    def _create_fallback_data(self):
        """
        Créer des données de base si le fichier CSV n'est pas trouvé.

        Ce jeu comprend 9 aéroports canadiens et américains de référence.

        :return: None
        """
        fallback_data = {
            'ident': ['CYUL', 'CYQB', 'CYOW', 'CYYC', 'CYVR', 'CYYZ', 'KBOS', 'KJFK', 'CSE4'],
            'icao_code': ['CYUL', 'CYQB', 'CYOW', 'CYYC', 'CYVR', 'CYYZ', 'KBOS', 'KJFK', ''],
            'iata_code': ['YUL', 'YQB', 'YOW', 'YYC', 'YVR', 'YYZ', 'BOS', 'JFK', ''],
            'local_code': ['', '', '', '', '', '', '', '', 'CSE4'],
            'gps_code': ['', '', '', '', '', '', '', '', 'CSE4'],
            'name': ['Montreal Trudeau', 'Quebec Jean Lesage', 'Ottawa Macdonald-Cartier',
                     'Calgary', 'Vancouver', 'Toronto Pearson', 'Boston Logan', 'New York JFK', 'Saint-Esprit'],
            'latitude_deg': [45.458, 46.791, 45.323, 51.114, 49.194, 43.677, 42.364, 40.640, 45.9],
            'longitude_deg': [-73.749, -71.393, -75.669, -114.019, -123.184, -79.631, -71.005, -73.779, -73.6],
            'municipality': ['Montreal', 'Quebec', 'Ottawa', 'Calgary', 'Vancouver', 'Toronto', 'Boston', 'New York',
                             'Saint-Esprit'],
            'iso_country': ['CA', 'CA', 'CA', 'CA', 'CA', 'CA', 'US', 'US', 'CA'],
            'type': ['large_airport', 'large_airport', 'large_airport', 'large_airport', 'large_airport',
                     'large_airport', 'large_airport', 'large_airport', 'small_airport']
        }

        self.airports_df = pd.DataFrame(fallback_data)
        print("Utilisation des données de base (9 aéroports)")

    def apply_filters(self):
        """
        Appliquer les filtres actuels définis sur la base d'aéroports.

        Les filtres incluent :

        - ``countries`` : Liste de codes pays (ISO 3166-1 alpha-2) à inclure
        - ``types`` : Types d’aéroports à retenir (ex: ``small_airport``, ``large_airport``)
        - ``icao_only`` : Si vrai, ne garder que les aéroports avec un code ICAO
        - ``iata_only`` : Si vrai, ne garder que les aéroports avec un code IATA

        Met à jour l’attribut ``filtered_airports``, un DataFrame avec colonne ``display_name``.
        """
        if self.airports_df is None:
            return

        filtered_df = self.airports_df.copy()

        # Filtre par pays
        if self.current_filters['countries']:
            filtered_df = filtered_df[filtered_df['iso_country'].isin(self.current_filters['countries'])]

        # Filtre par type
        if self.current_filters['types']:
            filtered_df = filtered_df[filtered_df['type'].isin(self.current_filters['types'])]

        # Filtre ICAO seulement
        if self.current_filters['icao_only']:
            filtered_df = filtered_df[filtered_df['icao_code'] != '']

        # Filtre IATA seulement
        if self.current_filters['iata_only']:
            filtered_df = filtered_df[filtered_df['iata_code'] != '']

        self.filtered_airports = filtered_df.copy()
        self.filtered_airports['display_name'] = self._create_display_names(self.filtered_airports)

        print(f"Filtres appliqués: {len(self.filtered_airports)} aéroports retenus")

    def _create_display_names(self, df):
        """
        Créer les noms d'affichage pour les aéroports.

        Chaque nom est construit en priorisant les codes dans l'ordre : ICAO, IATA, ident, local_code.
        Le nom inclut aussi la municipalité et le pays si disponibles, ainsi qu'un indicateur visuel
        pour le type de code (🔵 ICAO, 🟡 IATA, 🟢 autre).

        :param df: DataFrame contenant les données des aéroports
        :type df: pd.DataFrame
        :return: Liste des noms d'affichage formatés
        :rtype: List[str]
        """
        display_names = []
        for _, row in df.iterrows():
            # Prioriser: ICAO > IATA > ident > local_code
            code = (row.get('icao_code', '') if row.get('icao_code', '') else
                    row.get('iata_code', '') if row.get('iata_code', '') else
                    row.get('ident', '') if row.get('ident', '') else
                    row.get('local_code', '') if row.get('local_code', '') else
                    f"ID{row.get('id', 'Unknown')}")

            name = f"{code} - {row.get('name', 'Unknown')}"
            if row.get('municipality') and row.get('municipality') != 'Unknown':
                name += f" ({row['municipality']})"
            if row.get('iso_country'):
                name += f" [{row['iso_country']}]"

            # Indicateur du type de code
            if row.get('icao_code'):
                name += " 🔵"  # ICAO
            elif row.get('iata_code'):
                name += " 🟡"  # IATA
            else:
                name += " 🟢"  # Local/GPS

            display_names.append(name)
        return display_names

    def search_airports(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Rechercher des aéroports dans la base filtrée.

        La recherche est insensible à la casse et porte sur plusieurs colonnes :
        codes ICAO, IATA, ident, local_code, gps_code, nom et municipalité.

        :param query: Terme de recherche (code ou texte)
        :type query: str
        :param max_results: Nombre maximum de résultats à retourner
        :type max_results: int
        :return: Liste des aéroports correspondants sous forme de dictionnaires
        :rtype: List[Dict]
        """
        if self.filtered_airports is None or not query:
            return []

        query = query.upper().strip()

        # Recherche dans toutes les colonnes pertinentes
        mask = (
                self.filtered_airports['icao_code'].str.match(query, na=False) |
                self.filtered_airports['iata_code'].str.match(query, na=False) |
                self.filtered_airports['ident'].str.match(query, na=False) |
                self.filtered_airports['local_code'].str.match(query, na=False) |
                self.filtered_airports['gps_code'].str.match(query, na=False) |
                self.filtered_airports['name'].str.upper().str.match(query, na=False) |
                self.filtered_airports['municipality'].str.upper().str.match(query, na=False)
        )

        results = self.filtered_airports[mask].head(max_results)

        return [self._row_to_dict(row) for _, row in results.iterrows()]

    def get_airport_by_code(self, code: str) -> Optional[Dict]:
        """
        Obtenir un aéroport via un code unique (ICAO, IATA, ident, local_code ou gps_code).

        :param code: Code d'aéroport recherché
        :type code: str
        :return: Dictionnaire représentant l'aéroport, ou None si aucun résultat
        :rtype: Optional[Dict]
        """
        if self.filtered_airports is None:
            return None

        code = code.upper().strip()
        match = self.filtered_airports[
            (self.filtered_airports['icao_code'] == code) |
            (self.filtered_airports['iata_code'] == code) |
            (self.filtered_airports['ident'] == code) |
            (self.filtered_airports['local_code'] == code) |
            (self.filtered_airports['gps_code'] == code)
            ]

        if not match.empty:
            return self._row_to_dict(match.iloc[0])
        return None

    def _row_to_dict(self, row) -> Dict:
        """
        Convertit une ligne de DataFrame en dictionnaire.

        :param row: Ligne du DataFrame contenant les données d'un aéroport.
        :type row: dict-like
        :return: Dictionnaire avec les informations extraites de la ligne.
        :rtype: Dict
        """
        return {
            'icao': row.get('icao_code', '') if row.get('icao_code', '') else row.get('ident', ''),
            'iata': row.get('iata_code', ''),
            'ident': row.get('ident', ''),
            'local_code': row.get('local_code', ''),
            'gps_code': row.get('gps_code', ''),
            'name': row.get('name', 'Unknown'),
            'city': row.get('municipality', 'Unknown'),
            'country': row.get('iso_country', ''),
            'type': row.get('type', 'unknown'),
            'lat': float(row.get('latitude_deg', 0)),
            'lon': float(row.get('longitude_deg', 0)),
            'elevation': float(row.get('elevation_ft', 0)) if 'elevation_ft' in row and pd.notna(
                row.get('elevation_ft')) else 0,
            'display': row.get('display_name', str(row.get('ident', 'Unknown')))
        }

    def get_available_countries(self) -> List[str]:
        """
        Obtient la liste des pays disponibles dans le DataFrame des aéroports.

        :return: Liste triée des codes pays ISO uniques.
        :rtype: List[str]
        """
        if self.airports_df is None:
            return []
        return sorted(self.airports_df['iso_country'].dropna().unique())

    def get_available_types(self) -> List[str]:
        """
        Obtient la liste des types d'aéroports disponibles dans le DataFrame.

        :return: Liste triée des types uniques d'aéroports.
        :rtype: List[str]
        """
        if self.airports_df is None:
            return []
        return sorted(self.airports_df['type'].dropna().unique())

    def update_filters(self, countries=None, types=None, icao_only=None, iata_only=None):
        """
        Met à jour les filtres appliqués sur les aéroports et applique les nouveaux filtres.

        :param countries: Liste des codes pays ISO à filtrer, defaults to None
        :type countries: list or None
        :param types: Liste des types d'aéroports à filtrer, defaults to None
        :type types: list or None
        :param icao_only: Filtrer uniquement les aéroports avec code ICAO, defaults to None
        :type icao_only: bool or None
        :param iata_only: Filtrer uniquement les aéroports avec code IATA, defaults to None
        :type iata_only: bool or None
        """
        if countries is not None:
            self.current_filters['countries'] = countries
        if types is not None:
            self.current_filters['types'] = types
        if icao_only is not None:
            self.current_filters['icao_only'] = icao_only
        if iata_only is not None:
            self.current_filters['iata_only'] = iata_only

        self.apply_filters()

    def reset_filters(self):
        """
        Réinitialise tous les filtres aux valeurs par défaut et applique ces filtres.

        :return: None
        """
        self.current_filters = {
            'countries': [],
            'types': [],
            'icao_only': False,
            'iata_only': False
        }
        self.apply_filters()

    def get_filter_stats(self) -> Dict:
        """
        Obtenir des statistiques sur les filtres appliqués aux aéroports.

        :return: Dictionnaire contenant le nombre total d'aéroports, le nombre filtré et le pourcentage filtré.
        :rtype: Dict[str, int or float]
        """
        total = len(self.airports_df) if self.airports_df is not None else 0
        filtered = len(self.filtered_airports) if self.filtered_airports is not None else 0
        return {
            'total': total,
            'filtered': filtered,
            'percentage': (filtered / total * 100) if total > 0 else 0
        }

    def get_airports_near_point(self, lat: float, lon: float, radius_nm: float = 50) -> List[Dict]:
        """
        Obtenir les aéroports situés dans un rayon donné autour d'un point géographique.

        :param lat: Latitude du point de référence.
        :type lat: float
        :param lon: Longitude du point de référence.
        :type lon: float
        :param radius_nm: Rayon de recherche en milles nautiques, par défaut 50.
        :type radius_nm: float, optional
        :return: Liste des aéroports sous forme de dictionnaires situés dans le rayon spécifié.
        :rtype: List[Dict]
        """
        if self.filtered_airports is None:
            return []

        from ..calculations.navigation import calculate_distance

        nearby_airports = []
        for _, row in self.filtered_airports.iterrows():
            distance = calculate_distance(lat, lon, row['latitude_deg'], row['longitude_deg'])
            if distance <= radius_nm:
                airport_dict = self._row_to_dict(row)
                airport_dict['distance'] = distance
                nearby_airports.append(airport_dict)

        # Trier par distance
        nearby_airports.sort(key=lambda x: x['distance'])
        return nearby_airports

    def get_airports_by_type(self, airport_type: str) -> List[Dict]:
        """
        Obtenir la liste des aéroports correspondant à un type donné.

        :param airport_type: Type d'aéroport à filtrer.
        :type airport_type: str
        :return: Liste des aéroports du type spécifié sous forme de dictionnaires.
        :rtype: List[Dict]
        """
        if self.filtered_airports is None:
            return []

        matching = self.filtered_airports[self.filtered_airports['type'] == airport_type]
        return [self._row_to_dict(row) for _, row in matching.iterrows()]

    def export_filtered_airports(self, filename: str):
        """
        Exporter les aéroports filtrés vers un fichier CSV.

        :param filename: Nom du fichier de sortie.
        :type filename: str
        """
        if self.filtered_airports is not None:
            self.filtered_airports.to_csv(filename, index=False)
            print(f"Aéroports exportés vers {filename}")

    def get_statistics(self) -> Dict:
        """
        Obtenir des statistiques détaillées sur la base de données des aéroports.

        :return: Dictionnaire contenant diverses statistiques.
        :rtype: Dict[str, int or dict]
        """
        if self.airports_df is None:
            return {}

        stats = {
            'total_airports': len(self.airports_df),
            'filtered_airports': len(self.filtered_airports) if self.filtered_airports is not None else 0,
            'countries': len(self.airports_df['iso_country'].unique()),
            'types': len(self.airports_df['type'].unique()),
            'with_icao': len(self.airports_df[self.airports_df['icao_code'] != '']),
            'with_iata': len(self.airports_df[self.airports_df['iata_code'] != '']),
        }

        # Statistiques par pays
        country_counts = self.airports_df['iso_country'].value_counts().head(10)
        stats['top_countries'] = country_counts.to_dict()

        # Statistiques par type
        type_counts = self.airports_df['type'].value_counts()
        stats['type_distribution'] = type_counts.to_dict()

        return stats

    def __len__(self) -> int:
        """
        Nombre d'aéroports filtrés.

        :return: Nombre d'aéroports dans la liste filtrée.
        :rtype: int
        """
        """Nombre d'aéroports filtrés"""
        return len(self.filtered_airports) if self.filtered_airports is not None else 0

    def __str__(self) -> str:
        """
        Représentation en chaîne de caractères de l'objet, affichant le nombre d'aéroports filtrés.

        :return: Chaîne descriptive.
        :rtype: str
        """
        stats = self.get_filter_stats()
        return f"AirportDatabase: {stats['filtered']} / {stats['total']} aéroports"

    def __repr__(self) -> str:
        """
        Représentation officielle de l'objet.

        :return: Chaîne représentant l'objet avec chemin CSV et nombre d'aéroports.
        :rtype: str
        """
        return f"AirportDatabase(csv_path='{self.csv_path}', airports={len(self)})"


# Instance globale pour faciliter l'utilisation
airport_db = AirportDatabase()


# Fonctions utilitaires exportées
def search_airports(query: str, max_results: int = 20) -> List[Dict]:
    """
    Rechercher des aéroports par chaîne de caractères.

    :param query: Terme de recherche.
    :type query: str
    :param max_results: Nombre maximum de résultats à retourner, par défaut 20.
    :type max_results: int, optional
    :return: Liste des aéroports correspondant à la recherche.
    :rtype: List[Dict]
    """
    return airport_db.search_airports(query, max_results)


def get_airport_by_code(code: str) -> Optional[Dict]:
    """
    Obtenir un aéroport par son code ICAO ou IATA.

    :param code: Code ICAO ou IATA de l'aéroport.
    :type code: str
    :return: Dictionnaire contenant les informations de l'aéroport, ou None si non trouvé.
    :rtype: Optional[Dict]
    """
    return airport_db.get_airport_by_code(code)


def get_airports_near(lat: float, lon: float, radius_nm: float = 50) -> List[Dict]:
    """
    Obtenir la liste des aéroports proches d’un point géographique.

    :param lat: Latitude du point.
    :type lat: float
    :param lon: Longitude du point.
    :type lon: float
    :param radius_nm: Rayon de recherche en milles nautiques, par défaut 50.
    :type radius_nm: float, optional
    :return: Liste des aéroports proches.
    :rtype: List[Dict]
    """
    return airport_db.get_airports_near_point(lat, lon, radius_nm)