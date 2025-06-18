# fuel_management.py
"""
Module de gestion du carburant et des ravitaillements pour la planification de vol VFR
"""

import math
from typing import List, Dict, Tuple, Optional
from geopy.distance import geodesic
import pandas as pd


class FuelManager:
    """Gestionnaire de carburant et ravitaillements"""

    def __init__(self, airport_db):
        self.airport_db = airport_db

        # Réglementation canadienne VFR
        self.VFR_RESERVE_DAY = 30  # minutes
        self.VFR_RESERVE_NIGHT = 45  # minutes
        self.SAFETY_MARGIN = 0.15  # 15% de marge additionnelle

        # Paramètres de recherche
        self.MAX_DETOUR_FACTOR = 1.2  # Détour max 20% de la distance directe
        self.MAX_SEARCH_RADIUS_NM = 50  # Rayon de recherche initial

    def calculate_fuel_requirements(self, distance_nm: float, tas: float, fuel_burn_gph: float,
                                    reserve_minutes: float = 45) -> Dict[str, float]:
        """
        Calculer les besoins en carburant pour un segment

        Args:
            distance_nm: Distance en milles nautiques
            tas: True Air Speed en noeuds
            fuel_burn_gph: Consommation en gallons/heure
            reserve_minutes: Réserve réglementaire en minutes

        Returns:
            Dictionnaire avec les calculs de carburant
        """
        # Temps de vol en heures
        flight_time_hours = distance_nm / tas

        # Carburant pour le segment
        fuel_segment = flight_time_hours * fuel_burn_gph

        # Carburant de réserve
        fuel_reserve = (reserve_minutes / 60) * fuel_burn_gph

        # Marge de sécurité
        fuel_safety = fuel_segment * self.SAFETY_MARGIN

        # Total requis
        fuel_total_required = fuel_segment + fuel_reserve + fuel_safety

        return {
            'segment_fuel': fuel_segment,
            'reserve_fuel': fuel_reserve,
            'safety_fuel': fuel_safety,
            'total_required': fuel_total_required,
            'flight_time_hours': flight_time_hours
        }

    def calculate_range(self, fuel_available_gal: float, fuel_burn_gph: float,
                        tas: float, reserve_minutes: float = 45) -> float:
        """
        Calculer l'autonomie en distance avec le carburant disponible

        Args:
            fuel_available_gal: Carburant disponible en gallons
            fuel_burn_gph: Consommation en gallons/heure
            tas: Vitesse vraie en noeuds
            reserve_minutes: Réserve réglementaire

        Returns:
            Distance maximale en NM
        """
        # Soustraire les réserves et marges
        fuel_reserve = (reserve_minutes / 60) * fuel_burn_gph
        fuel_usable = fuel_available_gal - fuel_reserve

        # Appliquer marge de sécurité
        fuel_usable *= (1 - self.SAFETY_MARGIN)

        if fuel_usable <= 0:
            return 0

        # Temps de vol disponible
        flight_time_hours = fuel_usable / fuel_burn_gph

        # Distance maximale
        max_range_nm = flight_time_hours * tas

        return max_range_nm

    def find_fuel_stops(self, waypoints: List[Dict], aircraft_params: Dict) -> List[Dict]:
        """
        Trouver les arrêts de ravitaillement nécessaires

        Args:
            waypoints: Liste des waypoints du vol
            aircraft_params: Paramètres de l'avion (fuel_capacity, fuel_burn, tas)

        Returns:
            Liste des arrêts de ravitaillement proposés
        """
        fuel_stops = []
        current_fuel = aircraft_params['fuel_capacity']
        fuel_burn = aircraft_params['fuel_burn']
        tas = aircraft_params['tas']

        # Analyser chaque segment
        for i in range(len(waypoints) - 1):
            wp1 = waypoints[i]
            wp2 = waypoints[i + 1]

            # Distance du segment
            distance = self._calculate_distance(wp1['lat'], wp1['lon'],
                                                wp2['lat'], wp2['lon'])

            # Besoins en carburant
            fuel_req = self.calculate_fuel_requirements(distance, tas, fuel_burn)

            # Vérifier si on peut faire le segment
            if fuel_req['total_required'] > current_fuel:
                # Chercher un aéroport de ravitaillement
                fuel_stop = self._find_best_fuel_stop(wp1, wp2, current_fuel,
                                                      aircraft_params)
                if fuel_stop:
                    fuel_stops.append({
                        'after_waypoint': i,
                        'airport': fuel_stop,
                        'reason': f"Carburant insuffisant pour {wp2['name']}"
                    })
                    # Réinitialiser le carburant après ravitaillement
                    current_fuel = aircraft_params['fuel_capacity']
                else:
                    # Aucun aéroport trouvé - vol impossible
                    fuel_stops.append({
                        'after_waypoint': i,
                        'airport': None,
                        'reason': f"ATTENTION: Aucun aéroport de ravitaillement trouvé!"
                    })

            # Déduire le carburant utilisé
            current_fuel -= fuel_req['segment_fuel']

        return fuel_stops

    def _find_best_fuel_stop(self, wp1: Dict, wp2: Dict, current_fuel: float,
                             aircraft_params: Dict) -> Optional[Dict]:
        """
        Trouver le meilleur aéroport de ravitaillement entre deux waypoints

        Args:
            wp1, wp2: Waypoints de départ et d'arrivée
            current_fuel: Carburant disponible
            aircraft_params: Paramètres avion

        Returns:
            Meilleur aéroport ou None
        """
        # Calculer l'autonomie actuelle
        max_range = self.calculate_range(current_fuel, aircraft_params['fuel_burn'],
                                         aircraft_params['tas'])

        # Distance directe
        direct_distance = self._calculate_distance(wp1['lat'], wp1['lon'],
                                                   wp2['lat'], wp2['lon'])

        # Chercher les aéroports dans la zone
        candidates = self._find_airports_in_corridor(wp1, wp2, max_range)

        # Filtrer et scorer les candidats
        best_score = float('inf')
        best_airport = None

        for airport in candidates:
            # Vérifier que l'aéroport a du carburant (type approprié)
            if not self._has_fuel_service(airport):
                continue

            # Calculer les distances
            dist1 = self._calculate_distance(wp1['lat'], wp1['lon'],
                                             airport['lat'], airport['lon'])
            dist2 = self._calculate_distance(airport['lat'], airport['lon'],
                                             wp2['lat'], wp2['lon'])

            # Vérifier l'accessibilité
            if dist1 > max_range * 0.9:  # Garder 10% de marge
                continue

            # Calculer le détour
            total_distance = dist1 + dist2
            detour_factor = total_distance / direct_distance

            if detour_factor > self.MAX_DETOUR_FACTOR:
                continue

            # Score (privilégier moins de détour et aéroports plus grands)
            airport_type_score = self._get_airport_type_score(airport['type'])
            score = detour_factor * airport_type_score

            if score < best_score:
                best_score = score
                best_airport = airport

        return best_airport

    def _find_airports_in_corridor(self, wp1: Dict, wp2: Dict,
                                   max_range: float) -> List[Dict]:
        """
        Trouver les aéroports dans le corridor entre deux waypoints

        Args:
            wp1, wp2: Waypoints définissant le corridor
            max_range: Distance maximale depuis wp1

        Returns:
            Liste d'aéroports candidats
        """
        candidates = []

        # Centre du corridor
        center_lat = (wp1['lat'] + wp2['lat']) / 2
        center_lon = (wp1['lon'] + wp2['lon']) / 2

        # Rayon de recherche (basé sur la distance entre waypoints)
        corridor_length = self._calculate_distance(wp1['lat'], wp1['lon'],
                                                   wp2['lat'], wp2['lon'])
        search_radius = min(corridor_length / 2 + 50, 150)  # Max 150 NM

        # Rechercher dans la base de données
        if self.airport_db.filtered_airports is not None:
            for _, airport in self.airport_db.filtered_airports.iterrows():
                # Distance depuis le centre
                dist_from_center = self._calculate_distance(
                    center_lat, center_lon,
                    airport['latitude_deg'], airport['longitude_deg']
                )

                if dist_from_center <= search_radius:
                    # Convertir en format dict
                    airport_dict = {
                        'icao': airport['icao_code'] if airport['icao_code'] else airport['ident'],
                        'name': airport['name'],
                        'lat': airport['latitude_deg'],
                        'lon': airport['longitude_deg'],
                        'type': airport['type'],
                        'city': airport['municipality']
                    }
                    candidates.append(airport_dict)

        return candidates

    def _calculate_distance(self, lat1: float, lon1: float,
                            lat2: float, lon2: float) -> float:
        """Calculer distance en milles nautiques"""
        try:
            return geodesic((lat1, lon1), (lat2, lon2)).nm
        except:
            # Formule haversine si geodesic échoue
            R = 6371.0  # km
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)

            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad

            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            return R * c / 1.852  # km to nm

    def _has_fuel_service(self, airport: Dict) -> bool:
        """
        Vérifier si un aéroport a du service de carburant
        Basé sur le type d'aéroport et d'autres critères
        """
        # Types d'aéroports avec carburant probable
        fuel_types = ['large_airport', 'medium_airport']

        # Certains petits aéroports ont aussi du carburant
        if airport['type'] == 'small_airport':
            # Vérifier si c'est un aéroport avec code ICAO (plus probable d'avoir du service)
            if airport.get('icao') and len(airport['icao']) == 4:
                return True

        return airport['type'] in fuel_types

    def _get_airport_type_score(self, airport_type: str) -> float:
        """
        Score basé sur le type d'aéroport
        Plus petit score = meilleur
        """
        scores = {
            'large_airport': 1.0,
            'medium_airport': 1.5,
            'small_airport': 2.0,
            'heliport': 5.0,
            'seaplane_base': 3.0,
            'closed': 10.0
        }
        return scores.get(airport_type, 5.0)

    def optimize_route_with_fuel_stops(self, waypoints: List[Dict],
                                       aircraft_params: Dict) -> Tuple[List[Dict], List[str]]:
        """
        Optimiser la route avec les arrêts de ravitaillement

        Args:
            waypoints: Liste originale des waypoints
            aircraft_params: Paramètres avion

        Returns:
            Tuple (nouvelle liste de waypoints, liste de messages)
        """
        messages = []
        fuel_stops = self.find_fuel_stops(waypoints, aircraft_params)

        if not fuel_stops:
            messages.append("✅ Aucun ravitaillement nécessaire - autonomie suffisante")
            return waypoints, messages

        # Créer nouvelle liste avec arrêts
        new_waypoints = []
        wp_index = 0

        for i, wp in enumerate(waypoints):
            new_waypoints.append(wp)

            # Vérifier s'il faut ajouter un arrêt après ce waypoint
            for stop in fuel_stops:
                if stop['after_waypoint'] == i and stop['airport']:
                    airport = stop['airport']
                    fuel_wp = {
                        'name': f"FUEL-{airport['icao']}",
                        'lat': airport['lat'],
                        'lon': airport['lon'],
                        'type': 'fuel_stop',
                        'info': airport
                    }
                    new_waypoints.append(fuel_wp)
                    messages.append(f"⛽ Ravitaillement ajouté: {airport['icao']} - {airport['name']}")
                elif stop['after_waypoint'] == i and not stop['airport']:
                    messages.append(f"⚠️ {stop['reason']}")

        return new_waypoints, messages

    def generate_fuel_report(self, waypoints: List[Dict], legs_data: List[Dict],
                             aircraft_params: Dict) -> str:
        """
        Générer un rapport détaillé sur le carburant

        Args:
            waypoints: Liste des waypoints
            legs_data: Données des segments calculés
            aircraft_params: Paramètres avion

        Returns:
            Rapport formaté
        """
        report = "RAPPORT DE GESTION DU CARBURANT\n"
        report += "=" * 50 + "\n\n"

        # Paramètres avion
        report += f"Capacité réservoir: {aircraft_params.get('fuel_capacity', 0):.1f} gallons\n"
        report += f"Consommation: {aircraft_params.get('fuel_burn', 0):.1f} GPH\n"
        report += f"Vitesse de croisière: {aircraft_params.get('tas', 0):.0f} noeuds\n\n"

        # Analyse par segment
        report += "ANALYSE PAR SEGMENT:\n"
        report += "-" * 40 + "\n"

        fuel_remaining = aircraft_params.get('fuel_capacity', 0)

        for i, leg in enumerate(legs_data):
            report += f"\nSegment {i + 1}: {leg.get('from', '')} → {leg.get('to', '')}\n"
            report += f"  Distance: {leg.get('distance', 0):.1f} NM\n"
            report += f"  Temps: {leg.get('leg_time', 0):.0f} min\n"
            report += f"  Carburant requis: {leg.get('fuel_leg', 0):.1f} gal\n"

            fuel_remaining -= leg.get('fuel_leg', 0)
            report += f"  Carburant restant: {fuel_remaining:.1f} gal\n"

            # Vérifier les marges
            if fuel_remaining < 10:
                report += f"  ⚠️ ATTENTION: Carburant faible!\n"

            # Si c'est un arrêt carburant
            if 'FUEL-' in leg.get('to', ''):
                fuel_remaining = aircraft_params.get('fuel_capacity', 0)
                report += f"  ⛽ RAVITAILLEMENT - Plein fait\n"

        # Résumé
        report += "\n" + "=" * 50 + "\n"
        report += "RÉSUMÉ:\n"

        total_fuel = sum(leg.get('fuel_leg', 0) for leg in legs_data)
        report += f"Carburant total requis: {total_fuel:.1f} gallons\n"

        # Nombre de ravitaillements
        fuel_stops = sum(1 for leg in legs_data if 'FUEL-' in leg.get('to', ''))
        report += f"Ravitaillements nécessaires: {fuel_stops}\n"

        # Autonomie maximale
        max_range = self.calculate_range(aircraft_params.get('fuel_capacity', 0),
                                         aircraft_params.get('fuel_burn', 7.5),
                                         aircraft_params.get('tas', 110))
        report += f"Autonomie maximale: {max_range:.0f} NM\n"

        return report