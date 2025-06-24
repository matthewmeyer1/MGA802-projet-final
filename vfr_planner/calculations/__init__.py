"""
Calculs pour la navigation et la météorologie
"""

from .navigation import (
    NavigationCalculator, nav_calc,
    calculate_distance, calculate_bearing, calculate_wind_correction, true_to_magnetic
)
from .weather import (
    WeatherService, weather_service,
    get_weather_for_leg, get_weather_summary, check_vfr_conditions
)

__all__ = [
    'NavigationCalculator',
    'nav_calc',
    'calculate_distance',
    'calculate_bearing',
    'calculate_wind_correction',
    'true_to_magnetic',
    'WeatherService',
    'weather_service',
    'get_weather_for_leg',
    'get_weather_summary',
    'check_vfr_conditions'
]