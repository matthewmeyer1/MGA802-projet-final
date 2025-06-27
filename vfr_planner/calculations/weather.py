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
        Obtenir la météo pour un segment de vol avec timing précis

        Args:
            start_wp: Waypoint de départ
            end_wp: Waypoint d'arrivée
            start_time: Heure pour laquelle récupérer la météo (peut être milieu du leg)

        Returns:
            Dictionnaire avec données météo
        """
        try:
            if not self.api_key:
                raise ValueError("Clé API Tomorrow.io requise")

            # Utiliser le centre du segment pour la météo
            center_lat = (start_wp.lat + end_wp.lat) / 2
            center_lon = (start_wp.lon + end_wp.lon) / 2

            print(f"      🌤️ Récupération météo:")
            print(f"         Position: {center_lat:.4f}, {center_lon:.4f} (centre du leg)")
            print(f"         Heure: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")

            # Vérifier le cache avec timing précis
            cache_key = f"{center_lat:.3f},{center_lon:.3f},{start_time.strftime('%Y%m%d%H%M')}"
            if cache_key in self._cache:
                cached_data, cache_time = self._cache[cache_key]
                cache_age = (datetime.datetime.now() - cache_time).seconds
                if cache_age < self._cache_duration:
                    print(f"         📋 Cache hit (âge: {cache_age}s)")
                    return cached_data

            # Faire l'appel API
            print(f"         🌐 Appel API Tomorrow.io...")
            weather_data = self._fetch_tomorrow_io_weather(center_lat, center_lon, start_time)

            # Mettre en cache avec timing précis
            self._cache[cache_key] = (weather_data, datetime.datetime.now())

            print(f"         ✅ Météo récupérée: {weather_data['wind_direction']:.0f}°/{weather_data['wind_speed']:.0f}kn")

            return weather_data

        except Exception as e:
            print(f"         ❌ Erreur météo: {e}")
            return self._get_default_weather()

    def _fetch_tomorrow_io_weather(self, lat: float, lon: float,
                                  start_time: datetime.datetime) -> Dict[str, Any]:
        """Récupérer la météo depuis Tomorrow.io avec gestion de timing améliorée"""

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

        # Convertir start_time en format API (arrondi à l'heure)
        target_hour = start_time.replace(minute=0, second=0, microsecond=0)
        target_time = target_hour.strftime("%Y-%m-%dT%H:00:00Z")

        print(f"         🕐 Recherche données pour: {target_time}")

        # Chercher l'heure exacte ou la plus proche
        best_match = None
        min_time_diff = float('inf')

        for hour_data in data["timelines"]["hourly"]:
            # Convertir le timestamp de l'API en datetime
            api_time_str = hour_data["time"]
            if api_time_str.endswith('Z'):
                api_time_str = api_time_str[:-1] + '+00:00'
            hour_time = datetime.datetime.fromisoformat(api_time_str)

            time_diff = abs((hour_time - target_hour).total_seconds())

            if time_diff < min_time_diff:
                min_time_diff = time_diff
                best_match = hour_data

            # Si match exact, utiliser directement
            if hour_data["time"] == target_time:
                print(f"         🎯 Match exact trouvé: {target_time}")
                return self._parse_tomorrow_io_data(hour_data)

        # Utiliser le meilleur match trouvé
        if best_match:
            time_diff_hours = min_time_diff / 3600
            print(f"         📍 Meilleur match: {best_match['time']} (écart: {time_diff_hours:.1f}h)")
            return self._parse_tomorrow_io_data(best_match)

        # Fallback sur la première heure disponible
        if data["timelines"]["hourly"]:
            first_hour = data["timelines"]["hourly"][0]
            print(f"         ⚠️ Utilisation première heure disponible: {first_hour['time']}")
            return self._parse_tomorrow_io_data(first_hour)

        raise Exception("Aucune donnée météo disponible")

    def _parse_tomorrow_io_data(self, hour_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parser les données de Tomorrow.io avec info de timing"""
        values = hour_data["values"]

        parsed_data = {
            'time': hour_data["time"],
            'wind_direction': values.get("windDirection", 270),
            'wind_speed': values.get("windSpeed", 15) * 1.943844,  # m/s -> knots
            'temperature': values.get("temperature", 15),  # Celsius
            'visibility': values.get("visibility", 10),  # km
            'cloud_cover': values.get("cloudCover", 20),  # %
            'precipitation': values.get("precipitationIntensity", 0),  # mm/h
            'weather_code': values.get("weatherCode", 1000),
            'source': 'Tomorrow.io API',
            'api_timestamp': datetime.datetime.now().isoformat()
        }

        print(f"         📊 Données parsées: Vent {parsed_data['wind_direction']:.0f}°/{parsed_data['wind_speed']:.0f}kn, "
              f"Temp {parsed_data['temperature']:.0f}°C, Vis {parsed_data['visibility']:.0f}km")

        return parsed_data

    def _get_default_weather(self) -> Dict[str, Any]:
        """Retourner des valeurs météo par défaut avec timestamp"""
        default_data = {
            'time': datetime.datetime.now().isoformat(),
            'wind_direction': 270,  # Vent d'ouest
            'wind_speed': 15,  # 15 knots
            'temperature': 15,
            'visibility': 10,
            'cloud_cover': 25,
            'precipitation': 0,
            'weather_code': 1000,
            'source': 'Default values (API error)',
            'api_timestamp': datetime.datetime.now().isoformat()
        }

        print(f"         🔧 Utilisation valeurs par défaut: {default_data['wind_direction']:.0f}°/{default_data['wind_speed']:.0f}kn")

        return default_data

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
                                 start_time: datetime.datetime,
                                 aircraft_speed: float = 110) -> Dict[str, Any]:
        """
        Analyser la météo pour un itinéraire complet avec timing réaliste

        Args:
            waypoints: Liste des waypoints
            start_time: Heure de départ RÉELLE du vol
            aircraft_speed: Vitesse de croisière pour calculer les temps de vol

        Returns:
            Analyse météo de la route avec timing correct
        """
        weather_points = []
        current_time = start_time

        print(f"🌤️ Analyse météo route avec timing réel:")
        print(f"   Départ: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"   Vitesse: {aircraft_speed} kn")

        try:
            for i, wp in enumerate(waypoints):
                print(f"   WP{i+1}: {wp.name} à {current_time.strftime('%H:%M UTC')}")

                weather = self.get_weather_for_point(wp, current_time)
                weather_points.append({
                    'waypoint': wp.name,
                    'time': current_time.strftime("%H:%M UTC"),
                    'weather': weather
                })

                # Calculer le temps de vol vers le prochain waypoint (si il y en a un)
                if i < len(waypoints) - 1:
                    next_wp = waypoints[i + 1]

                    # Calculer distance vers le prochain waypoint
                    from ..calculations.navigation import calculate_distance
                    distance_nm = calculate_distance(wp.lat, wp.lon, next_wp.lat, next_wp.lon)

                    # Calculer temps de vol (en minutes)
                    flight_time_minutes = (distance_nm / aircraft_speed) * 60

                    print(f"      → {next_wp.name}: {distance_nm:.1f}NM, {flight_time_minutes:.0f}min")

                    # Avancer l'heure pour le prochain waypoint
                    current_time += datetime.timedelta(minutes=flight_time_minutes)

            # Analyser les tendances
            analysis = self._analyze_weather_trends(weather_points)

            print(f"✅ Analyse météo terminée: {len(weather_points)} points")

            return {
                'route_weather': weather_points,
                'analysis': analysis,
                'generated_at': datetime.datetime.now().isoformat(),
                'flight_start_time': start_time.isoformat(),
                'aircraft_speed': aircraft_speed
            }

        except Exception as e:
            print(f"❌ Erreur analyse météo route: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

    def analyze_weather_for_itinerary(self, itinerary) -> Dict[str, Any]:
        """
        Analyser la météo pour un itinéraire déjà calculé avec timing précis

        Cette méthode utilise les temps de vol précis de l'itinéraire calculé

        Args:
            itinerary: Objet Itinerary avec legs calculés

        Returns:
            Analyse météo détaillée avec timing exact
        """
        if not itinerary.waypoints or not itinerary.start_time:
            return {'error': 'Itinéraire incomplet (pas de waypoints ou heure de départ)'}

        weather_points = []
        current_time = itinerary.start_time

        print(f"🌤️ Analyse météo pour itinéraire calculé:")
        print(f"   Départ: {current_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"   Waypoints: {len(itinerary.waypoints)}")
        print(f"   Legs: {len(itinerary.legs)}")

        try:
            # Premier waypoint (départ)
            wp = itinerary.waypoints[0]
            print(f"   WP1: {wp.name} à {current_time.strftime('%H:%M UTC')} (départ)")

            weather = self.get_weather_for_point(wp, current_time)
            weather_points.append({
                'waypoint': wp.name,
                'time': current_time.strftime("%H:%M UTC"),
                'weather': weather,
                'leg_info': 'Départ'
            })

            # Waypoints suivants basés sur les legs calculés
            for i, leg in enumerate(itinerary.legs):
                # Temps d'arrivée au waypoint = temps de départ + temps total du leg
                arrival_time = itinerary.start_time + datetime.timedelta(minutes=leg.time_tot)

                wp = leg.ending_wp
                print(f"   WP{i+2}: {wp.name} à {arrival_time.strftime('%H:%M UTC')} "
                      f"(après {leg.time_leg:.0f}min de vol)")

                weather = self.get_weather_for_point(wp, arrival_time)
                weather_points.append({
                    'waypoint': wp.name,
                    'time': arrival_time.strftime("%H:%M UTC"),
                    'weather': weather,
                    'leg_info': f"Leg {i+1}: {leg.time_leg:.0f}min, {leg.distance:.1f}NM"
                })

            # Analyser les tendances
            analysis = self._analyze_weather_trends(weather_points)

            # Ajouter des informations spécifiques à l'itinéraire
            if itinerary.legs:
                analysis['flight_summary'] = {
                    'total_time_minutes': itinerary.legs[-1].time_tot,
                    'total_distance_nm': sum(leg.distance for leg in itinerary.legs),
                    'departure_time': itinerary.start_time.strftime('%Y-%m-%d %H:%M UTC'),
                    'arrival_time': (itinerary.start_time +
                                   datetime.timedelta(minutes=itinerary.legs[-1].time_tot)).strftime('%H:%M UTC')
                }

            print(f"✅ Analyse météo itinéraire terminée: {len(weather_points)} points")

            return {
                'route_weather': weather_points,
                'analysis': analysis,
                'generated_at': datetime.datetime.now().isoformat(),
                'flight_start_time': itinerary.start_time.isoformat(),
                'method': 'calculated_itinerary'
            }

        except Exception as e:
            print(f"❌ Erreur analyse météo itinéraire: {e}")
            import traceback
            traceback.print_exc()
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