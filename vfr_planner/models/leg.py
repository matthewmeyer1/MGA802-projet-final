"""
Modèle de données pour les segments de vol (legs)
"""

import math
import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from .waypoint import Waypoint
from .. import calculations
from ..calculations.navigation import NavigationCalculator
from ..calculations.weather import WeatherService

@dataclass
class Leg:
    """Modèle de données pour un segment de vol entre deux waypoints"""

    starting_wp: Waypoint
    ending_wp: Waypoint
    name: str = ""
    tas: float = 110.0  # True Air Speed en knots

    # Données calculées
    distance: float = field(init=False, default=0.0)  # Distance en NM
    tc: float = field(init=False, default=0.0)  # True Course en degrés
    wind_dir: float = field(init=False, default=0.0)  # Direction du vent en degrés
    wind_speed: float = field(init=False, default=0.0)  # Vitesse du vent en knots
    th: float = field(init=False, default=0.0)  # True Heading en degrés
    mh: float = field(init=False, default=0.0)  # Magnetic Heading en degrés
    wca: float = field(init=False, default=0.0)  # Wind Correction Angle en degrés
    gs: float = field(init=False, default=0.0)  # Ground Speed en knots
    time_leg: float = field(init=False, default=0.0)  # Temps du segment en minutes
    time_tot: float = field(init=False, default=0.0)  # Temps total cumulé en minutes
    fuel_burn_leg: float = field(init=False, default=0.0)  # Carburant segment en gallons
    fuel_burn_total: float = field(init=False, default=0.0)  # Carburant total cumulé en gallons
    fuel_left: float = field(init=False, default=0.0)

    # Métadonnées
    time_start: Optional[str] = field(init=False, default=None)  # Heure de début
    weather_error: Optional[str] = field(init=False, default=None)  # Erreur météo

    def __post_init__(self):
        """Initialisation après création - calculs de base"""
        if self.name == "":
            self.name = f"{self.starting_wp.name}-{self.ending_wp.name}"

        # Calculs de base (sans vent)
        self.distance = self._calc_distance()
        self.tc = self._calc_true_course()

        # Initialiser caps sans vent
        self.th = self.tc
        self.mh = self.tc  # Sera recalculé avec déclinaison magnétique
        self.gs = self.tas

    def _calc_distance(self) -> float:
        """Calculer distance en milles nautiques"""
        return self.starting_wp.distance_to(self.ending_wp)

    def _calc_true_course(self) -> float:
        """Calculer le cap vrai"""
        return self.starting_wp.bearing_to(self.ending_wp)

    def calculate_wind_effects(self, start_time: datetime.datetime,
                               api_key: Optional[str] = None,
                               manual_wind_speed: Optional[float] = None,
                               manual_wind_direction: Optional[float] = None):
        """
        Calculer les effets du vent

        Args:
            start_time: Heure de début du segment
            api_key: Clé API pour météo en ligne
            manual_wind_speed: Vitesse du vent manuelle (knots)
            manual_wind_direction: Direction du vent manuelle (degrés)
        """
        try:
            # Utiliser vent manuel si fourni
            if manual_wind_speed is not None:
                self.wind_speed = manual_wind_speed
                if manual_wind_direction is not None:
                    self.wind_dir = manual_wind_direction
            else:
                # Utiliser service météo
                weather_service = WeatherService(api_key)
                weather_data = weather_service.get_weather_for_leg(
                    self.starting_wp, self.ending_wp, start_time
                )

                self.wind_dir = weather_data['wind_direction']
                self.wind_speed = weather_data['wind_speed']
                self.time_start = weather_data.get('time', start_time.isoformat())

            # Calculer les corrections de vent
            self._calculate_wind_correction()

        except Exception as e:
            print(f"Erreur météo pour {self.name}: {e}")
            self.weather_error = str(e)
            self._use_default_wind()

    def _use_default_wind(self):
        """Utiliser des valeurs de vent par défaut"""
        self.wind_dir = 270  # Vent d'ouest
        self.wind_speed = 15  # 15 knots
        self._calculate_wind_correction()

    def _calculate_wind_correction(self):
        """Calculer les corrections de cap et vitesse dues au vent"""
        try:
            if self.wind_speed > 0 and self.tas > 0:
                # Calcul WCA (Wind Correction Angle)
                wind_angle = math.radians(self.tc - (self.wind_dir + 180))

                # Vérifier que le vent n'est pas trop fort
                sine_wca = (self.wind_speed / self.tas) * math.sin(wind_angle)
                if abs(sine_wca) > 1:
                    # Vent trop fort, approximation
                    self.wca = 30 if sine_wca > 0 else -30
                else:
                    wca_rad = math.asin(sine_wca)
                    self.wca = math.degrees(wca_rad)

                # True Heading
                self.th = self.tc + self.wca

                # Ground Speed
                wind_component = self.wind_speed * math.cos(wind_angle + math.radians(self.wca))
                self.gs = self.tas + wind_component

            else:
                # Pas de vent
                self.wca = 0
                self.th = self.tc
                self.gs = self.tas

        except (ValueError, ZeroDivisionError) as e:
            print(f"Erreur calcul vent: {e}")
            # Valeurs de fallback
            self.wca = 0
            self.th = self.tc
            self.gs = self.tas

    def calculate_magnetic_heading(self):
        """Calculer le cap magnétique avec déclinaison"""
        try:
            nav_calc = NavigationCalculator()
            self.mh = nav_calc.true_to_magnetic_heading(
                self.th, self.starting_wp.lat, self.starting_wp.lon
            )
        except Exception as e:
            print(f"Erreur calcul magnétique: {e}")
            # Approximation pour l'est du Canada
            magnetic_variation = -15.0
            self.mh = (self.th + magnetic_variation) % 360

    def calculate_times(self, previous_total_time: float = 0):
        """
        Calculer les temps de vol

        Args:
            previous_total_time: Temps total cumulé des segments précédents en minutes
        """
        if self.gs > 0:
            self.time_leg = (self.distance / self.gs) * 60  # minutes
        else:
            self.time_leg = (self.distance / self.tas) * 60  # fallback

        self.time_tot = self.time_leg + previous_total_time

    def calculate_fuel_burn(self, fuel_burn_rate: float, previous_total_fuel: float = 0, previous_fuel_left: float=0):
        """
        Calculer la consommation de carburant

        Args:
            fuel_burn_rate: Taux de consommation en GPH
            previous_total_fuel: Carburant total cumulé des segments précédents en gallons
        """

        self.fuel_burn_leg = (self.time_leg / 60) * fuel_burn_rate
        self.fuel_burn_total = self.fuel_burn_leg + previous_total_fuel
        self.fuel_left = previous_fuel_left - self.fuel_burn_leg

    def calculate_all(self, start_time: datetime.datetime,
                      previous_total_time: float = 0,
                      previous_total_fuel: float = 0,
                      fuel_burn_rate: float = 6.7,
                      previous_fuel_left: float = 0,
                      api_key: Optional[str] = None,
                      manual_wind_speed: Optional[float] = None,
                      manual_wind_direction: Optional[float] = None):
        """
        Effectuer tous les calculs pour ce segment

        Args:
            start_time: Heure de début
            previous_total_time: Temps cumulé des segments précédents
            previous_total_fuel: Carburant cumulé des segments précédents
            previouse_fuel_left: Carburant restant dans la tank
            fuel_burn_rate: Taux de consommation en GPH
            api_key: Clé API météo
            manual_wind_speed: Vent manuel (knots)
            manual_wind_direction: Direction vent manuel (degrés)
        """
        # 1. Calculer vent et corrections
        self.calculate_wind_effects(start_time, api_key, manual_wind_speed, manual_wind_direction)

        # 2. Calculer cap magnétique
        self.calculate_magnetic_heading()

        # 3. Calculer temps
        self.calculate_times(previous_total_time)

        # 4. Calculer carburant
        self.calculate_fuel_burn(fuel_burn_rate, previous_total_fuel, previous_fuel_left)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire pour affichage et export"""
        return {
            'Starting WP': self.starting_wp.name,
            'Ending WP': self.ending_wp.name,
            'Distance (NM)': round(self.distance, 1),
            'Time start': self.time_start or '',
            'Wind Direction (deg)': round(self.wind_dir, 0),
            'Wind Speed (kn)': round(self.wind_speed, 1),
            'True course (deg)': round(self.tc, 0),
            'True heading (deg)': round(self.th, 0),
            'Magnetic heading (deg)': round(self.mh, 0),
            'WCA (deg)': round(self.wca, 1),
            'Groundspeed (kn)': round(self.gs, 0),
            'TAS (kn)': round(self.tas, 0),
            'Leg time (min)': round(self.time_leg, 0),
            'Total time (min)': round(self.time_tot, 0),
            'Fuel burn leg (gal)': round(self.fuel_burn_leg, 1),
            'Fuel burn tot (gal)': round(self.fuel_burn_total, 1),
            'Fuel left (gal)': round(self.fuel_left, 1),
            'Weather error': self.weather_error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Leg':
        """Créer un Leg depuis un dictionnaire"""
        starting_wp = Waypoint.from_dict(data['starting_wp'])
        ending_wp = Waypoint.from_dict(data['ending_wp'])

        leg = cls(
            starting_wp=starting_wp,
            ending_wp=ending_wp,
            name=data.get('name', ''),
            tas=data.get('tas', 110.0)
        )

        # Restaurer les valeurs calculées si disponibles
        if 'wind_dir' in data:
            leg.wind_dir = data['wind_dir']
        if 'wind_speed' in data:
            leg.wind_speed = data['wind_speed']
        if 'th' in data:
            leg.th = data['th']
        if 'mh' in data:
            leg.mh = data['mh']
        if 'gs' in data:
            leg.gs = data['gs']
        if 'time_leg' in data:
            leg.time_leg = data['time_leg']
        if 'time_tot' in data:
            leg.time_tot = data['time_tot']
        if 'fuel_burn_leg' in data:
            leg.fuel_burn_leg = data['fuel_burn_leg']
        if 'fuel_burn_total' in data:
            leg.fuel_burn_total = data['fuel_burn_total']

        return leg

    def get_eta(self, departure_time: datetime.datetime) -> datetime.datetime:
        """
        Calculer l'ETA pour ce segment

        Args:
            departure_time: Heure de départ du vol

        Returns:
            Heure d'arrivée estimée pour ce segment
        """
        return departure_time + datetime.timedelta(minutes=self.time_tot)

    def get_eta_string(self, departure_time: datetime.datetime, format_str: str = "%H:%M") -> str:
        """
        Obtenir l'ETA sous forme de chaîne

        Args:
            departure_time: Heure de départ du vol
            format_str: Format d'affichage de l'heure

        Returns:
            ETA formatée
        """
        eta = self.get_eta(departure_time)
        return eta.strftime(format_str)

    def has_weather_data(self) -> bool:
        """Vérifier si des données météo sont disponibles"""
        return self.wind_speed > 0 and self.weather_error is None

    def get_wind_summary(self) -> str:
        """Obtenir un résumé du vent"""
        if self.has_weather_data():
            return f"{self.wind_dir:03.0f}°/{self.wind_speed:.0f}kn"
        else:
            return "Vent non disponible"

    def __str__(self) -> str:
        return f"{self.name}: {self.distance:.1f}NM, {self.tc:.0f}°"

    def __repr__(self) -> str:
        return f"Leg(from='{self.starting_wp.name}', to='{self.ending_wp.name}', distance={self.distance:.1f})"