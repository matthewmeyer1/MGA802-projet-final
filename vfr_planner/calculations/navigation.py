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
        Calcule la distance haversine entre deux points.

        :param lat1: Latitude du premier point (en degrés).
        :type lat1: float
        :param lon1: Longitude du premier point (en degrés).
        :type lon1: float
        :param lat2: Latitude du second point (en degrés).
        :type lat2: float
        :param lon2: Longitude du second point (en degrés).
        :type lon2: float
        :return: Distance entre les deux points en milles nautiques.
        :rtype: float
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
        Calcule le cap initial du grand cercle entre deux points.

        :param lat1: Latitude du point de départ (en degrés).
        :type lat1: float
        :param lon1: Longitude du point de départ (en degrés).
        :type lon1: float
        :param lat2: Latitude du point d'arrivée (en degrés).
        :type lat2: float
        :param lon2: Longitude du point d'arrivée (en degrés).
        :type lon2: float
        :return: Cap initial en degrés (0–360).
        :rtype: float
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
        Calcule l'angle de correction de vent et la vitesse sol.

        :param true_course: Cap vrai désiré (en degrés).
        :type true_course: float
        :param wind_direction: Direction du vent (d'où il vient, en degrés).
        :type wind_direction: float
        :param wind_speed: Vitesse du vent (en knots).
        :type wind_speed: float
        :param tas: Vitesse vraie de l'aéronef (en knots).
        :type tas: float
        :return: Un tuple contenant :
                 - wca : Wind Correction Angle (en degrés),
                 - true_heading : Cap vrai corrigé (en degrés),
                 - ground_speed : Vitesse sol (en knots).
        :rtype: tuple[float, float, float]
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
        Convertit un cap vrai en cap magnétique.

        :param true_heading: Cap vrai (en degrés).
        :type true_heading: float
        :param lat: Latitude (en degrés).
        :type lat: float
        :param lon: Longitude (en degrés).
        :type lon: float
        :return: Cap magnétique (en degrés).
        :rtype: float
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
        Approxime la déclinaison magnétique pour l'Amérique du Nord.

        :param lat: Latitude (en degrés).
        :type lat: float
        :param lon: Longitude (en degrés).
        :type lon: float
        :return: Déclinaison magnétique approximative (en degrés).
        :rtype: float
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
        Calcule la distance perpendiculaire d'un point à une route.

        :param lat1: Latitude du point de départ de la route (en degrés).
        :type lat1: float
        :param lon1: Longitude du point de départ de la route (en degrés).
        :type lon1: float
        :param lat2: Latitude du point d'arrivée de la route (en degrés).
        :type lat2: float
        :param lon2: Longitude du point d'arrivée de la route (en degrés).
        :type lon2: float
        :param lat3: Latitude du point dont on veut la distance à la route (en degrés).
        :type lat3: float
        :param lon3: Longitude du point dont on veut la distance à la route (en degrés).
        :type lon3: float
        :return: Distance perpendiculaire en milles nautiques (positive = à droite de la route, négative = à gauche).
        :rtype: float
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
        Calcule la distance le long de la route jusqu'au point perpendiculaire.

        :param lat1: Latitude du point de départ de la route (en degrés).
        :type lat1: float
        :param lon1: Longitude du point de départ de la route (en degrés).
        :type lon1: float
        :param lat2: Latitude du point d'arrivée de la route (en degrés).
        :type lat2: float
        :param lon2: Longitude du point d'arrivée de la route (en degrés).
        :type lon2: float
        :param lat3: Latitude du point de référence (en degrés).
        :type lat3: float
        :param lon3: Longitude du point de référence (en degrés).
        :type lon3: float
        :return: Distance le long de la route en milles nautiques.
        :rtype: float
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
        Calcule un point intermédiaire sur une route.

        :param lat1: Latitude du point de départ (en degrés).
        :type lat1: float
        :param lon1: Longitude du point de départ (en degrés).
        :type lon1: float
        :param lat2: Latitude du point d'arrivée (en degrés).
        :type lat2: float
        :param lon2: Longitude du point d'arrivée (en degrés).
        :type lon2: float
        :param fraction: Fraction de la route (0.0 = départ, 1.0 = arrivée).
        :type fraction: float
        :return: Tuple contenant la latitude et la longitude du point intermédiaire (en degrés).
        :rtype: tuple[float, float]
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
        Calcule le temps de vol.

        :param distance_nm: Distance en milles nautiques.
        :type distance_nm: float
        :param ground_speed_kn: Vitesse sol en knots.
        :type ground_speed_kn: float
        :return: Temps de vol en minutes.
        :rtype: float
        """
        if ground_speed_kn <= 0:
            return float('inf')

        return (distance_nm / ground_speed_kn) * 60.0

    def fuel_consumption(self, time_minutes: float, burn_rate_gph: float) -> float:
        """
        Calcule la consommation de carburant.

        :param time_minutes: Temps de vol en minutes.
        :type time_minutes: float
        :param burn_rate_gph: Taux de consommation en gallons par heure.
        :type burn_rate_gph: float
        :return: Consommation totale en gallons.
        :rtype: float
        """
        return (time_minutes / 60.0) * burn_rate_gph

    def descent_distance(self, altitude_loss_ft: float, descent_rate_fpm: float,
                         ground_speed_kn: float) -> float:
        """
        Calcule la distance de descente.

        :param altitude_loss_ft: Perte d'altitude en pieds.
        :type altitude_loss_ft: float
        :param descent_rate_fpm: Taux de descente en pieds par minute.
        :type descent_rate_fpm: float
        :param ground_speed_kn: Vitesse sol en knots.
        :type ground_speed_kn: float
        :return: Distance de descente en milles nautiques.
        :rtype: float
        """
        if descent_rate_fpm <= 0:
            return 0.0

        descent_time_minutes = altitude_loss_ft / descent_rate_fpm
        return (ground_speed_kn * descent_time_minutes) / 60.0

    def climb_distance(self, altitude_gain_ft: float, climb_rate_fpm: float,
                       ground_speed_kn: float) -> float:
        """
        Calcule la distance de montée.

        :param altitude_gain_ft: Gain d'altitude en pieds.
        :type altitude_gain_ft: float
        :param climb_rate_fpm: Taux de montée en pieds par minute.
        :type climb_rate_fpm: float
        :param ground_speed_kn: Vitesse sol en knots.
        :type ground_speed_kn: float
        :return: Distance de montée en milles nautiques.
        :rtype: float
        """
        if climb_rate_fpm <= 0:
            return 0.0

        climb_time_minutes = altitude_gain_ft / climb_rate_fpm
        return (ground_speed_kn * climb_time_minutes) / 60.0


# Instance globale pour faciliter l'utilisation
nav_calc = NavigationCalculator()


# Fonctions utilitaires exportées
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule la distance entre deux points géographiques.

    :param lat1: Latitude du premier point (en degrés).
    :type lat1: float
    :param lon1: Longitude du premier point (en degrés).
    :type lon1: float
    :param lat2: Latitude du second point (en degrés).
    :type lat2: float
    :param lon2: Longitude du second point (en degrés).
    :type lon2: float
    :return: Distance entre les deux points en milles nautiques.
    :rtype: float
    """
    return nav_calc.haversine_distance(lat1, lon1, lat2, lon2)


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule le cap initial (bearing) entre deux points géographiques.

    :param lat1: Latitude du point de départ (en degrés).
    :type lat1: float
    :param lon1: Longitude du point de départ (en degrés).
    :type lon1: float
    :param lat2: Latitude du point d'arrivée (en degrés).
    :type lat2: float
    :param lon2: Longitude du point d'arrivée (en degrés).
    :type lon2: float
    :return: Cap initial entre les deux points en degrés (0-360).
    :rtype: float
    """
    return nav_calc.great_circle_bearing(lat1, lon1, lat2, lon2)


def calculate_wind_correction(true_course: float, wind_direction: float,
                              wind_speed: float, tas: float) -> tuple[float, float, float]:
    """
    Calcule l'angle de correction de vent, le cap vrai corrigé et la vitesse sol.

    :param true_course: Cap vrai désiré (en degrés).
    :type true_course: float
    :param wind_direction: Direction du vent (d'où vient le vent, en degrés).
    :type wind_direction: float
    :param wind_speed: Vitesse du vent (en knots).
    :type wind_speed: float
    :param tas: Vitesse vraie de l'aéronef (en knots).
    :type tas: float
    :return: Tuple contenant :
             - l'angle de correction de vent (WCA) en degrés,
             - le cap vrai corrigé en degrés,
             - la vitesse sol en knots.
    :rtype: tuple[float, float, float]
    """
    return nav_calc.wind_correction_angle(true_course, wind_direction, wind_speed, tas)


def true_to_magnetic(true_heading: float, lat: float, lon: float) -> float:
    """
    Convertit un cap vrai en cap magnétique selon la position géographique.

    :param true_heading: Cap vrai (en degrés).
    :type true_heading: float
    :param lat: Latitude du point (en degrés).
    :type lat: float
    :param lon: Longitude du point (en degrés).
    :type lon: float
    :return: Cap magnétique correspondant (en degrés).
    :rtype: float
    """
    return nav_calc.true_to_magnetic_heading(true_heading, lat, lon)
