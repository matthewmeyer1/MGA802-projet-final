from . import nav_calc
from ..data import airport_db
from .navigation import calculate_distance
from ..models.leg import Leg
from ..models.waypoint import Waypoint

def aeroport_proche(leg, aircraft):
    """
    Finds the closest airport.

    :param leg: The first number.
    :type leg: int
    :param aircraft: The second number.
    :type aircraft: int
    :return: None
    :rtype: None
    """
    start_wp = leg.starting_wp
    end_wp = leg.ending_wp

    lat_start_wp = start_wp.lat
    lon_start_wp = start_wp.lon

    lat_end_wp = end_wp.lat
    lon_end_wp = end_wp.lon
    fuel_start_leg = leg.fuel_left + leg.fuel_burn_leg

    reserve_fuel = (45 / 60) * aircraft.fuel_burn
    autonomy_from_start_wp = (aircraft.fuel_capacity - (fuel_start_leg + reserve_fuel)) / aircraft.fuel_burn * aircraft.cruise_speed

    print(f"Max distance before refuel: {autonomy_from_start_wp}")
    print(f"og distance {leg.distance}")

    airports = airport_db.get_airports_near_point(lat_start_wp, lon_start_wp, autonomy_from_start_wp)
    for a in airports:
        print(a['icao'], a['lat'], a['lon'])
        ap_lat = a['lat']
        ap_lon = a['lon']

        leg1 = Leg(Waypoint(lat_start_wp, lon_start_wp, name=start_wp.name), Waypoint(ap_lat, ap_lon, name=a['icao']), tas=aircraft.cruise_speed)
        leg2 = Leg(Waypoint(ap_lat, ap_lon, name=a['icao']), Waypoint(lat_end_wp, lon_end_wp, name=end_wp.name), tas=aircraft.cruise_speed)

        print(f"Distance à l'aéroport: {leg1.distance}, distance totale ajoutée: {leg1.distance + leg2.distance - leg.distance}")
        wp = Waypoint(ap_lat, ap_lon, name=a['icao'])
        return wp, leg1, leg2

    return None, None, None
