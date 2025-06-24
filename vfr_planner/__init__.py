"""
Outil de planification de vol VFR
Projet MGA802-01

Package principal pour la planification de vols VFR.
"""

__version__ = "1.0.0"
__author__ = "Antoine Gingras, Matthew Meyer, Richard Nguekam, Gabriel Wong-Lapierre"
__description__ = "Outil de planification de vol VFR pour pilotes privés"

# Imports principaux pour faciliter l'utilisation
from .models.aircraft import Aircraft
from .models.waypoint import Waypoint
from .models.leg import Leg
from .models.itinerary import Itinerary

__all__ = [
    'Aircraft',
    'Waypoint', 
    'Leg',
    'Itinerary'
]