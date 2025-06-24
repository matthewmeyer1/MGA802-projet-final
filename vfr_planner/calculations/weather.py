"""
Service météorologique pour la planification VFR
"""

import datetime
import requests
import json
from typing import Dict, Any, Optional, Tuple
import math

from ..models.waypoint import Waypoint


class WeatherService:
    """Service pour obtenir les données météorologiques"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.tomorrow.io/v4"
        self.timeout = 10

        # Cache pour éviter les appels répétés
        self._cache = {}
        self._cache_duration = 3600  # 1 heure

    def set_api_key(self, api_key: str):
        """Définir la clé API"""
        self.api_key = api_key

    def get_weather_for_leg(self, start_wp: Waypoint, end_wp: Waypoint,
                           start_time: datetime.datetime) -> Dict[str, Any]:
        """
        Obtenir la météo pour un segment de vol

        Args:
            start_wp: Waypoint de départ
            end_wp: Waypoint d'arrivée
            start_time: Heure de début du segment

        Returns:
            Dictionnaire avec données météo
        """
        try:
            if not self.api_key:
                raise ValueError("Clé API Tomorrow.io requise")

            # Utiliser le centre du segment pour la météo
            center_lat = (start_wp.lat + end_wp.lat) / 2
            center_lon = (start_wp.lon + end_wp.lon) / 2

            # Vérifier le cache
            cache_key = f"{center_lat:.3f},{center_lon:.3f},{start_time.strftime('%Y%m%d%H')}"
            if cache_key in self._cache:
                cached_data, cache_time = self._cache[cache_key]
                if (datetime.datetime.now() - cache_time).seconds < self._cache_duration:
                    return cached_data

            # Faire l'appel API
            weather_data = self._fetch_tomorrow_io_weather(center_lat, center_lon, start_time)

            # Mettre en cache
            self._cache[cache_key] = (weather_data, datetime.datetime.now())

            return weather_data

        except Exception as e:
            print(f"Erreur météo: {e}")
            return self._get_default_weather()

    def _fetch_tomorrow_io_weather(self, lat: float, lon: float,
                                  start_time: datetime.datetime) -> Dict[str, Any]:
        """Récupérer la météo depuis Tomorrow.io"""

        url = f"{self.base_url}/weather/forecast"
        params = {
            "location": f"{lat},{lon}",
            "timesteps": "hourly",
            "apikey": self.api_key,
            "fields": [
                "windSpeed",
                "windDirection",
                "temperature",
                "visibility",
                "cloudCover",
                "precipitationIntensity",
                "weatherCode"
            ]
        }

        headers = {
            "accept": "application/json",
            "accept-encoding": "deflate, gzip, br"
        }

        response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()

        # Trouver l'heure la plus proche
        target_time = start_time.strftime("%Y-%m-%dT%H:00:00Z")

        # Chercher la bonne heure dans les données
        for hour_data in data["timelines"]["hourly"]:
            if hour_data["time"] == target_time:
                return self._parse_tomorrow_io_data(hour_data)

        # Si l'heure exacte n'est pas trouvée, utiliser la première disponible
        if data["timelines"]["hourly"]:
            first_hour = data["timelines"]["hourly"][0]
            return self._parse_tomorrow_io_data(first_hour)

        raise Exception("Aucune donnée météo disponible")

    def _parse_tomorrow_io_data(self, hour_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parser les données de Tomorrow.io"""
        values = hour_data["values"]

        return {
            'time': hour_data["time"],
            'wind_direction': values.get("windDirection", 270),
            'wind_speed': values.get("windSpeed", 15) * 1.943844,  # m/s -> knots
            'temperature': values.get("temperature", 15),  # Celsius
            'visibility': values.get("visibility", 10),  # km
            'cloud_cover': values.get("cloudCover", 20),  # %
            'precipitation': values.get("precipitationIntensity", 0),  # mm/h
            'weather_code': values.get("weatherCode", 1000),
            'source': 'Tomorrow.io'
        }

    def _get_default_weather(self) -> Dict[str, Any]:
        """Retourner des valeurs météo par défaut"""
        return {
            'time': datetime.datetime.now().isoformat(),
            'wind_direction': 270,  # Vent d'ouest
            'wind_speed': 15,  # 15 knots
            'temperature': 15,
            'visibility': 10,
            'cloud_cover': 25,
            'precipitation': 0,
            'weather_code': 1000,
            'source': 'Default values'
        }

    def get_weather_for_point(self, waypoint: Waypoint,
                             time: datetime.datetime) -> Dict[str, Any]:
        """
        Obtenir la météo pour un point spécifique

        Args:
            waypoint: Point de navigation
            time: Heure désirée

        Returns:
            Données météo
        """
        return self.get_weather_for_leg(waypoint, waypoint, time)

    def get_extended_forecast(self, waypoint: Waypoint,
                            days: int = 3) -> Dict[str, Any]:
        """
        Obtenir les prévisions étendues pour un point

        Args:
            waypoint: Point de navigation
            days: Nombre de jours de prévision

        Returns:
            Prévisions étendues
        """
        try:
            if not self.api_key:
                raise ValueError("Clé API requise")

            url = f"{self.base_url}/weather/forecast"
            params = {
                "location": f"{waypoint.lat},{waypoint.lon}",
                "timesteps": "daily",
                "apikey": self.api_key
            }

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            forecast_days = []
            for day_data in data["timelines"]["daily"][:days]:
                values = day_data["values"]
                forecast_days.append({
                    'date': day_data["time"][:10],
                    'temp_min': values.get("temperatureMin", 10),
                    'temp_max': values.get("temperatureMax", 20),
                    'wind_speed_avg': values.get("windSpeedAvg", 15) * 1.943844,
                    'wind_direction': values.get("windDirectionAvg", 270),
                    'visibility': values.get("visibilityAvg", 10),
                    'precipitation': values.get("precipitationIntensityAvg", 0),
                    'weather_code': values.get("weatherCodeMax", 1000)
                })

            return {
                'location': f"{waypoint.name} ({waypoint.lat:.3f}, {waypoint.lon:.3f})",
                'forecast': forecast_days,
                'source': 'Tomorrow.io'
            }

        except Exception as e:
            print(f"Erreur prévisions étendues: {e}")
            return {'error': str(e)}

    def analyze_weather_for_route(self, waypoints: list,
                                 start_time: datetime.datetime) -> Dict[str, Any]:
        """
        Analyser la météo pour un itinéraire complet

        Args:
            waypoints: Liste des waypoints
            start_time: Heure de départ

        Returns:
            Analyse météo de la route
        """
        weather_points = []
        current_time = start_time

        try:
            for i, wp in enumerate(waypoints):
                weather = self.get_weather_for_point(wp, current_time)
                weather_points.append({
                    'waypoint': wp.name,
                    'time': current_time.strftime("%H:%M"),
                    'weather': weather
                })

                # Avancer d'une heure pour le prochain waypoint (approximation)
                current_time += datetime.timedelta(hours=1)

            # Analyser les tendances
            analysis = self._analyze_weather_trends(weather_points)

            return {
                'route_weather': weather_points,
                'analysis': analysis,
                'generated_at': datetime.datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Erreur analyse météo route: {e}")
            return {'error': str(e)}

    def _analyze_weather_trends(self, weather_points: list) -> Dict[str, Any]:
        """Analyser les tendances météo sur la route"""
        if not weather_points:
            return {}

        wind_speeds = [wp['weather']['wind_speed'] for wp in weather_points]
        wind_directions = [wp['weather']['wind_direction'] for wp in weather_points]
        visibilities = [wp['weather']['visibility'] for wp in weather_points]
        precipitations = [wp['weather']['precipitation'] for wp in weather_points]

        return {
            'wind_speed': {
                'min': min(wind_speeds),
                'max': max(wind_speeds),
                'avg': sum(wind_speeds) / len(wind_speeds)
            },
            'wind_direction': {
                'avg': self._circular_mean(wind_directions),
                'variation': max(wind_directions) - min(wind_directions)
            },
            'visibility': {
                'min': min(visibilities),
                'avg': sum(visibilities) / len(visibilities)
            },
            'precipitation': {
                'max': max(precipitations),
                'total': sum(precipitations)
            },
            'alerts': self._generate_weather_alerts(weather_points)
        }

    def _circular_mean(self, angles: list) -> float:
        """Calculer la moyenne d'angles (pour direction du vent)"""
        if not angles:
            return 0

        x = sum(math.cos(math.radians(angle)) for angle in angles)
        y = sum(math.sin(math.radians(angle)) for angle in angles)

        mean_rad = math.atan2(y, x)
        return (math.degrees(mean_rad) + 360) % 360

    def _generate_weather_alerts(self, weather_points: list) -> list:
        """Générer des alertes météo"""
        alerts = []

        for wp in weather_points:
            weather = wp['weather']

            # Alerte vent fort
            if weather['wind_speed'] > 25:
                alerts.append(f"Vent fort à {wp['waypoint']}: {weather['wind_speed']:.0f} kn")

            # Alerte visibilité réduite
            if weather['visibility'] < 5:
                alerts.append(f"Visibilité réduite à {wp['waypoint']}: {weather['visibility']:.1f} km")

            # Alerte précipitations
            if weather['precipitation'] > 1:
                alerts.append(f"Précipitations à {wp['waypoint']}: {weather['precipitation']:.1f} mm/h")

            # Alerte couverture nuageuse élevée
            if weather['cloud_cover'] > 80:
                alerts.append(f"Ciel très nuageux à {wp['waypoint']}: {weather['cloud_cover']:.0f}%")

        return alerts

    def get_weather_summary_text(self, weather_data: Dict[str, Any]) -> str:
        """
        Générer un résumé textuel de la météo

        Args:
            weather_data: Données météo

        Returns:
            Résumé textuel
        """
        if 'error' in weather_data:
            return f"Erreur météo: {weather_data['error']}"

        wind_dir = weather_data.get('wind_direction', 270)
        wind_speed = weather_data.get('wind_speed', 15)
        temp = weather_data.get('temperature', 15)
        visibility = weather_data.get('visibility', 10)

        # Direction cardinale du vent
        wind_cardinal = self._wind_direction_to_cardinal(wind_dir)

        summary = f"Vent: {wind_cardinal} {wind_speed:.0f} kn"
        summary += f", Temp: {temp:.0f}°C"
        summary += f", Visibilité: {visibility:.0f} km"

        if weather_data.get('precipitation', 0) > 0:
            summary += f", Précip: {weather_data['precipitation']:.1f} mm/h"

        return summary

    def _wind_direction_to_cardinal(self, direction: float) -> str:
        """Convertir direction du vent en point cardinal"""
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]

        index = round(direction / 22.5) % 16
        return directions[index]

    def is_weather_suitable_for_vfr(self, weather_data: Dict[str, Any]) -> Tuple[bool, list]:
        """
        Vérifier si les conditions météo sont adaptées au VFR

        Args:
            weather_data: Données météo

        Returns:
            Tuple (suitable, reasons)
        """
        reasons = []
        suitable = True

        # Visibilité minimale VFR: 3 SM (≈5 km)
        visibility = weather_data.get('visibility', 10)
        if visibility < 5:
            suitable = False
            reasons.append(f"Visibilité insuffisante: {visibility:.1f} km (min: 5 km)")

        # Plafond nuageux
        cloud_cover = weather_data.get('cloud_cover', 0)
        if cloud_cover > 75:
            reasons.append(f"Couverture nuageuse élevée: {cloud_cover:.0f}%")

        # Précipitations
        precipitation = weather_data.get('precipitation', 0)
        if precipitation > 2:
            suitable = False
            reasons.append(f"Précipitations importantes: {precipitation:.1f} mm/h")

        # Vent fort
        wind_speed = weather_data.get('wind_speed', 0)
        if wind_speed > 30:
            reasons.append(f"Vent très fort: {wind_speed:.0f} kn")

        if suitable and not reasons:
            reasons.append("Conditions favorables au VFR")

        return suitable, reasons


# Instance globale pour faciliter l'utilisation
weather_service = WeatherService()

# Fonctions utilitaires exportées
def get_weather_for_leg(start_wp: Waypoint, end_wp: Waypoint,
                       start_time: datetime.datetime, api_key: str = None) -> Dict[str, Any]:
    """Obtenir la météo pour un segment"""
    if api_key:
        weather_service.set_api_key(api_key)
    return weather_service.get_weather_for_leg(start_wp, end_wp, start_time)

def get_weather_summary(weather_data: Dict[str, Any]) -> str:
    """Obtenir un résumé météo"""
    return weather_service.get_weather_summary_text(weather_data)

def check_vfr_conditions(weather_data: Dict[str, Any]) -> Tuple[bool, list]:
    """Vérifier les conditions VFR"""
    return weather_service.is_weather_suitable_for_vfr(weather_data)