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
    """
    Service pour obtenir les données météorologiques à partir de Tomorrow.io

    :param api_key: Clé API pour l'accès au service Tomorrow.io
    :type api_key: Optional[str]
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.tomorrow.io/v4"
        self.timeout = 10

        # Cache pour éviter les appels répétés
        self._cache = {}
        self._cache_duration = 3600  # 1 heure

    def set_api_key(self, api_key: str):
        """
        Définir ou mettre à jour la clé API utilisée pour accéder au service Tomorrow.io.

        :param api_key: Nouvelle clé API
        :type api_key: str
        """
        self.api_key = api_key

    def get_weather_for_leg(self, start_wp: Waypoint, end_wp: Waypoint,
                           start_time: datetime.datetime) -> Dict[str, Any]:
        """
        Obtenir la météo pour un segment de vol avec un timing précis.

        La position utilisée est le centre géographique du segment entre `start_wp` et `end_wp`.
        Les résultats peuvent être mis en cache pour éviter des appels redondants à l’API.

        :param start_wp: Waypoint de départ
        :type start_wp: Waypoint
        :param end_wp: Waypoint d'arrivée
        :type end_wp: Waypoint
        :param start_time: Heure exacte pour laquelle récupérer les conditions météo
        :type start_time: datetime.datetime

        :raises ValueError: Si la clé API n’est pas définie
        :raises Exception: En cas d’erreur lors de la récupération météo

        :return: Dictionnaire contenant les données météo, incluant la direction et la vitesse du vent
        :rtype: Dict[str, Any]
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
        """
        Récupérer les données météorologiques depuis Tomorrow.io pour une position et une heure données.

        Cette méthode effectue un appel à l'API Tomorrow.io, puis recherche dans la réponse
        l'heure correspondant le mieux à `start_time`. Si aucun match exact n'est trouvé,
        elle retourne la valeur la plus proche ou la première disponible.

        :param lat: Latitude du point d'intérêt
        :type lat: float
        :param lon: Longitude du point d'intérêt
        :type lon: float
        :param start_time: Date et heure pour lesquelles la météo est requise
        :type start_time: datetime.datetime

        :raises Exception: Si aucune donnée horaire n'est disponible dans la réponse API

        :return: Dictionnaire des données météo formatées
        :rtype: Dict[str, Any]
        """
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
            api_time_str = hour_data["time"]
            if api_time_str.endswith('Z'):
                api_time_str = api_time_str[:-1] + '+00:00'
            hour_time = datetime.datetime.fromisoformat(api_time_str)

            time_diff = abs((hour_time - target_hour).total_seconds())

            if time_diff < min_time_diff:
                min_time_diff = time_diff
                best_match = hour_data

            if hour_data["time"] == target_time:
                print(f"         🎯 Match exact trouvé: {target_time}")
                return self._parse_tomorrow_io_data(hour_data)

        if best_match:
            time_diff_hours = min_time_diff / 3600
            print(f"         📍 Meilleur match: {best_match['time']} (écart: {time_diff_hours:.1f}h)")
            return self._parse_tomorrow_io_data(best_match)

        if data["timelines"]["hourly"]:
            first_hour = data["timelines"]["hourly"][0]
            print(f"         ⚠️ Utilisation première heure disponible: {first_hour['time']}")
            return self._parse_tomorrow_io_data(first_hour)

        raise Exception("Aucune donnée météo disponible")

    def _parse_tomorrow_io_data(self, hour_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extraire et transformer les données météorologiques d'une heure donnée fournies par Tomorrow.io.

        Les unités sont converties si nécessaire (par exemple, m/s -> knots pour le vent).

        :param hour_data: Données brutes pour une heure donnée depuis l’API Tomorrow.io
        :type hour_data: Dict[str, Any]

        :return: Dictionnaire contenant les valeurs météo normalisées
        :rtype: Dict[str, Any]
        """
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

        print(
            f"         📊 Données parsées: Vent {parsed_data['wind_direction']:.0f}°/{parsed_data['wind_speed']:.0f}kn, "
            f"Temp {parsed_data['temperature']:.0f}°C, Vis {parsed_data['visibility']:.0f}km")

        return parsed_data

    def _get_default_weather(self) -> Dict[str, Any]:
        """
        Fournir un jeu de données météo par défaut en cas d'échec de l’appel à l’API.

        Ces valeurs peuvent être utilisées comme solution de repli pour assurer la continuité du traitement.

        :return: Dictionnaire contenant des valeurs météo par défaut
        :rtype: Dict[str, Any]
        """
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

        print(
            f"         🔧 Utilisation valeurs par défaut: {default_data['wind_direction']:.0f}°/{default_data['wind_speed']:.0f}kn")

        return default_data

    def get_weather_for_point(self, waypoint: Waypoint,
                              time: datetime.datetime) -> Dict[str, Any]:
        """
        Obtenir la météo pour un point spécifique à un instant donné.

        Cette méthode est un raccourci utilisant `get_weather_for_leg` avec le même point en départ et arrivée.

        :param waypoint: Point de navigation
        :type waypoint: Waypoint
        :param time: Heure pour laquelle la météo est demandée
        :type time: datetime.datetime

        :return: Données météo au point donné
        :rtype: Dict[str, Any]
        """
        return self.get_weather_for_leg(waypoint, waypoint, time)

    def get_extended_forecast(self, waypoint: Waypoint,
                              days: int = 3) -> Dict[str, Any]:
        """
        Obtenir les prévisions météorologiques étendues (par jour) pour un point.

        Cette méthode interroge l'API Tomorrow.io avec un pas de temps journalier,
        et retourne les prévisions pour le nombre de jours spécifié.

        :param waypoint: Point géographique pour lequel obtenir les prévisions
        :type waypoint: Waypoint
        :param days: Nombre de jours de prévision (maximum 5 recommandé)
        :type days: int

        :raises Exception: Si l'appel à l'API échoue ou les données sont invalides

        :return: Dictionnaire contenant les prévisions journalières ou une erreur
        :rtype: Dict[str, Any]
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
        Analyser la météo tout au long d'un itinéraire aérien en tenant compte du timing réel.

        Cette méthode calcule les horaires de passage aux différents waypoints en fonction de
        la vitesse de croisière, puis récupère la météo à chaque point en conséquence.
        Une synthèse météo est ensuite générée via `_analyze_weather_trends`.

        :param waypoints: Liste ordonnée des points de passage de la route
        :type waypoints: list[Waypoint]
        :param start_time: Heure réelle de départ du vol
        :type start_time: datetime.datetime
        :param aircraft_speed: Vitesse de croisière en nœuds (knots)
        :type aircraft_speed: float

        :raises Exception: En cas d’erreur pendant le traitement météo de l’itinéraire

        :return: Dictionnaire avec les conditions météo détaillées par segment et une analyse globale
        :rtype: Dict[str, Any]
        """
        weather_points = []
        current_time = start_time

        print(f"🌤️ Analyse météo route avec timing réel:")
        print(f"   Départ: {start_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"   Vitesse: {aircraft_speed} kn")

        try:
            for i, wp in enumerate(waypoints):
                print(f"   WP{i + 1}: {wp.name} à {current_time.strftime('%H:%M UTC')}")

                weather = self.get_weather_for_point(wp, current_time)
                weather_points.append({
                    'waypoint': wp.name,
                    'time': current_time.strftime("%H:%M UTC"),
                    'weather': weather
                })

                # Calcul du temps de vol vers le prochain point
                if i < len(waypoints) - 1:
                    next_wp = waypoints[i + 1]

                    # Import dynamique pour éviter la dépendance globale
                    from ..calculations.navigation import calculate_distance
                    distance_nm = calculate_distance(wp.lat, wp.lon, next_wp.lat, next_wp.lon)

                    flight_time_minutes = (distance_nm / aircraft_speed) * 60

                    print(f"      → {next_wp.name}: {distance_nm:.1f}NM, {flight_time_minutes:.0f}min")

                    current_time += datetime.timedelta(minutes=flight_time_minutes)

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
        Analyser la météo pour un itinéraire déjà calculé, avec des timings précis.

        Cette méthode utilise les durées de vol précalculées dans les `legs` de l'objet `Itinerary`,
        et récupère les conditions météo à chaque point de l'itinéraire au moment estimé de passage.

        :param itinerary: Objet contenant les waypoints, les legs (segments) et l'heure de départ
        :type itinerary: Itinerary

        :return: Dictionnaire contenant les conditions météo par segment et une analyse globale
        :rtype: Dict[str, Any]
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
            wp = itinerary.waypoints[0]
            print(f"   WP1: {wp.name} à {current_time.strftime('%H:%M UTC')} (départ)")

            weather = self.get_weather_for_point(wp, current_time)
            weather_points.append({
                'waypoint': wp.name,
                'time': current_time.strftime("%H:%M UTC"),
                'weather': weather,
                'leg_info': 'Départ'
            })

            for i, leg in enumerate(itinerary.legs):
                arrival_time = itinerary.start_time + datetime.timedelta(minutes=leg.time_tot)
                wp = leg.ending_wp

                print(f"   WP{i + 2}: {wp.name} à {arrival_time.strftime('%H:%M UTC')} "
                      f"(après {leg.time_leg:.0f}min de vol)")

                weather = self.get_weather_for_point(wp, arrival_time)
                weather_points.append({
                    'waypoint': wp.name,
                    'time': arrival_time.strftime("%H:%M UTC"),
                    'weather': weather,
                    'leg_info': f"Leg {i + 1}: {leg.time_leg:.0f}min, {leg.distance:.1f}NM"
                })

            analysis = self._analyze_weather_trends(weather_points)

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
        """
        Analyser les tendances météo globales à partir des différents points de l'itinéraire.

        Cette méthode agrège les données météo (vent, visibilité, précipitations) et
        génère une synthèse statistique, ainsi que des alertes pertinentes.

        :param weather_points: Liste de points contenant des données météo
        :type weather_points: list[Dict[str, Any]]

        :return: Analyse statistique et alertes météo
        :rtype: Dict[str, Any]
        """
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
        """
        Calculer la moyenne circulaire d'une liste d'angles (en degrés).

        Utile pour déterminer la moyenne des directions du vent,
        en prenant en compte la circularité (0° ≈ 360°).

        :param angles: Liste d'angles en degrés
        :type angles: list[float]

        :return: Moyenne circulaire en degrés (0–360)
        :rtype: float
        """
        if not angles:
            return 0

        x = sum(math.cos(math.radians(angle)) for angle in angles)
        y = sum(math.sin(math.radians(angle)) for angle in angles)

        mean_rad = math.atan2(y, x)
        return (math.degrees(mean_rad) + 360) % 360

    def _generate_weather_alerts(self, weather_points: list) -> list:
        """
        Générer une liste d'alertes météo à partir des conditions observées sur l'itinéraire.

        Les alertes incluent :
        - Vent fort (>25 kn)
        - Visibilité réduite (<5 km)
        - Précipitations significatives (>1 mm/h)
        - Couverture nuageuse élevée (>80%)

        :param weather_points: Liste des points météo analysés
        :type weather_points: list[Dict[str, Any]]

        :return: Liste d'alertes (chaînes de caractères)
        :rtype: list[str]
        """
        alerts = []

        for wp in weather_points:
            weather = wp['weather']

            if weather['wind_speed'] > 25:
                alerts.append(f"Vent fort à {wp['waypoint']}: {weather['wind_speed']:.0f} kn")

            if weather['visibility'] < 5:
                alerts.append(f"Visibilité réduite à {wp['waypoint']}: {weather['visibility']:.1f} km")

            if weather['precipitation'] > 1:
                alerts.append(f"Précipitations à {wp['waypoint']}: {weather['precipitation']:.1f} mm/h")

            if weather['cloud_cover'] > 80:
                alerts.append(f"Ciel très nuageux à {wp['waypoint']}: {weather['cloud_cover']:.0f}%")

        return alerts

    def get_weather_summary_text(self, weather_data: Dict[str, Any]) -> str:
        """
        Générer un résumé textuel des conditions météo.

        Le résumé inclut la direction et la vitesse du vent, la température,
        la visibilité, ainsi que les précipitations si présentes.

        :param weather_data: Dictionnaire des données météo
        :type weather_data: Dict[str, Any]

        :return: Chaîne de résumé textuel des conditions météo
        :rtype: str
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
        """
        Convertir une direction angulaire (en degrés) en point cardinal.

        :param direction: Direction en degrés (0 à 360)
        :type direction: float

        :return: Point cardinal (ex. : N, NE, SSW)
        :rtype: str
        """
        directions = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]

        index = round(direction / 22.5) % 16
        return directions[index]

    def is_weather_suitable_for_vfr(self, weather_data: Dict[str, Any]) -> Tuple[bool, list]:
        """
        Vérifier si les conditions météo sont compatibles avec un vol en VFR (Visual Flight Rules).

        Évalue la visibilité, la couverture nuageuse, les précipitations et le vent.

        :param weather_data: Données météo analysées
        :type weather_data: Dict[str, Any]

        :return: Tuple (adapté, raisons), où 'adapté' est un booléen et 'raisons' une liste d'explications
        :rtype: Tuple[bool, list]
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
    """
    Obtenir les données météo pour un segment de vol entre deux waypoints.

    :param start_wp: Waypoint de départ
    :type start_wp: Waypoint
    :param end_wp: Waypoint d’arrivée
    :type end_wp: Waypoint
    :param start_time: Heure à laquelle le segment est survolé
    :type start_time: datetime.datetime
    :param api_key: Clé API Tomorrow.io (optionnelle)
    :type api_key: str, optional

    :return: Données météo pour ce segment
    :rtype: Dict[str, Any]
    """
    if api_key:
        weather_service.set_api_key(api_key)
    return weather_service.get_weather_for_leg(start_wp, end_wp, start_time)

def get_weather_summary(weather_data: Dict[str, Any]) -> str:
    """
    Générer un résumé textuel à partir des données météo.

    :param weather_data: Dictionnaire contenant les données météo
    :type weather_data: Dict[str, Any]

    :return: Résumé texte
    :rtype: str
    """
    return weather_service.get_weather_summary_text(weather_data)

def check_vfr_conditions(weather_data: Dict[str, Any]) -> Tuple[bool, list]:
    """
    Vérifier si les conditions météo sont favorables au vol à vue (VFR).

    :param weather_data: Données météo
    :type weather_data: Dict[str, Any]

    :return: Tuple contenant un booléen (conditions favorables ou non)
             et une liste d’explications/alertes
    :rtype: Tuple[bool, list]
    """
    return weather_service.is_weather_suitable_for_vfr(weather_data)