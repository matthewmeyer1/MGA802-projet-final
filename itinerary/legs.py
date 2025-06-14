import math
from geopy.distance import geodesic
import requests
import json
import datetime



class Leg:

    def __init__(self, starting_wp, ending_wp, name=""):
        self.starting_wp = starting_wp
        self.ending_wp = ending_wp
        self.distance = self.calc_dist()
        self.tc = self.calc_tc()
        self.wind_dir = 0
        self.wind_speed = 0
        self.time_start = 0


        if name=="":
            self.name = self.starting_wp.name
        else:
            self.name = name



    def calc_dist(self):
        return geodesic((self.starting_wp.lat, self.starting_wp.lon), (self.ending_wp.lat, self.ending_wp.lon)).nm

    def calc_tc(self):
        lat1 = math.radians(self.starting_wp.lat)
        lat2 = math.radians(self.ending_wp.lat)


        del_lon = math.radians(self.ending_wp.lon) - math.radians(self.starting_wp.lon)
        y = math.sin(del_lon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(del_lon)
        brng = math.atan2(y, x)
        brng = math.degrees(brng)
        return (brng + 360) % 360

    def calc_wind(self, time):
        url = ("https://api.tomorrow.io/v4/weather/forecast?location=" + str((self.ending_wp.lat + self.starting_wp.lat) / 2) +
               "%2C%20" + str((self.ending_wp.lon + self.starting_wp.lon) / 2) + "&timesteps=hourly&apikey=CmIKizbzjlLBf8XngqoIAU271bBYNZbk")
        print(url)
        headers = {
            "accept": "application/json",
            "accept-encoding": "deflate, gzip, br"
        }


        response = requests.get(url, headers=headers)
        json_str = json.loads(response.text)
        for x in json_str["timelines"]["hourly"]:
            if x["time"] == "2025-" + str(time.month).zfill(2) + "-" + str(time.day).zfill(2) + "T" + str(time.hour).zfill(2) + ":00:00Z":
                self.time_start = x["time"]
                self.wind_dir = x["values"]["windDirection"]
                self.wind_speed = x["values"]["windSpeed"]

    def to_dict(self):
        return {'Starting WP': self.starting_wp.name,
               'Ending WP': self.ending_wp.name,
               'Distance (NM)': self.distance,
               'True course (deg)': self.tc,
               'Time start': self.time_start,
               'Wind Direction': self.wind_dir,
               'Wind Speed': self.wind_speed}