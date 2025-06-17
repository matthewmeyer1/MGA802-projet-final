from itinerary.itinerary import Itinerary
from .legs import Leg
from geopy.distance import geodesic



def calc_dist(self):
    return geodesic((self.starting_wp.lat, self.starting_wp.lon), (self.ending_wp.lat, self.ending_wp.lon)).nm

def calculate_distance(wp, airport, next_wp):

    return


