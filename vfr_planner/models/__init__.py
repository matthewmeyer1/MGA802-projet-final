"""
Modèles de données pour la planification VFR
"""

from .aircraft import Aircraft, get_aircraft_preset, list_aircraft_presets, AIRCRAFT_PRESETS
from .waypoint import Waypoint, create_waypoint_from_coordinates, create_waypoint_from_dms
from .leg import Leg
from .itinerary import Itinerary, create_itinerary_from_gui

__all__ = [
    'Aircraft',
    'Waypoint',
    'Leg',
    'Itinerary',
    'get_aircraft_preset',
    'list_aircraft_presets',
    'AIRCRAFT_PRESETS',
    'create_waypoint_from_coordinates',
    'create_waypoint_from_dms',
    'create_itinerary_from_gui'
]