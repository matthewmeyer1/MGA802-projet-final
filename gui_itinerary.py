# gui_itinerary.py
"""
Classes adaptées pour l'interface GUI - Version sans input() console
"""

import pandas as pd
import datetime
import pytz
import math
import requests
import json
from typing import Optional, List, Dict, Any


class GuiWaypoint:
    """Version GUI de la classe Waypoint"""

    def __init__(self, lat: float, lon: float, name: str = "", alt: float = 0):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.alt = alt

    def to_dict(self):
        return {
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.alt
        }


class GuiLeg:
    """Version GUI de la classe Leg avec gestion d'erreurs améliorée"""

    def __init__(self, starting_wp: GuiWaypoint, ending_wp: GuiWaypoint, name: str = "", tas: float = 110):
        self.starting_wp = starting_wp
        self.ending_wp = ending_wp
        self.distance = self.calc_dist()
        self.tc = self.calc_tc()
        self.wind_dir = 0
        self.wind_speed = 0
        self.time_start = 0
        self.th = 0
        self.mh = 0
        self.wca = 0
        self.gs = 0
        self.tas = tas
        self.time_leg = 0
        self.time_tot = 0
        self.fuel_burn_leg = 0
        self.fuel_burn_total = 0
        self.weather_error = None

        if name == "":
            self.name = self.starting_wp.name
        else:
            self.name = name

    def calc_dist(self) -> float:
        """Calculer distance en milles nautiques"""
        try:
            # Utiliser formule haversine si geopy pas disponible
            return self._haversine_distance(
                self.starting_wp.lat, self.starting_wp.lon,
                self.ending_wp.lat, self.ending_wp.lon
            )
        except Exception:
            # Fallback vers geopy si disponible
            try:
                from geopy.distance import geodesic
                return geodesic(
                    (self.starting_wp.lat, self.starting_wp.lon),
                    (self.ending_wp.lat, self.ending_wp.lon)
                ).nm
            except ImportError:
                # Formule haversine basique
                return self._haversine_distance(
                    self.starting_wp.lat, self.starting_wp.lon,
                    self.ending_wp.lat, self.ending_wp.lon
                )

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculer distance haversine en milles nautiques"""
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

    def calc_tc(self) -> float:
        """Calculer le cap vrai"""
        lat1 = math.radians(self.starting_wp.lat)
        lat2 = math.radians(self.ending_wp.lat)

        del_lon = math.radians(self.ending_wp.lon) - math.radians(self.starting_wp.lon)
        y = math.sin(del_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(del_lon)
        brng = math.atan2(y, x)
        brng = math.degrees(brng)
        return (brng + 360) % 360

    def calc_wind(self, start_time: datetime.datetime, api_key: str = None,
                  windspeed: float = None, winddirection: float = None):
        """Calculer le vent avec gestion d'erreurs robuste"""

        # Si vent manuel fourni
        if windspeed is not None:
            self.wind_speed = windspeed
            if winddirection is not None:
                self.wind_dir = winddirection
            return

        # Essayer l'API Tomorrow.io
        try:
            if api_key:
                self._fetch_weather_tomorrow_io(start_time, api_key)
            else:
                # Valeurs par défaut si pas d'API
                self._use_default_wind()
        except Exception as e:
            print(f"Erreur météo: {e}")
            self.weather_error = str(e)
            self._use_default_wind()

    def _fetch_weather_tomorrow_io(self, start_time: datetime.datetime, api_key: str):
        """Récupérer météo de Tomorrow.io"""
        center_lat = (self.starting_wp.lat + self.ending_wp.lat) / 2
        center_lon = (self.starting_wp.lon + self.ending_wp.lon) / 2

        url = f"https://api.tomorrow.io/v4/weather/forecast"
        params = {
            "location": f"{center_lat},{center_lon}",
            "timesteps": "hourly",
            "apikey": api_key
        }

        headers = {
            "accept": "application/json",
            "accept-encoding": "deflate, gzip, br"
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        target_time = start_time.strftime("%Y-%m-%dT%H:00:00Z")

        # Chercher la bonne heure
        for hour_data in data["timelines"]["hourly"]:
            if hour_data["time"] == target_time:
                self.time_start = hour_data["time"]
                self.wind_dir = hour_data["values"]["windDirection"]
                self.wind_speed = hour_data["values"]["windSpeed"] * 1.943844  # m/s -> knots
                print(f"Météo trouvée: {self.wind_dir}° {self.wind_speed:.1f}kn")
                return

        # Si heure exacte pas trouvée, utiliser la première disponible
        if data["timelines"]["hourly"]:
            first_hour = data["timelines"]["hourly"][0]
            self.time_start = first_hour["time"]
            self.wind_dir = first_hour["values"]["windDirection"]
            self.wind_speed = first_hour["values"]["windSpeed"] * 1.943844
            print(f"Météo approximative: {self.wind_dir}° {self.wind_speed:.1f}kn")
        else:
            raise Exception("Aucune donnée météo disponible")

    def _use_default_wind(self):
        """Utiliser vent par défaut en cas d'erreur API"""
        # Vent typique: 270° à 15 kn (vent d'ouest léger)
        self.wind_dir = 270
        self.wind_speed = 15
        print("Utilisation vent par défaut: 270° 15kn")

    def calc_th(self):
        """Calculer le cap vrai avec correction de vent"""
        try:
            if self.wind_speed > 0 and self.tas > 0:
                wind_angle = math.radians(self.tc - (180 + self.wind_dir))
                wca_rad = math.asin(self.wind_speed / self.tas * math.sin(wind_angle))
                self.wca = math.degrees(wca_rad)
                self.th = self.tc + self.wca
            else:
                self.wca = 0
                self.th = self.tc
        except (ValueError, ZeroDivisionError):
            # Si calcul impossible (vent trop fort, etc.)
            self.wca = 0
            self.th = self.tc

    def calc_mh(self):
        """Calculer le cap magnétique"""
        try:
            # Essayer d'utiliser geomag
            import geomag
            center_lat = (self.starting_wp.lat + self.ending_wp.lat) / 2
            center_lon = (self.starting_wp.lon + self.ending_wp.lon) / 2
            self.mh = geomag.mag_heading(self.th, center_lat, center_lon)
        except ImportError:
            # Approximation pour l'est du Canada: -15° de déclinaison
            magnetic_variation = -15.0
            self.mh = (self.th + magnetic_variation) % 360
        except Exception:
            # En cas d'erreur, utiliser cap vrai
            self.mh = self.th

    def calc_gs(self):
        """Calculer la vitesse sol"""
        try:
            if self.wind_speed > 0:
                # Formule vectorielle pour vitesse sol
                wind_angle = math.radians(self.tc - self.wind_dir + self.wca)
                self.gs = math.sqrt(
                    self.tas ** 2 + self.wind_speed ** 2 -
                    (2 * self.tas * self.wind_speed * math.cos(wind_angle))
                )
            else:
                self.gs = self.tas
        except Exception:
            # En cas d'erreur, utiliser TAS
            self.gs = self.tas

    def calc_time(self, prev_time: float):
        """Calculer les temps de vol"""
        if self.gs > 0:
            self.time_leg = self.distance / self.gs * 60  # minutes
        else:
            self.time_leg = self.distance / self.tas * 60  # fallback

        self.time_tot = self.time_leg + prev_time

    def calc_speeds(self):
        """Calculer tous les caps et vitesses"""
        self.calc_th()
        self.calc_mh()
        self.calc_gs()

    def calc_fuel_burn(self, burn_rate: float):
        """Calculer la consommation de carburant"""
        self.fuel_burn_leg = self.time_leg * burn_rate / 60
        self.fuel_burn_total = self.time_tot * burn_rate / 60

    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire pour affichage"""
        return {
            'Starting WP': self.starting_wp.name,
            'Ending WP': self.ending_wp.name,
            'Distance (NM)': round(self.distance, 1),
            'Time start': self.time_start,
            'Wind Direction (deg)': round(self.wind_dir, 0),
            'Wind Speed (kn)': round(self.wind_speed, 1),
            'True course (deg)': round(self.tc, 0),
            'True heading (deg)': round(self.th, 0),
            'Magnetic heading (deg)': round(self.mh, 0),
            'Groundspeed (kn)': round(self.gs, 0),
            'Leg time (min)': round(self.time_leg, 0),
            'Total time (min)': round(self.time_tot, 0),
            'Fuel burn leg (gal)': round(self.fuel_burn_leg, 1),
            'Fuel burn tot (gal)': round(self.fuel_burn_total, 1)
        }


class GuiItinerary:
    """Version GUI de la classe Itinerary"""

    def __init__(self):
        self.wp: List[GuiWaypoint] = []
        self.legs: List[GuiLeg] = []
        self.start_time: Optional[datetime.datetime] = None
        self.api_key: Optional[str] = None

    def set_start_time(self, date_str: str, time_str: str):
        """Définir l'heure de départ depuis les champs GUI"""
        try:
            # Parser la date (YYYY-MM-DD)
            if date_str:
                year, month, day = map(int, date_str.split('-'))
            else:
                # Date d'aujourd'hui par défaut
                today = datetime.date.today()
                year, month, day = today.year, today.month, today.day

            # Parser l'heure (HH:MM)
            if time_str and ':' in time_str:
                hour, minute = map(int, time_str.split(':'))
            elif time_str:
                hour = int(time_str)
                minute = 0
            else:
                hour, minute = 10, 0  # 10h00 par défaut

            # Créer datetime en timezone locale puis convertir UTC
            dt = datetime.datetime(year, month, day, hour, minute)
            tz = pytz.timezone('America/Montreal')
            dt = tz.localize(dt)
            self.start_time = dt.astimezone(pytz.utc)

            print(f"Heure de départ: {self.start_time.strftime('%Y-%m-%d %H:%M UTC')}")

        except Exception as e:
            print(f"Erreur parsing date/heure: {e}")
            # Heure par défaut: maintenant
            self.start_time = datetime.datetime.now(pytz.utc)

    def set_api_key(self, api_key: str):
        """Définir la clé API Tomorrow.io"""
        self.api_key = api_key

    def add_waypoint(self, lat: float, lon: float, name: str = "", wp_index: Optional[int] = None):
        """Ajouter un waypoint"""
        waypoint = GuiWaypoint(lat, lon, name)
        if wp_index is None:
            self.wp.append(waypoint)
        else:
            self.wp.insert(wp_index, waypoint)

    def remove_waypoint(self, index: int):
        """Supprimer un waypoint"""
        if 0 <= index < len(self.wp):
            self.wp.pop(index)

    def create_legs(self, tas: float = 110, fuel_burn_rate: float = 7.5):
        """Créer les legs avec les paramètres GUI"""
        if len(self.wp) < 2:
            raise ValueError("Au moins 2 waypoints requis")

        if not self.start_time:
            # Utiliser heure actuelle par défaut
            self.start_time = datetime.datetime.now(pytz.utc)

        leg_list = []
        current_time = self.start_time

        for i in range(len(self.wp) - 1):
            leg = GuiLeg(self.wp[i], self.wp[i + 1], tas=tas)

            # Calculer le vent pour cette heure
            leg.calc_wind(current_time, self.api_key)

            # Calculer caps et vitesses
            leg.calc_speeds()

            # Calculer temps
            if i == 0:
                leg.calc_time(prev_time=0)
            else:
                leg.calc_time(prev_time=leg_list[i - 1].time_tot)

            # Calculer carburant
            leg.calc_fuel_burn(fuel_burn_rate)

            leg_list.append(leg)

            # Avancer l'heure pour le prochain leg
            current_time += datetime.timedelta(minutes=leg.time_leg)

        self.legs = leg_list

    def get_summary(self) -> Dict[str, Any]:
        """Obtenir un résumé de l'itinéraire"""
        if not self.legs:
            return {}

        total_distance = sum(leg.distance for leg in self.legs)
        total_time = self.legs[-1].time_tot if self.legs else 0
        total_fuel = self.legs[-1].fuel_burn_total if self.legs else 0

        return {
            'total_distance': total_distance,
            'total_time': total_time,
            'total_fuel': total_fuel,
            'num_legs': len(self.legs),
            'departure': self.wp[0].name if self.wp else '',
            'destination': self.wp[-1].name if self.wp else ''
        }

    def to_dataframe(self) -> pd.DataFrame:
        """Convertir les legs en DataFrame"""
        if not self.legs:
            return pd.DataFrame()

        return pd.DataFrame([leg.to_dict() for leg in self.legs])


# Fonction utilitaire pour créer un itinéraire depuis l'interface GUI
def create_itinerary_from_gui(waypoints: List[Dict], aircraft_params: Dict,
                              flight_params: Dict, api_key: str = None) -> GuiItinerary:
    """
    Créer un itinéraire depuis les données GUI

    Args:
        waypoints: Liste de {'name': str, 'lat': float, 'lon': float}
        aircraft_params: {'tas': float, 'fuel_burn': float}
        flight_params: {'date': str, 'time': str}
        api_key: Clé API Tomorrow.io optionnelle
    """

    # Créer l'itinéraire
    itinerary = GuiItinerary()

    # Ajouter waypoints
    for wp in waypoints:
        itinerary.add_waypoint(wp['lat'], wp['lon'], wp['name'])

    # Configurer heure de départ
    itinerary.set_start_time(
        flight_params.get('date', ''),
        flight_params.get('time', '')
    )

    # Configurer API
    if api_key:
        itinerary.set_api_key(api_key)

    # Créer les legs
    tas = aircraft_params.get('tas', 110)
    fuel_burn = aircraft_params.get('fuel_burn', 7.5)
    itinerary.create_legs(tas, fuel_burn)

    return itinerary


# Tests unitaires intégrés
if __name__ == "__main__":
    # Test basique
    print("Test des classes GUI...")

    # Créer waypoints de test
    wp1 = GuiWaypoint(45.458, -73.75, "CYUL")
    wp2 = GuiWaypoint(46.791, -71.393, "CYQB")

    # Créer leg de test
    leg = GuiLeg(wp1, wp2, tas=120)
    print(f"Distance CYUL-CYQB: {leg.distance:.1f} NM")
    print(f"Cap vrai: {leg.tc:.0f}°")

    # Test itinéraire
    it = GuiItinerary()
    it.add_waypoint(45.458, -73.75, "CYUL")
    it.add_waypoint(46.791, -71.393, "CYQB")
    it.set_start_time("2025-06-17", "14:00")

    try:
        it.create_legs(tas=120, fuel_burn_rate=8.0)
        summary = it.get_summary()
        print(f"Itinéraire: {summary['total_distance']:.1f} NM, {summary['total_time']:.0f} min")
        print("✅ Tests réussis!")
    except Exception as e:
        print(f"❌ Erreur de test: {e}")