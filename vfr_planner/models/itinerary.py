"""
Modèle de données pour l'itinéraire complet - VERSION CORRIGÉE
Corrections du timing météo
"""

import datetime
import pytz
import pandas as pd
from typing import List, Dict, Any, Optional

from .waypoint import Waypoint
from .leg import Leg
from .aircraft import Aircraft
from ..calculations.aeroport_refuel import aeroport_proche

class Itinerary:
    """Modèle de données pour un itinéraire de vol complet"""

    def __init__(self, aircraft: Optional[Aircraft] = None):
        self.waypoints: List[Waypoint] = []
        self.legs: List[Leg] = []
        self.aircraft = aircraft
        self.start_time: Optional[datetime.datetime] = None
        self.api_key: Optional[str] = None
        self.flight_info: Dict[str, Any] = {}

    def set_aircraft(self, aircraft: Aircraft):
        """Définir l'aéronef"""
        self.aircraft = aircraft

    def set_start_time_from_flight_info(self, flight_info: Dict[str, Any], timezone_str: str = "America/Montreal"):
        """
        Définir l'heure de départ à partir des informations de vol de l'utilisateur

        Args:
            flight_info: Dictionnaire contenant 'date' et 'departure_time'
            timezone_str: Fuseau horaire
        """
        try:
            date_str = flight_info.get('date', '')
            time_str = flight_info.get('departure_time', '')

            print(f"Setting start time from flight info: date='{date_str}', time='{time_str}'")

            # Parser la date
            if date_str and '-' in date_str:
                try:
                    year, month, day = map(int, date_str.split('-'))
                except ValueError:
                    # Format alternatif possible
                    today = datetime.date.today()
                    year, month, day = today.year, today.month, today.day
                    print(f"Date parsing failed, using today: {year}-{month}-{day}")
            else:
                today = datetime.date.today()
                year, month, day = today.year, today.month, today.day
                print(f"No date provided, using today: {year}-{month}-{day}")

            # Parser l'heure
            if time_str and ':' in time_str:
                try:
                    hour, minute = map(int, time_str.split(':'))
                except ValueError:
                    hour, minute = 10, 0
                    print(f"Time parsing failed, using default: {hour}:{minute}")
            elif time_str:
                try:
                    hour = int(time_str)
                    minute = 0
                except ValueError:
                    hour, minute = 10, 0
                    print(f"Time parsing failed, using default: {hour}:{minute}")
            else:
                hour, minute = 10, 0
                print(f"No time provided, using default: {hour}:{minute}")

            # Créer datetime avec timezone
            dt = datetime.datetime(year, month, day, hour, minute)
            tz = pytz.timezone(timezone_str)
            dt = tz.localize(dt)
            self.start_time = dt.astimezone(pytz.utc)

            print(f"✅ Heure de départ définie: {self.start_time.strftime('%Y-%m-%d %H:%M UTC')} (local: {dt.strftime('%Y-%m-%d %H:%M %Z')})")

        except Exception as e:
            print(f"❌ Erreur parsing date/heure: {e}")
            # Fallback vers maintenant
            self.start_time = datetime.datetime.now(pytz.utc)
            print(f"Using current time as fallback: {self.start_time.strftime('%Y-%m-%d %H:%M UTC')}")

    def set_start_time(self, date_str: str, time_str: str, timezone_str: str = "America/Montreal"):
        """
        Définir l'heure de départ (méthode legacy - utilisez set_start_time_from_flight_info)

        Args:
            date_str: Date au format YYYY-MM-DD
            time_str: Heure au format HH:MM
            timezone_str: Fuseau horaire
        """
        flight_info = {'date': date_str, 'departure_time': time_str}
        self.set_start_time_from_flight_info(flight_info, timezone_str)

    def set_api_key(self, api_key: str):
        """Définir la clé API météo"""
        self.api_key = api_key

    def set_flight_info(self, info: Dict[str, Any]):
        """Définir les informations de vol"""
        self.flight_info.update(info)
        # Automatiquement mettre à jour l'heure de départ si les infos sont présentes
        if 'date' in info or 'departure_time' in info:
            self.set_start_time_from_flight_info(self.flight_info)

    def add_waypoint(self, waypoint: Waypoint, index: Optional[int] = None):
        """
        Ajouter un waypoint

        Args:
            waypoint: Waypoint à ajouter
            index: Position d'insertion (None = à la fin)
        """
        if index is None:
            self.waypoints.append(waypoint)
        else:
            self.waypoints.insert(index, waypoint)

    def add_waypoint_from_coords(self, lat: float, lon: float, name: str = "",
                                 index: Optional[int] = None):
        """Ajouter un waypoint depuis des coordonnées"""
        waypoint = Waypoint(lat=lat, lon=lon, name=name)
        self.add_waypoint(waypoint, index)

    def add_waypoint_from_airport(self, airport_data: Dict[str, Any],
                                  index: Optional[int] = None):
        """Ajouter un waypoint depuis des données d'aéroport"""
        waypoint = Waypoint.from_airport(airport_data)
        self.add_waypoint(waypoint, index)

    def remove_waypoint(self, index: int):
        """Supprimer un waypoint par index"""
        if 0 <= index < len(self.waypoints):
            self.waypoints.pop(index)

    def clear_waypoints(self):
        """Supprimer tous les waypoints"""
        self.waypoints.clear()
        self.legs.clear()

    def move_waypoint(self, from_index: int, to_index: int):
        """Déplacer un waypoint"""
        if (0 <= from_index < len(self.waypoints) and
                0 <= to_index < len(self.waypoints)):
            waypoint = self.waypoints.pop(from_index)
            self.waypoints.insert(to_index, waypoint)

    def create_legs(self, recalculate: bool = True):
        """
        Créer les segments de vol entre les waypoints avec timing météo corrigé

        Args:
            recalculate: Recalculer tous les paramètres de vol
        """
        if len(self.waypoints) < 2:
            raise ValueError("Au moins 2 waypoints requis pour créer des segments")

        if not self.aircraft:
            raise ValueError("Aéronef requis pour les calculs")

        # S'assurer qu'on a une heure de départ
        if not self.start_time:
            print("⚠️ Pas d'heure de départ définie, utilisation des infos de vol ou heure actuelle")
            if self.flight_info:
                self.set_start_time_from_flight_info(self.flight_info)
            else:
                self.start_time = datetime.datetime.now(pytz.utc)

        print(f"🕐 Création des legs avec heure de départ: {self.start_time.strftime('%Y-%m-%d %H:%M UTC')}")

        self.legs.clear()
        leg_start_time = self.start_time  # Heure de début du leg courant

        for i in range(len(self.waypoints) - 1):
            print(f"\n--- Leg {i+1}: {self.waypoints[i].name} → {self.waypoints[i+1].name} ---")

            leg = Leg(
                starting_wp=self.waypoints[i],
                ending_wp=self.waypoints[i + 1],
                tas=self.aircraft.cruise_speed
            )

            if recalculate:
                # Calculer tous les paramètres
                previous_total_time = self.legs[-1].time_tot if self.legs else 0
                previous_total_fuel = self.legs[-1].fuel_burn_total if self.legs else 0
                previous_fuel = self.legs[-1].fuel_left if self.legs else self.aircraft.fuel_capacity

                print(f"   Heure début leg: {leg_start_time.strftime('%H:%M UTC')}")

                # CORRECTION: Calculer la météo au milieu du leg
                leg.calculate_all_with_timing(
                    leg_start_time=leg_start_time,
                    previous_total_time=previous_total_time,
                    previous_fuel_left=previous_fuel,
                    previous_total_fuel=previous_total_fuel,
                    fuel_burn_rate=self.aircraft.fuel_burn,
                    api_key=self.api_key
                )

                print(f"   Durée leg: {leg.time_leg:.1f} min")
                print(f"   Météo au milieu du leg: {leg.wind_dir:.0f}°/{leg.wind_speed:.0f}kn")

                # Mettre à jour l'heure pour le prochain leg
                leg_start_time += datetime.timedelta(minutes=leg.time_leg)
                print(f"   Prochaine heure début: {leg_start_time.strftime('%H:%M UTC')}")

            # Vérification carburant et ajout d'arrêts si nécessaire
            reserve_fuel = (45 / 60) * self.aircraft.fuel_burn
            if leg.fuel_left - reserve_fuel < 0:
                print(f"⛽ Carburant insuffisant, recherche aéroport de ravitaillement")
                added_wp, leg1, leg2 = aeroport_proche(leg, self.aircraft)

                if leg1 is not None:
                    print(f"   Ajout arrêt carburant: {added_wp.name}")

                    # Recalculer le premier segment
                    previous_total_time = self.legs[-1].time_tot if self.legs else 0
                    previous_total_fuel = self.legs[-1].fuel_burn_total if self.legs else 0
                    previous_fuel = self.legs[-1].fuel_left if self.legs else self.aircraft.fuel_capacity

                    leg1.calculate_all_with_timing(
                        leg_start_time=leg_start_time,
                        previous_total_time=previous_total_time,
                        previous_fuel_left=previous_fuel,
                        previous_total_fuel=previous_total_fuel,
                        fuel_burn_rate=self.aircraft.fuel_burn,
                        api_key=self.api_key
                    )

                    self.legs.append(leg1)
                    leg_start_time += datetime.timedelta(minutes=leg1.time_leg)

                    # Faire le plein
                    leg1.fuel_left = self.aircraft.fuel_capacity

                    # Recalculer le second segment
                    previous_total_time = self.legs[-1].time_tot if self.legs else 0
                    previous_total_fuel = self.legs[-1].fuel_burn_total if self.legs else 0

                    leg2.calculate_all_with_timing(
                        leg_start_time=leg_start_time,
                        previous_total_time=previous_total_time,
                        previous_fuel_left=self.aircraft.fuel_capacity,  # Plein fait
                        previous_total_fuel=previous_total_fuel,
                        fuel_burn_rate=self.aircraft.fuel_burn,
                        api_key=self.api_key
                    )

                    self.legs.append(leg2)
                    leg_start_time += datetime.timedelta(minutes=leg2.time_leg)
                else:
                    self.legs.append(leg)
            else:
                self.legs.append(leg)

        print(f"\n✅ {len(self.legs)} segments créés avec timing météo corrigé")

    def recalculate_all(self):
        """Recalculer tous les segments avec les paramètres actuels"""
        if self.legs:
            self.create_legs(recalculate=True)

    def get_departure_airport(self) -> Optional[Waypoint]:
        """Obtenir l'aéroport de départ"""
        if self.waypoints and self.waypoints[0].is_airport():
            return self.waypoints[0]
        return None

    def get_destination_airport(self) -> Optional[Waypoint]:
        """Obtenir l'aéroport de destination"""
        if self.waypoints and self.waypoints[-1].is_airport():
            return self.waypoints[-1]
        return None

    def get_summary(self) -> Dict[str, Any]:
        """Obtenir un résumé de l'itinéraire"""
        if not self.legs:
            return {
                'total_distance': 0,
                'total_time': 0,
                'total_fuel': 0,
                'num_legs': 0,
                'departure': '',
                'destination': '',
                'num_waypoints': len(self.waypoints)
            }

        total_distance = sum(leg.distance for leg in self.legs)
        total_time = self.legs[-1].time_tot
        total_fuel = self.legs[-1].fuel_burn_total

        return {
            'total_distance': total_distance,
            'total_time': total_time,
            'total_fuel': total_fuel,
            'num_legs': len(self.legs),
            'departure': self.waypoints[0].name if self.waypoints else '',
            'destination': self.waypoints[-1].name if self.waypoints else '',
            'num_waypoints': len(self.waypoints)
        }

    def get_fuel_analysis(self, reserve_minutes: float = 45) -> Dict[str, Any]:
        """
        Analyser les besoins en carburant

        Args:
            reserve_minutes: Réserve de carburant en minutes

        Returns:
            Analyse du carburant
        """
        summary = self.get_summary()

        if not self.aircraft:
            return {'error': 'Aéronef non défini'}

        route_fuel = summary['total_fuel']
        reserve_fuel = (reserve_minutes / 60) * self.aircraft.fuel_burn
        total_fuel_required = route_fuel + reserve_fuel

        return {
            'route_fuel': route_fuel,
            'reserve_fuel': reserve_fuel,
            'total_required': total_fuel_required,
            'aircraft_capacity': self.aircraft.fuel_capacity,
            'remaining': self.aircraft.fuel_capacity - total_fuel_required,
            'is_sufficient': total_fuel_required <= self.aircraft.fuel_capacity,
            'reserve_minutes': reserve_minutes
        }

    def needs_fuel_stops(self, reserve_minutes: float = 45) -> bool:
        """Vérifier si des arrêts carburant sont nécessaires"""
        fuel_analysis = self.get_fuel_analysis(reserve_minutes)
        return not fuel_analysis.get('is_sufficient', False)

    def to_dataframe(self) -> pd.DataFrame:
        """Convertir les segments en DataFrame pandas"""
        if not self.legs:
            return pd.DataFrame()

        data = [leg.to_dict() for leg in self.legs]
        return pd.DataFrame(data)

    def to_dict(self) -> Dict[str, Any]:
        """Convertir l'itinéraire complet en dictionnaire"""
        return {
            'waypoints': [wp.to_dict() for wp in self.waypoints],
            'legs': [leg.to_dict() for leg in self.legs],
            'aircraft': self.aircraft.to_dict() if self.aircraft else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'flight_info': self.flight_info,
            'summary': self.get_summary()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Itinerary':
        """Créer un Itinerary depuis un dictionnaire"""
        itinerary = cls()

        # Charger aircraft si disponible
        if data.get('aircraft'):
            itinerary.aircraft = Aircraft.from_dict(data['aircraft'])

        # Charger waypoints
        for wp_data in data.get('waypoints', []):
            waypoint = Waypoint.from_dict(wp_data)
            itinerary.waypoints.append(waypoint)

        # Charger legs si disponibles
        for leg_data in data.get('legs', []):
            leg = Leg.from_dict(leg_data)
            itinerary.legs.append(leg)

        # Charger heure de départ
        if data.get('start_time'):
            itinerary.start_time = datetime.datetime.fromisoformat(data['start_time'])

        # Charger infos de vol
        itinerary.flight_info = data.get('flight_info', {})

        return itinerary

    def get_eta_for_waypoint(self, waypoint_index: int) -> Optional[datetime.datetime]:
        """
        Obtenir l'ETA pour un waypoint spécifique

        Args:
            waypoint_index: Index du waypoint

        Returns:
            ETA ou None si impossible à calculer
        """
        if not self.start_time or waypoint_index <= 0:
            return self.start_time

        if waypoint_index > len(self.legs):
            return None

        # ETA = heure de départ + temps total du leg précédent
        leg_index = waypoint_index - 1
        if leg_index < len(self.legs):
            total_time = self.legs[leg_index].time_tot
            return self.start_time + datetime.timedelta(minutes=total_time)

        return None

    def get_flight_plan_data(self) -> Dict[str, Any]:
        """
        Obtenir les données formatées pour la génération de plan de vol

        Returns:
            Données formatées pour l'export
        """
        summary = self.get_summary()
        fuel_analysis = self.get_fuel_analysis()

        flight_data = {
            'aircraft_id': self.aircraft.registration if self.aircraft else 'N/A',
            'aircraft_type': self.aircraft.aircraft_type if self.aircraft else 'N/A',
            'tas': self.aircraft.cruise_speed if self.aircraft else 110,
            'departure': summary['departure'],
            'destination': summary['destination'],
            'date': self.flight_info.get('date', 'N/A'),
            'etd': self.flight_info.get('departure_time', 'N/A'),
            'pilot': self.flight_info.get('pilot_name', 'N/A'),
            'fuel_capacity': self.aircraft.fuel_capacity if self.aircraft else 0,
            'fuel_burn': self.aircraft.fuel_burn if self.aircraft else 7.5,
            'reserve_fuel': self.flight_info.get('reserve_time', 45),
            'weather_brief': 'Obtained via Tomorrow.io API with timing correction',
            'notam_check': 'Required',
            'flight_following': 'Recommended'
        }

        legs_data = []
        for i, leg in enumerate(self.legs):
            leg_dict = leg.to_dict()

            # Calculer ETA
            eta = self.get_eta_for_waypoint(i + 1)
            eta_str = eta.strftime("%H:%M") if eta else "N/A"

            leg_data = {
                'from': leg_dict['Starting WP'],
                'to': leg_dict['Ending WP'],
                'distance': leg_dict['Distance (NM)'],
                'true_course': leg_dict['True course (deg)'],
                'true_heading': leg_dict['True heading (deg)'],
                'mag_heading': leg_dict['Magnetic heading (deg)'],
                'wind_dir': leg_dict['Wind Direction (deg)'],
                'wind_speed': leg_dict['Wind Speed (kn)'],
                'ground_speed': leg_dict['Groundspeed (kn)'],
                'leg_time': leg_dict['Leg time (min)'],
                'total_time': leg_dict['Total time (min)'],
                'fuel_leg': leg_dict['Fuel burn leg (gal)'],
                'fuel_total': leg_dict['Fuel burn tot (gal)'],
                'fuel_left': leg_dict['Fuel left (gal)'],
                'eta': eta_str,
                'remarks': f"Wind @ midpoint: {leg_dict['Wind Direction (deg)']}°/{leg_dict['Wind Speed (kn)']}kn",
                'weather_time': leg_dict.get('Time start', 'N/A')
            }
            legs_data.append(leg_data)

        return flight_data, legs_data

    def __len__(self) -> int:
        """Nombre de waypoints"""
        return len(self.waypoints)

    def __str__(self) -> str:
        summary = self.get_summary()
        return (f"Itinéraire: {summary['departure']} → {summary['destination']} "
                f"({summary['total_distance']:.1f}NM, {summary['total_time']:.0f}min)")

    def __repr__(self) -> str:
        return f"Itinerary(waypoints={len(self.waypoints)}, legs={len(self.legs)})"


# Fonctions utilitaires pour créer des itinéraires

def create_itinerary_from_gui(waypoints: List[Dict], aircraft_params: Dict,
                              flight_params: Dict, api_key: str = None) -> Itinerary:
    """
    Créer un itinéraire depuis les données de l'interface GUI avec timing corrigé

    Args:
        waypoints: Liste de {'name': str, 'lat': float, 'lon': float}
        aircraft_params: {'tas': float, 'fuel_burn': float, etc.}
        flight_params: {'date': str, 'departure_time': str, etc.}
        api_key: Clé API météo

    Returns:
        Itinéraire configuré avec timing météo corrigé
    """
    print(f"🔧 Création itinéraire GUI avec flight_params: {flight_params}")

    # Créer l'aéronef
    aircraft = Aircraft(
        cruise_speed=aircraft_params.get('tas', 110),
        fuel_burn=aircraft_params.get('fuel_burn', 7.5),
        fuel_capacity=aircraft_params.get('fuel_capacity', 40),
        registration=aircraft_params.get('registration', ''),
        aircraft_type=aircraft_params.get('aircraft_type', '')
    )

    # Créer l'itinéraire
    itinerary = Itinerary(aircraft)

    # Ajouter waypoints
    for wp_data in waypoints:
        waypoint = Waypoint(
            lat=wp_data['lat'],
            lon=wp_data['lon'],
            name=wp_data['name'],
            waypoint_type=wp_data.get('type', 'custom'),
            info=wp_data.get('info', {})
        )
        itinerary.add_waypoint(waypoint)

    # CORRECTION: Utiliser les informations de vol pour définir l'heure de départ
    itinerary.set_flight_info(flight_params)

    # Configurer API météo
    if api_key:
        itinerary.set_api_key(api_key)

    print(f"🕐 Heure de départ configurée: {itinerary.start_time}")

    # Créer les segments avec timing corrigé
    itinerary.create_legs()

    return itinerary