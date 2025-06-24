"""
Utilitaires pour VFR Planner
"""

from .constants import (
    # Constantes de navigation
    EARTH_RADIUS_KM, EARTH_RADIUS_NM, NM_TO_KM, KM_TO_NM,

    # Constantes météo
    VFR_MIN_VISIBILITY_KM, VFR_MIN_CEILING_FEET, WEATHER_CODES, WEATHER_ALERTS,

    # Types d'aéroports
    AIRPORT_TYPES, AIRPORT_TYPE_LABELS, PRIORITY_COUNTRIES, COUNTRY_NAMES,

    # Paramètres par défaut
    DEFAULT_AIRCRAFT_PARAMS, DEFAULT_FLIGHT_PARAMS,

    # Configuration interface
    GUI_DEFAULTS, COLORS, MAP_ICONS,

    # Messages
    ERROR_MESSAGES, STATUS_MESSAGES,

    # Validation
    VALIDATION_LIMITS, CALCULATION_DEFAULTS
)

__all__ = [
    # Constantes de navigation
    'EARTH_RADIUS_KM', 'EARTH_RADIUS_NM', 'NM_TO_KM', 'KM_TO_NM',

    # Constantes météo
    'VFR_MIN_VISIBILITY_KM', 'VFR_MIN_CEILING_FEET', 'WEATHER_CODES', 'WEATHER_ALERTS',

    # Types d'aéroports
    'AIRPORT_TYPES', 'AIRPORT_TYPE_LABELS', 'PRIORITY_COUNTRIES', 'COUNTRY_NAMES',

    # Paramètres par défaut
    'DEFAULT_AIRCRAFT_PARAMS', 'DEFAULT_FLIGHT_PARAMS',

    # Configuration interface
    'GUI_DEFAULTS', 'COLORS', 'MAP_ICONS',

    # Messages
    'ERROR_MESSAGES', 'STATUS_MESSAGES',

    # Validation
    'VALIDATION_LIMITS', 'CALCULATION_DEFAULTS'
]