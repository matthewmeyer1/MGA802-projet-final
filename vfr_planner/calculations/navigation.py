"""
Calculs de navigation pour la planification VFR
"""

import math
from typing import Tuple, Optional


class NavigationCalculator:
    """Calculateur pour les opérations de navigation aérienne"""

    def __init__(self):
        # Constantes de navigation
        self.EARTH_RADIUS_KM = 6371.0
        self.NM_TO_KM = 1.852
        self.KM_TO_NM = 1.0 / 1.852

    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculer la distance haversine entre deux points

        Args:
            lat1, lon1: Coordonnées du premier point (degrés)
            lat2, lon2: Coordonnées du second point (degrés)

        Returns:
            Distance en milles nautiques
        """
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

        distance_km = self.EARTH_RADIUS_KM * c
        return distance_km * self.KM_TO_NM

    def great_circle_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculer le cap initial du grand cercle entre deux points

        Args:
            lat1, lon1: Coordonnées du point de départ (degrés)
            lat2, lon2: Coordonnées du point d'arrivée (degrés)

        Returns:
            Cap en degrés (0-360)
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)

        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))

        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)

        return (bearing_deg + 360) % 360

    def wind_correction_angle(self, true_course: float, wind_direction: float,
                              wind_speed: float, tas: float) -> Tuple[float, float, float]:
        """
        Calculer l'angle de correction de vent et la vitesse sol

        Args:
            true_course: Cap vrai désiré (degrés)
            wind_direction: Direction du vent (d'où vient le vent, degrés)
            wind_speed: Vitesse du vent (knots)
            tas: Vitesse vraie de l'aéronef (knots)

        Returns:
            Tuple (wca, true_heading, ground_speed)
        """
        if wind_speed == 0 or tas == 0:
            return 0.0, true_course, tas

        try:
            # Angle entre le cap désiré et la direction d'où vient le vent
            wind_angle = math.radians(true_course - (wind_direction + 180))

            # Calcul de l'angle de correction de vent (WCA)
            sine_wca = (wind_speed / tas) * math.sin(wind_angle)

            # Vérifier que la solution est possible
            if abs(sine_wca) > 1:
                # Vent trop fort par rapport à la vitesse de l'avion
                wca = 30.0 if sine_wca > 0 else -30.0
                print(f"Attention: Vent très fort par rapport à TAS")
            else:
                wca_rad = math.asin(sine_wca)
                wca = math.degrees(wca_rad)

            # Cap vrai à maintenir
            true_heading = true_course + wca

            # Calcul de la vitesse sol
            wind_component = wind_speed * math.cos(wind_angle + math.radians(wca))
            ground_speed = tas + wind_component

            return wca, true_heading, max(0, ground_speed)

        except (ValueError, ZeroDivisionError) as e:
            print(f"Erreur calcul vent: {e}")
            return 0.0, true_course, tas

    def true_to_magnetic_heading(self, true_heading: float, lat: float, lon: float) -> float:
        """
        Convertir un cap vrai en cap magnétique

        Args:
            true_heading: Cap vrai (degrés)
            lat: Latitude (degrés)
            lon: Longitude (degrés)

        Returns:
            Cap magnétique (degrés)
        """
        try:
            # Essayer d'utiliser la bibliothèque geomag si disponible
            import geomag
            magnetic_declination = geomag.declination(lat, lon)
            magnetic_heading = (true_heading - magnetic_declination) % 360
            return magnetic_heading

        except ImportError:
            # Utiliser une approximation pour l'est du Canada
            magnetic_variation = self._approximate_magnetic_variation(lat, lon)
            magnetic_heading = (true_heading - magnetic_variation) % 360
            return magnetic_heading

        except Exception as e:
            print(f"Erreur calcul magnétique: {e}")
            # Fallback: utiliser approximation
            magnetic_variation = self._approximate_magnetic_variation(lat, lon)
            magnetic_heading = (true_heading - magnetic_variation) % 360
            return magnetic_heading

    def _approximate_magnetic_variation(self, lat: float, lon: float) -> float:
        """
        Approximation de la déclinaison magnétique pour l'Amérique du Nord

        Args:
            lat: Latitude (degrés)
            lon: Longitude (degrés)

        Returns:
            Déclinaison magnétique approximative (degrés)
        """
        # Approximations basées sur les zones géographiques
        if -100 <= lon <= -60 and 40 <= lat <= 60:
            # Est du Canada et nord-est des États-Unis
            if lon >= -80:  # Provinces maritimes
                return -20.0
            elif lon >= -90:  # Québec/Ontario
                return -15.0
            else:  # Prairies
                return -10.0
        else:
            # Valeur par défaut
            return -15.0

    def cross_track_distance(self, lat1: float, lon1: float, lat2: float, lon2: float,
                             lat3: float, lon3: float) -> float:
        """
        Calculer la distance perpendiculaire d'un point à une route

        Args:
            lat1, lon1: Point de départ de la route
            lat2, lon2: Point d'arrivée de la route
            lat3, lon3: Point dont on veut la distance à la route

        Returns:
            Distance perpendiculaire en milles nautiques (positive = droite, négative = gauche)
        """
        # Convertir en radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat3_rad = math.radians(lat3)

        # Distance du point de départ au point test
        d13 = self.haversine_distance(lat1, lon1, lat3, lon3) * self.NM_TO_KM / self.EARTH_RADIUS_KM

        # Cap de la route principale
        bearing_12 = math.radians(self.great_circle_bearing(lat1, lon1, lat2, lon2))

        # Cap vers le point test
        bearing_13 = math.radians(self.great_circle_bearing(lat1, lon1, lat3, lon3))

        # Distance perpendiculaire
        cross_track_rad = math.asin(math.sin(d13) * math.sin(bearing_13 - bearing_12))
        cross_track_km = cross_track_rad * self.EARTH_RADIUS_KM

        return cross_track_km * self.KM_TO_NM

    def along_track_distance(self, lat1: float, lon1: float, lat2: float, lon2: float,
                             lat3: float, lon3: float) -> float:
        """
        Calculer la distance le long de la route jusqu'au point perpendiculaire

        Args:
            lat1, lon1: Point de départ de la route
            lat2, lon2: Point d'arrivée de la route
            lat3, lon3: Point de référence

        Returns:
            Distance le long de la route en milles nautiques
        """
        # Distance du point de départ au point test
        d13 = self.haversine_distance(lat1, lon1, lat3, lon3) * self.NM_TO_KM / self.EARTH_RADIUS_KM

        # Distance perpendiculaire
        cross_track_km = self.cross_track_distance(lat1, lon1, lat2, lon2, lat3, lon3) * self.NM_TO_KM
        cross_track_rad = cross_track_km / self.EARTH_RADIUS_KM

        # Distance le long de la route
        along_track_rad = math.acos(math.cos(d13) / math.cos(cross_track_rad))
        along_track_km = along_track_rad * self.EARTH_RADIUS_KM

        return along_track_km * self.KM_TO_NM

    def intermediate_point(self, lat1: float, lon1: float, lat2: float, lon2: float,
                           fraction: float) -> Tuple[float, float]:
        """
        Calculer un point intermédiaire sur une route

        Args:
            lat1, lon1: Point de départ
            lat2, lon2: Point d'arrivée
            fraction: Fraction de la route (0.0 = départ, 1.0 = arrivée)

        Returns:
            Tuple (latitude, longitude) du point intermédiaire
        """
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Distance angulaire
        d = self.haversine_distance(lat1, lon1, lat2, lon2) * self.NM_TO_KM / self.EARTH_RADIUS_KM

        a = math.sin((1 - fraction) * d) / math.sin(d)
        b = math.sin(fraction * d) / math.sin(d)

        x = a * math.cos(lat1_rad) * math.cos(lon1_rad) + b * math.cos(lat2_rad) * math.cos(lon2_rad)
        y = a * math.cos(lat1_rad) * math.sin(lon1_rad) + b * math.cos(lat2_rad) * math.sin(lon2_rad)
        z = a * math.sin(lat1_rad) + b * math.sin(lat2_rad)

        lat_inter = math.atan2(z, math.sqrt(x * x + y * y))
        lon_inter = math.atan2(y, x)

        return math.degrees(lat_inter), math.degrees(lon_inter)

    def time_to_fly(self, distance_nm: float, ground_speed_kn: float) -> float:
        """
        Calculer le temps de vol

        Args:
            distance_nm: Distance en milles nautiques
            ground_speed_kn: Vitesse sol en knots

        Returns:
            Temps en minutes
        """
        if ground_speed_kn <= 0:
            return float('inf')

        return (distance_nm / ground_speed_kn) * 60.0

    def fuel_consumption(self, time_minutes: float, burn_rate_gph: float) -> float:
        """
        Calculer la consommation de carburant

        Args:
            time_minutes: Temps de vol en minutes
            burn_rate_gph: Taux de consommation en gallons par heure

        Returns:
            Consommation en gallons
        """
        return (time_minutes / 60.0) * burn_rate_gph

    def descent_distance(self, altitude_loss_ft: float, descent_rate_fpm: float,
                         ground_speed_kn: float) -> float:
        """
        Calculer la distance de descente

        Args:
            altitude_loss_ft: Perte d'altitude en pieds
            descent_rate_fpm: Taux de descente en pieds par minute
            ground_speed_kn: Vitesse sol en knots

        Returns:
            Distance de descente en milles nautiques
        """
        if descent_rate_fpm <= 0:
            return 0.0

        descent_time_minutes = altitude_loss_ft / descent_rate_fpm
        return (ground_speed_kn * descent_time_minutes) / 60.0

    def climb_distance(self, altitude_gain_ft: float, climb_rate_fpm: float,
                       ground_speed_kn: float) -> float:
        """
        Calculer la distance de montée

        Args:
            altitude_gain_ft: Gain d'altitude en pieds
            climb_rate_fpm: Taux de montée en pieds par minute
            ground_speed_kn: Vitesse sol en knots

        Returns:
            Distance de montée en milles nautiques
        """
        if climb_rate_fpm <= 0:
            return 0.0

        climb_time_minutes = altitude_gain_ft / climb_rate_fpm
        return (ground_speed_kn * climb_time_minutes) / 60.0


# Instance globale pour faciliter l'utilisation
nav_calc = NavigationCalculator()


# Fonctions utilitaires exportées
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculer la distance entre deux points"""
    return nav_calc.haversine_distance(lat1, lon1, lat2, lon2)


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculer le cap entre deux points"""
    return nav_calc.great_circle_bearing(lat1, lon1, lat2, lon2)


def calculate_wind_correction(true_course: float, wind_direction: float,
                              wind_speed: float, tas: float) -> Tuple[float, float, float]:
    """Calculer la correction de vent"""
    return nav_calc.wind_correction_angle(true_course, wind_direction, wind_speed, tas)


def true_to_magnetic(true_heading: float, lat: float, lon: float) -> float:
    """Convertir cap vrai en cap magnétique"""
    return nav_calc.true_to_magnetic_heading(true_heading, lat, lon)